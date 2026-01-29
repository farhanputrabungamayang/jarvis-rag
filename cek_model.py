import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print("🕵️‍♂️ SEDANG MENGECEK KONEKSI KE GOOGLE...")

if not api_key:
    print("❌ BAHAYA: API Key tidak terbaca dari file .env!")
else:
    print(f"✅ API Key terdeteksi: {api_key[:5]}*******")
    
    try:
        genai.configure(api_key=api_key)
        print("\n📋 DAFTAR MODEL YANG TERSEDIA DI AKUN MASBRO:")
        
        found_embedding = False
        for m in genai.list_models():
            # Kita cuma cari yang ada kata 'embed' (buat ingatan) atau 'gemini' (buat chat)
            if 'embed' in m.name or 'gemini' in m.name:
                print(f"   👉 {m.name}")
            
            if 'embed' in m.name:
                found_embedding = True

        if not found_embedding:
            print("\n⚠️ WADUH: Gak nemu model embedding sama sekali. Cek API Key!")
        else:
            print("\n✅ Mantap! Tinggal pilih satu nama di atas buat dipasang di brain.py.")

    except Exception as e:
        print(f"\n❌ ERROR KONEKSI: {e}")