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
        "tab_screener": "📊 Hisse Taraması (Screener)",
        "tab_analysis": "🔍 Tek Hisse Analizi",
        "tab_watchlist": "⭐ İzleme Listem",
        "tab_ai_analysis": "🤖 Yapay Zeka Derin Analiz",
        "sidebar_header": "Ayarlar ve Filtreler",
        "list_selection_label": "Taranacak Hisse Listesi",
        "list_sp500": "S&P 500",
        "list_btc": "Bitcoin Tutan Şirketler",
        "sidebar_preset_expander": "Tarama Filtreleri",
        "sidebar_preset_info": "Bir ön ayar seçin veya filtreleri manuel olarak ayarlayın.",
        "sidebar_preset_select": "Hazır Filtre Ön Ayarları",
        "preset_manual": "Manuel Filtreleme",
        "preset_strong_bullish": "Güçlü Yükseliş Potansiyeli",
        "preset_reversal": "Dipten Dönüş Sinyali (Aşırı Satım)",
        "filter_rsi": "RSI Değerine Göre Filtrele",
        "filter_rsi_slider": "Maksimum RSI Değeri",
        "filter_macd": "MACD Al Sinyali Yakala (Yeni Kesişim)",
        "filter_sma": "Fiyat 50 Günlük Ortalamayı Yukarı Kessin",
        "filter_sector": "Sektöre Göre Filtrele",
        "filter_market_cap": "Piyasa Değeri",
        "cap_all": "Tümü",
        "cap_mega": "Mega-Cap (>200B$)",
        "cap_large": "Large-Cap (10B$ - 200B$)",
        "cap_mid": "Mid-Cap (2B$ - 10B$)",
        "cap_small": "Small-Cap (<2B$)",
        "sidebar_ai_expander": "Yapay Zeka Ayarları",
        "sidebar_api_key": "Gemini API Anahtarınız",
        "screener_header": "için Gelişmiş Filtreleme",
        "screener_button": "Taramayı Başlat",
        "screener_sort_by": "Sonuçları Sırala:",
        "screener_warning_no_filter": "Lütfen tarama yapmak için en az bir filtre kriteri seçin veya bir ön ayar kullanın.",
        "screener_spinner": "listesi taranıyor... Bu işlem seçilen hisse sayısına göre değişebilir.",
        "screener_success": "adet potansiyel fırsat bulundu!",
        "screener_warning_no_stock": "Belirtilen kriterlere uygun hisse bulunamadı.",
        "col_symbol": "Sembol", "col_company": "Şirket Adı", "col_sector": "Sektör", "col_price": "Fiyat", "col_rsi": "RSI", "col_signals": "Tespit Edilen Sinyal(ler)",
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
        "summary_rsi_oversold": "RSI ({rsi:.2f}) aşırı satım bölgesinde, tepki alımı potansiyeli olabilir.",
        "summary_rsi_overbought": "RSI ({rsi:.2f}) aşırı alım bölgesinde, düzeltme riski olabilir.",
        "summary_rsi_neutral": "RSI ({rsi:.2f}) nötr bölgede.",
        "summary_macd_bullish": "MACD, sinyal çizgisini yukarı keserek 'Al' sinyali üretiyor.",
        "summary_macd_bearish": "MACD, sinyal çizgisini aşağı keserek 'Sat' sinyali üretiyor.",
        "summary_sma_golden": "Fiyat, 50 ve 200 günlük ortalamaların üzerinde (Golden Cross). Güçlü yükseliş trendi.",
        "summary_sma_death": "Fiyat, 50 ve 200 günlük ortalamaların altında (Death Cross). Düşüş trendi.",
        "summary_sma_bullish": "Fiyat, 50 günlük ortalamanın üzerinde, kısa vadeli görünüm pozitif.",
        "summary_sma_bearish": "Fiyat, 50 günlük ortalamanın altında, kısa vadede baskı olabilir.",
        "gemini_prompt": "Sen kıdemli bir finansal analistsin. {company_name} ({ticker}) hissesi için Türkçe, profesyonel bir yatırımcı raporu hazırla. Rapor, temel ve teknik verileri sentezleyerek hem olumlu yönleri hem de riskleri dengeli bir şekilde vurgulamalı. Kısa ve orta vade için analiz yap. Net bir yatırım tavsiyesi verme, yatırımcının dikkat etmesi gereken noktaları özetle.\n\n**Temel Bilgiler:**\n- Şirket Adı: {company_name}\n- Sektör: {sector}\n- Piyasa Değeri: {market_cap:,} USD\n- F/K Oranı: {pe_ratio}\n- Profil: {profile}...\n\n**Teknik Göstergeler:**\n- Son Fiyat: {price:.2f} USD\n- RSI (14): {rsi:.2f}\n- MACD Durumu: {macd_status}\n- 50 Günlük Ortalama: {sma50:.2f} USD\n- 200 Günlük Ortalama: {sma200:.2f} USD",
        "watchlist_header": "Kişisel İzleme Listeniz",
        "watchlist_empty": "İzleme listeniz boş. 'Tek Hisse Analizi' sekmesinden hisse ekleyebilirsiniz.",
    },
    "EN": {
        "page_title": "AI-Powered Stock Analysis Bot",
        "app_title": "🤖 AI-Powered Stock Analysis Bot",
        "app_caption": "This application performs basic analysis using yfinance data and AI. This is not investment advice.",
        "tab_screener": "📊 Stock Screener",
        "tab_analysis": "🔍 Single Stock Analysis",
        "tab_watchlist": "⭐ My Watchlist",
        "tab_ai_analysis": "🤖 AI Deep Analysis",
        "sidebar_header": "Settings and Filters",
        "list_selection_label": "Stock List to Scan",
        "list_sp500": "S&P 500",
        "list_btc": "Companies Holding Bitcoin",
        "sidebar_preset_expander": "Screener Filters",
        "sidebar_preset_info": "Select a preset or adjust filters manually.",
        "sidebar_preset_select": "Filter Presets",
        "preset_manual": "Manual Filtering",
        "preset_strong_bullish": "Strong Bullish Potential",
        "preset_reversal": "Reversal Signal (Oversold)",
        "filter_rsi": "Filter by RSI Value",
        "filter_rsi_slider": "Maximum RSI Value",
        "filter_macd": "Catch MACD Buy Signal (New Cross)",
        "filter_sma": "Price Crosses Above 50-Day MA",
        "filter_sector": "Filter by Sector",
        "filter_market_cap": "Market Cap",
        "cap_all": "All",
        "cap_mega": "Mega-Cap (>$200B)",
        "cap_large": "Large-Cap ($10B - $200B)",
        "cap_mid": "Mid-Cap ($2B - $10B)",
        "cap_small": "Small-Cap (<$2B)",
        "sidebar_ai_expander": "AI Settings",
        "sidebar_api_key": "Your Gemini API Key",
        "screener_header": "Advanced Filtering for",
        "screener_button": "Start Scan",
        "screener_sort_by": "Sort Results By:",
        "screener_warning_no_filter": "Please select at least one filter criterion (RSI, MACD, or 50-Day MA) to start scanning.",
        "screener_spinner": "list is being scanned... This may take a few minutes.",
        "screener_success": "potential opportunities found!",
        "screener_warning_no_stock": "No stocks found matching the specified criteria.",
        "col_symbol": "Symbol", "col_company": "Company Name", "col_sector": "Sector", "col_price": "Price", "col_rsi": "RSI", "col_signals": "Detected Signal(s)",
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
        "summary_rsi_oversold": "RSI ({rsi:.2f}) is in the oversold region, suggesting a potential for a rebound.",
        "summary_rsi_overbought": "RSI ({rsi:.2f}) is in the overbought region, suggesting a risk of a correction.",
        "summary_rsi_neutral": "RSI ({rsi:.2f}) is in the neutral zone.",
        "summary_macd_bullish": "MACD is generating a 'Buy' signal, crossing above its signal line.",
        "summary_macd_bearish": "MACD is generating a 'Sell' signal, crossing below its signal line.",
        "summary_sma_golden": "Price is above the 50-day and 200-day MAs (Golden Cross). Strong bullish trend.",
        "summary_sma_death": "Price is below the 50-day and 200-day MAs (Death Cross). Bearish trend.",
        "summary_sma_bullish": "Price is above the 50-day MA, indicating a positive short-term outlook.",
        "summary_sma_bearish": "Price is below the 50-day MA, which may indicate short-term pressure.",
        "gemini_prompt": "You are a senior financial analyst. Prepare an investor report for {company_name} ({ticker}) in professional English. The report should synthesize fundamental and technical data, highlighting both positive aspects and potential risks in a balanced manner. Analyze for the short and medium term. Do not give a direct investment recommendation, but summarize the key points an investor should consider.\n\n**Fundamental Data:**\n- Company Name: {company_name}\n- Sector: {sector}\n- Market Cap: {market_cap:,} USD\n- P/E Ratio: {pe_ratio}\n- Profile: {profile}...\n\n**Technical Indicators:**\n- Last Price: {price:.2f} USD\n- RSI (14): {rsi:.2f}\n- MACD Status: {macd_status}\n- 50-Day MA: {sma50:.2f} USD\n- 200-Day MA: {sma200:.2f} USD",
        "watchlist_header": "Your Personal Watchlist",
        "watchlist_empty": "Your watchlist is empty. You can add stocks from the 'Single Stock Analysis' tab.",
    }
}


