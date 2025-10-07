import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import google.generativeai as genai
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Dil ve Çeviri Ayarları
# -----------------------------------------------------------------------------
LANGUAGES = {
    "TR": {
        "page_title": "Yapay Zeka Destekli Borsa Analiz Botu",
        "app_title": "🤖 Yapay Zeka Destekli Borsa Analiz Botu",
        "app_caption": "Bu uygulama, yfinance verileri ve yapay zeka ile temel analiz yapar. Yatırım tavsiyesi değildir.",
        "tab_screener": "⚡ Otomatik Fırsat Tarama",
        "tab_analysis": "🔍 Tek Hisse Analizi",
        "tab_watchlist": "⭐ İzleme Listem",
        "tab_ai_analysis": "🤖 Yapay Zeka Derin Analiz",
        "sidebar_header": "Ayarlar",
        "sidebar_ai_expander": "Yapay Zeka Ayarları",
        "sidebar_api_key": "Gemini API Anahtarınız",
        "screener_header": "Optimal Alım Fırsatları Taraması",
        "screener_info": "Bu araç, Robinhood'da listelenen tüm hisseleri önceden tanımlanmış optimal bir stratejiye göre tarar. Strateji: RSI < 55, Fiyat > 50-Günlük Ortalama ve yeni bir MACD Al Sinyali.",
        "screener_button": "Optimal Alım Fırsatlarını Bul",
        "screener_spinner": "Robinhood hisseleri taranıyor... Bu işlem birkaç dakika sürebilir, lütfen bekleyin.",
        "screener_success": "adet potansiyel fırsat bulundu!",
        "screener_warning_no_stock": "Mevcut piyasa koşullarında optimal stratejiye uyan hiçbir hisse bulunamadı.",
        "col_symbol": "Sembol", "col_company": "Şirket Adı", "col_sector": "Sektör", "col_price": "Fiyat", "col_rsi": "RSI", "col_signals": "Tespit Edilen Sinyal(ler)",
        # ... (Diğer çeviriler aynı)
        "analysis_header": "Detaylı Hisse Senedi Analizi",
        "analysis_input_label": "Analiz için sembol girin (örn: AAPL, TSLA)",
        "add_to_watchlist": "İzleme Listesine Ekle ⭐",
        "remove_from_watchlist": "Listeden Kaldır",
        "added_to_watchlist": "izleme listenize eklendi!",
        "sub_tab_analysis_charts": "Teknik Analiz & Grafikler",
        "sub_tab_market_sentiment": "Piyasa Gündemi (Haberler & Reddit)",
        "spinner_analysis": "için veriler ve analiz hazırlanıyor...",
        "error_no_data": "Bu hisse için veri bulunamadı. Lütfen sembolü kontrol edin.",
        "error_no_technicals": "Teknik göstergeler hesaplanamadı. Yetersiz veri olabilir.",
        "metric_price": "Güncel Fiyat", "metric_cap": "Piyasa Değeri", "metric_volume": "Hacim", "metric_pe": "F/K Oranı",
        "metric_52w_range": "52 Haftalık Aralık", "metric_beta": "Beta (Volatilite)", "metric_dividend_yield": "Temettü Verimi",
        "subheader_rule_based": "Kural Tabanlı Teknik Analiz",
        "subheader_company_profile": "Şirket Profili",
        "subheader_charts": "Profesyonel Fiyat Grafiği (Mum Grafiği)",
        "chart_caption": "Fiyat, 50-Günlük (Mavi) ve 200-Günlük (Turuncu) Hareketli Ortalamalar",
        "subheader_news": "📰 Son Haberler",
        "subheader_reddit": "💬 Reddit Tartışmaları",
        "info_no_news_24h": "Son 24 saatte ilgili haber bulunamadı.",
        "info_no_news": "Haber bulunamadı.",
        "spinner_reddit": "Reddit gönderileri aranıyor...",
        "info_no_reddit": "Son 24 saatte ilgili Reddit gönderisi bulunamadı.",
        "ai_header": "Gemini Yapay Zeka ile Derinlemesine Analiz",
        "ai_input_label": "Yapay zeka analizi için sembol girin (örn: MSFT)",
        "ai_button": "Yapay Zeka Analizini Oluştur",
        "error_no_api_key": "Lütfen kenar çubuğundaki 'Yapay Zeka Ayarları' bölümüne Gemini API anahtarınızı girin.",
        "spinner_ai": "için yapay zeka analizi oluşturuluyor...",
        "summary_recommendation": "Öneri",
        "recommendation_buy": "AL", "recommendation_sell": "SAT", "recommendation_neutral": "NÖTR",
        "watchlist_header": "Kişisel İzleme Listeniz",
        "watchlist_empty": "İzleme listeniz boş. 'Tek Hisse Analizi' sekmesinden hisse ekleyebilirsiniz.",
    },
    "EN": {
        "page_title": "AI-Powered Stock Analysis Bot",
        "app_title": "🤖 AI-Powered Stock Analysis Bot",
        "app_caption": "This application performs basic analysis using yfinance data and AI. This is not investment advice.",
        "tab_screener": "⚡ Automatic Opportunity Scan",
        "tab_analysis": "🔍 Single Stock Analysis",
        "tab_watchlist": "⭐ My Watchlist",
        "tab_ai_analysis": "🤖 AI Deep Analysis",
        "sidebar_header": "Settings",
        "sidebar_ai_expander": "AI Settings",
        "sidebar_api_key": "Your Gemini API Key",
        "screener_header": "Optimal Buying Opportunity Scan",
        "screener_info": "This tool scans all stocks listed on Robinhood based on a predefined optimal strategy. Strategy: RSI < 55, Price > 50-Day MA, and a new MACD Buy Signal.",
        "screener_button": "Find Optimal Buying Opportunities",
        "screener_spinner": "Scanning Robinhood stocks... This process may take several minutes, please wait.",
        "screener_success": "potential opportunities found!",
        "screener_warning_no_stock": "No stocks matching the optimal strategy were found under current market conditions.",
        "col_symbol": "Symbol", "col_company": "Company Name", "col_sector": "Sector", "col_price": "Price", "col_rsi": "RSI", "col_signals": "Detected Signal(s)",
        # ... (Diğer çeviriler aynı)
        "analysis_header": "Detailed Stock Analysis",
        "analysis_input_label": "Enter symbol for analysis (e.g., AAPL, TSLA)",
        "add_to_watchlist": "Add to Watchlist ⭐",
        "remove_from_watchlist": "Remove",
        "added_to_watchlist": "has been added to your watchlist!",
        "sub_tab_analysis_charts": "Technical Analysis & Charts",
        "sub_tab_market_sentiment": "Market Sentiment (News & Reddit)",
        "spinner_analysis": "Preparing data and analysis for...",
        "error_no_data": "Could not find data for this stock. Please check the symbol.",
        "error_no_technicals": "Could not calculate technical indicators. There might be insufficient data.",
        "metric_price": "Current Price", "metric_cap": "Market Cap", "metric_volume": "Volume", "metric_pe": "P/E Ratio",
        "metric_52w_range": "52-Week Range", "metric_beta": "Beta (Volatility)", "metric_dividend_yield": "Dividend Yield",
        "subheader_rule_based": "Rule-Based Technical Analysis",
        "subheader_company_profile": "Company Profile",
        "subheader_charts": "Professional Price Chart (Candlestick)",
        "chart_caption": "Price, 50-Day (Blue) and 200-Day (Orange) Moving Averages",
        "subheader_news": "📰 Latest News",
        "subheader_reddit": "💬 Reddit Discussions",
        "info_no_news_24h": "No relevant news found in the last 24 hours.",
        "info_no_news": "No news found.",
        "spinner_reddit": "Searching for Reddit posts...",
        "info_no_reddit": "No relevant Reddit posts found in the last 24 hours.",
        "ai_header": "In-Depth Analysis with Gemini AI",
        "ai_input_label": "Enter symbol for AI analysis (e.g., MSFT)",
        "ai_button": "Generate AI Analysis",
        "error_no_api_key": "Please enter your Gemini API Key in the 'AI Settings' section of the sidebar.",
        "spinner_ai": "Generating AI analysis for...",
        "summary_recommendation": "Recommendation",
        "recommendation_buy": "BUY", "recommendation_sell": "SELL", "recommendation_neutral": "NEUTRAL",
        "watchlist_header": "Your Personal Watchlist",
        "watchlist_empty": "Your watchlist is empty. You can add stocks from the 'Single Stock Analysis' tab.",
    }
}


