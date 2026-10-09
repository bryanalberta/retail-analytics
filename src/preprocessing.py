"""
preprocessing.py — Modul pembersihan dan transformasi data.

Fungsi utama:
- Membersihkan nilai kosong dan anomali.
- Mengidentifikasi jenis transaksi (Sales, Cancellation, Return, Anomaly).
- Menghitung TotalValue (Pendapatan/Nilai Transaksi).
- Memisahkan data untuk Dashboard Penjualan dan Segmentasi RFM.
- Menghasilkan audit trail (log perubahan jumlah baris).
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict


def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict]:
    """
    Melakukan pipeline preprocessing lengkap pada dataset gabungan.
    
    Args:
        df: DataFrame mentah dari data_loader.py
        
    Returns:
        Tuple berisi:
        - df_cleaned: DataFrame utuh yang sudah dibersihkan dan ditandai
        - df_sales: DataFrame khusus untuk Analisis Penjualan
        - df_rfm: DataFrame khusus untuk Segmentasi Pelanggan
        - audit_log: Dictionary berisi catatan perubahan baris
    """
    audit_log = {}
    audit_log['1_initial_rows'] = len(df)
    
    # 1. Copy dataframe untuk menghindari SettingWithCopyWarning
    df_clean = df.copy()
    
    # 2. Penanganan Missing Values pada Description
    # Kita tidak menghapus baris karena masih bisa berguna untuk analisis pendapatan total
    missing_desc = df_clean['Description'].isna().sum()
    df_clean['Description'] = df_clean['Description'].fillna('UNKNOWN PRODUCT')
    audit_log['2_missing_description_filled'] = int(missing_desc)
    
    # 3. Penanganan Harga (Price)
    # Harga 0 atau negatif biasanya adalah penyesuaian akuntansi (Bad Debt, dll)
    # Kita akan menandainya sebagai anomali
    price_anomaly_mask = df_clean['Price'] <= 0
    audit_log['3_zero_or_negative_price_rows'] = int(price_anomaly_mask.sum())
    
    # 4. Identifikasi Jenis Transaksi
    # A. Pembatalan (Cancellation): Invoice diawali 'C'
    is_cancelled = df_clean['Invoice'].str.startswith('C', na=False)
    
    # B. Retur/Diskon tanpa 'C' (Kuantitas negatif, tapi bukan 'C')
    is_return_without_c = (df_clean['Quantity'] < 0) & (~is_cancelled)
    
    # C. Penjualan Valid (Kuantitas > 0, Harga > 0, bukan pembatalan)
    is_valid_sale = (df_clean['Quantity'] > 0) & (df_clean['Price'] > 0) & (~is_cancelled)
    
    # D. Anomali (Harga <= 0, atau kasus aneh lainnya)
    is_anomaly = price_anomaly_mask | ((df_clean['Quantity'] > 0) & is_cancelled)
    
    # Tambahkan kolom tipe transaksi
    df_clean['TransactionType'] = 'Unknown'
    df_clean.loc[is_valid_sale, 'TransactionType'] = 'Valid Sale'
    df_clean.loc[is_cancelled, 'TransactionType'] = 'Cancellation'
    df_clean.loc[is_return_without_c, 'TransactionType'] = 'Return/Adjustment'
    df_clean.loc[is_anomaly, 'TransactionType'] = 'Anomaly'
    
    audit_log['4_transaction_types'] = {
        'Valid Sale': int(is_valid_sale.sum()),
        'Cancellation': int(is_cancelled.sum()),
        'Return/Adjustment': int(is_return_without_c.sum()),
        'Anomaly': int(is_anomaly.sum())
    }
    
    # 5. Hitung Nilai Transaksi (TotalValue)
    # TotalValue = Quantity * Price
    # Definisi: Nilai kotor per baris transaksi. 
    # Untuk pembatalan/retur, nilainya akan negatif karena Quantity negatif.
    df_clean['TotalValue'] = df_clean['Quantity'] * df_clean['Price']
    
    # 6. Identifikasi Kode Stok Non-Produk (Biaya pengiriman, diskon, dll)
    # Biasanya kode non-produk berupa huruf saja atau kode khusus
    non_product_codes = ['POST', 'D', 'M', 'CRUK', 'DOT', 'BANK CHARGES', 'S', 'AMAZONFEE']
    is_non_product = df_clean['StockCode'].isin(non_product_codes)
    df_clean['IsProduct'] = ~is_non_product
    
    audit_log['5_non_product_transactions'] = int(is_non_product.sum())
    
    # =========================================================================
    # PEMBUATAN DATAFRAME SPESIFIK
    # =========================================================================
    
    # A. DataFrame untuk Analisis Penjualan (Sales Dashboard)
    # Menggunakan Valid Sales + Cancellations (untuk melihat gross vs net).
    # Mengecualikan Anomaly.
    df_sales = df_clean[df_clean['TransactionType'].isin(['Valid Sale', 'Cancellation'])].copy()
    audit_log['6_sales_df_rows'] = len(df_sales)
    
    # B. DataFrame untuk Segmentasi Pelanggan (RFM)
    # Aturan RFM:
    # - Harus memiliki Customer ID
    # - Hanya menggunakan 'Valid Sale' (pembelian positif aktual)
    # - Mengecualikan transaksi non-produk (seperti ongkos kirim) agar nilai Monetary murni dari produk
    rfm_mask = (
        df_clean['Customer ID'].notna() & 
        (df_clean['TransactionType'] == 'Valid Sale') &
        df_clean['IsProduct']
    )
    df_rfm = df_clean[rfm_mask].copy()
    audit_log['7_rfm_df_rows'] = len(df_rfm)
    
    # Validasi sanity check
    assert len(df_sales) <= len(df_clean), "Baris sales melebihi total data"
    assert len(df_rfm) <= len(df_clean), "Baris RFM melebihi total data"
    
    return df_clean, df_sales, df_rfm, audit_log


def format_audit_report(audit_log: Dict) -> str:
    """Memformat audit log menjadi laporan teks."""
    lines = []
    lines.append("=" * 60)
    lines.append("LAPORAN PREPROCESSING DATA")
    lines.append("=" * 60)
    lines.append(f"Total baris awal: {audit_log['1_initial_rows']:,}")
    lines.append(f"Missing Description diisi 'UNKNOWN': {audit_log['2_missing_description_filled']:,}")
    lines.append(f"Baris dengan Harga <= 0 (Anomali): {audit_log['3_zero_or_negative_price_rows']:,}")
    
    lines.append("\nDistribusi Jenis Transaksi:")
    for t_type, count in audit_log['4_transaction_types'].items():
        pct = (count / audit_log['1_initial_rows']) * 100
        lines.append(f"  - {t_type}: {count:,} ({pct:.2f}%)")
        
    lines.append(f"\nTransaksi kode non-produk (Ongkir, Diskon, dll): {audit_log['5_non_product_transactions']:,}")
    
    lines.append("\nHasil Pemisahan Dataset:")
    lines.append(f"  - Data Analisis Penjualan: {audit_log['6_sales_df_rows']:,} baris")
    lines.append(f"  - Data Segmentasi (RFM): {audit_log['7_rfm_df_rows']:,} baris")
    lines.append("=" * 60)
    
    return "\n".join(lines)


# --- Pengujian Mandiri Modul ---
if __name__ == '__main__':
    import os
    import sys
    
    # Tambahkan root path ke sys.path agar bisa import src
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from src.data_loader import load_and_combine
    
    print("Memuat data untuk pengujian preprocessing...")
    try:
        df_raw, load_info = load_and_combine()
        print("Data berhasil dimuat. Memulai preprocessing...")
        
        df_clean, df_sales, df_rfm, audit_log = preprocess_data(df_raw)
        
        print("\n" + format_audit_report(audit_log))
        
        print("\nSanity Check Data Penjualan:")
        print(f"Total Gross Revenue (Valid Sales): £{df_sales[df_sales['TransactionType'] == 'Valid Sale']['TotalValue'].sum():,.2f}")
        print(f"Total Cancelled Value: £{df_sales[df_sales['TransactionType'] == 'Cancellation']['TotalValue'].sum():,.2f}")
        
    except Exception as e:
        print(f"\n[ERROR] Pengujian gagal: {str(e)}")
