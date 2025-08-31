import pandas as pd
from langchain_experimental.tools import PythonAstREPLTool
from autogen_ext.tools.langchain import LangChainToolAdapter

# ------------- Utility: Load CSV robustly -------------
def load_financial_csv(path_or_url: str) -> pd.DataFrame:
    df = pd.read_csv(path_or_url)
    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    # Detect a datetime column
    ts_col = None
    for cand in ["datetime", "date", "timestamp", "time"]:
        if cand in df.columns:
            ts_col = cand
            break
    if ts_col is None:
        raise ValueError("No datetime/date column detected. Expected one of: datetime, date, timestamp, time")

    # Parse datetime and sort
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce", utc=True)
    df = df.dropna(subset=[ts_col]).sort_values(ts_col)

    # Set index for indicators that expect DatetimeIndex (e.g., VWAP)
    df = df.set_index(ts_col)

    return df

# ------------- Bind a safe tool environment -------------
# Only expose df and functions needed; avoid os/system access for safety.
async def get_py_tool(file_dir):
    df = load_financial_csv(file_dir)
    tool_locals = {
        "pd": pd,
        "df": df
        }
    py_repl = PythonAstREPLTool(locals=tool_locals)
    py_tool = LangChainToolAdapter(py_repl)

    return py_tool