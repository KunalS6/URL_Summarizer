import validators
import streamlit as st
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_community.document_loaders.youtube import YoutubeLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# -------------------- ENV --------------------
load_dotenv()
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found")
    st.stop()


# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="AI URL Summarizer", page_icon="✨")

st.title("🔗 AI URL Summarizer")
st.write("Summarize any Website or YouTube video instantly")


# -------------------- INPUT --------------------
generic_url = st.text_input("Enter URL")


# -------------------- LLM --------------------
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key
)


# -------------------- PROMPTS --------------------
map_prompt = PromptTemplate.from_template(
    "Summarize this content clearly:\n\n{text}"
)

combine_prompt = PromptTemplate.from_template(
    "Combine into a final structured summary (~300 words):\n\n{text}"
)


# -------------------- HELPER FUNCTION --------------------
def extract_text_from_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove scripts/styles
    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text(separator="\n")

    # Clean text
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


# -------------------- BUTTON --------------------
if st.button("✨ Generate Summary"):

    if not validators.url(generic_url):
        st.error("⚠️ Please enter a valid URL")
        st.stop()

    try:
        with st.spinner("🚀 Processing..."):

            # -------- LOAD --------
            if "youtube.com" in generic_url or "youtu.be" in generic_url:
                loader = YoutubeLoader.from_youtube_url(generic_url)
                docs = loader.load()
                text_data = " ".join([doc.page_content for doc in docs])

            else:
                text_data = extract_text_from_url(generic_url)

            if not text_data:
                st.error("❌ No content extracted")
                st.stop()

            # -------- SPLIT --------
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200
            )
            docs = splitter.create_documents([text_data])

            # -------- MAP --------
            map_chain = map_prompt | llm
            summaries = []

            for doc in docs:
                res = map_chain.invoke({"text": doc.page_content})
                summaries.append(res.content)

            # -------- REDUCE --------
            reduce_chain = combine_prompt | llm
            final_summary = reduce_chain.invoke({
                "text": "\n\n".join(summaries)
            })

            # -------- OUTPUT --------
            st.success("✅ Summary Generated")
            st.write(final_summary.content)

    except Exception as e:
        st.error("❌ Failed to process URL")
        st.write(e)