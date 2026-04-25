import validators
import streamlit as st
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.youtube import YoutubeLoader

from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs


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
    model="llama-3.1-8b-instant",   # ← replace 70B
    api_key=groq_api_key
)



# -------------------- PROMPTS --------------------
map_prompt = PromptTemplate.from_template(
    "Summarize this content clearly:\n\n{text}"
)

combine_prompt = PromptTemplate.from_template(
    "Combine into a final structured summary (~300 words):\n\n{text}"
)


# -------------------- WEBSITE LOADER --------------------
def extract_text_from_url(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)

    soup = BeautifulSoup(response.text, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    return "\n".join(lines)


# -------------------- YOUTUBE HELPERS --------------------
def get_video_id(url):
    query = urlparse(url)
    if "youtube.com" in url:
        return parse_qs(query.query).get("v", [None])[0]
    elif "youtu.be" in url:
        return query.path[1:]
    return None


def load_youtube_content(url):
    try:
        # Try LangChain loader
        loader = YoutubeLoader.from_youtube_url(url)
        docs = loader.load()
        return " ".join([doc.page_content for doc in docs])

    except Exception:
        try:
            # Fallback to transcript API
            video_id = get_video_id(url)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)

            return " ".join([t["text"] for t in transcript])

        except Exception:
            return None


# -------------------- BUTTON --------------------
if st.button("✨ Generate Summary"):

    if not validators.url(generic_url):
        st.error("⚠️ Please enter a valid URL")
        st.stop()

    try:
        with st.spinner("🚀 Processing..."):

            # -------- LOAD --------
            if "youtube.com" in generic_url or "youtu.be" in generic_url:
                text_data = load_youtube_content(generic_url)

                if not text_data:
                    st.error("❌ This YouTube video has no captions available")
                    st.stop()

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