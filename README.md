# 🤖 Jarvis RAG (Retrieval-Augmented Generation)

Jarvis adalah asisten AI cerdas yang dirancang untuk membantu pengguna memahami dokumen kompleks dengan cepat. Dibangun menggunakan teknologi **LangChain** dan **Google Gemini**, aplikasi ini mampu membaca, memahami, dan menjawab pertanyaan dari berbagai format dokumen.

🔗 **Coba Langsung (Live Demo):** [https://jarvis-rag-project.streamlit.app/]

## ✨ Fitur Unggulan
* **Omnivore Reader:** Mendukung format PDF, DOCX (Word), XLSX (Excel), dan TXT.
* **Context Aware:** Memiliki memori percakapan, sehingga diskusi bisa berjalan dua arah layaknya chatting dengan manusia.
* **Secure Access:** Dilengkapi sistem login sederhana untuk keamanan penggunaan.
* **Anti-Hallucination:** Menggunakan metode RAG untuk memastikan jawaban berdasarkan fakta di dalam dokumen, bukan karangan AI.

## 🛠️ Teknologi (Tech Stack)
* **Language:** Python 3.11
* **Framework:** Streamlit (Frontend), LangChain (Orchestrator)
* **AI Model:** Google Gemini 2.0 Flash / 1.5 Pro
* **Vector Database:** FAISS (Facebook AI Similarity Search)

## 🚀 Cara Menjalankan di Lokal
1. Clone repository ini.
2. Install dependencies: `pip install -r requirements.txt`
3. Buat file `.env` dan masukkan API Key Google Gemini.
4. Jalankan: `streamlit run app.py`

---
*Project ini dibuat sebagai bagian dari portofolio pengembangan AI Engineer.*
