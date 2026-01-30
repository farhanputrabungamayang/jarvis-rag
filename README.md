# 🤖 Jarvis Pro Max - AI Document Assistant

Jarvis adalah asisten AI berbasis **RAG (Retrieval-Augmented Generation)** yang dirancang untuk menganalisis dan berdiskusi mengenai isi dokumen. Tidak seperti chatbot biasa, Jarvis "membaca" dokumen Anda terlebih dahulu sebelum menjawab, sehingga jawabannya akurat dan berbasis fakta.

🔗 **Live Demo:** [https://jarvis-rag-project.streamlit.app/]

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![LangChain](https://img.shields.io/badge/LangChain-Integration-green?style=for-the-badge)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange?style=for-the-badge)

## ✨ Fitur Unggulan
* **🔐 Secure Access:** Dilengkapi sistem login sederhana untuk keamanan penggunaan.
* **📄 Omnivore Reader:** Mendukung format **PDF, Word (DOCX), Excel (XLSX), dan TXT**.
* **🧠 Context Memory:** Memiliki ingatan percakapan, bisa diajak diskusi panjang (Follow-up questions).
* **💬 Interactive UI:** Tampilan chat modern ala WhatsApp/ChatGPT.

## 🛠️ Tech Stack
Project ini dibangun menggunakan teknologi terkini di bidang Generative AI:
* **Framework:** Streamlit (Frontend), LangChain (Orchestrator).
* **LLM:** Google Gemini 2.0 Flash / 1.5 Pro.
* **Vector DB:** FAISS (Facebook AI Similarity Search).
* **Libraries:** `PyPDF2`, `python-docx`, `pandas`, `python-dotenv`.

## 🚀 Cara Menjalankan (Lokal)
1. Clone repo ini: `git clone https://github.com/farhanputrabungamayang/jarvis-rag.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Setup API Key Google Gemini di `.env`.
4. Jalankan: `streamlit run app.py`

---
*Created with ❤️ by Farhan.*
