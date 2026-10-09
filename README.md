# Online Retail Analytics

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-orange.svg)

Aplikasi *dashboard* analitik **Big Data** untuk mengeksplorasi tren penjualan dan perilaku pelanggan dari dataset e-commerce menggunakan **RFM Analysis** dan algoritma **K-Means Clustering**.

Proyek ini dibangun secara khusus untuk menganalisis dataset "Online Retail II" yang berukuran besar (>1 Juta baris).

---

## 📌 Fitur Utama

1. **Dashboard Penjualan Interaktif**
   - KPI Metrik (Net Revenue, Transaksi Valid, Pelanggan, Produk)
   - Area Chart Tren Pendapatan Bulanan
   - Analisis Top 10 Produk (berdasarkan jumlah & pendapatan)
   - Distribusi penjualan internasional
   - Filter data berdasarkan Negara dan Tahun

2. **Customer Segmentation (RFM & Machine Learning)**
   - Algoritma menghitung skor **Recency**, **Frequency**, dan **Monetary** untuk setiap pembeli aktual.
   - Pemanfaatan algoritma **K-Means Clustering** tanpa pengawasan untuk menemukan kelompok pembeli tersembunyi.
   - Menghilangkan anomali skewness dengan **Log Transform** & **Z-Score Scaling**.
   - Slider jumlah K interaktif dan Radar Chart untuk meraba profil *cluster*.
   - Kurva **Elbow Method** terintegrasi.

3. **Data Explorer & Audit Trail**
   - Menampilkan sampel data mentah yang telah dibersihkan.
   - Laporan rinci (Audit Log) jumlah klasifikasi jenis transaksi: *Valid Sale, Cancellation, Return, Anomaly*.

---

## 📁 Struktur Folder

```text
online-retail-analytics/
├── app.py                  # Entry point aplikasi Streamlit
├── requirements.txt        # Dependensi proyek
├── README.md               # Dokumentasi
├── .gitignore              # Pengecualian file dari Git
├── data/
│   └── online_retail_II.xlsx  # File dataset (HARUS DILETAKKAN DI SINI)
└── src/
    ├── __init__.py
    ├── data_loader.py      # Modul pembacaan dan penyatuan sheet Excel
    ├── preprocessing.py    # Pembersihan anomali dan klasifikasi tipe invoice
    ├── analytics.py        # Logika agregasi dan pembuatan metrik dashboard
    ├── segmentation.py     # Perhitungan algoritma RFM & K-Means
    └── visualization.py    # Logika rendering grafik menggunakan Plotly
```

---

## ⚙️ Persyaratan dan Cara Instalasi

Pastikan Anda memiliki **Python 3.10** atau lebih baru.

1.  **Klon repositori ini** (atau ekstrak foldernya).
2.  **Siapkan Dataset**:
    Unduh dataset `online_retail_II.xlsx` (45 MB) dari Kaggle dan letakkan di dalam folder `data/`.
3.  **Instal library**:
    Disarankan menggunakan *virtual environment*.
    ```bash
    pip install -r requirements.txt
    ```
4.  **Jalankan aplikasi**:
    ```bash
    streamlit run app.py
    ```
5.  Aplikasi akan terbuka otomatis di `http://localhost:8501`.

---

## 📖 Aturan Perhitungan dan Bisnis

Agar pelaporan akurat, aplikasi menerapkan filter ketat terhadap data kotor:
1.  **Missing Description**: Jika kolom nama produk kosong, diisi dengan `"UNKNOWN PRODUCT"`.
2.  **Anomali Harga**: Harga `≤ 0` dianggap sebagai penyesuaian (*adjustment*) akuntansi/sistem dan dikeluarkan dari perhitungan penjualan produk riil.
3.  **Penggabungan Transaksi**: Terdapat hari yang *tumpang tindih* antara Sheet 1 dan Sheet 2 di dataset Excel (Desember 2010). Baris duplikat dihapus secara spesifik agar nilai akhir pendapatan tidak ganda.
4.  **Kode Non-Produk**: Transaksi dengan kode saham tertentu seperti `POST` (Postage), `D` (Discount), dan `BANK CHARGES` akan disaring untuk perhitungan produk teratas & perhitungan RFM.

### Definisi RFM
- **Validitas RFM**: RFM hanya dihitung dari kelompok pelanggan **yang ID-nya diketahui** (tidak `NaN`) dan hanya untuk transaksi sukses (**Valid Sales**, bukan retur/pembatalan).
- **Reference Date**: Mengambil tanggal dari *transaksi terakhir + 1 hari*.
- **Recency**: Jumlah hari dari transaksi pelanggan terakhir sampai ke tanggal referensi.

---

## ⚠️ Keterbatasan Analisis

1.  Sekitar **22,8%** data transaksi tidak memiliki `Customer ID`. Karena hal ini, seperlima dari pendapatan e-commerce **tidak dapat dimasukkan ke dalam analisis Customer Segmentation**. Ini adalah batasan pada pengumpulan data sumber.
2.  Beberapa faktur pembatalan (*awalan 'C'*) muncul tanpa ada faktur pembelian aslinya di dataset ini (kemungkinan dibeli sebelum akhir 2009). Kami memasukkan nilai faktur pembatalan ke total Gross Revenue untuk mendapatkan *Net Revenue*.
3.  Pembacaan Excel 44 MB menggunakan OpenPyXL membutuhkan waktu **~1 menit** pada start awal. `app.py` menggunakan cache memori sehingga kelambatan ini **hanya terjadi satu kali** per siklus server.
