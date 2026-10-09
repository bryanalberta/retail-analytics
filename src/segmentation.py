"""
segmentation.py — Modul untuk Customer Segmentation menggunakan RFM dan K-Means.

Modul ini memproses data penjualan murni (df_rfm) untuk:
1. Menghitung Recency, Frequency, Monetary (RFM).
2. Melakukan transformasi logaritmik dan standarisasi.
3. Menjalankan K-Means Clustering.
4. Menghasilkan ringkasan statistik per cluster.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from typing import Tuple, Dict


def calculate_rfm(df_rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung skor Recency, Frequency, dan Monetary untuk setiap pelanggan.
    
    Args:
        df_rfm: DataFrame transaksi khusus (Valid Sale + Ada Customer ID).
        
    Returns:
        DataFrame dengan indeks Customer ID dan kolom R, F, M.
    """
    # Menentukan Tanggal Referensi (Tanggal transaksi terakhir + 1 hari)
    reference_date = df_rfm['InvoiceDate'].max() + pd.Timedelta(days=1)
    
    # Agregasi RFM
    # Recency: (Reference Date - Transaksi Terakhir).days
    # Frequency: Jumlah faktur/invoice unik
    # Monetary: Total nilai transaksi (Quantity * Price)
    rfm = df_rfm.groupby('Customer ID').agg(
        Recency=('InvoiceDate', lambda x: (reference_date - x.max()).days),
        Frequency=('Invoice', 'nunique'),
        Monetary=('TotalValue', 'sum')
    ).reset_index()
    
    # Filter monetary <= 0 (seharusnya tidak ada karena df_rfm hanya Valid Sale, 
    # tapi kita pastikan untuk keamanan log transform)
    rfm = rfm[rfm['Monetary'] > 0]
    
    return rfm


def perform_kmeans_clustering(rfm_df: pd.DataFrame, n_clusters: int = 4, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Menjalankan algoritma K-Means Clustering pada data RFM.
    Termasuk pipeline preprocessing: Log Transform -> Standard Scaler -> K-Means.
    
    Args:
        rfm_df: DataFrame RFM hasil calculate_rfm().
        n_clusters: Jumlah cluster yang diinginkan.
        random_state: Seed untuk reproduktibilitas.
        
    Returns:
        Tuple berisi:
        - DataFrame RFM yang sudah ditambah kolom 'Cluster'.
        - DataFrame RFM yang sudah distandardisasi (untuk visualisasi radar).
    """
    df = rfm_df.copy()
    
    # 1. Log Transformation untuk mengatasi skewness (distribusi tidak normal)
    # RFM biasanya sangat right-skewed (banyak pelanggan beli sedikit, sedikit pelanggan beli sangat banyak)
    df_log = pd.DataFrame()
    df_log['Recency'] = np.log1p(df['Recency'])
    df_log['Frequency'] = np.log1p(df['Frequency'])
    df_log['Monetary'] = np.log1p(df['Monetary'])
    
    # 2. Standardisasi agar skala fitur sama (mean=0, std=1)
    scaler = StandardScaler()
    scaler.fit(df_log)
    rfm_scaled = scaler.transform(df_log)
    
    df_scaled = pd.DataFrame(rfm_scaled, columns=['Recency', 'Frequency', 'Monetary'], index=df.index)
    
    # 3. K-Means Clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    kmeans.fit(rfm_scaled)
    
    # Tambahkan label cluster ke DataFrame asli
    df['Cluster'] = kmeans.labels_
    df_scaled['Cluster'] = kmeans.labels_
    
    # Ubah label menjadi string yang bersih agar tidak dianggap angka kontinyu oleh Plotly
    df['Cluster'] = df['Cluster'].apply(lambda x: f"Cluster {x}")
    df_scaled['Cluster'] = df_scaled['Cluster'].apply(lambda x: f"Cluster {x}")
    
    return df, df_scaled


def get_cluster_summary(rfm_clustered: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung statistik ringkasan (mean, median, count) untuk tiap cluster.
    Digunakan analis untuk menentukan pelabelan aktual.
    """
    summary = rfm_clustered.groupby('Cluster').agg(
        Pelanggan=('Customer ID', 'count'),
        Mean_Recency=('Recency', 'mean'),
        Median_Recency=('Recency', 'median'),
        Mean_Frequency=('Frequency', 'mean'),
        Median_Frequency=('Frequency', 'median'),
        Mean_Monetary=('Monetary', 'mean'),
        Median_Monetary=('Monetary', 'median')
    ).reset_index()
    
    # Hitung persentase populasi
    total_customers = summary['Pelanggan'].sum()
    summary['Persentase'] = (summary['Pelanggan'] / total_customers * 100).round(1)
    
    # Rapikan format
    summary['Mean_Recency'] = summary['Mean_Recency'].round(1)
    summary['Mean_Frequency'] = summary['Mean_Frequency'].round(1)
    summary['Mean_Monetary'] = summary['Mean_Monetary'].round(2)
    
    # Sortir berdasarkan nilai Monetary agar konsisten (Cluster terbaik di atas)
    summary = summary.sort_values('Mean_Monetary', ascending=False).reset_index(drop=True)
    
    return summary


def get_elbow_data(rfm_df: pd.DataFrame, max_k: int = 10) -> pd.DataFrame:
    """
    Menghitung Inertia (WCSS) untuk berbagai nilai K guna visualisasi Elbow Method.
    """
    # Preprocessing sama seperti perform_kmeans_clustering
    df_log = pd.DataFrame()
    df_log['Recency'] = np.log1p(rfm_df['Recency'])
    df_log['Frequency'] = np.log1p(rfm_df['Frequency'])
    df_log['Monetary'] = np.log1p(rfm_df['Monetary'])
    
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(df_log)
    
    sse = {}
    for k in range(1, max_k + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(rfm_scaled)
        sse[k] = kmeans.inertia_
        
    elbow_df = pd.DataFrame(list(sse.items()), columns=['K', 'Inertia'])
    return elbow_df
