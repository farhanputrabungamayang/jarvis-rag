import os
import time
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# --- IMPORT LIBRARY RAG ---
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

# Load API Key
load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

def main():
    print("🧠 THE BRAIN: RAG SYSTEM INITIALIZED...")
    
    # 1. SETUP MODEL EMBEDDING (Penyimpan Ingatan)
    # Pakai model yang ada di akun Masbro
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    vector_store = None
    
    # --- LOGIKA HEMAT KUOTA (Cek Ingatan Lama) ---
    if os.path.exists("faiss_index"):
        print("📂 ASYIK! Ingatan lama ditemukan. Langsung load (Hemat Kuota)...")
        try:
            vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            print("✅ Ingatan berhasil dipanggil kembali!")
        except Exception as e:
            print(f"⚠️ Gagal load ingatan lama: {e}. Terpaksa buat baru ya...")
            vector_store = None
            
    # --- LOGIKA BACA BARU (Kalau ingatan belum ada) ---
    if vector_store is None:
        print("📂 Ingatan belum ada. Memulai proses membaca & menghafal...")
        
        pdf_path = "dokumen.pdf"
        if not os.path.exists(pdf_path):
            print(f"❌ File {pdf_path} tidak ditemukan!")
            return

        text = ""
        pdf_reader = PdfReader(pdf_path)
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        print(f"✅ PDF Terbaca: {len(text)} karakter.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        print(f"✅ Dipecah menjadi {len(chunks)} bagian.")

        print("⏳ Sedang menghafal isi dokumen (Mode Cicil biar gak kena Tilang)...")
        batch_size = 10
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            print(f"   👉 Memproses bagian {i+1} sampai {min(i+batch_size, len(chunks))}...")
            
            try:
                if vector_store is None:
                    vector_store = FAISS.from_texts(batch, embedding=embeddings)
                else:
                    vector_store.add_texts(batch)
                time.sleep(3) # Istirahat 3 detik
            except Exception as e:
                print(f"⚠️ Gagal di batch {i}: {e}")
                print("⏳ Menunggu 60 detik karena limit habis...")
                time.sleep(60)
                if vector_store:
                    vector_store.add_texts(batch)

        if vector_store:
            vector_store.save_local("faiss_index")
            print("✅ Selesai menghafal & disimpan!")
        else:
            print("❌ Gagal total.")
            return

    # 4. MODE TANYA JAWAB
    print("🤖 Siap melayani pertanyaan Masbro!")
    
    # Pakai 'gemini-flash-latest' (Jalur Umum Stabil & Kuota Lega)
    model = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.3)
    
    chain = load_qa_chain(model, chain_type="stuff")

    while True:
        query = input("\n🤔 Tanya Dokumen (ketik 'exit' untuk keluar): ")
        if query.lower() == 'exit': break
        
        # Cari chunk yang relevan
        docs = vector_store.similarity_search(query)
        
        try:
            print("🤖 Sedang mikir...")
            response = chain.run(input_documents=docs, question=query)
            print(f"\n👉 Jawab:\n{response}")
        except Exception as e:
            print(f"❌ Error: {e}")
            if "429" in str(e):
                print("   (Waduh kena limit lagi. Tunggu 1 menit ya)")

if __name__ == "__main__":
    main()