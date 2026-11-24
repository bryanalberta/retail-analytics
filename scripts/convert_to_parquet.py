"""
Konversi data/online_retail_II.xlsx -> data/online_retail_II.parquet.

Excel asli (45 MB) terlalu besar untuk Git dan lambat dibaca (~2 menit).
Parquet hasilnya ~6 MB dan dibaca dalam beberapa detik. data_loader.py
memakai Parquet ini secara otomatis bila tersedia.

Jalankan dari root proyek:  python scripts/convert_to_parquet.py
"""
import pandas as pd

SRC = "data/online_retail_II.xlsx"
DST = "data/online_retail_II.parquet"
SHEETS = ["Year 2009-2010", "Year 2010-2011"]

xls = pd.ExcelFile(SRC, engine="openpyxl")
parts = []
for sheet in SHEETS:
    df = pd.read_excel(xls, sheet_name=sheet, engine="openpyxl")
    # Kolom campuran int/str harus satu tipe agar bisa disimpan ke Parquet
    df["Invoice"] = df["Invoice"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["Description"] = df["Description"].map(lambda v: v if pd.isna(v) else str(v))
    df["Country"] = df["Country"].astype(str)
    df["__sheet"] = sheet
    parts.append(df)

out = pd.concat(parts, ignore_index=True)
out["__sheet"] = out["__sheet"].astype("category")
out.to_parquet(DST, index=False, compression="zstd")
print(f"{DST}: {out.shape[0]:,} baris")
