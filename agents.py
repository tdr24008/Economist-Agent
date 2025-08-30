from __future__ import annotations

import os
import re
import sys
import subprocess
import textwrap
import tempfile
from typing import List, Tuple

from autogen import AssistantAgent

# Configuration for local Ollama (OpenAI-compatible)
LLM_CFG = {
    "config_list": [{
        "model": "llama3.1",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }],
    "temperature": 0.2,
    "timeout": 120,
}

ECON_SYSTEM = """
You are an economist. Produce a pre-analysis plan (outcomes, sample,
controls, fixed effects, hypotheses, robustness checks).

Then propose executable Python in ONE fenced block:

```python
# REQUIRED: write results to OUT_DIR and only read from DATA_DIR
import pandas as pd, duckdb as ddb
# your code...

Rules: no network/system calls; no I/O outside DATA_DIR/OUT_DIR.
Prefer parsimonious specs; report diagnostics (SEs, R2, units).
If data is insufficient, say so and propose next steps.
"""

DataAnalyst = AssistantAgent(
    name="data_analyst",
    llm_config=LLM_CFG,
    system_message=ECON_SYSTEM.strip(),
)

CODE_FENCE_RE = re.compile(r"python\s*(.*?)", re.DOTALL | re.IGNORECASE)

def extract_fenced_python(text: str) -> List[str]:
    """Return the contents of all fenced ```python blocks in text."""
    return [m.group(1).strip() for m in CODE_FENCE_RE.finditer(text or "")]

BLOCKED_TOKENS = [
    "subprocess", "socket", "requests", "urllib", "curl",
    "import os", "from os", "shutil.rmtree", "sys.exit",
    "pip ", "conda ", "eval(", "exec(", "__import__",
    "pathlib.Path.home(", "open('/", "open(\"/",
]

def run_python_in_subprocess(code: str, data_dir: str, out_dir: str,
                             timeout_s: int = 90) -> Tuple[bool, str]:
    """Execute code in a fresh Python process with file guards."""
    low = code.lower()
    for bad in BLOCKED_TOKENS:
        if bad in low:
            return False, f"Execution blocked: disallowed token -> {bad}"

    wrapped = textwrap.dedent(f"""
        import sys, pathlib, builtins
        DATA_DIR = pathlib.Path(r"{data_dir}").resolve()
        OUT_DIR  = pathlib.Path(r"{out_dir}").resolve()
        OUT_DIR.mkdir(parents=True, exist_ok=True)

        _open = builtins.open
        def _safe_open(*a, **k):
            p = pathlib.Path(a[0]).resolve() if a else None
            if p and not (str(p).startswith(str(DATA_DIR)) or
                          str(p).startswith(str(OUT_DIR))):
                raise PermissionError("Blocked file access outside DATA_DIR/OUT_DIR")
            return _open(*a, **k)
        builtins.open = _safe_open

        # --- agent code ---
        {code}
    """).strip()

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(wrapped)
        tmp = tf.name

    try:
        env = {k: v for k, v in os.environ.items()
               if k.lower() not in ("http_proxy", "https_proxy", "all_proxy", "no_proxy")}
        p = subprocess.run([sys.executable, tmp],
                           capture_output=True, text=True, timeout=timeout_s, env=env)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        ok = (p.returncode == 0)
        report = f"[stdout]\n{out}\n\n[stderr]\n{err}"
        return ok, report
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout_s}s."
    finally:
        try:
            os.remove(tmp)
        except Exception:
            pass

def analyst_reply(user_text: str) -> str:
    """Ask the analyst for plan + code; returns assistant text or error."""
    try:
        resp = DataAnalyst.generate_reply(messages=[{"role": "user", "content": user_text}])
        return resp if (resp and resp.strip()) else "(No model reply.)"
    except Exception as e:
        return f"(Model unavailable: {e})"

def maybe_execute_fenced_code(analyst_text: str, data_dir: str, out_dir: str) -> dict:
    """Run first fenced block if present; returns dict with status."""
    blocks = extract_fenced_python(analyst_text)
    if not blocks:
        return {
            "ran": False,
            "ok": False,
            "result": "No fenced ```python``` block found.",
            "num_blocks": 0
        }
    ok, report = run_python_in_subprocess(blocks[0], data_dir, out_dir, timeout_s=90)
    return {
        "ran": True,
        "ok": ok,
        "result": report,
        "num_blocks": len(blocks)
    }