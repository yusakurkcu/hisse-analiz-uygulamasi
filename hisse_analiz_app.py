import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import google.generativeai as genai

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Yapay Zeka Destekli Borsa Analiz Botu",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Önbelleğe Alınan Fonksiyonlar (Performans için)
# -----------------------------------------------------------------------------

@st.cache_data(ttl=86400) # S&P 500 listesini günde bir kez çek
def get_sp500_tickers():
    """Wikipedia'dan S&P 500 hisse senedi sembollerini çeker."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        html = pd.read_html(url, header=0)
        df = html[0]
        return df['Symbol'].tolist()
    except Exception as e:
        st.error(f"S&P 500 listesi çekilirken hata oluştu: {e}. Varsayılan liste kullanılacak.")
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']


@st.cache_data(ttl=900) # Hisse verilerini 15 dakika önbellekte tut
def get_stock_data(ticker, period="1y"):
    """Belirtilen hisse senedi için geçmiş verileri ve şirket bilgilerini çeker."""
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period=period, auto_adjust=False) # auto_adjust=False daha fazla veri sağlar
        info = stock.info
        return hist_data, info
    except Exception:
        # st.error(f"{ticker} için veri çekilirken bir hata oluştu: {e}")
        return None, None

@st.cache_data
def calculate_technicals(df):
    """Verilen DataFrame üzerine teknik göstergeleri hesaplar."""
    if df is not None and not df.empty:
        df.ta.rsi(append=True)
        df.ta.macd(append=True)
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.atr(append=True)
        df.dropna(inplace=True)
    return df

# -----------------------------------------------------------------------------
# Yardımcı Fonksiyonlar ve API Çağrıları
# -----------------------------------------------------------------------------

def estimate_target_price(current_price, atr):
    """Basit bir hedef fiyat tahmini yapar."""
    if pd.isna(atr) or atr == 0:
        atr = current_price * 0.02
    kisa_vade = current_price + (1 * atr)
    orta_vade = current_price + (2 * atr)
    uzun_vade = current_price + (4 * atr)
    return kisa_vade, orta_vade, uzun_vade

def generate_analysis_summary(ticker, info, last_row):
    """Teknik göstergelere dayalı kural tabanlı analiz özeti oluşturur."""
    summary_points = []
    recommendation = "NÖTR"
    buy_signals = 0
    sell_signals = 0

    # RSI Yorumu
    rsi = last_row.get('RSI_14', 50)
    if rsi < 30:
        summary_points.append(f"RSI ({rsi:.2f}) aşırı satım bölgesinde, tepki alımı potansiyeli olabilir.")
        buy_signals += 2
    elif rsi > 70:
        summary_points.append(f"RSI ({rsi:.2f}) aşırı alım bölgesinde, düzeltme riski olabilir.")
        sell_signals += 2
    else:
        summary_points.append(f"RSI ({rsi:.2f}) nötr bölgede.")

    # MACD Yorumu
    macd_line = last_row.get('MACD_12_26_9', 0)
    macd_signal = last_row.get('MACDs_12_26_9', 0)
    if macd_line > macd_signal and last_row.get('MACDh_12_26_9', 0) > 0:
        summary_points.append("MACD, sinyal çizgisini yukarı keserek 'Al' sinyali üretiyor.")
        buy_signals += 1
    elif macd_line < macd_signal and last_row.get('MACDh_12_26_9', 0) < 0:
        summary_points.append("MACD, sinyal çizgisini aşağı keserek 'Sat' sinyali üretiyor.")
        sell_signals += 1

    # Hareketli Ortalamalar Yorumu
    current_price = last_row.get('Close', 0)
    sma_50 = last_row.get('SMA_50', 0)
    sma_200 = last_row.get('SMA_200', 0)
    if current_price > sma_50 and sma_50 > sma_200:
        summary_points.append("Fiyat, 50 ve 200 günlük ortalamaların üzerinde (Golden Cross). Güçlü yükseliş trendi.")
        buy_signals += 2
    elif current_price < sma_50 and current_price < sma_200:
        summary_points.append("Fiyat, 50 ve 200 günlük ortalamaların altında (Death Cross). Düşüş trendi.")
        sell_signals += 2
    elif current_price > sma_50:
         summary_points.append("Fiyat, 50 günlük ortalamanın üzerinde, kısa vadeli görünüm pozitif.")
         buy_signals += 1
    else:
        summary_points.append("Fiyat, 50 günlük ortalamanın altında, kısa vadede baskı olabilir.")
        sell_signals += 1

    if buy_signals > sell_signals + 1: recommendation = "AL"
    elif sell_signals > buy_signals + 1: recommendation = "SAT"

    company_name = info.get('longName', ticker)
    final_summary = f"**{company_name} ({ticker}) Değerlendirmesi:**\n" + "- " + "\n- ".join(summary_points)
    return final_summary, recommendation

def get_gemini_analysis(api_key, ticker, info, last_row):
    """Gemini API'sini kullanarak derinlemesine bir analiz yapar."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # MACD durumunu daha anlaşılır hale getir
        macd_status = "Yükseliş (Pozitif Kesişim)" if last_row.get('MACD_12_26_9', 0) > last_row.get('MACDs_12_26_9', 0) else "Düşüş (Negatif Kesişim)"

        prompt = f"""
        Sen kıdemli bir finansal analistsin. Aşağıdaki verilere dayanarak, {info.get('longName', ticker)} ({ticker}) hissesi için bir yatırımcı raporu hazırla. 
        Raporun dili akıcı, anlaşılır ve profesyonel bir tonda Türkçe olmalı. Hem olumlu yönleri hem de potansiyel riskleri dengeli bir şekilde vurgula. 
        Analizini kısa ve orta vade için yap. Raporun sonunda net bir yatırım tavsiyesi verme, bunun yerine yatırımcının dikkat etmesi gereken noktaları özetle.

        **Temel Bilgiler:**
        - Şirket Adı: {info.get('longName', 'N/A')}
        - Sektör: {info.get('sector', 'N/A')}
        - Piyasa Değeri: {info.get('marketCap', 'N/A'):,} USD
        - F/K Oranı: {info.get('trailingPE', 'N/A')}
        - Şirket Profili: {info.get('longBusinessSummary', 'N/A')[:500]}...

        **Teknik Göstergeler:**
        - Son Kapanış Fiyatı: {last_row.get('Close', 0):.2f} USD
        - RSI (14): {last_row.get('RSI_14', 0):.2f}
        - MACD Durumu: {macd_status}
        - 50 Günlük Ortalama (SMA50): {last_row.get('SMA_50', 0):.2f} USD
        - 200 Günlük Ortalama (SMA200): {last_row.get('SMA_200', 0):.2f} USD

        Bu verileri sentezleyerek kapsamlı bir analiz oluştur.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Yapay zeka analizi oluşturulurken bir hata oluştu: {e}. Lütfen API anahtarınızı kontrol edin."


# -----------------------------------------------------------------------------
# Streamlit Arayüzü
# -----------------------------------------------------------------------------

st.title("🤖 Yapay Zeka Destekli Borsa Analiz ve Tarama Uygulaması")
st.caption("Bu uygulama, yfinance verileri ve yapay zeka ile temel analiz yapar. Yatırım tavsiyesi değildir.")

# Sekmeleri oluştur
tab1, tab2, tab3 = st.tabs(["📊 Hisse Taraması (Screener)", "🔍 Tek Hisse Analizi", "🤖 Yapay Zeka Derin Analiz"])

# -------------------------- KENAR ÇUBUĞU (SIDEBAR) ---------------------------
st.sidebar.header("Ayarlar ve Filtreler")

# Tarama Filtreleri
with st.sidebar.expander("Tarama Filtreleri", expanded=True):
    rsi_filter = st.slider("Maksimum RSI Değeri", 0, 100, 40)
    
    market_cap_options = {
        "Tümü": (0, float('inf')),
        "Mega-Cap (>200B$)": (200e9, float('inf')),
        "Large-Cap (10B$ - 200B$)": (10e9, 200e9),
        "Mid-Cap (2B$ - 10B$)": (2e9, 10e9),
        "Small-Cap (<2B$)": (0, 2e9)
    }
    selected_cap = st.selectbox("Piyasa Değeri", options=list(market_cap_options.keys()))
    min_cap, max_cap = market_cap_options[selected_cap]

# Gemini API Anahtarı
with st.sidebar.expander("Yapay Zeka Ayarları"):
    gemini_api_key = st.text_input("Gemini API Anahtarınız", type="password", help="Google AI Studio'dan ücretsiz alabilirsiniz.")


# -----------------------------------------------------------------------------
# Sekme 1: Hisse Taraması
# -----------------------------------------------------------------------------
with tab1:
    st.header("S&P 500 için Potansiyel Alım Fırsatları")
    
    # Tarama butonu
    if st.button("Taramayı Başlat", type="primary"):
        with st.spinner("S&P 500 taranıyor... Bu işlem birkaç dakika sürebilir."):
            stock_list = get_sp500_tickers()
            results = []
            progress_bar = st.progress(0, text="Başlatılıyor...")

            for i, ticker in enumerate(stock_list):
                progress_bar.progress((i + 1) / len(stock_list), text=f"Taranıyor: {ticker} ({i+1}/{len(stock_list)})")
                
                data, info = get_stock_data(ticker, "6mo")
                if data is not None and not data.empty and info and info.get('marketCap'):
                    # Piyasa değeri filtresi
                    if not (min_cap <= info.get('marketCap', 0) <= max_cap):
                        continue
                    
                    data = calculate_technicals(data)
                    if not data.empty:
                        last_row = data.iloc[-1]
                        current_price = last_row['Close']
                        rsi = last_row['RSI_14']
                        
                        # RSI filtresi
                        if rsi < rsi_filter:
                            signals = [f"RSI Düşük ({rsi:.2f})"]
                            # Diğer sinyal koşulları eklenebilir
                            
                            results.append({
                                "Sembol": ticker,
                                "Şirket Adı": info.get('shortName', ticker),
                                "Sektör": info.get('sector', 'N/A'),
                                "Piyasa Değeri (Milyar $)": f"{(info.get('marketCap', 0) / 1e9):.2f}",
                                "Güncel Fiyat": f"${current_price:.2f}",
                                "RSI": f"{rsi:.2f}",
                                "Alım Sinyali": ", ".join(signals)
                            })
            
            progress_bar.empty()

        if results:
            df_results = pd.DataFrame(results)
            st.success(f"{len(df_results)} adet potansiyel fırsat bulundu!")
            st.dataframe(df_results, use_container_width=True)
        else:
            st.warning("Belirtilen kriterlere uygun hisse bulunamadı.")


# -----------------------------------------------------------------------------
# Paylaşılan Tek Hisse Analiz Bölümü
# -----------------------------------------------------------------------------

def display_single_stock_analysis(ticker_input):
    with st.spinner(f"{ticker_input} için veriler ve analiz hazırlanıyor..."):
        hist_data, info = get_stock_data(ticker_input)

        if hist_data is None or hist_data.empty:
            st.error("Bu hisse için veri bulunamadı. Lütfen sembolü kontrol edin.")
            return None, None, None

        technicals_df = calculate_technicals(hist_data.copy())
        last_row = technicals_df.iloc[-1]
        
        st.subheader(f"{info.get('longName', ticker_input)} ({ticker_input})")
        
        # --- Metrikler ---
        col1, col2, col3, col4 = st.columns(4)
        current_price = last_row['Close']
        prev_close = info.get('previousClose', current_price)
        price_change = current_price - prev_close
        price_change_pct = (price_change / prev_close) * 100
        
        col1.metric("Güncel Fiyat", f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.2f}%)")
        col2.metric("Piyasa Değeri", f"${(info.get('marketCap', 0) / 1e9):.1f}B")
        col3.metric("Hacim", f"{info.get('volume', 0):,}")
        col4.metric("F/K Oranı", f"{info.get('trailingPE', 'N/A')}")
        
        st.divider()

        # --- Analiz ve Grafik ---
        analysis_col, chart_col = st.columns([1, 1.2])

        with analysis_col:
            st.subheader("Kural Tabanlı Teknik Analiz")
            summary, recommendation = generate_analysis_summary(ticker_input, info, last_row)
            
            # Renkli öneri kutusu
            if recommendation == "AL": st.success(f"**Öneri: {recommendation}**")
            elif recommendation == "SAT": st.error(f"**Öneri: {recommendation}**")
            else: st.warning(f"**Öneri: {recommendation}**")
            
            st.markdown(summary)

            st.subheader("Şirket Profili")
            st.info(info.get('longBusinessSummary', 'Şirket özeti bulunamadı.'))

        with chart_col:
            st.subheader("Fiyat Grafiği ve Göstergeler")
            chart_df = technicals_df.tail(252) # Son 1 yıl
            st.line_chart(chart_df[['Close', 'SMA_50', 'SMA_200']])
            st.bar_chart(chart_df['MACDh_12_26_9'])
            st.line_chart(chart_df['RSI_14'])
            st.caption("Üst: Fiyat ve Ortalamalar, Orta: MACD Histogram, Alt: RSI")
        
        return info, last_row, technicals_df


# -----------------------------------------------------------------------------
# Sekme 2: Tek Hisse Analizi
# -----------------------------------------------------------------------------
with tab2:
    st.header("Detaylı Hisse Senedi Analizi")
    ticker_input_tab2 = st.text_input("Analiz için sembol girin (örn: AAPL, TSLA)", "NVDA", key="tab2_input").upper()
    if ticker_input_tab2:
        display_single_stock_analysis(ticker_input_tab2)

# -----------------------------------------------------------------------------
# Sekme 3: Yapay Zeka Derin Analiz
# -----------------------------------------------------------------------------
with tab3:
    st.header("Gemini Yapay Zeka ile Derinlemesine Analiz")
    ticker_input_tab3 = st.text_input("Yapay zeka analizi için sembol girin (örn: MSFT)", "MSFT", key="tab3_input").upper()
    
    if st.button("Yapay Zeka Analizini Oluştur", type="primary"):
        if not gemini_api_key:
            st.error("Lütfen kenar çubuğundaki 'Yapay Zeka Ayarları' bölümüne Gemini API anahtarınızı girin.")
        elif ticker_input_tab3:
            with st.spinner(f"{ticker_input_tab3} için yapay zeka analizi oluşturuluyor..."):
                _, info, last_row = get_stock_data(ticker_input_tab3)
                if info and last_row is not None:
                     # Gemini API'sini çağırmadan önce teknik verileri tekrar hesapla
                    technicals = calculate_technicals(yf.Ticker(ticker_input_tab3).history(period="1y"))
                    if not technicals.empty:
                        last_technical_row = technicals.iloc[-1]
                        ai_summary = get_gemini_analysis(gemini_api_key, ticker_input_tab3, info, last_technical_row)
                        st.markdown(ai_summary)
                    else:
                        st.error("Teknik veri hesaplanamadı, AI analizi oluşturulamıyor.")
                else:
                    st.error(f"{ticker_input_tab3} için veri bulunamadı. Analiz yapılamıyor.")

