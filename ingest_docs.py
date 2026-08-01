import os
import glob
import json
import pdfplumber
import docx
from langchain_text_splitters import RecursiveCharacterTextSplitter

LPDP_DIR = os.path.join(os.path.dirname(__file__), "LPDP")
OUTPUT_CACHE_PATH = os.path.join(LPDP_DIR, "corpus_cache.json")

def extract_text_from_pdf(filepath):
    """Extracts text page-by-page using pdfplumber."""
    pages_data = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for page_num, page in enumerate(pdf.pages[:30], 1):
                page_text = page.extract_text()
                if page_text and len(page_text.strip()) > 30:
                    pages_data.append({"page": page_num, "text": page_text.strip()})
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")
    return pages_data

def extract_text_from_docx(filepath):
    """Extracts text paragraphs from docx."""
    pages_data = []
    try:
        doc = docx.Document(filepath)
        full_text = "\n".join([para.text.strip() for para in doc.paragraphs if len(para.text.strip()) > 20])
        if full_text:
            pages_data.append({"page": 1, "text": full_text})
    except Exception as e:
        print(f"Error reading DOCX {filepath}: {e}")
    return pages_data

def load_documents(directory):
    documents = []
    
    # Load PDFs
    for filepath in glob.glob(os.path.join(directory, "*.pdf")):
        filename = os.path.basename(filepath)
        print(f"📄 Reading PDF: {filename}...")
        pages_data = extract_text_from_pdf(filepath)
        for item in pages_data:
            documents.append({
                "text": item["text"],
                "metadata": {"source": filename, "page": item["page"]}
            })

    # Load DOCXs
    for filepath in glob.glob(os.path.join(directory, "*.docx")):
        filename = os.path.basename(filepath)
        print(f"📄 Reading DOCX: {filename}...")
        pages_data = extract_text_from_docx(filepath)
        for item in pages_data:
            documents.append({
                "text": item["text"],
                "metadata": {"source": filename, "page": item["page"]}
            })

    return documents

def chunk_documents(documents):
    """Splits text using RecursiveCharacterTextSplitter from langchain_text_splitters (Project reference)."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = []
    for doc in documents:
        if not doc["text"].strip():
            continue
        split_texts = text_splitter.split_text(doc["text"])
        for i, chunk in enumerate(split_texts):
            chunks.append({
                "source": doc["metadata"]["source"],
                "page": doc["metadata"]["page"],
                "chunk_index": i,
                "text": chunk
            })
    return chunks

def main():
    print(f"🚀 Starting RAG Document Ingestion from {LPDP_DIR}")
    if not os.path.exists(LPDP_DIR):
        print(f"Directory {LPDP_DIR} does not exist.")
        return

    documents = load_documents(LPDP_DIR)
    print(f"✅ Loaded {len(documents)} document pages. Chunking using RecursiveCharacterTextSplitter...")

    chunks = chunk_documents(documents)
    print(f"✅ Created {len(chunks)} RAG chunks using RecursiveCharacterTextSplitter!")

    with open(OUTPUT_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"🎉 Saved RAG corpus chunks to {OUTPUT_CACHE_PATH}!")

if __name__ == "__main__":
    main()
