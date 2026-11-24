"""
data_loader.py — Modul pembacaan dan validasi dataset Online Retail II.

Fungsi utama:
- Membaca kedua sheet dari file Excel (Year 2009-2010, Year 2010-2011).
- Menggabungkan tanpa menggandakan data (menangani overlap Desember 2010).
- Memvalidasi struktur kolom dan tipe data.
- Melaporkan statistik dataset: jumlah baris, missing values, duplikasi.

Catatan:
- File tidak dimodifikasi. Semua operasi bersifat read-only.
- Modul ini TIDAK melakukan pembersihan data (itu tugas preprocessing.py).
"""

import pandas as pd
import os
from typing import Tuple, Dict, Optional


# Kolom yang diharapkan ada di dataset
EXPECTED_COLUMNS = [
    'Invoice', 'StockCode', 'Description', 'Quantity',
    'InvoiceDate', 'Price', 'Customer ID', 'Country'
]

# Nama sheet yang diharapkan
EXPECTED_SHEETS = ['Year 2009-2010', 'Year 2010-2011']

# Lokasi default dataset
DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'online_retail_II.xlsx'
)
DEFAULT_PARQUET_PATH = os.path.splitext(DEFAULT_DATA_PATH)[0] + '.parquet'


class DataLoadError(Exception):
    """Exception khusus untuk error saat memuat data."""
    pass


def validate_file(filepath: str) -> None:
    """
    Validasi keberadaan dan format file dataset.
    
    Args:
        filepath: Path absolut ke file Excel.
        
    Raises:
        DataLoadError: Jika file tidak ditemukan atau bukan file Excel.
    """
    if not os.path.isfile(filepath):
        raise DataLoadError(
            f"File dataset tidak ditemukan: {filepath}\n"
            f"Pastikan file 'online_retail_II.xlsx' tersedia di folder 'data/'."
        )
    
    if not filepath.lower().endswith(('.xlsx', '.xls')):
        raise DataLoadError(
            f"Format file tidak didukung: {filepath}\n"
            f"File harus berformat Excel (.xlsx atau .xls)."
        )


def validate_sheets(xls: pd.ExcelFile) -> list:
    """
    Validasi sheet yang tersedia dalam workbook Excel.
    
    Args:
        xls: Objek ExcelFile pandas.
        
    Returns:
        List nama sheet yang ditemukan.
        
    Raises:
        DataLoadError: Jika tidak ada sheet yang diharapkan.
    """
    available_sheets = xls.sheet_names
    found_sheets = [s for s in EXPECTED_SHEETS if s in available_sheets]
    
    if not found_sheets:
        raise DataLoadError(
            f"Sheet yang diharapkan tidak ditemukan.\n"
            f"Diharapkan: {EXPECTED_SHEETS}\n"
            f"Tersedia: {available_sheets}"
        )
    
    missing_sheets = [s for s in EXPECTED_SHEETS if s not in available_sheets]
    if missing_sheets:
        print(f"[PERINGATAN] Sheet berikut tidak ditemukan: {missing_sheets}")
        print(f"Hanya akan memproses sheet: {found_sheets}")
    
    return found_sheets


def validate_columns(df: pd.DataFrame, sheet_name: str) -> None:
    """
    Validasi bahwa kolom yang diharapkan tersedia dalam DataFrame.
    
    Args:
        df: DataFrame yang akan divalidasi.
        sheet_name: Nama sheet untuk pesan error.
        
    Raises:
        DataLoadError: Jika kolom penting tidak ditemukan.
    """
    actual_columns = list(df.columns)
    missing_columns = [c for c in EXPECTED_COLUMNS if c not in actual_columns]
    
    if missing_columns:
        raise DataLoadError(
            f"Kolom penting tidak ditemukan di sheet '{sheet_name}'.\n"
            f"Kolom hilang: {missing_columns}\n"
            f"Kolom tersedia: {actual_columns}"
        )


