import streamlit as st
import os
import time
import pandas as pd
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder
import io

# Import LangChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain

# 1. SETUP HALAMAN WEB
st.set_page_config(page_title="Jarvis Pro Max", page_icon="🤖", layout="wide")

# --- FITUR PENGAMAN (LOGIN) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2593/2593491.png", width=50)
    st.subheader("🔒 Login Area")
    sandi = st.text_input("Masukkan Password:", type="password")

    if sandi != "admin123": 
        st.warning("⚠️ Masukkan password dulu!")
        st.stop()
    else:
        st.success("🔓 Akses Diterima!")
        st.divider()

# --- SETUP API KEY ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.error("❌ API Key belum disetting!")
        st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# --- FUNGSI AUDIO MENJADI TEKS ---
def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        # Ubah bytes jadi file audio yang bisa dibaca
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            # Pakai Google Speech Recognition (Gratis & Support Bahasa Indo)
            text = r.recognize_google(audio_data, language="id-ID")
            return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return "Error koneksi ke Google Speech API"
    except Exception as e:
        return f"Error: {e}"

# --- FUNGSI BACA DOKUMEN ---
def get_files_text(uploaded_files):
    text = ""
    for file in uploaded_files:
        file_extension = file.name.split('.')[-1].lower()
        try:
            if file_extension == 'pdf':
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages: text += page.extract_text()
            elif file_extension == 'docx':
                doc = Document(file)
                for para in doc.paragraphs: text += para.text + "\n"
            elif file_extension == 'xlsx':
                df = pd.read_excel(file)
                text += df.to_string(index=False)
            elif file_extension == 'txt':
                text += str(file.read(), "utf-8")
        except Exception as e:
            st.error(f"Gagal membaca file {file.name}: {e}")
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    return text_splitter.split_text(text)

def get_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vector_store = None
    batch_size = 10
    progress_text = "Sedang melahap dokumen... (Mode Hemat Kuota)"
    my_bar = st.progress(0, text=progress_text)
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        try:
            if vector_store is None:
                vector_store = FAISS.from_texts(batch, embedding=embeddings)
            else:
                vector_store.add_texts(batch)
            percent = min((i + batch_size) / len(chunks), 1.0)
            my_bar.progress(percent, text=f"Menghafal bagian {i} - {i+batch_size}...")
            time.sleep(3) 
        except Exception as e:
            time.sleep(60)
            if vector_store: vector_store.add_texts(batch)
    my_bar.empty()
    return vector_store

def get_conversational_chain():
    model = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.3)
    return load_qa_chain(model, chain_type="stuff")

# --- SIDEBAR: UPLOAD & VOICE ---
with st.sidebar:
    st.subheader("📂 Dokumen Saya")
    uploaded_files = st.file_uploader("Upload disini", type=['pdf', 'docx', 'xlsx', 'txt'], accept_multiple_files=True)
    
    if st.button("Proses & Hafalkan"):
        if uploaded_files:
            with st.spinner("Sedang memproses..."):
                raw_text = get_files_text(uploaded_files)
                if raw_text:
                    text_chunks = get_text_chunks(raw_text)
                    st.session_state.vector_store = get_vector_store(text_chunks)
                    st.session_state.vector_store.save_local("faiss_index")
                    st.success("✅ Hafalan Selesai!")
    
    st.divider()
    st.subheader("🎙️ Voice Input")
    st.write("Klik ikon mic untuk bicara:")
    # Widget Mic Recorder
    audio = mic_recorder(start_prompt="Mulai Rekam", stop_prompt="Stop Rekam", key='recorder')

# --- LOGIKA CHAT UTAMA ---
st.header("🤖 Jarvis Pro Max (Voice Edition)")

# Tampilkan Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Tentukan Input: Dari Suara atau Ketikan?
prompt = None

# 1. Cek Input Suara
if audio:
    # Jika ada data audio baru yang belum diolah
    if "last_audio" not in st.session_state or st.session_state.last_audio != audio['bytes']:
        with st.spinner("Mendengarkan..."):
            text_from_audio = transcribe_audio(audio['bytes'])
            if text_from_audio:
                prompt = text_from_audio
                st.session_state.last_audio = audio['bytes'] # Tandai sudah diproses
            else:
                st.warning("Suara tidak terdengar jelas.")

# 2. Cek Input Ketikan (Kalau tidak ada suara)
if not prompt:
    prompt = st.chat_input("Tanya dokumen (ketik atau pakai mic di kiri)...")

# --- PROSES JAWABAN ---
if prompt:
    # Tampilkan Chat User
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Proses AI
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vector_db = st.session_state.vector_store
        
        if vector_db is None and os.path.exists("faiss_index"):
             vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

        if vector_db:
            try:
                docs = vector_db.similarity_search(prompt)
                chain = get_conversational_chain()
                with st.spinner("Mikiri dulu..."):
                    response = chain.run(input_documents=docs, question=prompt)
                message_placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                message_placeholder.error(f"Error: {e}")
        else:
            message_placeholder.warning("⚠️ Belum ada ingatan. Upload file dulu ya!")
