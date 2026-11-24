"""
analytics.py — Modul analitik bisnis untuk agregasi data penjualan.

Fungsi-fungsi di sini menerima data penjualan (df_sales) dan filter yang diberikan
pengguna, kemudian menghasilkan metrik agregasi (KPI) dan DataFrame summary untuk divisualisasikan.
"""

import pandas as pd
from typing import Dict, Any, Tuple


def calculate_kpi(df_sales: pd.DataFrame) -> Dict[str, Any]:
    """
    Menghitung metrik KPI utama untuk ringkasan Dashboard.
    
    Args:
        df_sales: DataFrame khusus data penjualan.
        
    Returns:
        Dictionary berisi metrik-metrik KPI.
    """
    # 1. Total Net Revenue (Valid Sale + Cancellation)
    # Pembatalan akan mengurangi nilai karena Quantity-nya negatif
    net_revenue = df_sales['TotalValue'].sum()
    
    # 2. Jumlah Transaksi Valid (Total faktur valid)
    valid_sales = df_sales[df_sales['TransactionType'] == 'Valid Sale']
    total_valid_transactions = valid_sales['Invoice'].nunique()
    
    # 3. Jumlah Pelanggan Teridentifikasi
    total_customers = valid_sales['Customer ID'].nunique()
    
    # 4. Jumlah Produk Unik yang terjual (mengabaikan kode non-produk)
    products_sold = valid_sales[valid_sales['IsProduct']]
    unique_products = products_sold['StockCode'].nunique()
    
    # 5. Rata-rata nilai keranjang (AOV - Average Order Value)
    aov = net_revenue / total_valid_transactions if total_valid_transactions > 0 else 0
    
    # 6. Tingkat Pembatalan (Cancellation Rate)
    cancellations = df_sales[df_sales['TransactionType'] == 'Cancellation']
    total_cancellations = cancellations['Invoice'].nunique()
    cancellation_rate = (total_cancellations / (total_valid_transactions + total_cancellations) * 100) if (total_valid_transactions + total_cancellations) > 0 else 0
    
    return {
        'net_revenue': net_revenue,
        'transactions': total_valid_transactions,
        'customers': total_customers,
        'products': unique_products,
        'aov': aov,
        'cancellation_rate': cancellation_rate
    }


def get_monthly_sales_trend(df_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Menghasilkan tren penjualan kotor dan bersih per bulan.
    """
    # Buat kolom Tahun-Bulan (YYYY-MM)
    df = df_sales[['InvoiceDate', 'TotalValue', 'Invoice']].copy()
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')
    
    # Agregasi
    trend = df.groupby('YearMonth').agg(
        NetRevenue=('TotalValue', 'sum'),
        Transactions=('Invoice', 'nunique')
    ).reset_index()
    
    # Konversi YearMonth ke timestamp untuk plotting yang mudah
    trend['Month'] = trend['YearMonth'].dt.to_timestamp()
    return trend.sort_values('Month')


def get_top_products(df_sales: pd.DataFrame, n: int = 10) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Mendapatkan Top N produk berdasarkan Revenue dan Kuantitas.
    Hanya menggunakan Valid Sale dan produk fisik.
    """
    # Filter hanya penjualan valid untuk produk fisik
    valid_products = df_sales[(df_sales['TransactionType'] == 'Valid Sale') & (df_sales['IsProduct'])]
    
    # Top by Quantity
    top_qty = valid_products.groupby(['StockCode', 'Description']).agg(
        TotalQuantity=('Quantity', 'sum')
    ).reset_index().sort_values('TotalQuantity', ascending=False).head(n)
    
    # Top by Revenue
    top_rev = valid_products.groupby(['StockCode', 'Description']).agg(
        TotalRevenue=('TotalValue', 'sum')
    ).reset_index().sort_values('TotalRevenue', ascending=False).head(n)
    
    return top_qty, top_rev


def get_country_activity(df_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Menghasilkan aktivitas transaksi berdasarkan negara.
    """
    activity = df_sales.groupby('Country').agg(
        TotalRevenue=('TotalValue', 'sum'),
        Transactions=('Invoice', 'nunique'),
        Customers=('Customer ID', 'nunique')
    ).reset_index().sort_values('TotalRevenue', ascending=False)
    
    return activity