def read_single_sheet(xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
    """
    Membaca satu sheet dari workbook Excel dan melakukan validasi dasar.
    
    Args:
        xls: Objek ExcelFile pandas.
        sheet_name: Nama sheet yang akan dibaca.
        
    Returns:
        DataFrame dari sheet yang dibaca.
        
    Raises:
        DataLoadError: Jika terjadi error saat membaca atau validasi.
    """
    try:
        df = pd.read_excel(xls, sheet_name=sheet_name, engine='openpyxl')
    except Exception as e:
        raise DataLoadError(
            f"Gagal membaca sheet '{sheet_name}': {str(e)}"
        )
    
    if df.empty:
        raise DataLoadError(f"Sheet '{sheet_name}' tidak berisi data.")
    
    validate_columns(df, sheet_name)
    
    return df


def get_sheet_info(df: pd.DataFrame, sheet_name: str) -> Dict:
    """
    Mengumpulkan informasi statistik dari satu sheet.
    
    Args:
        df: DataFrame sheet.
        sheet_name: Nama sheet.
        
    Returns:
        Dictionary berisi statistik sheet.
    """
    missing = df.isnull().sum().to_dict()
    missing_pct = {col: (v / len(df)) * 100 for col, v in missing.items()}
    
    # Hitung invoice pembatalan (diawali 'C')
    invoice_str = df['Invoice'].astype(str)
    cancelled_count = invoice_str.str.startswith('C').sum()
    
    # Customer ID
    customer_filled = df['Customer ID'].notna().sum()
    customer_unique = df['Customer ID'].dropna().nunique()
    
    info = {
        'sheet_name': sheet_name,
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': list(df.columns),
        'dtypes': {col: str(df[col].dtype) for col in df.columns},
        'missing_values': missing,
        'missing_pct': missing_pct,
        'total_missing': df.isnull().sum().sum(),
        'duplicated_rows': int(df.duplicated().sum()),
        'date_range': {
            'min': str(df['InvoiceDate'].min()),
            'max': str(df['InvoiceDate'].max())
        },
        'cancelled_invoices': int(cancelled_count),
        'cancelled_pct': (cancelled_count / len(df)) * 100,
        'customer_id_filled': int(customer_filled),
        'customer_id_unique': int(customer_unique),
        'country_unique': int(df['Country'].nunique()),
        'invoice_unique': int(df['Invoice'].astype(str).nunique()),
    }
    
    return info


def load_and_combine(
    filepath: str = None,
    uploaded_file=None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Membaca kedua sheet dataset dan menggabungkan dengan penanganan overlap.
    
    Dataset Online Retail II memiliki dua sheet dengan periode yang bertumpang
    tindih di Desember 2010 (Sheet 1 berakhir 2010-12-09, Sheet 2 dimulai
    2010-12-01). Ada ~1.088 invoice yang muncul di kedua sheet.
    
    Strategi penggabungan:
    1. Membaca kedua sheet secara terpisah.
    2. Menggabungkan dengan pd.concat().
    3. Menghapus baris duplikat (drop_duplicates) untuk menangani overlap.
    4. Mereset index.
    
    Args:
        filepath: Path ke file Excel. Jika None, gunakan DEFAULT_DATA_PATH.
        uploaded_file: File yang diunggah melalui Streamlit (BytesIO/UploadedFile).
        
    Returns:
        Tuple berisi:
        - DataFrame gabungan yang sudah dideduplikasi.
        - Dictionary berisi metadata/info loading (per sheet dan gabungan).
        
    Raises:
        DataLoadError: Jika terjadi error saat memuat atau memvalidasi data.
    """
    load_info = {
        'source': None,
        'sheets': [],
        'overlap': {},
        'combined': {}
    }
    
    # Sumber cepat: Parquet hasil konversi dari Excel yang sama
    # (dipakai di deployment karena Excel 45 MB terlalu besar untuk Git)
    if uploaded_file is None and filepath is None and os.path.isfile(DEFAULT_PARQUET_PATH):
        df_all = pd.read_parquet(DEFAULT_PARQUET_PATH)
        load_info['source'] = DEFAULT_PARQUET_PATH
        dataframes = []
        for sheet_name in EXPECTED_SHEETS:
            df = df_all[df_all['__sheet'] == sheet_name].drop(columns='__sheet').reset_index(drop=True)
            if df.empty:
                continue
            validate_columns(df, sheet_name)
            load_info['sheets'].append(get_sheet_info(df, sheet_name))
            dataframes.append(df)
        if not dataframes:
            raise DataLoadError("File Parquet tidak berisi sheet yang diharapkan.")
        return _combine(dataframes, load_info)

    # Tentukan sumber data
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file, engine='openpyxl')
            load_info['source'] = 'upload'
        except Exception as e:
            raise DataLoadError(f"Gagal membaca file yang diunggah: {str(e)}")
    else:
        if filepath is None:
            filepath = DEFAULT_DATA_PATH
        validate_file(filepath)
        try:
            xls = pd.ExcelFile(filepath, engine='openpyxl')
            load_info['source'] = filepath
        except Exception as e:
            raise DataLoadError(f"Gagal membaca file Excel: {str(e)}")
    
    # Validasi sheet
    found_sheets = validate_sheets(xls)
    
    # Baca setiap sheet
    dataframes = []
    for sheet_name in found_sheets:
        df = read_single_sheet(xls, sheet_name)
        sheet_info = get_sheet_info(df, sheet_name)
        load_info['sheets'].append(sheet_info)
        dataframes.append(df)
    
    xls.close()

    return _combine(dataframes, load_info)


def _combine(dataframes: list, load_info: Dict) -> Tuple[pd.DataFrame, Dict]:
    """Menggabungkan sheet, menghapus overlap, dan mengisi statistik gabungan."""
    # Gabungkan
    if len(dataframes) == 1:
        df_combined = dataframes[0].copy()
        total_before = len(df_combined)
        duplicates_removed = 0
    else:
        df_combined = pd.concat(dataframes, ignore_index=True)
        total_before = len(df_combined)
        
        # Hapus baris duplikat untuk menangani overlap
        df_combined = df_combined.drop_duplicates()
        df_combined = df_combined.reset_index(drop=True)
        duplicates_removed = total_before - len(df_combined)
    
    # Pastikan tipe data yang benar
    df_combined = _enforce_dtypes(df_combined)
    
    # Info gabungan
    load_info['overlap'] = {
        'total_before_dedup': total_before,
        'duplicates_removed': duplicates_removed,
        'total_after_dedup': len(df_combined),
    }
    
    # Statistik gabungan
    invoice_str = df_combined['Invoice'].astype(str)
    cancelled_count = int(invoice_str.str.startswith('C').sum())
    
    load_info['combined'] = {
        'rows': len(df_combined),
        'columns': len(df_combined.columns),
        'date_range': {
            'min': str(df_combined['InvoiceDate'].min()),
            'max': str(df_combined['InvoiceDate'].max())
        },
        'invoice_unique': int(df_combined['Invoice'].astype(str).nunique()),
        'cancelled_invoices': cancelled_count,
        'customer_id_filled': int(df_combined['Customer ID'].notna().sum()),
        'customer_id_unique': int(df_combined['Customer ID'].dropna().nunique()),
        'customer_id_missing': int(df_combined['Customer ID'].isna().sum()),
        'country_unique': int(df_combined['Country'].nunique()),
        'total_missing': int(df_combined.isnull().sum().sum()),
        'duplicated_rows': int(df_combined.duplicated().sum()),
    }
    
    return df_combined, load_info


def _enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Memastikan tipe data kolom sesuai yang diharapkan.
    Tidak mengubah nilai data, hanya tipe kolom.
    
    Args:
        df: DataFrame yang akan diperbaiki tipe datanya.
        
    Returns:
        DataFrame dengan tipe data yang dikoreksi.
    """
    # Invoice dan StockCode sebagai string
    df['Invoice'] = df['Invoice'].astype(str)
    df['StockCode'] = df['StockCode'].astype(str)
    
    # Description sebagai string (termasuk NaN tetap NaN)
    # Tidak mengkonversi karena akan mengubah NaN menjadi 'nan'
    
    # InvoiceDate sebagai datetime
    if not pd.api.types.is_datetime64_any_dtype(df['InvoiceDate']):
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    
    # Quantity sebagai integer
    # (sudah int64 dari pembacaan Excel, biarkan)
    
    # Price sebagai float
    # (sudah float64 dari pembacaan Excel, biarkan)
    
    # Customer ID sebagai float (karena ada NaN, int tidak bisa menampung NaN di pandas biasa)
    # Biarkan sebagai float64
    
    # Country sebagai string
    df['Country'] = df['Country'].astype(str)
    
    return df


def format_load_report(load_info: Dict) -> str:
    """
    Memformat informasi loading menjadi laporan teks yang mudah dibaca.
    
    Args:
        load_info: Dictionary dari load_and_combine().
        
    Returns:
        String laporan terformat.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("LAPORAN PEMBACAAN DATASET")
    lines.append("=" * 60)
    lines.append(f"Sumber: {load_info['source']}")
    lines.append(f"Jumlah sheet dibaca: {len(load_info['sheets'])}")
    
    for sheet in load_info['sheets']:
        lines.append(f"\n--- Sheet: {sheet['sheet_name']} ---")
        lines.append(f"  Baris: {sheet['rows']:,}")
        lines.append(f"  Kolom: {sheet['columns']}")
        lines.append(f"  Rentang tanggal: {sheet['date_range']['min']} s/d {sheet['date_range']['max']}")
        lines.append(f"  Invoice unik: {sheet['invoice_unique']:,}")
        lines.append(f"  Invoice pembatalan: {sheet['cancelled_invoices']:,} ({sheet['cancelled_pct']:.2f}%)")
        lines.append(f"  Customer ID terisi: {sheet['customer_id_filled']:,}")
        lines.append(f"  Customer ID unik: {sheet['customer_id_unique']:,}")
        lines.append(f"  Negara unik: {sheet['country_unique']}")
        lines.append(f"  Duplikasi baris: {sheet['duplicated_rows']:,}")
        lines.append(f"  Missing values:")
        for col, count in sheet['missing_values'].items():
            if count > 0:
                pct = sheet['missing_pct'][col]
                lines.append(f"    {col}: {count:,} ({pct:.2f}%)")
    
    overlap = load_info['overlap']
    lines.append(f"\n--- Penggabungan ---")
    lines.append(f"  Total baris sebelum deduplikasi: {overlap['total_before_dedup']:,}")
    lines.append(f"  Baris duplikat dihapus: {overlap['duplicates_removed']:,}")
    lines.append(f"  Total baris setelah deduplikasi: {overlap['total_after_dedup']:,}")
    
    combined = load_info['combined']
    lines.append(f"\n--- Dataset Gabungan ---")
    lines.append(f"  Baris: {combined['rows']:,}")
    lines.append(f"  Kolom: {combined['columns']}")
    lines.append(f"  Rentang tanggal: {combined['date_range']['min']} s/d {combined['date_range']['max']}")
    lines.append(f"  Invoice unik: {combined['invoice_unique']:,}")
    lines.append(f"  Invoice pembatalan: {combined['cancelled_invoices']:,}")
    lines.append(f"  Customer ID terisi: {combined['customer_id_filled']:,}")
    lines.append(f"  Customer ID unik: {combined['customer_id_unique']:,}")
    lines.append(f"  Customer ID kosong: {combined['customer_id_missing']:,}")
    lines.append(f"  Negara unik: {combined['country_unique']}")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)


# --- Entry point untuk pengujian mandiri ---
if __name__ == '__main__':
    print("Memuat dataset...")
    try:
        df, info = load_and_combine()
        print(format_load_report(info))
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Tipe data:\n{df.dtypes}")
        print(f"\n5 baris pertama:")
        print(df.head().to_string())
    except DataLoadError as e:
        print(f"[ERROR] {e}")
