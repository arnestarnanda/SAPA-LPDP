import os
import json
import re
import pandas as pd

print("🚀 Fixing and Re-cleaning docs/Daftar_Perguruan_Tinggi.xlsx dataset...")

input_excel_path = os.path.join(os.path.dirname(__file__), "docs", "Daftar_Perguruan_Tinggi.xlsx")
output_excel_path = os.path.join(os.path.dirname(__file__), "LPDP", "daftar_perguruan_tinggi.xlsx")
output_json_path = os.path.join(os.path.dirname(__file__), "LPDP", "daftar_perguruan_tinggi.json")

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
    "university of bologna": "https://www.unibo.it",
    "university of edinburgh": "https://www.ed.ac.uk",
    "university of manchester": "https://www.manchester.ac.uk",
    "university of washington": "https://www.washington.edu",
    "king's college london": "https://www.kcl.ac.uk",
    "purdue university": "https://www.purdue.edu",
    "zhejiang university": "https://www.zju.edu.cn",
    "university of british columbia": "https://www.ubc.ca"
}

def get_website_url(univ_name):
    clean = univ_name.lower().strip()
    for k, v in WEBSITE_MAP.items():
        if k in clean:
            return v
    q = re.sub(r'[^a-zA-Z0-9\s]', '', univ_name).strip().replace(' ', '+')
    return f"https://www.google.com/search?q={q}+official+website"

if not os.path.exists(input_excel_path):
    print(f"Error: {input_excel_path} not found!")
    exit(1)

df_raw = pd.read_excel(input_excel_path)
print(f"Loaded raw file with {len(df_raw)} rows.")

univ_keywords = r'university|universitas|college|institute|institut|politeknik|ecole|universit|hochschule'

swapped_count = 0
clean_records = []

for idx, row in df_raw.iterrows():
    jenjang = str(row.get('jenjang', '')).strip()
    
    # Hapus Jenjang S1 as requested
    if jenjang == 'S1':
        continue

    u = str(row.get('universitas', '')).strip()
    p = str(row.get('prodi', '')).strip()
    negara = str(row.get('negara', 'Indonesia')).strip()
    lokasi = str(row.get('lokasi', 'Dalam Negeri')).strip()
    sumber = str(row.get('sumber', '')).strip()

    # Detect if 'prodi' contains university keywords and 'universitas' does not
    is_p_univ = bool(re.search(univ_keywords, p, re.IGNORECASE))
    is_u_univ = bool(re.search(univ_keywords, u, re.IGNORECASE))

    if is_p_univ and not is_u_univ:
        u, p = p, u
        swapped_count += 1

    # Clean concatenated prefixes
    u = re.sub(r'^(Master|Magister|Doktor|Sarjana|S1|S2|S3|Digitalisasi|Energi|Kesehatan|Ketahanan Pangan)\s+', '', u, flags=re.IGNORECASE).strip()
    
    if len(u) < 3 or u.lower() in ['universitas', 'university', 'perguruan tinggi']:
        continue

    website = get_website_url(u)

    # Note: 'kategori' column omitted as requested ("hapus kolom Kategori yang isinya LPDP semua")
    clean_records.append({
        "universitas": u,
        "prodi": p if p else "Semua Program Studi / Umum",
        "jenjang": jenjang,
        "negara": negara,
        "lokasi": lokasi,
        "website": website,
        "sumber": sumber
    })

df_clean = pd.DataFrame(clean_records)
df_clean.drop_duplicates(subset=["universitas", "prodi", "jenjang"], inplace=True)

# Save to Excel
df_clean.to_excel(output_excel_path, index=False)
print(f"✅ Successfully swapped {swapped_count} misaligned rows and saved {len(df_clean)} cleaned rows to Excel: {output_excel_path}")

# Save to JSON
df_clean.to_json(output_json_path, orient="records", force_ascii=False, indent=2)
print(f"✅ Successfully saved {len(df_clean)} cleaned rows to JSON: {output_json_path}")
