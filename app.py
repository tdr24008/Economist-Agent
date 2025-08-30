import streamlit as st

st.set_page_config(page_title="Economist Agent", layout="wide")

# Title and intro
st.title("Economist Agent 📈🏦💰")
st.write("Interactive economist research assistant (Streamlit + Autogen).")

# Sidebar for dataset / specialism
st.sidebar.header("Settings")
specialism = st.sidebar.selectbox(
    "Choose a specialism",
    ["General", "Macroeconomics", "Labour", "Trade", "IO"]
)

uploaded_file = st.sidebar.file_uploader("Upload dataset (CSV/Parquet)", type=["csv", "parquet"])

# Chat interface placeholder
st.subheader("Chat with the Economist Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input box
if prompt := st.chat_input("Ask me about your data or economics..."):
    # Store user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Placeholder response until Ollama is hooked up
    response = f"(Analyst Agent placeholder) You asked: {prompt}"
    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.write(response)
