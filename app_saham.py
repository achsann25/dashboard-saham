import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(layout="wide")

# 1. Judul Dashboard
st.title('Dashboard Analisis Saham Indonesia 🇮🇩')
st.markdown("---")

# 2. Sidebar (Kolom Kiri) untuk Input Pengguna
st.sidebar.header('⚙️ Pengaturan Pengguna')

# --- UPDATE: DROPDOWN SAHAM ---
# Daftar Saham Blue Chip / Populer
daftar_saham = {
    "BBCA.JK": "Bank Central Asia",
    "BBRI.JK": "Bank Rakyat Indonesia",
    "BMRI.JK": "Bank Mandiri",
    "BBNI.JK": "Bank Negara Indonesia",
    "TLKM.JK": "Telkom Indonesia",
    "ASII.JK": "Astra International",
    "ICBP.JK": "Indofood CBP",
    "UNVR.JK": "Unilever Indonesia",
    "GOTO.JK": "GoTo Gojek Tokopedia",
    "ADRO.JK": "Adaro Energy",
    "ANTM.JK": "Aneka Tambang",
    "PGAS.JK": "Perusahaan Gas Negara"
}

# Membuat list opsi format: "BBCA.JK - Bank Central Asia"
pilihan_saham = [f"{kode} - {nama}" for kode, nama in daftar_saham.items()]

# Widget Selectbox
saham_dipilih = st.sidebar.selectbox('Pilih Saham:', options=pilihan_saham)

# Ambil kodenya saja (pisahkan dari nama perusahaan)
kode_saham = saham_dipilih.split(' - ')[0]
# ------------------------------

# Input Rentang Tanggal
col1, col2 = st.sidebar.columns(2)
with col1:
    tgl_mulai = st.date_input('Tanggal Mulai', pd.to_datetime('2023-01-01'))
with col2:
    tgl_akhir = st.date_input('Tanggal Akhir', pd.to_datetime('today'))

# Input Indikator
st.sidebar.subheader("Pilih Indikator:")
tampilkan_sma50 = st.sidebar.checkbox('Tampilkan SMA 50 (Jangka Pendek)')
tampilkan_sma200 = st.sidebar.checkbox('Tampilkan SMA 200 (Jangka Panjang)')
tampilkan_rsi = st.sidebar.checkbox('Tampilkan RSI (Momentum)', value=True)

# 3. Tombol Eksekusi
if st.sidebar.button('🚀 Tampilkan Analisis'):
    
    st.info(f"Sedang mengambil data **{kode_saham}**...")
    
    try:
        # Download data
        df = yf.download(kode_saham, start=tgl_mulai, end=tgl_akhir)
        
        # FIX MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty:
            st.error("Data kosong. Cek koneksi atau tanggal.")
        else:
            # Hitung Indikator
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Logika Sinyal
            last_price = df['Close'].iloc[-1]
            last_open = df['Open'].iloc[-1]
            last_sma200 = df['SMA_200'].iloc[-1]
            last_rsi = df['RSI'].iloc[-1]
            
            if last_price > last_sma200:
                tren_status = "📈 BULLISH (Uptrend)"
            else:
                tren_status = "📉 BEARISH (Downtrend)"
            
            if last_rsi > 70:
                rsi_status = "⚠️ Overbought (Mahal)"
            elif last_rsi < 30:
                rsi_status = "✅ Oversold (Murah)"
            else:
                rsi_status = "neutral"

            # Tampilkan Ringkasan
            st.subheader(f'Analisis Saham: {daftar_saham.get(kode_saham, kode_saham)}')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                perubahan = last_price - last_open
                st.metric("Harga Terakhir", f"Rp {last_price:,.0f}", f"{perubahan:,.0f}")
            with col2:
                st.metric("Tren Jangka Panjang", tren_status)
            with col3:
                st.metric("Momentum RSI", f"{last_rsi:.2f}", rsi_status if rsi_status != "neutral" else None)

            st.markdown("---")

            # Visualisasi
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'], name='Harga Pasar'))

            if tampilkan_sma50:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='orange'), name='SMA 50'))
            if tampilkan_sma200:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='blue'), name='SMA 200'))

            fig.update_layout(height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            if tampilkan_rsi:
                st.subheader('Indikator RSI')
                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple'), name='RSI'))
                fig_rsi.add_hline(y=70, line_dash="dot", line_color="red")
                fig_rsi.add_hline(y=30, line_dash="dot", line_color="green")
                fig_rsi.update_layout(height=300, yaxis_range=[0, 100])
                st.plotly_chart(fig_rsi, use_container_width=True)
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

else:
    st.write("👈 Silakan pilih saham di sebelah kiri untuk mulai.")
