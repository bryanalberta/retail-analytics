import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Konfigurasi Palet Warna
COLOR_PRIMARY = "#3B82F6" # Bright Blue (Aman untuk Dark/Light Mode)
COLOR_ACCENT = "#0F766E"  # Teal
COLOR_BG = "rgba(0,0,0,0)" # Transparent background for Streamlit integration

# Template standar untuk semua chart
CHART_LAYOUT = dict(
    plot_bgcolor=COLOR_BG,
    paper_bgcolor=COLOR_BG,
    font=dict(family="Inter, sans-serif"),
    margin=dict(l=20, r=20, t=40, b=20),
    hovermode="x unified"
)


def plot_monthly_trend(df_trend: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_trend['Month'], 
        y=df_trend['NetRevenue'],
        mode='lines+markers',
        name='Net Revenue',
        line=dict(color=COLOR_PRIMARY, width=3),
        fill='tozeroy',
        fillcolor='rgba(27, 54, 93, 0.1)',
        marker=dict(size=8, color=COLOR_PRIMARY)
    ))
    fig.update_layout(
        title="Tren Pendapatan Bulanan", 
        xaxis_title="", 
        yaxis_title="Pendapatan (£)", 
        xaxis=dict(tickformat="%b %Y", dtick="M1", showgrid=True),
        yaxis=dict(tickformat=",.0f", showgrid=True), 
        **CHART_LAYOUT
    )
    return fig


def plot_transactions_trend(df_trend: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_trend['Month'], y=df_trend['Transactions'],
        name='Transaksi', marker_color=COLOR_ACCENT, marker_line_width=0, opacity=0.8
    ))
    fig.update_layout(
        title="Jumlah Transaksi Bulanan", 
        xaxis_title="", 
        yaxis_title="Jumlah Faktur", 
        xaxis=dict(tickformat="%b %Y", dtick="M1", showgrid=True),
        yaxis=dict(showgrid=True),
        **CHART_LAYOUT
    )
    return fig


def plot_top_products_bar(df_top: pd.DataFrame, by_revenue: bool = True) -> go.Figure:
    y_col = 'TotalRevenue' if by_revenue else 'TotalQuantity'
    title = "Top 10 Produk (Berdasarkan Pendapatan)" if by_revenue else "Top 10 Produk (Berdasarkan Kuantitas)"
    text_format = "£ %{x:,.0f}" if by_revenue else "%{x:,.0f} item"
    df_plot = df_top.sort_values(y_col, ascending=True)
    labels = df_plot['Description'].apply(lambda x: x[:30] + '...' if len(x) > 30 else x)
    
    fig = go.Figure(go.Bar(
        x=df_plot[y_col], y=labels, orientation='h',
        marker_color=COLOR_ACCENT,
        text=df_plot[y_col], texttemplate=text_format, textposition="outside"
    ))
    fig.update_layout(title=title, xaxis_title="", yaxis_title="", xaxis=dict(showticklabels=False), **CHART_LAYOUT)
    fig.update_layout(margin=dict(l=150, r=50, t=40, b=20))
    return fig


def plot_country_distribution(df_country: pd.DataFrame) -> go.Figure:
    df_non_uk = df_country[df_country['Country'] != 'United Kingdom'].head(10).sort_values('TotalRevenue', ascending=True)
    fig = go.Figure(go.Bar(
        x=df_non_uk['TotalRevenue'], y=df_non_uk['Country'], orientation='h', marker_color=COLOR_ACCENT
    ))
    fig.update_layout(title="Top 10 Negara Internasional (Luar UK) by Revenue", xaxis_title="Pendapatan (£)", yaxis_title="", xaxis=dict(tickformat=",.0f"), **CHART_LAYOUT)
    return fig

# ==============================================================================
# FUNGSI VISUALISASI CUSTOMER SEGMENTATION (RFM & K-MEANS)
# ==============================================================================

def plot_elbow_method(df_elbow: pd.DataFrame) -> go.Figure:
    """Membuat line chart untuk Elbow Method."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_elbow['K'], y=df_elbow['Inertia'],
        mode='lines+markers', line=dict(color=COLOR_PRIMARY, width=3),
        marker=dict(size=10, color=COLOR_ACCENT)
    ))
    
    layout = CHART_LAYOUT.copy()
    layout['hovermode'] = 'closest'
    fig.update_layout(
        title="Evaluasi Jumlah Cluster (Elbow Method)",
        xaxis_title="Jumlah Cluster (K)",
        yaxis_title="Inertia (WCSS)",
        xaxis=dict(tickmode='linear', tick0=1, dtick=1),
        **layout
    )
    return fig


def plot_rfm_scatter_3d(rfm_clustered: pd.DataFrame) -> go.Figure:
    """Membuat 3D Scatter Plot untuk visualisasi cluster."""
    # Plotly Express lebih ringkas untuk 3D scatter dengan warna
    
    # Ambil sampel jika data terlalu besar agar browser tidak crash (maksimal 5000)
    df_plot = rfm_clustered.copy()
    if len(df_plot) > 5000:
        df_plot = df_plot.sample(5000, random_state=42)
        
    fig = px.scatter_3d(
        df_plot, 
        x='Recency', y='Frequency', z='Monetary',
        color='Cluster',
        color_discrete_sequence=px.colors.qualitative.Safe, # Palet warna yang bagus
        opacity=0.7,
        size_max=10
    )
    
    # Membiarkan background dihandle secara native
    fig.update_layout(
        title="Distribusi Pelanggan 3D (Sub-sampel jika data besar)",
        scene=dict(
            xaxis_title="Recency (Hari)",
            yaxis_title="Frequency (Trx)",
            zaxis_title="Monetary (£)"
        ),
        paper_bgcolor=COLOR_BG,
        font=dict(family="Inter, sans-serif"),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    return fig


def plot_rfm_radar(df_scaled: pd.DataFrame, cluster_summary: pd.DataFrame) -> go.Figure:
    """
    Membuat Radar Chart menggunakan nilai rata-rata Z-score (Scaled Data) 
    untuk melihat profil per cluster dengan adil.
    """
    # Hitung rata-rata nilai standar (Z-score) untuk tiap cluster
    radar_data = df_scaled.groupby('Cluster').mean().reset_index()
    
    # Sortir agar urutan warnanya konsisten dengan summary tabel
    radar_data['Cluster_ID'] = radar_data['Cluster'].str.extract(r'(\d+)').astype(int)
    radar_data = radar_data.sort_values('Cluster_ID').drop(columns=['Cluster_ID'])
    
    categories = ['Recency', 'Frequency', 'Monetary']
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Safe
    
    for i, row in radar_data.iterrows():
        # Tambahkan elemen pertama ke akhir agar garis tertutup (loop back)
        values = [row['Recency'], row['Frequency'], row['Monetary']]
        values.append(values[0])
        
        cat_closed = categories + [categories[0]]
        
        # Cari populasi cluster dari summary
        pop = cluster_summary.loc[cluster_summary['Cluster'] == row['Cluster'], 'Persentase'].values
        pop_str = f" ({pop[0]}%)" if len(pop) > 0 else ""
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=cat_closed,
            fill='toself',
            name=f"{row['Cluster']}{pop_str}",
            line=dict(color=colors[i % len(colors)])
        ))
        
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, showline=False)
        ),
        showlegend=True,
        title="Profil Cluster (Berdasarkan Z-Score)",
        paper_bgcolor=COLOR_BG,
        font=dict(family="Inter, sans-serif")
    )
    
    return fig
