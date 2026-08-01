# 🎓 SAPA LPDP — Scholarship Application & Preparation Assistant

[![Built with Gemma](https://img.shields.io/badge/Model-Gemma_4_26B_MaaS-orange.svg)](https://cloud.google.com/vertex-ai)
[![Google Cloud Vertex AI](https://img.shields.io/badge/Google_Cloud-Vertex_AI-4285F4.svg)](https://cloud.google.com/)
[![Built with Antigravity](https://img.shields.io/badge/Agent-Google_Antigravity-4285F4.svg)](https://antigravity.google.com)
[![FastAPI](https://img.shields.io/badge/UI-FastAPI_Web_Preview-009688.svg)](https://fastapi.tiangolo.com/)

> **SAPA LPDP (Scholarship Application & Preparation Assistant)** adalah asisten AI interaktif dan konsultan pintar untuk pendaftaran Beasiswa LPDP (Lembaga Pengelola Dana Pendidikan) resmi. Ditenagai oleh **Google Gemma 4 26B** melalui **Google Cloud Vertex AI Model Garden**, platform ini menyediakan penelusuran dokumen RAG, analisis kelayakan CV, *Live Web Scraping* persyarat kampus, serta database **14.442 Perguruan Tinggi Mitra LPDP**.

Dikembangkan untuk **Gemma Hackathon – Cloud Next Extended**.

---

## 📌 Problem Statement
Memahami ratusan halaman buku panduan Beasiswa LPDP, kebijakan bahasa (IELTS/TOEFL), serta syarat admission perguruan tinggi tujuan (seperti ITB, UI, UGM, Oxford, Harvard) seringkali membingungkan calon pendaftar. Pendaftar rawan mengalami kesalahan strategi, gagal memenuhi batas IPK, atau memilih jurusan yang tidak tercover dalam daftar resmi LPDP.

---

## 💡 Solution Overview & Core Features

### 1. 💬 Chat SAPA LPDP & Live University Web Scraper
- **RAG Document Intelligence:** Menjawab pertanyaan berdasarkan **30 Dokumen PDF & DOCX Resmi LPDP** (Panduan Beasiswa LPDP 2025/2026, Dokter Spesialis, Talenta Indonesia, dll.).
- **Live Web Scraping Tool (`fetch_live_university_web_content`):** Saat pengguna menanyakan syarat pendaftaran di perguruan tinggi tertentu (misal: SBM ITB, UI, Oxford), agent secara otomatis mengutip dan men-scrape informasi persyarat langsung dari situs resmi universitas.
- **Attachment CV di Chat:** Pengguna dapat mengunggah CV langsung di dalam obrolan chat untuk dianalisis bersama asisten.

### 2. 📊 Evaluasi & Analisis CV Komprehensif
- Penilaian rekam jejak akademik, kepemimpinan, dan pengalaman organisasi kandidat terhadap kriteria kelayakan reviewer LPDP.
- Menyajikan skor kelayakan, poin kritis, serta rekomendasi perbaikan essay kontribusi.

### 3. 🏛️ Database Perguruan Tinggi Resmi LPDP (14.442 Rekor)
- **Data Terverifikasi:** Memuat **14.442 baris data kampus S2/S3/Spesialis** hasil ekstraksi presisi dari dokumen resmi LPDP.
- **Tautan Website Resmi:** Setiap perguruan tinggi dilengkapi dengan tautan situs web resmi yang dapat diklik langsung oleh pengguna.
- **Fitur Pencarian & Ekspor:** Pencarian real-time, filter jenjang & lokasi, serta ekspor file Excel [daftar_perguruan_tinggi.xlsx](file:///home/devstar9569/SAPA-LPDP/LPDP/daftar_perguruan_tinggi.xlsx).

### 4. 🛡️ 5-Layer Agentic Guardrail System
- **Layer 1 (Input Sanitization):** Batas input 32.000 karakter & HTML escaping (`html.escape`).
- **Layer 2 (Anti-Prompt Injection):** Deteksi ekspresi reguler terhadap frasa pembajakan instruksi (*jailbreak*).
- **Layer 3 (Topic Alignment):** Menjaga fokus obrolan pada domain Beasiswa, Pendidikan, & Karir Akademik.
- **Layer 4 (PII Redaction):** Filtering data pribadi sensitif (API Key, NIK 16 digit, No. Telp, Email) sebelum ditampilkan.
- **Layer 5 (Quota & Context Safety):** Pemangkasan konteks RAG (~2.500 karakter) dan *Exponential Backoff 429 Retry Handler*.

---

## 🏗️ Architecture & Control Flow

```
+-------------------------------------------------------------------+
|               FastAPI Web Interface (Port 8080)                   |
|               Aksen Orange #f26712 & Responsive UI                 |
+---------------------------------+---------------------------------+
                                  |
          +-----------------------+-----------------------+
          |                                               |
          v                                               v
+-----------------------------------+           +-----------------------------------+
|  5-Layer Agentic Guardrails       |           |   Automated CV & Document         |
|  (Input Sanitizer, PII Redaction) |           |   Parser (pdfplumber & docx)      |
+-----------------+-----------------+           +-----------------+-----------------+
                  |                                               |
                  +-----------------------+-----------------------+
                                          |
                                          v
                  +-----------------------------------------------+
                  |  Multi-Format Document RAG & Web Scraper      |
                  |  - RecursiveCharacterTextSplitter (1.910 Ch)  |
                  |  - Live Web Scraper Tool (requests & bs4)     |
                  +-----------------------+-----------------------+
                                          |
                                          v
                  +-----------------------------------------------+
                  |  Google Cloud Vertex AI Model Garden          |
                  |  Model: publishers/google/models/             |
                  |         gemma-4-26b-a4b-it-maas               |
                  +-----------------------------------------------+
```

---

## 📁 File Structure

```
SAPA-LPDP/
├── app.py                         # FastAPI Web Server & API Endpoints (/api/chat, /api/universities, dll)
├── rag_agent.py                   # RAG Agent, Live Web Scraper Tool, & Vertex AI Gemma Integration
├── guardrails.py                  # 5-Layer Agentic Guardrail System Implementation
├── ingest_docs.py                 # RAG Ingestion Script using RecursiveCharacterTextSplitter
├── extract_universities_clean.py  # Precise PDF Table Extraction for LPDP University Directory
├── fix_university_excel.py        # Dataset Cleaning & Misaligned Row Corrector
├── requirements.txt               # Python Dependencies
├── templates/
│   └── index.html                 # Main Web Application UI (HTML/CSS/JS with Orange #f26712 accent)
├── docs/
│   └── Daftar_Perguruan_Tinggi.xlsx# Raw & Refined University Master Dataset
└── LPDP/
    ├── corpus_cache.json          # Pre-parsed RAG Corpus Chunks (1.910 Chunks)
    ├── daftar_perguruan_tinggi.json# Clean University Dataset (JSON format)
    └── daftar_perguruan_tinggi.xlsx# Clean University Dataset (Excel format)
```

---

## 🚀 How to Run in Google Cloud Shell (Web Preview)

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Google Cloud Project:**
   ```bash
   export GOOGLE_CLOUD_PROJECT="kodingdeepdive0826-9569"
   ```

3. **Run RAG Document Ingestion (Optional - Cache Pre-loaded):**
   ```bash
   python3 ingest_docs.py
   ```

4. **Start Web Server:**
   ```bash
   python3 app.py
   ```

5. **Open Cloud Shell Web Preview:**
   - Di bagian kanan atas Cloud Shell, klik ikon **Web Preview** (layar).
   - Pilih **Preview on port 8080**.
   - Aplikasi web **SAPA LPDP** akan terbuka secara live!

---

## 🏆 Hackathon Compliance Checklist

- [x] **Gemma Model Centrality:** Powered by `publishers/google/models/gemma-4-26b-a4b-it-maas` on Vertex AI Model Garden.
- [x] **Antigravity Development:** Designed and orchestrated within Google Antigravity Agentic IDE.
- [x] **Agentic Guardrails:** Integrated 5-layer safety architecture (`guardrails.py`).
- [x] **RAG Chunking Strategy:** Implemented `RecursiveCharacterTextSplitter` (`chunk_size=1000`, `chunk_overlap=200`).
- [x] **Live Agentic Tools:** Built-in **Live Web Scraper Tool** for scraping official university websites.
- [x] **Real-World Dataset:** Ingested 30 official LPDP policy documents and 14.442 university records.
- [x] **Cloud Shell Web Preview Ready:** Native FastAPI execution on port 8080.