# --- Diğer Fonksiyonlar (Öncekiyle aynı, kısaltıldı) ---
def t(key): return LANGUAGES[st.session_state.lang].get(key, key)
@st.cache_data(ttl=86400)
def get_sp500_tickers():
    try:
        url='https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        df=pd.read_html(url, header=0)[0]
        return df['Symbol'].tolist(), sorted(df['GICS Sector'].unique().tolist())
    except Exception: return ['AAPL', 'MSFT', 'GOOGL', 'AMZN'], ['Information Technology', 'Health Care']
@st.cache_data(ttl=86400)
def get_bitcoin_holders_tickers():
    tickers = ["MSTR", "MARA", "TSLA", "COIN", "SQ", "RIOT", "HUT", "BITF", "CLSK", "BTBT", "HIVE", "CIFR", "IREN", "WULF"]
    sectors, valid_tickers = [], []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            if 'sector' in info and info['sector']: sectors.append(info['sector']); valid_tickers.append(ticker)
        except Exception: continue
    return valid_tickers, sorted(list(set(sectors)))
@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period=period, auto_adjust=False), stock.info, stock.news
    except Exception: return None, None, None
@st.cache_data
def calculate_technicals(df):
    if df is not None and not df.empty and len(df) > 20:
        df.ta.rsi(append=True); df.ta.macd(append=True); df.ta.sma(length=50, append=True); df.ta.sma(length=200, append=True)
        df.dropna(inplace=True)
    return df
