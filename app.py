import streamlit as st

st.set_page_config(
    page_title="AI Search APP",
    page_icon="🦈",
)


with st.sidebar:
    choice = (
        st.selectbox(
            "Choose what you want to use.",
            (
                "Home",
                "Source Code",
            ),
        ),
    )
    st.link_button("Open Git", "https://github.com/JangSeonguk/Assistants_AI"),


ASSIST_PATH = "pages/Assistants_AI.py"

with open(ASSIST_PATH, "r", encoding="utf-8") as file:
    site_code = file.read()

if choice == "Source Code":
    st.subheader("Assistants AI 페이지에 대한 소스 코드입니다.")
    st.code(site_code, language="python")

else:
    st.title("Home")
    st.write(
        """
        OpenAI에서 제공하는 AI Assistants를 활용한 AI Search App 입니다.    
        Assistants AI 페이지에서 챗봇에게 질문해보세요.
        """
    )

    st.link_button(
        "OpenAI Document", "https://platform.openai.com/docs/assistants/overview"
    )
