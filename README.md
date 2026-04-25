# 🔗 AI URL Summarizer

An AI-powered web application that extracts and summarizes content from **websites and YouTube videos** using LLMs. Built with Streamlit, LangChain, and Groq for fast, scalable summarization.

---

## 🚀 Live Demo
👉 https://urlsummarizer-project3.streamlit.app/

---

## ✨ Features

- 🔗 Summarize any website URL  
- 🎥 Supports YouTube video summarization (via transcripts)  
- ⚡ Fast inference using Groq (LLaMA 3)  
- 🧠 Handles long content using Map-Reduce style summarization  
- 🎨 Clean and modern Streamlit UI  
- 🔐 Secure API key handling  

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit  
- **LLM:** Groq (LLaMA 3)  
- **Framework:** LangChain  
- **Language:** Python  
- **Data Sources:**  
  - Web scraping  
  - YouTube transcripts  

---

## 📸 Screenshot

<p align="center">
  <img src="assets/output.png" width="700"/>
</p>

## ⚙️ Installation

```bash
git clone https://github.com/KunalS6/URL_Summarizer.git
cd URL_Summarizer
pip install -r requirements.txt
streamlit run app.py