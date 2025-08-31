from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient


# ----------------------------
# Model client (Ollama local)
# ----------------------------
# Tip: pull a small/quantized model for CPU:
#   ollama pull qwen2.5:3b-instruct-q4_K_M
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL_NAME = "llama3.1:8b"

model_client = OllamaChatCompletionClient(
    model=MODEL_NAME,
    host=OLLAMA_HOST,
)

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

def build_data_analyst(tools:list) -> AssistantAgent:
    DataAnalyst = AssistantAgent(
        name="data_analyst",
        model_client=model_client,
        tools=tools,
        system_message=ECON_SYSTEM,
        reflect_on_tool_use=False,
        model_client_stream=False,  # set True if you implement streaming in the UI
    )

    return DataAnalyst