@st.cache_data(ttl=3600)
def get_reddit_posts(ticker, limit=10):
    posts, subreddits = [], ['wallstreetbets', 'stocks', 'investing', 'StockMarket']
    try:
        for subreddit in subreddits:
            headers = {'User-Agent': 'Mozilla/5.0'}; url = f"https://www.reddit.com/r/{subreddit}/search.json?q={ticker}&sort=new&restrict_sr=on&t=day"
            response = requests.get(url, headers=headers); response.raise_for_status()
            for post in response.json()['data']['children']: posts.append({'title': post['data']['title'], 'url': f"https://reddit.com{post['data']['permalink']}", 'subreddit': f"r/{subreddit}"})
        return [dict(t) for t in {tuple(d.items()) for d in posts}][:limit]
    except Exception: return []
def generate_analysis_summary(ticker, info, last_row):
    # Bu fonksiyon, çeviri anahtarlarıyla birlikte öncekiyle aynıdır.
    summary_points, buy_signals, sell_signals = [], 0, 0; rsi = last_row.get('RSI_14', 50)
    if rsi < 30: summary_points.append(t('summary_rsi_oversold').format(rsi=rsi)); buy_signals += 2
    elif rsi > 70: summary_points.append(t('summary_rsi_overbought').format(rsi=rsi)); sell_signals += 2
    else: summary_points.append(t('summary_rsi_neutral').format(rsi=rsi))
    if last_row.get('MACD_12_26_9', 0) > last_row.get('MACDs_12_26_9', 0): summary_points.append(t('summary_macd_bullish')); buy_signals += 1
    else: summary_points.append(t('summary_macd_bearish')); sell_signals += 1
    current_price, sma_50, sma_200 = last_row.get('Close', 0), last_row.get('SMA_50', 0), last_row.get('SMA_200', 0)
    if current_price > sma_50 and sma_50 > sma_200: summary_points.append(t('summary_sma_golden')); buy_signals += 2
    elif current_price < sma_50 and current_price < sma_200: summary_points.append(t('summary_sma_death')); sell_signals += 2
    elif current_price > sma_50: summary_points.append(t('summary_sma_bullish')); buy_signals += 1
    else: summary_points.append(t('summary_sma_bearish')); sell_signals += 1
    if buy_signals > sell_signals + 1: recommendation = t('recommendation_buy')
    elif sell_signals > buy_signals + 1: recommendation = t('recommendation_sell')
    else: recommendation = t('recommendation_neutral')
    return f"**{info.get('longName', ticker)} ({ticker})**: \n" + "- " + "\n- ".join(summary_points), recommendation
