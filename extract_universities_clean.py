import os
import json
import re
import pandas as pd
import pypdf

print("🚀 Refining Official LPDP University Directory with Precise Extraction...")

lpdp_dir = os.path.join(os.path.dirname(__file__), "LPDP")

target_files = [
    {
        "filename": "Daftar Perguruan Tinggi Tujuan Dalam Negeri Kelompok Pendaftar Umum dan PNSTNIPolri.pdf",
        "lokasi_default": "Dalam Negeri",
        "negara_default": "Indonesia"
    },
    {
        "filename": "Daftar Perguruan Tinggi Tujuan Dalam Negeri Kelompok Pendaftar Afirmasi.pdf",
        "lokasi_default": "Dalam Negeri",
        "negara_default": "Indonesia"
    },
    {
        "filename": "Daftar Perguruan Tinggi Tujuan Luar Negeri.pdf",
        "lokasi_default": "Luar Negeri",
        "negara_default": "Luar Negeri"
    },
    {
        "filename": "Daftar Universitas Unggulan.pdf",
        "lokasi_default": "Luar Negeri",
        "negara_default": "Luar Negeri"
    },
    {
        "filename": "Beasiswa Kerjasama Khusus LPDP Tahap 1 Tahun 2026 Daftar Perguruan Tinggi Dokter Spesialis dan Subspesialis.pdf",
        "lokasi_default": "Dalam Negeri",
        "negara_default": "Indonesia"
    }
]

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
    "california institute of technology": "https://www.caltech.edu",
    "aalborg university": "https://www.aau.dk",
    "university of bologna": "https://www.unibo.it"
}

known_industries = ["digitalisasi", "energi", "kesehatan", "ketahanan pangan", "keanekaragaman hayati", "kedaulatan maritim", "pertahanan", "industri strategis", "sumber daya alam", "kebudayaan", "keolahragaan", "keagamaan"]

known_univs = [
    "Institut Pertanian Bogor", "Institut Teknologi Bandung", "Universitas Indonesia", "Universitas Gadjah Mada",
    "Universitas Diponegoro", "Universitas Airlangga", "Universitas Padjadjaran", "Universitas Brawijaya",
    "Universitas Sebelas Maret", "Universitas Hasanuddin", "Universitas Pendidikan Indonesia", "Universitas Negeri Yogyakarta",
    "Universitas Negeri Jakarta", "Universitas Udayana", "Universitas Andalas", "Universitas Riau", "Universitas Syiah Kuala",
    "Universitas Sumatera Utara", "Universitas Jember", "Universitas Lampung", "Universitas Negeri Malang", "Universitas Negeri Surabaya",
    "Universitas Negeri Semarang", "Universitas Negeri Makassar", "Universitas Negeri Medan", "Universitas Negeri Padang",
    "Universitas Sam Ratulangi", "Universitas Tadulako", "Universitas Mataram", "Universitas Jenderal Soedirman", "Universitas Mulawarman",
    "Aalborg University", "California Institute of Technology (Caltech)", "Harvard University", "University of Oxford",
    "University of Cambridge", "Massachusetts Institute of Technology", "Stanford University", "National University of Singapore",
    "Nanyang Technological University", "Alma Mater Studiorum - University of Bologna", "ETH Zurich", "Imperial College London"
]

def get_website_url(univ_name):
    clean = univ_name.lower().strip()
    for k, v in WEBSITE_MAP.items():
        if k in clean:
            return v
    q = re.sub(r'[^a-zA-Z0-9\s]', '', univ_name).strip().replace(' ', '+')
    return f"https://www.google.com/search?q={q}+official+website"

clean_records = []

for target in target_files:
    file_path = os.path.join(lpdp_dir, target["filename"])
    if not os.path.exists(file_path):
        continue

    print(f"📄 Extracting: {target['filename']}...")
    try:
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages[:35]:
            text = page.extract_text() or ""
            lines = text.split("\n")
            for line in lines:
                line_str = line.strip()
                if len(line_str) < 8:
                    continue

                if any(kw in line_str for kw in ["Universitas", "University", "Institute", "Institut", "Politeknik", "College", "Sekolah Tinggi", "UIN"]):
                    clean_line = re.sub(r'^\d+[\.\s\-]*', '', line_str).strip()

                    if any(header_kw in clean_line.lower() for header_kw in ["strategis universitas", "program studi no", "jenjang studi industri"]):
                        continue

                    jenjang = "S2"
                    if "S1" in clean_line or "Sarjana" in clean_line:
                        jenjang = "S1"
                    elif "S3" in clean_line or "Doktor" in clean_line:
                        jenjang = "S3"
                    elif "Spesialis" in clean_line:
                        jenjang = "Spesialis"
                    elif "Magister" in clean_line or "S2" in clean_line or "Master" in clean_line:
                        jenjang = "S2"

                    # Strip degree prefix
                    clean_line = re.sub(r'^(Master|Magister|Doktor|Sarjana|S1|S2|S3)\s+', '', clean_line, flags=re.IGNORECASE).strip()

                    # Strip industry prefix
                    for ind in known_industries:
                        if clean_line.lower().startswith(ind):
                            clean_line = clean_line[len(ind):].strip()

                    found_univ = ""
                    prodi = "Semua Program Studi / Umum"

                    # Match known univs
                    for u in known_univs:
                        if u.lower() in clean_line.lower():
                            found_univ = u
                            idx = clean_line.lower().find(u.lower()) + len(u)
                            remainder = clean_line[idx:].strip()
                            if len(remainder) > 2:
                                prodi = remainder[:90]
                            break

                    if not found_univ:
                        parts = [p.strip() for p in re.split(r'\s{2,}|\t|\|', clean_line) if len(p.strip()) > 1]
                        found_univ = parts[0] if parts else clean_line[:70]
                        if len(parts) > 1:
                            prodi = parts[1][:90]

                    if len(found_univ) < 4 or found_univ.lower() in ["universitas", "university"]:
                        continue

                    negara = target["negara_default"]
                    if target["lokasi_default"] == "Luar Negeri":
                        for c_kw in ["Denmark", "Inggris", "Amerika Serikat", "Jepang", "Jerman", "Singapura", "Belanda", "Kanada", "Korea Selatan", "Australia", "Italia", "Prancis", "Swiss"]:
                            if c_kw in clean_line:
                                negara = c_kw
                                break

                    website = get_website_url(found_univ)

                    clean_records.append({
                        "kategori": "LPDP",
                        "universitas": found_univ,
                        "prodi": prodi,
                        "jenjang": jenjang,
                        "negara": negara,
                        "lokasi": target["lokasi_default"],
                        "website": website,
                        "sumber": target["filename"]
                    })
    except Exception as e:
        print(f"Error reading {target['filename']}: {e}")

df = pd.DataFrame(clean_records)
if not df.empty:
    df.drop_duplicates(subset=["universitas", "prodi", "jenjang", "kategori"], inplace=True)

excel_path = os.path.join(lpdp_dir, "daftar_perguruan_tinggi.xlsx")
df.to_excel(excel_path, index=False)
print(f"✅ Refined LPDP extracted {len(df)} rows to Excel: {excel_path}")

json_path = os.path.join(lpdp_dir, "daftar_perguruan_tinggi.json")
df.to_json(json_path, orient="records", force_ascii=False, indent=2)
print(f"✅ Refined LPDP extracted {len(df)} rows to JSON: {json_path}")
