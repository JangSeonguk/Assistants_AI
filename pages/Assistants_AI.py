import json
import streamlit as st
import openai
from openai import OpenAI
from typing import Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.document_loaders import WebBaseLoader


client = OpenAI()

st.set_page_config(
    page_title="AI Search App",
    page_icon="🖥️",
)


class DuckDuckGoSearchToolArgsSchema(BaseModel):
    query: str = Field(description="The query you will search for")


class DuckDuckGoSearchTool(BaseTool):
    name: str = "DuckDuckGoSearchTool"
    description: str = """
    Use this tool to perform web searches using the DuckDuckGo search engine.
    It takes a query as an argument.
    Example query: "Latest technology news"
    """
    args_schema: Type[DuckDuckGoSearchToolArgsSchema] = DuckDuckGoSearchToolArgsSchema

    def _run(self, query):
        search = DuckDuckGoSearchResults()
        return search.run(query)


class WikipediaSearchToolArgsSchema(BaseModel):
    query: str = Field(description="The query you will search for on Wikipedia")


class WikipediaSearchTool(BaseTool):
    name: str = "WikipediaSearchTool"
    description: str = """
    Use this tool to perform searches on Wikipedia.
    It takes a query as an argument.
    Example query: "Artificial Intelligence"
    """
    args_schema: Type[WikipediaSearchToolArgsSchema] = WikipediaSearchToolArgsSchema

    def _run(self, query) -> Any:
        wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        return wiki.run(query)


class WebScrapingToolArgsSchema(BaseModel):
    url: str = Field(description="The URL of the website you want to scrape")


class WebScrapingTool(BaseTool):
    name: str = "WebScrapingTool"
    description: str = """
    If you found the website link in DuckDuckGo,
    Use this to get the content of the link for my research.
    """
    args_schema: Type[WebScrapingToolArgsSchema] = WebScrapingToolArgsSchema

    def _run(self, url):
        loader = WebBaseLoader([url])
        docs = loader.load()
        text = "\n\n".join([doc.page_content for doc in docs])
        return text


class SaveToTXTToolArgsSchema(BaseModel):
    text: str = Field(description="The text you will save to a file.")


class SaveToTXTTool(BaseTool):
    name: str = "SaveToTXTTOOL"
    description: str = """
    Use this tool to save the content as a .txt file.
    """
    args_schema: Type[SaveToTXTToolArgsSchema] = SaveToTXTToolArgsSchema

    def _run(self, text) -> Any:
        print(text)
        with open("research_results.txt", "w") as file:
            file.write(text)
        return "Research results saved to research_results.txt"


def wikipedia_search_tool(inputs):
    wk = WikipediaSearchTool()
    query = inputs["query"]
    result = wk.run(query)
    return json.dumps({"result": result}, ensure_ascii=False)


def duckduckgo_search_tool(inputs):
    ddg = DuckDuckGoSearchTool()
    query = inputs["query"]
    result = ddg.run(query)
    return json.dumps({"result": result})


valid_api_key = False
functions_map = {
    "wikipedia_search_tool": wikipedia_search_tool,
    "duckduckgo_search_tool": duckduckgo_search_tool,
}
functions = [
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search_tool",
            "description": "Use this tool to search information on Wikipedia. Use 'query' as a parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query you want to search on Wikipedia",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "duckduckgo_search_tool",
            "description": "Use this tool to search information on DuckDuckGo. Use 'query' as a parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query you want to search on DuckDuckGo",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def check_api_key(api_key):
    """# OpenAI API Key 사용 가능여부 확인"""
    openai.api_key = api_key
    try:
        openai.models.list()
        st.success("유효한 API Key 가 확인되었습니다.")
        return True

    except Exception as e:
        st.error(f"Open API key 값이 유효하지 않습니다. {e}")
        return False


with st.sidebar:
    api_key = st.text_input("Enter your Open API Key", type="password")
    if api_key:
        valid_api_key = check_api_key(api_key)


def save_message(message, role):
    st.session_state["messages"].append({"message": message, "role": role})


def send_message(message, role, save=True):
    with st.chat_message(role):
        st.markdown(message)
    if save:
        save_message(message, role)


def paint_history():
    for message in st.session_state["messages"]:
        send_message(
            message["message"],
            message["role"],
            save=False,
        )


def create_assistant():
    """AI Assistants 생성"""
    return client.beta.assistants.create(
        name="3gpp expert",
        instructions=(
            "You answer questions related to wireless communication such as LTE and 5G, and provide additional links for reference."
        ),
        tools=functions,
        model="gpt-4o-mini",
    )


def create_thread(content):
    """Thread를 생성"""
    return client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ]
    )


def create_run(thread_id, assistant_id):
    """run 생성"""
    return client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )


def get_run(run_id, thread_id):
    """run 정보 추출"""
    return client.beta.threads.runs.retrieve(
        run_id=run_id,
        thread_id=thread_id,
    )


def get_messages(thread_id):
    """메세지 정보 추출"""
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    messages = list(messages)
    messages.reverse()
    answer = ""
    for message in messages:
        answer = f"{message.role}: {message.content[0].text.value}"
    return answer


def get_tool_outputs(run_id, thread_id):
    """Assistant가 요청한 function output 리턴"""
    cr_run = get_run(run_id, thread_id)
    outputs = []
    for action in cr_run.required_action.submit_tool_outputs.tool_calls:
        action_id = action.id
        function = action.function
        print(f"Calling function: {function.name} with arg {function.arguments}")
        outputs.append(
            {
                "output": functions_map[function.name](json.loads(function.arguments)),
                "tool_call_id": action_id,
            }
        )
    return outputs


def submit_tool_outputs(run_id, thread_id):
    """output 전달"""
    outpus = get_tool_outputs(run_id, thread_id)
    return client.beta.threads.runs.submit_tool_outputs(
        run_id=run_id, thread_id=thread_id, tool_outputs=outpus
    )


if valid_api_key:
    # assistant 재생성 방지 로직 검토 필요
    if st.session_state["assistant"] == None:
        st.session_state["assistant"] = create_assistant()
    assistant = st.session_state["assistant"]

    send_message("뭐든지 물어보세요.", "assistant", save=False)
    paint_history()

    query = st.chat_input("질문을 입력해주세요.")
    if query:
        send_message(query, "user", save=True)

        thread = create_thread(query)
        run = create_run(thread.id, assistant.id)

        with st.chat_message("assistant"):
            with st.status("실행중") as status:
                while True:
                    run_info = get_run(run.id, thread.id)
                    if run_info.status == "requires_action":
                        status.update(
                            label=f"실행중: {run_info.status}", state="running"
                        )
                        submit_tool_outputs(run.id, thread.id)
                    if run_info.status == "completed":
                        result = get_messages(thread.id)
                        break
        if result:
            send_message(result, "assistant")
        else:
            st.error("답변을 가져오지 못했습니다. 다시 시도해주세요.")


else:
    st.session_state["messages"] = []
    st.session_state["assistant"] = None

    st.markdown(
        """
    # AI Assistants
            
챗봇에게 무엇이든 물어보세요.\n
먼저 유효한 OpenAI API Key 값을 입력해주세요.

"""
    )
