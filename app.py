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
from PIL import Image
import google.generativeai as genai

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
genai.configure(api_key=api_key) # Konfigurasi buat Vision

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# --- FUNGSI AUDIO ---
def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language="id-ID")
            return text
    except Exception:
        return None

# --- FUNGSI BACA DOKUMEN ---
def get_files_text(uploaded_files):
    text = ""
    for file in uploaded_files:
        ext = file.name.split('.')[-1].lower()
        try:
            if ext == 'pdf':
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages: text += page.extract_text()
            elif ext == 'docx':
                doc = Document(file)
                for para in doc.paragraphs: text += para.text + "\n"
            elif ext == 'xlsx':
                df = pd.read_excel(file)
                text += df.to_string(index=False)
            elif ext == 'txt':
                text += str(file.read(), "utf-8")
        except Exception as e:
            st.error(f"Error baca file {file.name}: {e}")
    return text

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    return splitter.split_text(text)

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
            time.sleep(2) 
        except Exception:
            time.sleep(60)
            if vector_store: vector_store.add_texts(batch)
        my_bar.progress(min((i + batch_size) / len(chunks), 1.0))
    my_bar.empty()
    return vector_store

def get_conversational_chain():
    model = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.3)
    return load_qa_chain(model, chain_type="stuff")

# --- FUNGSI KHUSUS VISION (MATA DEWA) ---
def analyze_image(image_file, prompt):
    # Pakai model khusus Vision (Gemini 1.5 Flash)
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(image_file)
    response = model.generate_content([prompt, img])
    return response.text

# --- SIDEBAR: UPLOAD FILE & GAMBAR ---
with st.sidebar:
    st.subheader("📂 Dokumen (RAG)")
    uploaded_files = st.file_uploader("Upload PDF/Doc/Excel", type=['pdf', 'docx', 'xlsx', 'txt'], accept_multiple_files=True)
    
    if st.button("Proses Dokumen"):
        if uploaded_files:
            with st.spinner("Memproses dokumen..."):
                raw_text = get_files_text(uploaded_files)
                if raw_text:
                    text_chunks = get_text_chunks(raw_text)
                    st.session_state.vector_store = get_vector_store(text_chunks)
                    st.session_state.vector_store.save_local("faiss_index")
                    st.success("✅ Dokumen tersimpan!")
    
    st.divider()
    st.subheader("👁️ Mata Dewa (Vision)")
    uploaded_image = st.file_uploader("Upload Gambar/Screenshot", type=['jpg', 'jpeg', 'png'])
    if uploaded_image:
        st.image(uploaded_image, caption="Gambar yang akan dianalisa", use_column_width=True)

    st.divider()
    st.subheader("🎙️ Voice Input")
    audio = mic_recorder(start_prompt="Rekam", stop_prompt="Stop", key='recorder')

# --- LOGIKA CHAT UTAMA ---
st.header("🤖 Jarvis Pro Max (Vision Edition)")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = None
# Cek Audio
if audio:
    if "last_audio" not in st.session_state or st.session_state.last_audio != audio['bytes']:
        text_from_audio = transcribe_audio(audio['bytes'])
        if text_from_audio:
            prompt = text_from_audio
            st.session_state.last_audio = audio['bytes']

# Cek Ketikan
if not prompt:
    prompt = st.chat_input("Kirim pesan (Teks/Suara/Gambar)...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        response = ""
        
        try:
            # === LOGIKA PENTING: CEK GAMBAR DULU ===
            if uploaded_image:
                # Jika ada gambar, masuk Mode Vision
                with st.spinner("Melihat gambar..."):
                    response = analyze_image(uploaded_image, prompt)
            
            # === JIKA TIDAK ADA GAMBAR, CEK DOKUMEN (RAG) ===
            else:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
                vector_db = st.session_state.vector_store
                
                if vector_db is None and os.path.exists("faiss_index"):
                     vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

                if vector_db:
                    with st.spinner("Membaca dokumen..."):
                        docs = vector_db.similarity_search(prompt)
                        chain = get_conversational_chain()
                        response = chain.run(input_documents=docs, question=prompt)
                else:
                    response = "⚠️ Saya bingung. Belum ada dokumen yang diupload dan tidak ada gambar yang dilampirkan."

            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            message_placeholder.error(f"Error: {e}")
