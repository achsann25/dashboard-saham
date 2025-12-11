import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN WEB ---
st.set_page_config(layout="wide", page_title="Dashboard Saham Dunia")

# Judul Utama
st.title('Dashboard Analisis Saham Indonesia 🇮🇩')
st.markdown("---")

# --- 2. SIDEBAR (PENGATURAN) ---
st.sidebar.header('⚙️ Pengaturan Pengguna')

# A. Input Kode Saham (Sistem Hybrid: Dropdown + Manual)
# Daftar saham populer untuk memudahkan pemula
daftar_saham = {
    "BBCA.JK": "Bank Central Asia",
    "BBRI.JK": "Bank Rakyat Indonesia",
    "BMRI.JK": "Bank Mandiri",
    "BBNI.JK": "Bank Negara Indonesia",
    "TLKM.JK": "Telkom Indonesia",
    "ASII.JK": "Astra International",
    "GOTO.JK": "GoTo Gojek Tokopedia",
    "UNVR.JK": "Unilever Indonesia",
    "ICBP.JK": "Indofood CBP",
    "ADRO.JK": "Adaro Energy",
    "ANTM.JK": "Aneka Tambang"
}

# Membuat opsi dropdown
opsi_saham = [f"{kode} - {nama}" for kode, nama in daftar_saham.items()]
opsi_saham.append("🔍 Lainnya (Input Manual)") # Opsi tambahan

# Widget Dropdown
pilihan_user = st.sidebar.selectbox('Pilih Saham:', options=opsi_saham)

# Logika penentuan kode saham
if pilihan_user == "🔍 Lainnya (Input Manual)":
    # Jika pilih manual, munculkan kotak ketik
    kode_saham = st.sidebar.text_input('Ketik Kode Saham (cth: KLBF.JK, AAPL):', 'BBCA.JK')
else:
    # Jika pilih dari list, ambil kodenya saja (bagian depan sebelum tanda ' - ')
    kode_saham = pilihan_user.split(' - ')[0]

# B. Input Tanggal
col1, col2 = st.sidebar.columns(2)
with col1:
    tgl_mulai = st.date_input('Tanggal Mulai', pd.to_datetime('2023-01-01'))
with col2:
    tgl_akhir = st.date_input('Tanggal Akhir', pd.to_datetime('today'))

# C. Pilihan Indikator
st.sidebar.subheader("Pilih Indikator:")
tampilkan_sma50 = st.sidebar.checkbox('Tampilkan SMA 50 (Tren Pendek)')
tampilkan_sma200 = st.sidebar.checkbox('Tampilkan SMA 200 (Tren Panjang)')
tampilkan_rsi = st.sidebar.checkbox('Tampilkan RSI (Momentum)', value=True)

# --- 3. TOMBOL EKSEKUSI UTAMA ---
if st.sidebar.button('🚀 Tampilkan Analisis'):
    
    st.info(f"Sedang mengambil data **{kode_saham}** dari Yahoo Finance...")
    
    try:
        # --- A. PROSES DATA (BACKEND) ---
        # 1. Download Data
        df = yf.download(kode_saham, start=tgl_mulai, end=tgl_akhir)
        
        # 2. FIX PENTING: Ratakan kolom MultiIndex (Masalah yfinance terbaru)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # 3. Cek apakah data berhasil didapat
        if df.empty:
            st.error(f"Data tidak ditemukan untuk kode **{kode_saham}**. Periksa ejaan atau koneksi internet.")
        else:
            # 4. Hitung Moving Average (SMA)
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # 5. Hitung RSI (Relative Strength Index)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # --- B. SISTEM CERDAS (SMART INSIGHTS) ---
            # Ambil data hari terakhir (paling kanan)
            last_price = df['Close'].iloc[-1]
            last_open = df['Open'].iloc[-1]
            last_sma200 = df['SMA_200'].iloc[-1]
            last_rsi = df['RSI'].iloc[-1]
            
            # Tentukan Status Tren
            if last_price > last_sma200:
                tren_status = "📈 BULLISH (Uptrend)"
                tren_desc = "Harga di ATAS rata-rata jangka panjang."
            else:
                tren_status = "📉 BEARISH (Downtrend)"
                tren_desc = "Harga di BAWAH rata-rata jangka panjang."
            
            # Tentukan Status RSI
            if last_rsi > 70:
                rsi_status = "⚠️ Overbought (Mahal)"
                rsi_desc = "Hati-hati, potensi koreksi turun."
            elif last_rsi < 30:
                rsi_status = "✅ Oversold (Murah)"
                rsi_desc = "Potensi rebound/naik."
            else:
                rsi_status = "Neutral"
                rsi_desc = "Harga wajar (tengah-tengah)."

            # --- C. TAMPILAN DASHBOARD (FRONTEND) ---
            
            # 1. Judul Saham yang Dipilih
            nama_perusahaan = daftar_saham.get(kode_saham, kode_saham) # Cek nama di kamus, kalau tidak ada pakai kode saja
            st.subheader(f'Laporan Analisis: {nama_perusahaan}')
            
            # 2. Panel Metrik (Ringkasan)
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                perubahan = last_price - last_open
                st.metric("Harga Terakhir", f"Rp {last_price:,.0f}", f"{perubahan:,.0f}")
            
            with col_b:
                st.metric("Status Tren (SMA 200)", tren_status)
                st.caption(tren_desc)
            
            with col_c:
                st.metric("Momentum RSI", f"{last_rsi:.2f}", rsi_status if rsi_status != "Neutral" else None)
                st.caption(rsi_desc)

            st.markdown("---")

            # 3. Grafik Harga (Candlestick + SMA)
            st.subheader('Grafik Pergerakan Harga')
            
            fig = go.Figure()

            # Candlestick
            fig.add_trace(go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='Harga Pasar'))

            # Garis SMA 50
            if tampilkan_sma50:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], 
                                        line=dict(color='orange', width=1.5), name='SMA 50 (Short)'))
            
            # Garis SMA 200
            if tampilkan_sma200:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], 
                                        line=dict(color='blue', width=2), name='SMA 200 (Long)'))

            fig.update_layout(height=500, xaxis_rangeslider_visible=False, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)

            # 4. Grafik RSI (Momentum)
            if tampilkan_rsi:
                st.subheader('Indikator RSI (Momentum)')
                fig_rsi = go.Figure()
                
                # Garis RSI
                fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], 
                                            line=dict(color='purple', width=2), name='RSI'))
                
                # Garis Batas
                fig_rsi.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="Jenuh Beli (70)")
                fig_rsi.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="Jenuh Jual (30)")
                
                fig_rsi.update_layout(height=300, yaxis_range=[0, 100], template='plotly_white')
                st.plotly_chart(fig_rsi, use_container_width=True)

            # 5. Tabel Data (Opsional)
            with st.expander("Lihat Data Mentah (Tabel)"):
                st.write(df.tail(10))
            
    except Exception as e:
        st.error(f"Terjadi kesalahan teknis: {e}")

else:
    # Tampilan Awal sebelum tombol ditekan
    st.info("👈 Silakan pilih saham di menu sebelah kiri dan tekan tombol 'Tampilkan Analisis'")

