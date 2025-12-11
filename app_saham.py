import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(layout="wide") # Agar tampilan grafik lebar (fullscreen)

# 1. Judul Dashboard
st.title('Dashboard Analisis Saham Indonesia 🇮🇩')
st.markdown("---") # Garis pemisah

# 2. Sidebar (Kolom Kiri) untuk Input Pengguna
st.sidebar.header('⚙️ Pengaturan Pengguna')

# Input Kode Saham
kode_saham = st.sidebar.text_input('Masukkan Kode Saham (Yahoo Finance):', 'BBCA.JK')

# Input Rentang Tanggal
col1, col2 = st.sidebar.columns(2)
with col1:
    tgl_mulai = st.date_input('Tanggal Mulai', pd.to_datetime('2023-01-01'))
with col2:
    tgl_akhir = st.date_input('Tanggal Akhir', pd.to_datetime('today'))

# Input Indikator (Checkbox)
st.sidebar.subheader("Pilih Indikator:")
tampilkan_sma50 = st.sidebar.checkbox('Tampilkan SMA 50 (Jangka Pendek)')
tampilkan_sma200 = st.sidebar.checkbox('Tampilkan SMA 200 (Jangka Panjang)')
tampilkan_rsi = st.sidebar.checkbox('Tampilkan RSI (Momentum)', value=True)

# 3. Tombol Eksekusi
if st.sidebar.button('🚀 Tampilkan Analisis'):
    
    # --- PROSES (Backend) ---
    st.info(f"Sedang mengambil data **{kode_saham}**...")
    
    try:
        # Download data
        df = yf.download(kode_saham, start=tgl_mulai, end=tgl_akhir)
        
        # FIX: Ratakan kolom MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        if df.empty:
            st.error("Data kosong. Cek kode saham atau tanggal.")
        else:
            # --- HITUNG INDIKATOR (Dari Fase 1) ---
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            
            # Hitung RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            st.success("Analisis Selesai!")
            
            # --- VISUALISASI HARGA (Chart 1) ---
            st.subheader(f'📈 Pergerakan Harga & Tren: {kode_saham}')
            
            fig = go.Figure()

            # 1. Candlestick (Harga)
            fig.add_trace(go.Candlestick(x=df.index,
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='Harga Pasar'))

            # 2. Garis SMA (Jika dicentang user)
            if tampilkan_sma50:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], 
                                        line=dict(color='orange', width=1.5), name='SMA 50'))
            
            if tampilkan_sma200:
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], 
                                        line=dict(color='red', width=1.5), name='SMA 200'))

            fig.update_layout(height=600, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # --- VISUALISASI RSI (Chart 2) ---
            if tampilkan_rsi:
                st.subheader('📊 Indikator RSI (Momentum)')
                fig_rsi = go.Figure()
                
                # Garis RSI
                fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], 
                                            line=dict(color='purple', width=2), name='RSI'))
                
                # Garis Batas (30 & 70)
                fig_rsi.add_hline(y=70, line_dash="dot", line_color="red", annotation_text="Overbought")
                fig_rsi.add_hline(y=30, line_dash="dot", line_color="green", annotation_text="Oversold")
                
                fig_rsi.update_layout(height=300, yaxis_range=[0, 100])
                st.plotly_chart(fig_rsi, use_container_width=True)
            
            # Tampilkan Data Mentah di bawah (Opsional)
            with st.expander("Lihat Data Mentah (Tabel)"):
                st.write(df.tail(10))
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")

else:
    st.write("👈 Silakan tekan tombol di sebelah kiri untuk mulai.")