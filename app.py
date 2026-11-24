"""
app.py — Entry point aplikasi Streamlit Online Retail Analytics.
"""

import streamlit as st
import pandas as pd

# Konfigurasi Halaman (Harus dipanggil paling pertama!)
st.set_page_config(
    page_title="Online Retail Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kustomisasi CSS untuk UI/UX yang elegan
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    /* Premium KPI Cards */
    .premium-card {
        background: var(--secondary-background-color);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid var(--background-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.05);
        display: flex;
        align-items: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
    }
    .premium-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
    }
    .card-icon {
        background-color: rgba(15, 118, 110, 0.15);
        color: #14B8A6;
        border-radius: 12px;
        width: 55px;
        height: 55px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 24px;
        margin-right: 15px;
        flex-shrink: 0;
    }
    .card-content {
        display: flex;
        flex-direction: column;
    }
    .card-title {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
    }
    .card-value {
        color: var(--text-color);
        font-size: 1.6rem;
        font-weight: 800;
    }
    
    /* Header/Title */
    .main-header {
        font-size: 2.2rem;
        color: var(--text-color);
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.1rem;
        color: var(--text-color);
        opacity: 0.8;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Spacing adjustments */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Import modul internal
from src.data_loader import load_and_combine
from src.preprocessing import preprocess_data
from src.analytics import calculate_kpi, get_monthly_sales_trend, get_top_products, get_country_activity
from src.visualization import (
    plot_monthly_trend, plot_transactions_trend, plot_top_products_bar, plot_country_distribution,
    plot_elbow_method, plot_rfm_scatter_3d, plot_rfm_radar
)
from src.segmentation import calculate_rfm, perform_kmeans_clustering, get_cluster_summary, get_elbow_data
from streamlit_option_menu import option_menu

# ==============================================================================
# CACHED DATA LOADING & PREPROCESSING
# ==============================================================================

STRING_COLUMNS = ['Invoice', 'StockCode', 'Description', 'Country', 'TransactionType']


@st.cache_resource(show_spinner="Memuat dataset...")
def get_data():
    """
    Memuat dan membersihkan data sekali per server, lalu dibagi ke semua sesi.

    cache_resource (bukan cache_data) agar dataframe ~1 juta baris tidak
    disalin ulang di setiap interaksi. Hanya yang dipakai halaman yang disimpan:
    data sales, tabel RFM per pelanggan, dan 100 baris contoh data bersih.
    Kode di bawah tidak boleh mengubah dataframe ini secara in-place.
    """
    df_raw, load_info = load_and_combine()
    df_clean, df_sales, df_rfm, audit_log = preprocess_data(df_raw)
    del df_raw
    clean_preview = df_clean.head(100).copy()
    clean_rows = len(df_clean)
    del df_clean
    rfm_df = calculate_rfm(df_rfm)
    del df_rfm
    for col in STRING_COLUMNS:
        df_sales[col] = df_sales[col].astype('string[pyarrow]')
    return clean_preview, clean_rows, df_sales, rfm_df, load_info, audit_log

# Muat data
try:
    clean_preview, clean_rows, df_sales, rfm_df, load_info, audit_log = get_data()
except Exception as e:
    st.error(f"Gagal memuat dataset: {str(e)}")
    st.info("Pastikan file 'online_retail_II.xlsx' ada di dalam folder 'data/'.")
    st.stop()


# ==============================================================================
# SIDEBAR NAVIGATION & FILTERS
# ==============================================================================
with st.sidebar:
    st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 25px; margin-top: 10px;">
            <div style="background: linear-gradient(135deg, #0F766E, #14B8A6); padding: 12px; border-radius: 12px; margin-right: 15px; box-shadow: 0 4px 6px rgba(15,118,110,0.2); width: 55px; height: 55px; display: flex; justify-content: center; align-items: center;">
                <i class="fa-solid fa-chart-pie" style="color: white; font-size: 26px;"></i>
            </div>
            <h2 style="margin: 0; color: var(--text-color); font-size: 1.4rem; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2;">Online Retail<br><span style="color: #0F766E;">Analytics</span></h2>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Menu Navigasi Premium
    menu = option_menu(
        menu_title=None,
        options=["Ringkasan Dashboard", "Eksplorasi Data", "Segmentasi Pelanggan"],
        icons=["bar-chart-fill", "database-fill", "people-fill"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#0F766E", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "rgba(15, 118, 110, 0.15)"},
            "nav-link-selected": {"background-color": "#0F766E", "color": "white", "icon-color": "white"},
        }
    )
    
    st.markdown("---")
    
    # Filter Global (hanya aktif untuk Dashboard Overview untuk sekarang)
    if menu == "Ringkasan Dashboard":
        st.markdown('<h3 style="color: var(--text-color); font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;"><i class="fa-solid fa-filter" style="color: #0F766E; margin-right: 8px;"></i> Filter Data</h3>', unsafe_allow_html=True)
        
        # Filter Negara
        all_countries = ['Semua Negara'] + sorted(list(df_sales['Country'].unique()))
        selected_country = st.selectbox("Pilih Negara", all_countries, index=0)
        
        # Filter Tahun
        all_years = ['Semua Tahun'] + sorted([str(y) for y in df_sales['InvoiceDate'].dt.year.unique()])
        selected_year_str = st.selectbox("Pilih Tahun", all_years, index=0)
        
        if st.button("Reset Filter"):
            st.rerun()

# Terapkan Filter
df_filtered = df_sales  # filter di bawah membuat frame baru; jangan diubah in-place
if menu == "Ringkasan Dashboard":
    if selected_country != 'Semua Negara':
        df_filtered = df_filtered[df_filtered['Country'] == selected_country]
    if selected_year_str != 'Semua Tahun':
        df_filtered = df_filtered[df_filtered['InvoiceDate'].dt.year == int(selected_year_str)]

# ==============================================================================
# HALAMAN 1: DASHBOARD OVERVIEW
# ==============================================================================
if menu == "Ringkasan Dashboard":
    st.markdown('<p class="main-header">Dashboard Penjualan</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ringkasan performa penjualan dan tren transaksi</p>', unsafe_allow_html=True)
    
    if df_filtered.empty:
        st.warning("Tidak ada data untuk kombinasi filter yang dipilih.")
    else:
        # --- 1. KPI Cards ---
        kpi = calculate_kpi(df_filtered)
        
        def premium_card(title, value, icon_class):
            return f"""
            <div class="premium-card">
                <div class="card-icon"><i class="{icon_class}"></i></div>
                <div class="card-content">
                    <div class="card-title">{title}</div>
                    <div class="card-value">{value}</div>
                </div>
            </div>
            """
            
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(premium_card("Net Revenue", f"£ {kpi['net_revenue']:,.0f}", "fa-solid fa-pound-sign"), unsafe_allow_html=True)
        with col2:
            st.markdown(premium_card("Total Transaksi", f"{kpi['transactions']:,}", "fa-solid fa-file-invoice-dollar"), unsafe_allow_html=True)
        with col3:
            st.markdown(premium_card("Pelanggan", f"{kpi['customers']:,}", "fa-solid fa-users"), unsafe_allow_html=True)
        with col4:
            st.markdown(premium_card("Produk Terjual", f"{kpi['products']:,}", "fa-solid fa-box-open"), unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- 2. Tren Chart ---
        trend_df = get_monthly_sales_trend(df_filtered)
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            fig_rev = plot_monthly_trend(trend_df)
            st.plotly_chart(fig_rev, use_container_width=True)
        with t_col2:
            fig_tx = plot_transactions_trend(trend_df)
            st.plotly_chart(fig_tx, use_container_width=True)
            
        # --- 3. Top Produk & Aktivitas Negara ---
        st.markdown("### Analisis Lanjutan")
        p_col1, p_col2 = st.columns(2)
        
        top_qty, top_rev = get_top_products(df_filtered, n=10)
        
        with p_col1:
            fig_top = plot_top_products_bar(top_rev, by_revenue=True)
            st.plotly_chart(fig_top, use_container_width=True)
            
        with p_col2:
            # Tampilkan distribusi negara hanya jika filter 'Semua Negara' dipilih
            if selected_country == 'Semua Negara':
                country_act = get_country_activity(df_filtered)
                fig_country = plot_country_distribution(country_act)
                st.plotly_chart(fig_country, use_container_width=True)
            else:
                fig_qty = plot_top_products_bar(top_qty, by_revenue=False)
                st.plotly_chart(fig_qty, use_container_width=True)


# ==============================================================================
# HALAMAN 2: DATA EXPLORER
# ==============================================================================
elif menu == "Eksplorasi Data":
    st.markdown('<p class="main-header">Eksplorasi Dataset</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Inspeksi data mentah dan hasil preprocessing</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Preview Data Bersih", "Statistik Preprocessing", "Laporan Loading (Tahap 1)"])
    
    with tab1:
        st.markdown("### Data Setelah Preprocessing")
        st.write(f"Menampilkan sampel dari **{clean_rows:,}** total baris data.")
        st.dataframe(clean_preview, use_container_width=True)
        
    with tab2:
        st.markdown("### Laporan Pembersihan Data (Tahap 2)")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Total Baris Awal:** {audit_log['1_initial_rows']:,}")
            st.warning(f"**Anomali Harga (<=0):** {audit_log['3_zero_or_negative_price_rows']:,}")
            st.success(f"**Baris Data Sales:** {audit_log['6_sales_df_rows']:,}")
            st.success(f"**Baris Data RFM:** {audit_log['7_rfm_df_rows']:,}")
            
        with col2:
            st.markdown("**Distribusi Jenis Transaksi:**")
            tx_types = audit_log['4_transaction_types']
            st.write(f"- Valid Sale: **{tx_types['Valid Sale']:,}**")
            st.write(f"- Cancellation: **{tx_types['Cancellation']:,}**")
            st.write(f"- Return/Adjustment: **{tx_types['Return/Adjustment']:,}**")
            st.write(f"- Anomaly: **{tx_types['Anomaly']:,}**")

    with tab3:
        st.markdown("### Metadata Pembacaan File")
        from src.data_loader import format_load_report
        st.text(format_load_report(load_info))

# ==============================================================================
# HALAMAN 3: CUSTOMER SEGMENTATION (RFM)
# ==============================================================================
elif menu == "Segmentasi Pelanggan":
    st.markdown('<p class="main-header">Customer Segmentation (RFM)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Clustering perilaku pembelian menggunakan K-Means Machine Learning</p>', unsafe_allow_html=True)
    
    if rfm_df.empty:
        st.warning("Tidak ada data valid untuk melakukan segmentasi RFM.")
    else:
        # Tabel RFM sudah dihitung sekali di get_data()

        # Pengaturan Clustering di Sidebar atau form
        st.markdown('<h3 style="color: var(--text-color); font-weight: 700; font-size: 1.2rem; margin-bottom: 1rem;"><i class="fa-solid fa-gears" style="color: #0F766E; margin-right: 8px;"></i> Pengaturan K-Means</h3>', unsafe_allow_html=True)
        col_k, col_info = st.columns([1, 2])
        
        with col_k:
            n_clusters = st.slider("Pilih Jumlah Cluster (K):", min_value=2, max_value=8, value=4, step=1)
        
        with col_info:
            st.info(f"""
            Analisis RFM dilakukan pada **{len(rfm_df):,}** pelanggan unik.
            Data telah ditransformasi menggunakan *Log1p* dan distandardisasi 
            sebelum dimasukkan ke algoritma K-Means.
            """)
            
        # Eksekusi K-Means (di-cache per nilai K)
        @st.cache_data(show_spinner=f"Menjalankan K-Means Clustering (K={n_clusters})...")
        def run_clustering(df, k):
            return perform_kmeans_clustering(df, n_clusters=k)
            
        rfm_clustered, rfm_scaled = run_clustering(rfm_df, n_clusters)
        cluster_summary = get_cluster_summary(rfm_clustered)
        
        st.markdown("---")
        
        # --- Visualisasi & Ringkasan ---
        tab_ringkasan, tab_grafik, tab_elbow = st.tabs(["Ringkasan Karakteristik (Tabel)", "Visualisasi Cluster", "Evaluasi (Elbow Method)"])
        
        with tab_ringkasan:
            st.markdown('<h3 style="color: var(--text-color); font-weight: 700; font-size: 1.2rem; margin-bottom: 0.5rem;"><i class="fa-solid fa-clipboard-list" style="color: #0F766E; margin-right: 8px;"></i> Profil Cluster RFM</h3>', unsafe_allow_html=True)
            st.markdown("""
            Gunakan tabel rata-rata (Mean) di bawah ini untuk mengidentifikasi perilaku tiap cluster.
            Misalnya: *Recency* rendah + *Frequency* tinggi = **Loyal Customers**.
            """)
            st.dataframe(cluster_summary, use_container_width=True)
            
            st.markdown("#### Detail Pelanggan")
            st.dataframe(rfm_clustered.sort_values('Monetary', ascending=False).head(100), use_container_width=True)
            
        with tab_grafik:
            c1, c2 = st.columns([1, 1])
            with c1:
                # Plot Radar Chart (pakai data yang discale)
                fig_radar = plot_rfm_radar(rfm_scaled, cluster_summary)
                st.plotly_chart(fig_radar, use_container_width=True)
            with c2:
                # Plot 3D Scatter (pakai data asli)
                fig_3d = plot_rfm_scatter_3d(rfm_clustered)
                st.plotly_chart(fig_3d, use_container_width=True)
                
        with tab_elbow:
            st.markdown("### Evaluasi Jumlah Cluster Ideal")
            st.write("Grafik ini menunjukkan Inersia (WCSS) untuk berbagai nilai K. Cari titik 'siku' (Elbow) di mana penurunan grafik mulai melambat untuk menentukan K paling optimal secara matematis.")
            
            @st.cache_data(show_spinner="Menghitung data evaluasi K-Means...")
            def get_elbow(df):
                return get_elbow_data(df, max_k=10)
                
            elbow_df = get_elbow(rfm_df)
            fig_elbow = plot_elbow_method(elbow_df)
            st.plotly_chart(fig_elbow, use_container_width=True)