# --- Yardımcı Fonksiyonlar ---
def t(key): return LANGUAGES[st.session_state.lang].get(key, key)

@st.cache_data(ttl=86400) # Veriyi günde bir kez çek
def get_robinhood_tickers():
    """Güvenilir bir kaynaktan Robinhood'da listelenen tüm hisselerin bir listesini çeker."""
    try:
        # Bu URL, halka açık ve güncel bir Robinhood hisse senedi listesi içeren bir CSV dosyasıdır.
        url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed-symbols.csv"
        df = pd.read_csv(url)
        # Sadece geçerli hisse senedi sembollerini al (ETF'leri ve diğerlerini hariç tut)
        tickers = df[~df['Symbol'].str.contains(r'\$|\.')]['Symbol'].dropna().unique().tolist()
        return tickers
    except Exception as e:
        st.error(f"Robinhood hisse listesi çekilirken hata oluştu: {e}")
        return [] # Hata durumunda boş liste döndür

# ... (Diğer @st.cache_data fonksiyonları öncekiyle aynı)
@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period=period, auto_adjust=False), stock.info, stock.news
    except Exception: return None, None, None
@st.cache_data
def calculate_technicals(df):
    if df is not None and not df.empty and len(df) > 50: # Daha güvenilir hesaplamalar için daha fazla veri iste
        df.ta.rsi(append=True); df.ta.macd(append=True); df.ta.sma(length=50, append=True)
        df.dropna(inplace=True)
    return df