def get_gemini_analysis(api_key, ticker, info, last_row):
    # Bu fonksiyon, çeviri anahtarlarıyla birlikte öncekiyle aynıdır.
    try:
        genai.configure(api_key=api_key); model = genai.GenerativeModel('gemini-pro')
        macd_status = "Bullish Crossover" if last_row.get('MACD_12_26_9', 0) > last_row.get('MACDs_12_26_9', 0) else "Bearish Crossover"
        prompt = t('gemini_prompt').format(company_name=info.get('longName','N/A'),ticker=ticker,sector=info.get('sector','N/A'),market_cap=info.get('marketCap',0),pe_ratio=info.get('trailingPE','N/A'),profile=info.get('longBusinessSummary','N/A')[:500],price=last_row.get('Close',0),rsi=last_row.get('RSI_14',0),macd_status=macd_status,sma50=last_row.get('SMA_50',0),sma200=last_row.get('SMA_200',0))
        return model.generate_content(prompt).text
    except Exception as e: return f"An error occurred during AI analysis: {e}."
# -----------------------------------------------------------------------------
# Oturum Durumu Başlatma
# -----------------------------------------------------------------------------
if 'lang' not in st.session_state: st.session_state.lang = "TR"
if 'watchlist' not in st.session_state: st.session_state.watchlist = []

# HATA DÜZELTMESİ: Filtre durumlarını burada başlat
if 'rsi_enabled' not in st.session_state: st.session_state.rsi_enabled = False
if 'rsi_value' not in st.session_state: st.session_state.rsi_value = 35
if 'macd_cross' not in st.session_state: st.session_state.macd_cross = False
if 'sma_cross' not in st.session_state: st.session_state.sma_cross = False


# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu ve Ana Başlık
# -----------------------------------------------------------------------------
st.set_page_config(page_title=t("page_title"), page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
# ... (CSS Kodu Kısaltıldı) ...
st.markdown("""<style>...</style>""", unsafe_allow_html=True)
st.title(t("app_title"))
st.caption(t("app_caption"))

# -----------------------------------------------------------------------------
# Ana Sekmeler
# -----------------------------------------------------------------------------
stock_list_sp500, sectors_sp500 = get_sp500_tickers()
stock_list_btc, sectors_btc = get_bitcoin_holders_tickers()
tab1, tab2, tab3, tab4 = st.tabs([t("tab_screener"), t("tab_analysis"), t("tab_watchlist"), t("tab_ai_analysis")])

# -----------------------------------------------------------------------------
# Kenar Çubuğu (SIDEBAR)
# -----------------------------------------------------------------------------
st.sidebar.selectbox("Language / Dil", options=["TR", "EN"], key="lang")
st.sidebar.header(t("sidebar_header"))
# ... (Sidebar kodu öncekiyle aynı, kısaltıldı) ...
list_selection = st.sidebar.radio(t("list_selection_label"), (t("list_sp500"), t("list_btc")), key='stock_list_selection')
tickers_to_scan, sectors_to_display = (stock_list_sp500, sectors_sp500) if list_selection == t("list_sp500") else (stock_list_btc, sectors_btc)
# ... (Filtreler ve Presetler öncekiyle aynı, kısaltıldı) ...

# HATA DÜZELTMESİ: Eksik filtre kodları buraya eklendi
filter_presets = {
    t("preset_manual"): {},
    t("preset_strong_bullish"): {'rsi_enabled': False, 'macd_cross': True, 'sma_cross': True},
    t("preset_reversal"): {'rsi_enabled': True, 'rsi_value': 35, 'macd_cross': False, 'sma_cross': False}
}
def apply_preset():
    preset_name = st.session_state.selected_preset
    for name, config in filter_presets.items():
        if name == preset_name:
            st.session_state.rsi_enabled = config.get('rsi_enabled', False)
            st.session_state.rsi_value = config.get('rsi_value', 35)
            st.session_state.macd_cross = config.get('macd_cross', False)
            st.session_state.sma_cross = config.get('sma_cross', False)
            break

with st.sidebar.expander(t("sidebar_preset_expander"), expanded=True):
    st.info(t("sidebar_preset_info"))
    st.selectbox(t("sidebar_preset_select"), options=list(filter_presets.keys()), key='selected_preset', on_change=apply_preset)
    st.divider()
    st.checkbox(t("filter_rsi"), key='rsi_enabled')
    st.slider(t("filter_rsi_slider"), 0, 100, key='rsi_value', disabled=not st.session_state.rsi_enabled)
    st.checkbox(t("filter_macd"), key='macd_cross')
    st.checkbox(t("filter_sma"), key='sma_cross')
    filter_sector = st.multiselect(t("filter_sector"), options=sectors_to_display, default=[])
    market_cap_options = {
        t("cap_all"): (0, float('inf')), t("cap_mega"): (200e9, float('inf')), t("cap_large"): (10e9, 200e9),
        t("cap_mid"): (2e9, 10e9), t("cap_small"): (0, 2e9)
    }
    selected_cap_label = st.selectbox(t("filter_market_cap"), options=list(market_cap_options.keys()))
    min_cap, max_cap = market_cap_options[selected_cap_label]

with st.sidebar.expander(t("sidebar_ai_expander")): gemini_api_key = st.text_input(t("sidebar_api_key"), type="password")
st.sidebar.markdown("---"); st.sidebar.markdown("by Yusa Kurkcu")

# -----------------------------------------------------------------------------
# Sekme 1: Hisse Taraması (Sıralama Eklendi)
# -----------------------------------------------------------------------------
with tab1:
    st.header(f"{list_selection} {t('screener_header')}")
    if st.button(t("screener_button"), type="primary"):
        # ... (Tarama mantığı öncekiyle aynı) ...
        if not any([st.session_state.rsi_enabled, st.session_state.macd_cross, st.session_state.sma_cross]):
            st.warning(t("screener_warning_no_filter"))
        else:
            with st.spinner(f"{list_selection} {t('screener_spinner')}"):
                results = [] #... tarama döngüsü
                #...
                for i, ticker in enumerate(tickers_to_scan):
                    #...
                    data, info, _ = get_stock_data(ticker, "6mo")
                    if data is not None and not data.empty and info and info.get('marketCap'):
                        #...
                        data = calculate_technicals(data)
                        if data is not None and len(data) > 2:
                            last_row, prev_row = data.iloc[-1], data.iloc[-2]
                            signals = []
                            #...
                            if st.session_state.rsi_enabled and last_row['RSI_14'] < st.session_state.get('rsi_value', 35): signals.append(f"RSI Low ({last_row['RSI_14']:.2f})")
                            if st.session_state.macd_cross and last_row['MACD_12_26_9'] > last_row['MACDs_12_26_9'] and prev_row['MACD_12_26_9'] < prev_row['MACDs_12_26_9']: signals.append("MACD Bull Cross")
                            if st.session_state.sma_cross and last_row['Close'] > last_row['SMA_50'] and prev_row['Close'] < prev_row['SMA_50']: signals.append("Crossed 50-MA")
                            if signals:
                                results.append({t("col_symbol"): ticker, t("col_company"): info.get('shortName', ticker), t("col_sector"): info.get('sector', 'N/A'), t("col_price"): last_row['Close'], t("col_rsi"): last_row['RSI_14'], t("col_signals"): ", ".join(signals)})

            if results:
                df_results = pd.DataFrame(results)
                col1, col2 = st.columns([3, 1])
                with col1: st.success(f"{len(df_results)} {t('screener_success')}")
                with col2: sort_by = st.selectbox(t("screener_sort_by"), options=df_results.columns, index=0)
                df_results[t("col_price")] = df_results[t("col_price")].apply(lambda x: f"${x:.2f}")
                st.dataframe(df_results.sort_values(by=sort_by).reset_index(drop=True), use_container_width=True)
            else: st.warning(t("screener_warning_no_stock"))

# -----------------------------------------------------------------------------
# Sekme 2: Tek Hisse Analizi (Yeniden Yapılandırıldı)
# -----------------------------------------------------------------------------
def display_single_stock_analysis(ticker_input):
    with st.spinner(f"{t('spinner_analysis')} {ticker_input}..."):
        hist_data, info, news = get_stock_data(ticker_input, period="2y") # Daha uzun veri
        if hist_data is None or hist_data.empty: st.error(t("error_no_data")); return
        technicals_df = calculate_technicals(hist_data.copy())
        if technicals_df is None or technicals_df.empty: st.error(t("error_no_technicals")); return
        last_row = technicals_df.iloc[-1]
        
        # --- BAŞLIK VE İZLEME LİSTESİ BUTONU ---
        col1, col2 = st.columns([3, 1])
        with col1: st.subheader(f"{info.get('longName', ticker_input)} ({ticker_input})")
        with col2:
            if ticker_input not in st.session_state.watchlist:
                if st.button(t("add_to_watchlist"), key=f"add_{ticker_input}"):
                    st.session_state.watchlist.append(ticker_input)
                    st.toast(f"{ticker_input} {t('added_to_watchlist')}")
                    st.rerun()

        # --- TEMEL METRİKLER ---
        c1, c2, c3, c4 = st.columns(4)
        current_price, prev_close = last_row['Close'], info.get('previousClose', 0)
        price_change, price_change_pct = (current_price - prev_close), ((current_price - prev_close) / prev_close) * 100 if prev_close else 0
        c1.metric(t("metric_price"), f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.2f}%)", delta_color="inverse" if price_change < 0 else "normal")
        c2.metric(t("metric_cap"), f"${(info.get('marketCap', 0) / 1e9):.1f}B")
        c3.metric(t("metric_volume"), f"{info.get('volume', 0):,}")
        c4.metric(t("metric_pe"), f"{info.get('trailingPE', 'N/A')}")

        c5, c6, c7 = st.columns(3)
        w52_range = f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}"
        c5.metric(t("metric_52w_range"), w52_range)
        c6.metric(t("metric_beta"), f"{info.get('beta', 'N/A'):.2f}")
        c7.metric(t("metric_dividend_yield"), f"{info.get('dividendYield', 0)*100:.2f}%")
        st.divider()

        # --- ANALİZ, GRAFİK, HABERLER İÇİN ALT SEKMELER ---
        sub_tab1, sub_tab2 = st.tabs([t('sub_tab_analysis_charts'), t('sub_tab_market_sentiment')])

        with sub_tab1:
            analysis_col, chart_col = st.columns([0.8, 1.2])
            with analysis_col:
                st.subheader(t("subheader_rule_based"))
                summary, recommendation = generate_analysis_summary(ticker_input, info, last_row)
                if recommendation == t('recommendation_buy'): st.success(f"**{t('summary_recommendation')}: {recommendation}**")
                elif recommendation == t('recommendation_sell'): st.error(f"**{t('summary_recommendation')}: {recommendation}**")
                else: st.warning(f"**{t('summary_recommendation')}: {recommendation}**")
                st.markdown(summary)
                st.subheader(t("subheader_company_profile"))
                st.info(info.get('longBusinessSummary', '...'))
            
            with chart_col:
                st.subheader(t("subheader_charts"))
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=technicals_df.index, open=technicals_df['Open'], high=technicals_df['High'], low=technicals_df['Low'], close=technicals_df['Close'], name='Fiyat'))
                fig.add_trace(go.Scatter(x=technicals_df.index, y=technicals_df['SMA_50'], mode='lines', name='50-MA', line=dict(color='blue', width=1)))
                fig.add_trace(go.Scatter(x=technicals_df.index, y=technicals_df['SMA_200'], mode='lines', name='200-MA', line=dict(color='orange', width=1)))
                fig.update_layout(xaxis_rangeslider_visible=False, template='plotly_dark', margin=dict(l=0, r=0, t=0, b=0), height=400)
                st.plotly_chart(fig, use_container_width=True)
                st.caption(t("chart_caption"))

        with sub_tab2:
            news_col, reddit_col = st.columns(2)
            #... Haber ve Reddit kodları öncekiyle aynı ...

