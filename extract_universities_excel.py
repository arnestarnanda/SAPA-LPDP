import os
import json
import re
import pandas as pd

print("🚀 Instant Extract & Mapping University Directory from Corpus Cache...")

lpdp_dir = os.path.join(os.path.dirname(__file__), "LPDP")
corpus_cache_path = os.path.join(lpdp_dir, "corpus_cache.json")

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

if os.path.exists(corpus_cache_path):
    with open(corpus_cache_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for c in chunks:
        src = c.get("source", "")
        text = c.get("text", "")

        kategori = "LPDP"
        if "BIB" in src or "Kemenag" in src:
            kategori = "BIB Kemenag"
        elif "Garuda" in src:
            kategori = "Garuda Sarjana"

        is_dalam_negeri = "Dalam Negeri" in src or ("Luar Negeri" not in src and "Foreign" not in src)
        lokasi = "Dalam Negeri" if is_dalam_negeri else "Luar Negeri"
        default_negara = "Indonesia" if is_dalam_negeri else "Luar Negeri"

        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()
            if len(line_str) < 6:
                continue

            if any(kw in line_str for kw in ["Universitas", "University", "Institute", "Institut", "Politeknik", "College", "Sekolah Tinggi", "UIN"]):
                clean_line = re.sub(r'^\d+[\.\s\-]*', '', line_str).strip()

                jenjang = "S2"
                if "S1" in clean_line or "Sarjana" in clean_line:
                    jenjang = "S1"
                elif "S3" in clean_line or "Doktor" in clean_line:
                    jenjang = "S3"
                elif "Spesialis" in clean_line:
                    jenjang = "Spesialis"
                elif "Magister" in clean_line or "S2" in clean_line:
                    jenjang = "S2"

                parts = [p.strip() for p in re.split(r'\s{2,}|\t|\|', clean_line) if len(p.strip()) > 1]
                univ_name = parts[0] if parts else clean_line
                univ_name = re.sub(r'^(Magister|Doktor|Sarjana|S1|S2|S3)\s+', '', univ_name)[:90]

                prodi = "Semua Program Studi / Umum"
                if len(parts) > 1 and not any(k in parts[1] for k in ["S1", "S2", "S3", "Magister", "Doktor"]):
                    prodi = parts[1][:90]

                negara = default_negara
                if not is_dalam_negeri:
                    for c_kw in ["Inggris", "Amerika Serikat", "Australia", "Jepang", "Jerman", "Singapura", "Belanda", "Kanada", "Korea Selatan"]:
                        if c_kw in clean_line:
                            negara = c_kw
                            break

                website = get_website_url(univ_name)

                records.append({
                    "kategori": kategori,
                    "universitas": univ_name,
                    "prodi": prodi,
                    "jenjang": jenjang,
                    "negara": negara,
                    "lokasi": lokasi,
                    "website": website,
                    "sumber": src
                })

df = pd.DataFrame(records)
if not df.empty:
    df.drop_duplicates(subset=["universitas", "prodi", "jenjang", "kategori"], inplace=True)

excel_path = os.path.join(lpdp_dir, "daftar_perguruan_tinggi.xlsx")
df.to_excel(excel_path, index=False)
print(f"✅ Instant Extracted {len(df)} rows to Excel: {excel_path}")

json_path = os.path.join(lpdp_dir, "daftar_perguruan_tinggi.json")
df.to_json(json_path, orient="records", force_ascii=False, indent=2)
print(f"✅ Instant Extracted {len(df)} rows to JSON: {json_path}")