# ... (Diğer yardımcı fonksiyonlar öncekiyle aynı)

# -----------------------------------------------------------------------------
# Oturum Durumu Başlatma
# -----------------------------------------------------------------------------
if 'lang' not in st.session_state: st.session_state.lang = "TR"
if 'watchlist' not in st.session_state: st.session_state.watchlist = []

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu ve Ana Başlık
# -----------------------------------------------------------------------------
st.set_page_config(page_title=t("page_title"), page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
# ... (CSS Kodu Kısaltıldı) ...
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # CSS for theme
st.title(t("app_title"))
st.caption(t("app_caption"))

# -----------------------------------------------------------------------------
# Ana Sekmeler
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([t("tab_screener"), t("tab_analysis"), t("tab_watchlist"), t("tab_ai_analysis")])

# -----------------------------------------------------------------------------
# Kenar Çubuğu (SIDEBAR) - Basitleştirildi
# -----------------------------------------------------------------------------
st.sidebar.selectbox("Language / Dil", options=["TR", "EN"], key="lang")
st.sidebar.header(t("sidebar_header"))
with st.sidebar.expander(t("sidebar_ai_expander")):
    gemini_api_key = st.text_input(t("sidebar_api_key"), type="password")
st.sidebar.markdown("---")
st.sidebar.markdown("by Yusa Kurkcu")

# -----------------------------------------------------------------------------
# Sekme 1: Otomatik Fırsat Tarama (Yeniden Yapılandırıldı)
# -----------------------------------------------------------------------------
with tab1:
    st.header(t("screener_header"))
    st.info(t("screener_info"))

    if st.button(t("screener_button"), type="primary"):
        with st.spinner(t("screener_spinner")):
            tickers_to_scan = get_robinhood_tickers()
            results = []
            
            if not tickers_to_scan:
                st.error("Taranacak hisse listesi alınamadı.")
            else:
                progress_bar = st.progress(0, text="Başlatılıyor...")
                for i, ticker in enumerate(tickers_to_scan):
                    progress_bar.progress((i + 1) / len(tickers_to_scan), text=f"Taranıyor: {ticker} ({i+1}/{len(tickers_to_scan)})")
                    
                    data, info, _ = get_stock_data(ticker, "6mo")
                    
                    # Ön filtreleme: Çok küçük ve verisiz şirketleri atla
                    if data is None or data.empty or info is None or info.get('marketCap', 0) < 300_000_000:
                        continue
                        
                    data = calculate_technicals(data)
                    
                    if data is not None and len(data) > 2:
                        last_row = data.iloc[-1]
                        prev_row = data.iloc[-2]

                        # --- Optimal Strateji Koşulları ---
                        is_rsi_ok = last_row['RSI_14'] < 55
                        is_above_sma50 = last_row['Close'] > last_row['SMA_50']
                        is_macd_crossed = last_row['MACD_12_26_9'] > last_row['MACDs_12_26_9'] and prev_row['MACD_12_26_9'] <= prev_row['MACDs_12_26_9']

                        if is_rsi_ok and is_above_sma50 and is_macd_crossed:
                            results.append({
                                t("col_symbol"): ticker,
                                t("col_company"): info.get('shortName', ticker),
                                t("col_sector"): info.get('sector', 'N/A'),
                                t("col_price"): f"${last_row['Close']:.2f}",
                                t("col_rsi"): f"{last_row['RSI_14']:.2f}"
                            })
                
                progress_bar.empty()

        if results:
            df_results = pd.DataFrame(results)
            st.success(f"{len(df_results)} {t('screener_success')}")
            st.dataframe(df_results, use_container_width=True)
        else:
            st.warning(t("screener_warning_no_stock"))

# -----------------------------------------------------------------------------
# Sekme 2, 3, 4 (Değişiklik yok)
# -----------------------------------------------------------------------------
# ... (Sekme 2: Tek Hisse Analizi, Sekme 3: İzleme Listesi, ve Sekme 4: Yapay Zeka Analizi kodları
# önceki versiyon ile aynı olduğu için burada tekrar edilmemiştir.)
def display_single_stock_analysis(ticker_input):
    # ... (kod aynı)
    pass
with tab2:
    st.header(t("analysis_header"))
    ticker_input_tab2 = st.text_input(t("analysis_input_label"), "NVDA", key="tab2_input").upper()
    if ticker_input_tab2: 
        # ... (display_single_stock_analysis çağrısı)
        pass

with tab3:
    st.header(t("watchlist_header"))
    # ... (izleme listesi kodu)
    pass

with tab4:
    st.header(t("ai_header"))
    # ... (yapay zeka analizi kodu)
    pass