with tab2:
    st.header(t("analysis_header"))
    ticker_input_tab2 = st.text_input(t("analysis_input_label"), "NVDA", key="tab2_input").upper()
    if ticker_input_tab2: display_single_stock_analysis(ticker_input_tab2)

# -----------------------------------------------------------------------------
# Sekme 3: İzleme Listesi
# -----------------------------------------------------------------------------
with tab3:
    st.header(t("watchlist_header"))
    if not st.session_state.watchlist:
        st.info(t("watchlist_empty"))
    else:
        for ticker in st.session_state.watchlist:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            try:
                info = yf.Ticker(ticker).info
                with col1: st.subheader(f"{info.get('shortName', ticker)} ({ticker})")
                with col2: st.metric("Fiyat", f"${info.get('currentPrice', 0):.2f}", f"{info.get('regularMarketChange', 0):.2f}$")
                with col3: st.metric("Piyasa Değeri", f"${(info.get('marketCap', 0)/1e9):.1f}B")
                with col4:
                    if st.button(t("remove_from_watchlist"), key=f"remove_{ticker}"):
                        st.session_state.watchlist.remove(ticker)
                        st.rerun()
            except Exception:
                st.error(f"{ticker} için veri çekilemedi.")
            st.divider()

# -----------------------------------------------------------------------------
# Sekme 4: Yapay Zeka Analizi
# -----------------------------------------------------------------------------
with tab4:
    st.header(t("ai_header"))
    ticker_input_tab4 = st.text_input(t("ai_input_label"), "MSFT", key="tab4_input").upper()
    if st.button(t("ai_button"), type="primary", key="ai_btn"):
        if not gemini_api_key: st.error(t("error_no_api_key"))
        elif ticker_input_tab4:
            with st.spinner(f"{t('spinner_ai')} {ticker_input_tab4}..."):
                #... AI Analiz Kodu ...
                st.success("Analiz tamamlandı.")




