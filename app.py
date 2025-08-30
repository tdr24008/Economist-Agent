import os, pathlib, streamlit as st
from agents import analyst_reply, maybe_execute_fenced_code  # ⬅️ add this

st.set_page_config(page_title="Economist Agent", layout="wide")

st.title("Economist Agent 📈🏦💰")
st.write("Interactive economist research assistant (Streamlit + Autogen).")

# Dirs for safe I/O
DATA_DIR = str(pathlib.Path("data").resolve()); os.makedirs(DATA_DIR, exist_ok=True)
OUT_DIR  = str(pathlib.Path("out").resolve());  os.makedirs(OUT_DIR,  exist_ok=True)

# Sidebar
st.sidebar.header("Settings")
specialism = st.sidebar.selectbox("Choose a specialism",
                                  ["General", "Macroeconomics", "Labour", "Trade", "IO"])
uploaded_file = st.sidebar.file_uploader("Upload dataset (CSV/Parquet)", type=["csv", "parquet"])

# Save uploaded file (optional)
if uploaded_file is not None:
    dest = pathlib.Path(DATA_DIR) / uploaded_file.name
    with open(dest, "wb") as f:
        f.write(uploaded_file.read())
    st.sidebar.success(f"Saved to {dest}")

# Chat UI
st.subheader("Chat with the Economist Agent")
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask me about your data or economics..."):
    # user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 🔌 call the analyst (uses Ollama via agents.py)
    analyst_text = analyst_reply(prompt)
    st.session_state.messages.append({"role": "assistant", "content": analyst_text})
    with st.chat_message("assistant"):
        st.write(analyst_text)

    # ▶️ execute first fenced ```python block if present
    exec_res = maybe_execute_fenced_code(analyst_text, DATA_DIR, OUT_DIR)
    if exec_res.get("ran"):
        st.divider(); st.subheader("Execution report")
        st.code(exec_res["result"])

