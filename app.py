import os
import sys
import pypdf
import docx
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from rag_agent import RAGAgent
from guardrails import GuardrailSystem

app = FastAPI(
    title="SAPA-LPDP — Scholarship Application & Preparation Assistant",
    description="FastAPI Web Application for SAPA-LPDP (Scholarship Application & Preparation Assistant) running natively on Cloud Shell Web Preview"
)

# Template configuration
templates = Jinja2Templates(directory="templates")

# Initialize RAG Agent and Guardrails
agent = RAGAgent()
guardrails = GuardrailSystem()

# --- Request Models ---
class ChatRequest(BaseModel):
    question: str
    cv_info: Optional[str] = "Tidak ada CV diunggah."
    preferences: Optional[str] = "Tidak ada preferensi"

class CvEvalRequest(BaseModel):
    cv_text: str
    preferences: Optional[str] = "Tidak ada preferensi"

class GuardrailTestRequest(BaseModel):
    text: str

# --- Helper Functions ---
def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extracts text from PDF or DOCX file bytes."""
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            import io
            pdf_file = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_file, strict=False)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif filename.lower().endswith(".docx"):
            import io
            docx_file = io.BytesIO(file_bytes)
            doc = docx.Document(docx_file)
            for p in doc.paragraphs:
                if p.text:
                    text += p.text + "\n"
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
    return text

# --- Routes ---

INDEX_HTML_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """Serves the primary Web UI."""
    if os.path.exists(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Index HTML not found</h1>", status_code=404)

@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """Handles CV PDF/DOCX file upload and text extraction."""
    try:
        contents = await file.read()
        extracted_text = extract_text_from_file(contents, file.filename)
        
        if not extracted_text.strip():
            return JSONResponse({
                "success": False,
                "error": "Gagal membaca teks dari file CV atau file kosong."
            }, status_code=400)
            
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "char_count": len(extracted_text),
            "text": extracted_text
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    """Handles chat interaction with Gemma 4 26B and Guardrails protection."""
    user_prompt = payload.question.strip()
    
    # 1. Guardrail Input Check
    guard_res = guardrails.process_request(user_prompt)
    if not guard_res["valid"]:
        return JSONResponse({
            "blocked": True,
            "reason": guard_res["reason"],
            "response": ""
        })

    sanitized_input = guard_res["sanitized_input"]
    cv_summary = payload.cv_info[:3000] if payload.cv_info else "Tidak ada CV diunggah."

    # 2. Gemma AI Model Query
    raw_response = agent.ask(
        question=sanitized_input,
        cv_info=cv_summary,
        preferences=payload.preferences
    )

    # 3. Guardrail Output PII Redaction
    safe_response = guardrails.validate_output(raw_response)

    return JSONResponse({
        "blocked": False,
        "reason": "",
        "response": safe_response
    })

@app.post("/api/evaluate-cv")
async def evaluate_cv_endpoint(payload: CvEvalRequest):
    """Evaluates uploaded CV text against LPDP standards using Gemma 4 26B."""
    if not payload.cv_text.strip():
        raise HTTPException(status_code=400, detail="Teks CV kosong.")

    eval_prompt = f"""Lakukan analisis kelayakan CV berikut untuk Beasiswa LPDP ({payload.preferences}).
Berikan analisis terstruktur meliputi:
1. Skor Kelayakan Keseluruhan (0 - 100)
2. Kekuatan Utama Rekam Jejak / Akademik
3. Area Yang Perlu Ditingkatkan / Catatan Kritis
4. Rekomendasi Langkah Konkret Persiapan Dokumen (Essay, Surat Rekomendasi, LOA)

Teks CV:
{payload.cv_text[:4000]}"""

    raw_eval = agent.ask(eval_prompt, cv_info=payload.cv_text[:3000], preferences=payload.preferences)
    safe_eval = guardrails.validate_output(raw_eval)

    return JSONResponse({"evaluation": safe_eval})

UNIV_JSON_PATH = os.path.join(os.path.dirname(__file__), "LPDP", "daftar_perguruan_tinggi.json")
UNIV_EXCEL_PATH = os.path.join(os.path.dirname(__file__), "LPDP", "daftar_perguruan_tinggi.xlsx")

@app.get("/api/universities")
async def get_universities(
    q: Optional[str] = "",
    kategori: Optional[str] = "Semua",
    jenjang: Optional[str] = "Semua",
    lokasi: Optional[str] = "Semua",
    page: int = 1,
    limit: int = 50
):
    """Returns paginated, searchable university records extracted from official documents."""
    import json
    if not os.path.exists(UNIV_JSON_PATH):
        return JSONResponse({"data": [], "total": 0, "page": page, "total_pages": 0})

    with open(UNIV_JSON_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    filtered = []
    q_clean = q.strip().lower() if q else ""

    for item in records:
        if item.get("jenjang") == "S1":
            continue
        if jenjang and jenjang != "Semua" and item.get("jenjang") != jenjang:
            continue
        if lokasi and lokasi != "Semua" and item.get("lokasi") != lokasi:
            continue
        if q_clean:
            univ_match = q_clean in item.get("universitas", "").lower()
            prodi_match = q_clean in item.get("prodi", "").lower()
            sumber_match = q_clean in item.get("sumber", "").lower()
            if not (univ_match or prodi_match or sumber_match):
                continue

        filtered.append(item)

    total = len(filtered)
    total_pages = (total + limit - 1) // limit if limit > 0 else 1
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_data = filtered[start_idx:end_idx]

    return JSONResponse({
        "data": paginated_data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages
    })

@app.get("/api/download-excel")
async def download_excel():
    """Serves the generated Excel file for download."""
    from fastapi.responses import FileResponse
    if os.path.exists(UNIV_EXCEL_PATH):
        return FileResponse(
            path=UNIV_EXCEL_PATH,
            filename="Daftar_Perguruan_Tinggi_LPDP_BIB_Garuda.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    raise HTTPException(status_code=404, detail="Berkas Excel tidak ditemukan.")

@app.post("/api/test-guardrail")
async def test_guardrail_endpoint(payload: GuardrailTestRequest):
    """Tests user prompt input against Guardrail security filters."""
    result = guardrails.process_request(payload.text)
    return JSONResponse(result)

@app.get("/api/system-status")
async def system_status_endpoint():
    """Returns real-time backend status metrics."""
    return JSONResponse({
        "gemma_ready": agent.gemma_ready,
        "docs_count": len(agent.documents_cache),
        "guardrails_active": True,
        "model": "Gemma 4 26B IT (MaaS)"
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"🚀 Starting SAPA-LPDP Web Server on http://0.0.0.0:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
