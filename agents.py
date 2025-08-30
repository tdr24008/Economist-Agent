# agents.py
from __future__ import annotations

import os
import re
import sys
import asyncio
import subprocess
import tempfile
import textwrap
from typing import List, Tuple, Dict, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


# ----------------------------
# Model client (Ollama local)
# ----------------------------
# Tip: pull a small/quantized model for CPU:
#   ollama pull qwen2.5:3b-instruct-q4_K_M
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL_NAME = "qwen2.5:3b-instruct-q4_K_M"

model_client = OllamaChatCompletionClient(
    model=MODEL_NAME,
    host=OLLAMA_HOST,  # must match your running ollama host/port
)


# -----------------------------------------
# Economist-tuned Data Analyst (no tools)
# -----------------------------------------
ECON_SYSTEM = """
You are an economist. First write a concise pre-analysis plan (outcomes, sample,
controls, fixed effects, hypotheses, robustness). Then output ONE executable Python block:

```python
# Only read from DATA_DIR and write to OUT_DIR
import pandas as pd, duckdb as ddb
# your analysis...
```

Rules: no network/system calls; no I/O outside DATA_DIR/OUT_DIR; keep models parsimonious;
report diagnostics (SEs, R², units); if data is insufficient, say so and propose next steps.
""".strip()

DataAnalyst = AssistantAgent(
    name="data_analyst",
    model_client=model_client,
    system_message=ECON_SYSTEM,
    reflect_on_tool_use=False,
    model_client_stream=False,  # set True if you implement streaming in the UI
)


# -----------------------------------------
# Fenced-code extraction (```python ... ```)
# -----------------------------------------
CODE_FENCE_RE = re.compile(r"```python\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_fenced_python(text: str) -> List[str]:
    """Return the contents of all fenced ```python blocks in text."""
    return [m.group(1).strip() for m in CODE_FENCE_RE.finditer(text or "")]


# ---------------------------------------------------------
# Safe(ish) runner (no Docker yet): separate subprocess
# ---------------------------------------------------------
# Blocks obvious exfil / system ops. Tighten as needed.
BLOCKED_TOKENS = [
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "curl",
    "import os",
    "from os",
    "shutil.rmtree",
    "sys.exit",
    "pip ",
    "conda ",
    "eval(",
    "exec(",
    "__import__",
    "pathlib.Path.home(",
    "open('/",
    "open(\"/",
]


def run_python_in_subprocess(code: str, data_dir: str, out_dir: str, timeout_s: int = 90) -> Tuple[bool, str]:
    """
    Execute the provided Python code in a fresh process with basic file-IO guards.
    Only DATA_DIR and OUT_DIR are readable/writable.
    Returns (ok, combined_stdout_stderr).
    """
    low = code.lower()
    for bad in BLOCKED_TOKENS:
        if bad in low:
            return False, f"Execution blocked: disallowed token -> {bad}"

    # Wrap the agent code to inject DATA_DIR/OUT_DIR and guard open()
    wrapped = textwrap.dedent(f"""
        import builtins, pathlib

        DATA_DIR = pathlib.Path(r"{data_dir}").resolve()
        OUT_DIR  = pathlib.Path(r"{out_dir}").resolve()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        _open = builtins.open
        def _safe_open(*a, **k):
            p = pathlib.Path(a[0]).resolve() if a else None
            if p and not (str(p).startswith(str(DATA_DIR)) or str(p).startswith(str(OUT_DIR))):
                raise PermissionError("Blocked file access outside DATA_DIR/OUT_DIR")
            return _open(*a, **k)
        builtins.open = _safe_open

        # --- agent code ---
        {code}
    """).strip()

    # Write to a temp file to avoid shell quoting issues
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(wrapped)
        tmp = tf.name

    try:
        # Minimal environment: strip proxy vars etc.
        env = {k: v for k, v in os.environ.items() if k.lower() not in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")}
        p = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=timeout_s, env=env)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        ok = (p.returncode == 0)
        report = f"[stdout]\\n{out}\\n\\n[stderr]\\n{err}"
        return ok, report
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout_s}s."
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass


# ---------------------------------------------------------
# Code Executor Agent (wrapper around the safe runner)
# ---------------------------------------------------------
class CodeExecutorAgent:
    """Minimal 'agent' that only executes fenced python blocks."""
    name: str = "code_executor"

    def run(self, task: str, data_dir: str, out_dir: str, timeout_s: int = 90) -> Dict[str, Any]:
        blocks = extract_fenced_python(task)
        if not blocks:
            return {"ran": False, "ok": False, "result": "No fenced ```python``` block found.", "num_blocks": 0}
        ok, report = run_python_in_subprocess(blocks[0], data_dir, out_dir, timeout_s=timeout_s)
        return {"ran": True, "ok": ok, "result": report, "num_blocks": len(blocks)}


CodeExecutor = CodeExecutorAgent()


# ---------------------------------------------------------
# Synchronous helpers for Streamlit to call
# ---------------------------------------------------------
async def _run_analyst_async(task: str) -> str:
    """
    Run the DataAnalyst agent asynchronously; return the last non-empty string message.
    """
    result = await DataAnalyst.run(task=task)  # TaskResult with .messages
    msgs = getattr(result, "messages", []) or []
    for m in reversed(msgs):
        content = getattr(m, "content", None)
        if isinstance(content, str) and content.strip():
            return content
    return "(No model reply.)"


def analyst_reply(user_text: str) -> str:
    """
    Synchronous wrapper for Streamlit: returns the agent's reply (plan + code block).
    """
    try:
        return asyncio.run(_run_analyst_async(user_text))
    except RuntimeError:
        # Fallback if an event loop already runs in the environment
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run_analyst_async(user_text))
        finally:
            loop.close()


def maybe_execute_fenced_code(analyst_text: str, data_dir: str, out_dir: str) -> dict:
    """
    Backwards-compatible helper: execute the FIRST fenced block in analyst_text.
    """
    return CodeExecutor.run(analyst_text, data_dir=data_dir, out_dir=out_dir, timeout_s=90)


# ---------------------------------------------------------
# Orchestrator: plan with analyst, then execute code
# ---------------------------------------------------------
async def _plan_and_execute_async(user_text: str, data_dir: str, out_dir: str) -> Dict[str, Any]:
    analyst_text = await _run_analyst_async(user_text)
    exec_res = CodeExecutor.run(analyst_text, data_dir=data_dir, out_dir=out_dir, timeout_s=90)
    return {"analyst_text": analyst_text, "exec": exec_res}


def plan_and_execute(user_text: str, data_dir: str, out_dir: str) -> Dict[str, Any]:
    """
    Synchronous wrapper that returns:
      { 'analyst_text': str, 'exec': {'ran':..., 'ok':..., 'result':..., 'num_blocks':...} }
    """
    try:
        return asyncio.run(_plan_and_execute_async(user_text, data_dir, out_dir))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_plan_and_execute_async(user_text, data_dir, out_dir))
        finally:
            loop.close()
            