import validators
import streamlit as st
import os
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_community.document_loaders.youtube import YoutubeLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter


# -------------------- ENV --------------------
load_dotenv()

groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not groq_api_key:
    st.error("❌ GROQ_API_KEY not found")
    st.stop()


# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI URL Summarizer",
    page_icon="✨",
    layout="centered"
)


# -------------------- CUSTOM UI --------------------
st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 2.5rem;
    font-weight: bold;
    color: #4CAF50;
}
.sub-text {
    text-align: center;
    color: grey;
    margin-bottom: 30px;
}
.stButton>button {
    width: 100%;
    border-radius: 10px;
    height: 3em;
    background-color: #4CAF50;
    color: white;
    font-size: 16px;
}
.result-box {
    padding: 20px;
    border-radius: 10px;
    background-color: #f5f5f5;
    color: black;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🔗 AI URL Summarizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">Summarize any Website or YouTube video instantly</div>', unsafe_allow_html=True)


# -------------------- INPUT --------------------
generic_url = st.text_input("🔍 Paste your URL here")


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
    "Combine these summaries into a clean, structured summary (~300 words):\n\n{text}"
)


# -------------------- BUTTON --------------------
if st.button("✨ Generate Summary"):

    if not validators.url(generic_url):
        st.error("⚠️ Please enter a valid URL")
        st.stop()

    try:
        with st.spinner("🚀 Processing..."):

            # -------- LOAD --------
            if "youtube.com" in generic_url or "youtu.be" in generic_url:
                try:
                    loader = YoutubeLoader.from_youtube_url(generic_url)
                    docs = loader.load()
                except Exception:
                    st.error("❌ Failed to load YouTube video (may not have captions)")
                    st.stop()

            else:
                loader = UnstructuredURLLoader(
                    urls=[generic_url],
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                    mode="elements",     # ✅ prevents heavy parsing
                    strategy="fast"      # ✅ avoids spaCy usage
                )
                docs = loader.load()

            if not docs:
                st.error("❌ No content extracted")
                st.stop()

            # -------- SPLIT --------
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200
            )
            docs = splitter.split_documents(docs)

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

            st.markdown(
                f'<div class="result-box">{final_summary.content}</div>',
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error("❌ Failed to process URL")
        st.write(e)