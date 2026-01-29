import sys
import langchain
print(f"Versi Python: {sys.version}")
print(f"Lokasi LangChain: {langchain.__file__}")

try:
    from langchain.chains.question_answering import load_qa_chain
    print("✅ SUKSES! Chains ditemukan.")
except ImportError as e:
    print(f"❌ MASIH ERROR: {e}")
    # Cek isi folder langchain
    import os
    folder = os.path.dirname(langchain.__file__)
    print(f"Isi folder LangChain di {folder}:")
    print(os.listdir(folder))