from autogen_core import CancellationToken

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import AgentEvent, ChatMessage, TextMessage, ToolCallRequestEvent
from autogen_agentchat.teams import RoundRobinGroupChat

from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor
from autogen_ext.tools.code_execution import PythonCodeExecutionTool

from dotenv import load_dotenv
import os
import re
import pathlib
import streamlit as st
from typing import AsyncGenerator, Sequence


# -------------------------------
# Environment-driven configuration
# -------------------------------
load_dotenv()  # allows .env or env vars

# Model server + model
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:3b-instruct-q4_K_M")  # TEMP on t3.micro

# Paths (optional but handy to keep consistent across the app)
DATA_DIR = pathlib.Path(os.getenv("DATA_DIR", "data")).resolve()
OUT_DIR = pathlib.Path(os.getenv("OUT_DIR", "out")).resolve()
CODE_WORK_DIR = pathlib.Path(os.getenv("CODE_WORK_DIR", "./code_executor")).resolve()

# Ensure the directories exist
for p in (DATA_DIR, OUT_DIR, CODE_WORK_DIR):
    p.mkdir(parents=True, exist_ok=True)


class TrackableAssistantAgent(AssistantAgent):
    """
    AssistantAgent that writes its responses to Streamlit as they stream in.
    """

    async def on_messages_stream(
        self, messages: Sequence[ChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[AgentEvent | ChatMessage | Response, None]:
        async for msg in super().on_messages_stream(
            messages=messages, cancellation_token=cancellation_token
        ):
            self._track_response_on_streamlit(msg)
            yield msg

    def _track_response_on_streamlit(self, msg):
        if isinstance(msg, ToolCallRequestEvent):
            content = (
                f"**[{msg.source}] Tool calls requested:** "
                + ", ".join(f"{tool.name}" for tool in msg.content)
            )
            st.session_state["messages"].append({"role": "assistant", "content": content})
            with st.chat_message("assistant", avatar="🛠️"):
                st.markdown(content)

        elif (isinstance(msg, TextMessage)) and msg.source != "user":
            self._handle_text_message(msg)

        elif isinstance(msg, Response) and isinstance(msg.chat_message, TextMessage):
            self._handle_text_message(msg.chat_message)

    def _handle_text_message(self, msg: TextMessage) -> None:
        msg_content = f"**[{msg.source}]**\n{msg.content.replace('TERMINATE', '').strip()}"
        st.session_state["messages"].append({"role": "assistant", "content": msg_content})

        if msg.source == "DataAnalystAgent":
            image_files = self._image_files_in_response(msg_content)
            with st.chat_message("assistant"):
                st.markdown(msg_content)
                for image_file in image_files:
                    image_path = CODE_WORK_DIR / image_file
                    if image_path.exists():
                        st.image(str(image_path), caption=image_file)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg_content)

    def _image_files_in_response(self, response: str) -> list[str]:
        """Return unique *.png names mentioned in the text."""
        pattern = r"([a-zA-Z0-9_\-]+\.png)"
        matches = re.findall(pattern, response)
        return list(set(matches))


def get_data_analyst_team(model: str | None = None) -> RoundRobinGroupChat:
    """
    Build a two-agent team:
      - DataAnalystAgent (plans analysis, writes Python)
      - CodeExecutorAgent (executes Python via local shell)

    Args:
        model: optional model name. If None, uses env var MODEL_NAME.
    """
    model_name = model or DEFAULT_MODEL_NAME

    # Chat client for Ollama
    model_client = OllamaChatCompletionClient(
        model=model_name,
        host=OLLAMA_HOST,  # e.g., http://127.0.0.1:11434
        model_info={
            "json_output": True,
            "function_calling": True,
            "vision": True,
            "family": "unknown",
        },
    )

    # Code execution tool (works in CODE_WORK_DIR)
    python_code_executor_tool = PythonCodeExecutionTool(
        LocalCommandLineCodeExecutor(work_dir=str(CODE_WORK_DIR))
    )

    data_analyst_agent = TrackableAssistantAgent(
        name="DataAnalystAgent",
        description=(
            "A data analyst agent that can analyze data, extract insights, "
            "create visualizations and generate reports."
        ),
        model_client=model_client,
        system_message=(
            "You are an expert data analyst.\n\n"
            "Guidelines:\n"
            "- First send a clear analysis plan for the user's dataset/query.\n"
            "- Write complete, executable Python (start with all imports).\n"
            "- Prefer tidy, parsimonious analysis and clear plots.\n"
            "- Save any figures to PNG files and mention their filenames.\n"
            "- Do not say 'TERMINATE' until code has executed successfully.\n"
            "TERMINATE only when you are fully done."
        ),
    )

    code_executor_agent = TrackableAssistantAgent(
        name="CodeExecutorAgent",
        description="Executes Python code locally and reports success/errors.",
        tools=[python_code_executor_tool],
        reflect_on_tool_use=True,
        model_client=model_client,
        system_message=(
            "You execute Python code and return results.\n"
            "- Always run the code provided by the analyst when possible.\n"
            "- If execution fails, explain fixes briefly (no code snippets).\n"
            "- If success, confirm and list any generated image filenames."
        ),
    )

    # Termination: mention of TERMINATE or max turns
    termination_condition = TextMentionTermination("TERMINATE") | MaxMessageTermination(
        max_messages=20
    )

    return RoundRobinGroupChat(
        [data_analyst_agent, code_executor_agent],
        termination_condition=termination_condition,
    )

