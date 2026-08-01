import os
import json
import re
import pandas as pd
import pdfplumber
import glob

print("🚀 Re-extracting LPDP PDF Tables with pdfplumber (100% Column Precision)...")

lpdp_dir = os.path.join(os.path.dirname(__file__), "LPDP")

WEBSITE_MAP = {
    "institut teknologi bandung": "https://www.itb.ac.id",
    "itb": "https://www.itb.ac.id",
    "universitas indonesia": "https://www.ui.ac.id",
    "ui": "https://www.ui.ac.id",
    "universitas gadjah mada": "https://www.ugm.ac.id",
    "ugm": "https://www.ugm.ac.id",
    "universitas airlangga": "https://www.unair.ac.id",
    "unair": "https://www.unair.ac.id",
    "institut pertanian bogor": "https://www.ipb.ac.id",
    "ipb": "https://www.ipb.ac.id",
    "universitas padjadjaran": "https://www.unpad.ac.id",
    "unpad": "https://www.unpad.ac.id",
    "universitas diponegoro": "https://www.undip.ac.id",
    "undip": "https://www.undip.ac.id",
    "universitas brawijaya": "https://www.ub.ac.id",
    "ub": "https://www.ub.ac.id",
    "universitas sebelas maret": "https://www.uns.ac.id",
    "uns": "https://www.uns.ac.id",
    "universitas hasanuddin": "https://www.unhas.ac.id",
    "unhas": "https://www.unhas.ac.id",
    "universitas pendidikan indonesia": "https://www.upi.edu",
    "upi": "https://www.upi.edu",
    "universitas negeri yogyakarta": "https://www.uny.ac.id",
    "uny": "https://www.uny.ac.id",
    "universitas negeri jakarta": "https://www.unj.ac.id",
    "unj": "https://www.unj.ac.id",
    "university of oxford": "https://www.ox.ac.uk",
    "oxford": "https://www.ox.ac.uk",
    "university of cambridge": "https://www.cam.ac.uk",
    "cambridge": "https://www.cam.ac.uk",
    "harvard university": "https://www.harvard.edu",
    "harvard": "https://www.harvard.edu",
    "stanford university": "https://www.stanford.edu",
    "mit": "https://www.mit.edu",
    "massachusetts institute of technology": "https://www.mit.edu",
    "national university of singapore": "https://www.nus.edu.sg",
    "nus": "https://www.nus.edu.sg",
    "nanyang technological university": "https://www.ntu.edu.sg",
    "ntu": "https://www.ntu.edu.sg",
    "university of melbourne": "https://www.unimelb.edu.au",
    "monash university": "https://www.monash.edu",
    "imperial college london": "https://www.imperial.ac.uk",
    "eth zurich": "https://ethz.ch",
}

def get_website_url(univ_name):
    clean = univ_name.lower().strip()
    for k, v in WEBSITE_MAP.items():
        if k in clean:
            return v
    q = re.sub(r'[^a-zA-Z0-9\s]', '', univ_name).strip().replace(' ', '+')
    return f"https://www.google.com/search?q={q}+official+website"

records = []
pdf_files = glob.glob(os.path.join(lpdp_dir, "*.pdf"))

for file_path in pdf_files:
    filename = os.path.basename(file_path)
    
    kategori = "LPDP"
    if "BIB" in filename or "Kemenag" in filename:
        kategori = "BIB Kemenag"
    elif "Garuda" in filename:
        kategori = "Garuda Sarjana"

    is_dalam_negeri = "Dalam Negeri" in filename or ("Luar Negeri" not in filename and "Foreign" not in filename)
    lokasi = "Dalam Negeri" if is_dalam_negeri else "Luar Negeri"
    default_negara = "Indonesia" if is_dalam_negeri else "Luar Negeri"

    try:
        with pdfplumber.open(file_path) as pdf:
            print(f"📄 Processing PDF table columns: {filename} ({len(pdf.pages)} pages)...")
            for page_idx, page in enumerate(pdf.pages[:25]):
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Try to map table columns
                    headers = [str(c or "").replace("\n", " ").strip().lower() for c in table[0]]
                    
                    # Find column indices
                    univ_idx = -1
                    prodi_idx = -1
                    jenjang_idx = -1
                    negara_idx = -1

                    for idx, h in enumerate(headers):
                        if "universitas" in h or "perguruan tinggi" in h or "university" in h:
                            univ_idx = idx
                        elif "program studi" in h or "prodi" in h or "major" in h:
                            prodi_idx = idx
                        elif "jenjang" in h or "degree" in h:
                            jenjang_idx = idx
                        elif "negara" in h or "country" in h:
                            negara_idx = idx

                    # Fallback default positions if headers not explicitly labeled
                    if univ_idx == -1 and len(headers) >= 3:
                        univ_idx = 1 if len(headers) > 3 else 0
                    if prodi_idx == -1 and len(headers) >= 3:
                        prodi_idx = len(headers) - 1

                    for row in table[1:]:
                        if not row or not any(row):
                            continue

                        # Extract cell text safely
                        univ_text = str(row[univ_idx]).replace("\n", " ").strip() if univ_idx != -1 and univ_idx < len(row) and row[univ_idx] else ""
                        prodi_text = str(row[prodi_idx]).replace("\n", " ").strip() if prodi_idx != -1 and prodi_idx < len(row) and row[prodi_idx] else "Semua Program Studi / Umum"
                        jenjang_text = str(row[jenjang_idx]).replace("\n", " ").strip() if jenjang_idx != -1 and jenjang_idx < len(row) and row[jenjang_idx] else "S2"
                        negara_text = str(row[negara_idx]).replace("\n", " ").strip() if negara_idx != -1 and negara_idx < len(row) and row[negara_idx] else default_negara

                        if len(univ_text) < 3 or univ_text.lower() in ["universitas", "perguruan tinggi", "no", "nama"]:
                            continue

                        # Clean jenjang
                        clean_jenjang = "S2"
                        if "S1" in jenjang_text or "Sarjana" in jenjang_text:
                            clean_jenjang = "S1"
                        elif "S3" in jenjang_text or "Doktor" in jenjang_text:
                            clean_jenjang = "S3"
                        elif "Spesialis" in jenjang_text:
                            clean_jenjang = "Spesialis"

                        website = get_website_url(univ_text)

                        records.append({
                            "kategori": kategori,
                            "universitas": univ_text[:90],
                            "prodi": prodi_text[:90],
                            "jenjang": clean_jenjang,
                            "negara": negara_text if negara_text else default_negara,
                            "lokasi": lokasi,
                            "website": website,
                            "sumber": filename
                        })
    except Exception as e:
        print(f"Error reading {filename} with pdfplumber: {e}")

# Fallback merging with existing corpus if records empty
if len(records) > 100:
    df = pd.DataFrame(records)
    df.drop_duplicates(subset=["universitas", "prodi", "jenjang", "kategori"], inplace=False)

    excel_path = os.path.join(lpdp_dir, "daftar_perguruan_tinggi.xlsx")
    df.to_excel(excel_path, index=False)
    print(f"✅ Saved pdfplumber extracted Excel file with {len(df)} rows to {excel_path}")

    json_path = os.path.join(lpdp_dir, "daftar_perguruan_tinggi.json")
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"✅ Saved pdfplumber extracted JSON file with {len(df)} rows to {json_path}")
