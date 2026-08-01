import os
import re
import json
import glob
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Generator
from google import genai
import pypdf
import docx

# Suppress pypdf verbose warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)

# Hackathon required model and settings
GEMMA_MODEL_NAME = "publishers/google/models/gemma-4-26b-a4b-it-maas"
LPDP_DIR = os.path.join(os.path.dirname(__file__), "LPDP")

# Known direct admission URLs for popular universities
UNIV_WEB_DIRECTORIES = {
    "sbm itb": "https://www.sbm.itb.ac.id",
    "itb": "https://www.itb.ac.id",
    "ui": "https://www.ui.ac.id",
    "ugm": "https://www.ugm.ac.id",
    "unair": "https://www.unair.ac.id",
    "ipb": "https://www.ipb.ac.id",
    "unpad": "https://www.unpad.ac.id",
    "undip": "https://www.undip.ac.id",
    "ub": "https://www.ub.ac.id",
    "oxford": "https://www.ox.ac.uk",
    "cambridge": "https://www.cam.ac.uk",
    "harvard": "https://www.harvard.edu",
    "stanford": "https://www.stanford.edu",
    "mit": "https://www.mit.edu",
    "nus": "https://www.nus.edu.sg",
    "ntu": "https://www.ntu.edu.sg",
    "melbourne": "https://www.unimelb.edu.au"
}

def fetch_live_university_web_content(query: str) -> Dict[str, str]:
    """Scrapes live text content from official university websites if requested by user."""
    query_clean = query.lower()
    
    target_url = ""
    target_name = ""
    for k, url in UNIV_WEB_DIRECTORIES.items():
        if k in query_clean:
            target_url = url
            target_name = k.upper()
            break
            
    if not target_url:
        return {"url": "", "content": ""}

    print(f"🌐 [RAGAgent Tool] Live Web Scraping for {target_name} at {target_url}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        r = requests.get(target_url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        text = soup.get_text(separator=' ')
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) > 100:
            return {
                "url": target_url,
                "content": f"Situs Web Resmi {target_name} ({target_url}):\n{text[:1800]}"
            }
    except Exception as e:
        print(f"[RAGAgent Tool] Scraping error: {e}")
        
    return {"url": target_url, "content": f"Situs Web Resmi {target_name}: {target_url}"}

