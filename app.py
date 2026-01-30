import streamlit as st
import os
import time
import pandas as pd
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

# Import LangChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain

# 1. SETUP HALAMAN WEB
st.set_page_config(page_title="Jarvis Pro Max", page_icon="🤖", layout="wide")

# --- FITUR PENGAMAN (LOGIN) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2593/2593491.png", width=50) # Hiasan ikon gembok
    st.subheader("🔒 Login Area")
    sandi = st.text_input("Masukkan Password:", type="password")

    # Ganti 'admin123' dengan password yang Masbro mau
    if sandi != "admin123": 
        st.warning("⚠️ Masukkan password dulu untuk mengakses Jarvis!")
        st.info("Hubungi pemilik jika butuh akses.")
        st.stop()  # 🛑 STOP DISINI kalau password salah
    else:
        st.success("🔓 Akses Diterima!")
        st.divider()

# --- SETUP API KEY (LOGIKA CERDAS) ---
load_dotenv()

# 1. Coba ambil dari .env (Cara Laptop)
api_key = os.getenv("GEMINI_API_KEY")

# 2. Kalau kosong, ambil dari Streamlit Secrets (Cara Cloud)
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.error("❌ API Key belum disetting! Cek 'Advanced Settings' di Streamlit Cloud.")
        st.stop()

# 3. Pasang kuncinya
os.environ["GOOGLE_API_KEY"] = api_key

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# 2. FUNGSI BACA FILE (PDF, WORD, EXCEL)
def get_files_text(uploaded_files):
    text = ""
    for file in uploaded_files:
        file_extension = file.name.split('.')[-1].lower()
        
        try:
            # === BACA PDF ===
            if file_extension == 'pdf':
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            # === BACA WORD (.docx) ===
            elif file_extension == 'docx':
                doc = Document(file)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            
            # === BACA EXCEL (.xlsx) ===
            elif file_extension == 'xlsx':
                df = pd.read_excel(file)
                text += df.to_string(index=False)
            
            # === BACA TEXT BIASA (.txt) ===
            elif file_extension == 'txt':
                text += str(file.read(), "utf-8")
                
        except Exception as e:
            st.error(f"Gagal membaca file {file.name}: {e}")
            
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    chunks = text_splitter.split_text(text)
    return chunks

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
            st.warning(f"⚠️ Kena Limit di batch {i}. Tunggu 60 detik...")
            time.sleep(60)
            if vector_store:
                vector_store.add_texts(batch)
    
    my_bar.empty()
    return vector_store

def get_conversational_chain():
    model = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.3)
    chain = load_qa_chain(model, chain_type="stuff")
    return chain

# 3. SIDEBAR LANJUTAN (UPLOAD MENU)
with st.sidebar:
    st.subheader("📂 Dokumen Saya")
    st.write("Format: PDF, DOCX, XLSX, TXT")
    
    uploaded_files = st.file_uploader("Upload disini", 
                                   type=['pdf', 'docx', 'xlsx', 'txt'], 
                                   accept_multiple_files=True)
    
    if st.button("Proses & Hafalkan"):
        if uploaded_files:
            with st.spinner("Sedang memproses berbagai jenis file..."):
                raw_text = get_files_text(uploaded_files)
                
                if raw_text:
                    text_chunks = get_text_chunks(raw_text)
                    st.session_state.vector_store = get_vector_store(text_chunks)
                    st.session_state.vector_store.save_local("faiss_index")
                    st.success("✅ Semua file berhasil dihafal!")
                else:
                    st.warning("File kosong atau tidak terbaca teksnya.")
        else:
            st.warning("Pilih file dulu dong Masbro!")

# 4. AREA CHAT UTAMA
st.header("🤖 Jarvis Pro Max (Omnivore Edition)")

# Tampilkan Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input User
if prompt := st.chat_input("Tanya sesuatu tentang dokumen..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        vector_db = st.session_state.vector_store
        
        # Coba load dari file lokal jika session kosong
        if vector_db is None and os.path.exists("faiss_index"):
             vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

        if vector_db:
            try:
                docs = vector_db.similarity_search(prompt)
                chain = get_conversational_chain()
                
                with st.spinner("Menganalisa data..."):
                    response = chain.run(input_documents=docs, question=prompt)
                
                message_placeholder.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                message_placeholder.error(f"Error: {e}")
        else:
            message_placeholder.warning("⚠️ Belum ada ingatan. Upload file dulu ya!")