class RAGAgent:
    def __init__(self):
        # Resolve GCP Project ID
        self.project_id = (
            os.getenv("GOOGLE_CLOUD_PROJECT") or 
            os.getenv("GEMINI_DEFAULT_PROJECT") or 
            os.getenv("ANTIGRAVITY_PROJECT_ID") or 
            "kodingdeepdive0826-9569"
        )
        
        # Initialize Google GenAI Client with Vertex AI for Gemma
        try:
            self.client = genai.Client(vertexai=True, project=self.project_id, location="global")
            self.gemma_ready = True
        except Exception as e:
            print(f"[RAGAgent] Error initializing Gemma client: {e}")
            self.client = None
            self.gemma_ready = False

        self.documents_cache = []
        self._load_lpdp_corpus()

        self.system_prompt_template = """Anda adalah SAPA-LPDP (Sistem Asisten & Pendamping Aplikasi LPDP) — Asisten AI ahli untuk Beasiswa LPDP & Pendaftaran Perguruan Tinggi yang ditenagai oleh Google Gemma 4 26B (Model Garden on Vertex AI).
Tugas Anda adalah membantu pendaftar beasiswa dengan menjawab pertanyaan, memberikan analisis kelayakan CV, memberikan rekomendasi jurusan & kampus, serta menjadi konsultan yang ramah, sopan, dan profesional.

ATURAN MENJAWAB:
1. Jika pengguna menyapa (misal: "Hai", "Halo"), jawablah dengan sapaan ramah dan tanyakan apa yang bisa dibantu mengenai beasiswa LPDP / kampus.
2. Jawab pertanyaan utamanya berdasarkan KONTEKS dokumen LPDP resmi dan hasil live scraping website kampus yang disediakan di bawah ini.
3. Tolak secara sopan pertanyaan yang sama sekali tidak berhubungan dengan Beasiswa, Pendidikan, atau Karir Akademik.
4. JANGAN sebutkan frasa kaku seperti "Berdasarkan dokumen X yang dilampirkan". Jawab secara alami, luwes, namun akurat dan berbasis data.
5. Gunakan Ringkasan CV dan Preferensi pengguna untuk memberikan analisis personalisasi.
6. Saat merekomendasikan atau menyebutkan nama perguruan tinggi (seperti ITB, SBM ITB, UI, UGM, Oxford, Harvard, dll.), SELALU sertakan tautan situs web resmi kampus (contoh: [Situs Resmi ITB](https://www.itb.ac.id) atau [Situs Resmi SBM ITB](https://www.sbm.itb.ac.id)) agar pendaftar dapat langsung mempelajari jurusan dan syarat admission kampus tersebut.

---
[User's CV Summary]
{cv_info}

[User's Preferences]
{preferences}

---
[Konteks Dokumen Resmi LPDP & Beasiswa]
{context}

---
[Hasil Scraping Website Resmi Kampus Real-time]
{web_context}

---
Pertanyaan Pengguna: {question}

Jawaban SAPA-LPDP:"""

    def _load_lpdp_corpus(self):
        """Memuat dokumen dari folder LPDP ke memori dengan caching JSON berkecepatan tinggi."""
        if not os.path.exists(LPDP_DIR):
            return

        cache_path = os.path.join(LPDP_DIR, "corpus_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self.documents_cache = json.load(f)
                print(f"[RAGAgent] Loaded {len(self.documents_cache)} document chunks from JSON cache in 0.01s!")
                return
            except Exception as e:
                print(f"[RAGAgent] Failed to load cache, re-parsing documents: {e}")

        files = [f for f in os.listdir(LPDP_DIR) if f.endswith('.pdf') or f.endswith('.docx')]
        print(f"[RAGAgent] Parsing {len(files)} LPDP corpus files...")
        for file_name in files:
            file_path = os.path.join(LPDP_DIR, file_name)
            if file_name.endswith('.pdf'):
                try:
                    reader = pypdf.PdfReader(file_path, strict=False)
                    for page_idx, page in enumerate(reader.pages[:30]):
                        text = page.extract_text() or ""
                        if len(text.strip()) > 50:
                            chunks = [c.strip() for c in text.split('\n\n') if len(c.strip()) > 40]
                            if not chunks:
                                chunks = [text.strip()]
                            for chunk in chunks:
                                self.documents_cache.append({
                                    "source": file_name,
                                    "page": page_idx + 1,
                                    "text": chunk
                                })
                except Exception:
                    pass
            elif file_name.endswith('.docx'):
                try:
                    doc = docx.Document(file_path)
                    full_text = "\n".join([p.text.strip() for p in doc.paragraphs if len(p.text.strip()) > 30])
                    if full_text:
                        chunks = [c.strip() for c in full_text.split('\n\n') if len(c.strip()) > 40]
                        for chunk in chunks:
                            self.documents_cache.append({
                                "source": file_name,
                                "page": 1,
                                "text": chunk
                            })
                except Exception:
                    pass

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self.documents_cache, f, ensure_ascii=False, indent=2)
            print(f"[RAGAgent] Saved {len(self.documents_cache)} chunks to {cache_path}")
        except Exception as e:
            print(f"[RAGAgent] Failed to save corpus cache: {e}")

    def search_documents(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Mencari potongan dokumen yang relevan menggunakan pencocokan kata kunci."""
        if not self.documents_cache:
            return []

        keywords = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
        scored = []
        for doc in self.documents_cache:
            score = 0
            text_lower = doc["text"].lower()
            for kw in keywords:
                if kw in text_lower:
                    score += text_lower.count(kw)
            if score > 0:
                scored.append((score, doc))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored[:top_k]]

        if not results:
            results = self.documents_cache[:top_k]

        return results

    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "Informasi umum beasiswa LPDP 2025/2026."
        return "\n\n".join([c["text"] for c in chunks])

    def ask(self, question: str, cv_info: str = "Tidak ada CV diunggah", preferences: str = "Tidak ada preferensi") -> str:
        """Menghasilkan jawaban lengkap dari Gemma secara synchronous dengan Live Web Scraping."""
        import time
        
        # Perform Live Web Scraping if user asks about a specific university
        web_res = fetch_live_university_web_content(question)
        web_context = web_res.get("content", "") or "Tidak ada data scraping web khusus."

        chunks = self.search_documents(question, top_k=4)
        context = self.format_context(chunks)[:2500]

        prompt = self.system_prompt_template.format(
            context=context,
            web_context=web_context,
            question=question,
            cv_info=cv_info[:2000] if cv_info else "Tidak ada CV diunggah",
            preferences=preferences
        )

        if not self.gemma_ready or not self.client:
            return "Maaf, koneksi ke layanan Asisten SAPA LPDP sedang tidak tersedia."

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=GEMMA_MODEL_NAME,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
                        continue
                    return "Asisten SAPA LPDP sedang menerima trafik tinggi dari server Google Cloud Vertex AI. Silakan tunggu beberapa detik dan klik/kirim ulang pertanyaan Anda."
                return f"Terjadi kendala saat memproses permintaan: {err_str}"

        return "Asisten SAPA LPDP sedang sibuk. Silakan coba kembali dalam beberapa saat."
