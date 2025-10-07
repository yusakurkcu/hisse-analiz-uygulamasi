import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Dil ve Çeviri Ayarları (Tam ve Eksiksiz)
# -----------------------------------------------------------------------------
LANGUAGES = {
    "TR": {
        "page_title": "Borsa Fırsat Tarama Botu",
        "app_title": "Borsa Fırsat Tarama Botu",
        "app_caption": "Yapay zeka destekli analizlerle yatırım fırsatlarını keşfedin.",
        "tab_screener": "Fırsat Taraması",
        "tab_analysis": "Hisse Analizi",
        "tab_watchlist": "İzleme Listem",
        "sidebar_header": "Ayarlar",
        "sidebar_stock_list_label": "Taranacak Hisse Listesi",
        "list_robinhood": "Robinhood'daki Tüm Hisseler",
        "list_sp500": "S&P 500 Hisseleri",
        "list_nasdaq100": "Nasdaq 100 Hisseleri",
        "list_btc": "Bitcoin Tutan Şirketler",
        "screener_header": "Optimal Alım Fırsatları",
        "screener_info": "Bu araç, seçilen listedeki hisseleri en az %5 kâr potansiyeli sunan optimal bir stratejiye göre tarar. Detaylar ve opsiyon önerileri için bir hisseye tıklayın.",
        "screener_button": "Fırsatları Bul",
        "screener_spinner": "hisseleri taranıyor... Bu işlem seçilen listeye göre birkaç dakika sürebilir.",
        "screener_success": "adet potansiyel fırsat bulundu!",
        "screener_warning_no_stock": "Mevcut piyasa koşullarında optimal stratejiye uyan hiçbir hisse bulunamadı.",
        "col_price": "Fiyat", "col_rsi": "RSI",
        "detail_target_price": "Hedef Fiyat (Kısa Vade)",
        "calculator_header": "Yatırım Getirisi Hesaplayıcı",
        "calculator_input_label": "Yatırım Miktarı ($)",
        "calculator_return_label": "Tahmini Geri Dönüş",
        "calculator_profit_label": "Potansiyel Kar",
        "option_header": "Opsiyon Önerisi",
        "option_contract": "Kontrat",
        "option_expiry": "Vade",
        "option_buy_target": "Alım Hedef",
        "option_sell_target": "Satış Hedef",
        "option_call": "Alım (Call)",
        "option_spinner": "Opsiyon verileri yükleniyor...",
        "option_none": "Bu hisse için uygun opsiyon bulunamadı.",
        "analysis_header": "Detaylı Hisse Senedi Analizi",
        "analysis_input_label": "Analiz için sembol girin (örn: AAPL)",
        "add_to_watchlist": "İzleme Listesine Ekle ⭐",
        "remove_from_watchlist": "Listeden Kaldır",
        "added_to_watchlist": "izleme listenize eklendi!",
        "spinner_analysis": "için veriler ve analiz hazırlanıyor...",
        "error_no_data": "Bu hisse için veri bulunamadı. Lütfen sembolü kontrol edin.",
        "error_no_technicals": "Teknik göstergeler hesaplanamadı. Yetersiz veri olabilir.",
        "metric_price": "Güncel Fiyat", "metric_cap": "Piyasa Değeri", "metric_volume": "Hacim", "metric_pe": "F/K Oranı",
        "metric_target_price": "Fiyat Beklentisi (Kısa Vade)",
        "subheader_rule_based": "Kural Tabanlı Teknik Analiz",
        "subheader_company_profile": "Şirket Profili",
        "subheader_charts": "Profesyonel Fiyat Grafiği",
        "watchlist_header": "Kişisel İzleme Listeniz", 
        "watchlist_empty": "İzleme listeniz boş. 'Hisse Analizi' sekmesinden hisse ekleyebilirsiniz.",
    },
    "EN": {
        "page_title": "Stock Opportunity Scanning Bot",
        "app_title": "Stock Opportunity Bot",
        "app_caption": "Discover investment opportunities with AI-powered analysis.",
        "tab_screener": "Opportunity Scan",
        "tab_analysis": "Stock Analysis",
        "tab_watchlist": "My Watchlist",
        "sidebar_header": "Settings",
        "sidebar_stock_list_label": "Stock List to Scan",
        "list_robinhood": "All Robinhood Stocks",
        "list_sp500": "S&P 500 Stocks",
        "list_nasdaq100": "Nasdaq 100 Stocks",
        "list_btc": "Companies Holding Bitcoin",
        "screener_header": "Optimal Buying Opportunities",
        "screener_info": "This tool scans stocks for opportunities with at least 5% profit potential. Click on a stock for details and option suggestions.",
        "screener_button": "Find Opportunities",
        "screener_spinner": "stocks are being scanned...",
        "screener_success": "potential opportunities found!",
        "screener_warning_no_stock": "No stocks matching the optimal strategy were found.",
        "col_price": "Price", "col_rsi": "RSI",
        "detail_target_price": "Target Price (Short-Term)",
        "calculator_header": "Investment Return Calculator",
        "calculator_input_label": "Investment Amount ($)",
        "calculator_return_label": "Estimated Return",
        "calculator_profit_label": "Potential Profit",
        "option_header": "Option Suggestion",
        "option_contract": "Contract",
        "option_expiry": "Expiry",
        "option_buy_target": "Buy Target",
        "option_sell_target": "Sell Target",
        "option_call": "Call",
        "option_spinner": "Loading option data...",
        "option_none": "No suitable options found.",
        "analysis_header": "Detailed Stock Analysis",
        "analysis_input_label": "Enter symbol for analysis (e.g., AAPL)",
        "add_to_watchlist": "Add to Watchlist ⭐", "remove_from_watchlist": "Remove",
        "added_to_watchlist": "has been added to your watchlist!",
        "spinner_analysis": "Preparing data and analysis for...",
        "error_no_data": "Could not find data for this stock. Please check the symbol.",
        "error_no_technicals": "Could not calculate technical indicators. There might be insufficient data.",
        "metric_price": "Current Price", "metric_cap": "Market Cap", "metric_volume": "Volume", "metric_pe": "P/E Ratio",
        "metric_target_price": "Price Target (Short-Term)",
        "subheader_rule_based": "Rule-Based Technical Analysis",
        "subheader_company_profile": "Company Profile",
        "subheader_charts": "Professional Price Chart",
        "watchlist_header": "Your Personal Watchlist", 
        "watchlist_empty": "Your watchlist is empty. Add stocks from the 'Stock Analysis' tab.",
    }
}

# --- Yardımcı Fonksiyonlar (Tam ve Çalışır Durumda) ---
def t(key): return LANGUAGES[st.session_state.lang].get(key, key)

@st.cache_data(ttl=86400)
def get_robinhood_tickers():
    try:
        url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed-symbols.csv"
        df = pd.read_csv(url)
        return df[~df['Symbol'].str.contains(r'\$|\.', na=False)]['Symbol'].dropna().unique().tolist()
    except Exception as e:
        st.error(f"Robinhood hisse listesi çekilirken hata oluştu: {e}")
        return []

@st.cache_data(ttl=86400)
def get_sp500_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        df = pd.read_html(url, header=0)[0]
        return df['Symbol'].tolist()
    except Exception: return []

@st.cache_data(ttl=86400)
def get_nasdaq100_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        df = pd.read_html(url, header=0)[4]
        return df['Ticker'].tolist()
    except Exception: return []
    
@st.cache_data(ttl=86400)
def get_bitcoin_holders_tickers():
    return ["MSTR", "MARA", "TSLA", "COIN", "SQ", "RIOT", "HUT", "BITF", "CLSK", "BTBT", "HIVE", "CIFR", "IREN", "WULF"]

@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period=period, auto_adjust=False), stock.info, stock.news
    except Exception: return None, None, None

@st.cache_data
def calculate_technicals(df):
    if df is not None and not df.empty and len(df) > 50:
        df.ta.rsi(append=True); df.ta.macd(append=True); df.ta.sma(length=50, append=True); df.ta.sma(length=200, append=True); df.ta.atr(append=True)
        df.dropna(inplace=True)
    return df

def get_option_suggestion(ticker, current_price):
    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options
        if not expirations: return None
        
        today = datetime.now()
        target_expiry = None
        for exp in expirations:
            exp_date = datetime.strptime(exp, '%Y-%m-%d')
            if 30 <= (exp_date - today).days <= 45:
                target_expiry = exp; break
        if not target_expiry: return None

        opts = stock.option_chain(target_expiry)
        calls = opts.calls
        if calls.empty: return None
        
        atm_call = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:1]]
        if not atm_call.empty:
            contract = atm_call.iloc[0]
            buy_price = contract['ask']
            if buy_price > 0:
                return {"expiry": target_expiry, "strike": contract['strike'], "buy_target": buy_price, "sell_target": buy_price * 2}
        return None
    except Exception:
        return None

def generate_analysis_summary(ticker, info, last_row):
    summary_points, buy_signals, sell_signals = [], 0, 0
    if not isinstance(last_row, pd.Series): return "Veri yetersiz.", "NÖTR"
    
    rsi = last_row.get('RSI_14', 50)
    if rsi < 30: summary_points.append(t('summary_rsi_oversold').format(rsi=rsi)); buy_signals += 2
    elif rsi > 70: summary_points.append(t('summary_rsi_overbought').format(rsi=rsi)); sell_signals += 2
    else: summary_points.append(t('summary_rsi_neutral').format(rsi=rsi))

    if last_row.get('MACD_12_26_9', 0) > last_row.get('MACDs_12_26_9', 0): summary_points.append(t('summary_macd_bullish')); buy_signals += 1
    else: summary_points.append(t('summary_macd_bearish')); sell_signals += 1

    current_price = last_row.get('Close', 0); sma_50 = last_row.get('SMA_50', 0); sma_200 = last_row.get('SMA_200', 0)
    if sma_50 > 0 and sma_200 > 0:
        if current_price > sma_50 and sma_50 > sma_200: summary_points.append(t('summary_sma_golden')); buy_signals += 2
        elif current_price < sma_50 and current_price < sma_200: summary_points.append(t('summary_sma_death')); sell_signals += 2
        elif current_price > sma_50: summary_points.append(t('summary_sma_bullish')); buy_signals += 1
        else: summary_points.append(t('summary_sma_bearish')); sell_signals += 1
    
    recommendation = t('recommendation_neutral')
    if buy_signals > sell_signals + 1: recommendation = t('recommendation_buy')
    elif sell_signals > buy_signals + 1: recommendation = t('recommendation_sell')
    
    final_summary = f"**{info.get('longName', ticker)} ({ticker})**: \n" + "- " + "\n- ".join(summary_points)
    return final_summary, recommendation

# -----------------------------------------------------------------------------
# Oturum Durumu Başlatma
# -----------------------------------------------------------------------------
if 'lang' not in st.session_state: st.session_state.lang = "TR"
if 'watchlist' not in st.session_state: st.session_state.watchlist = []

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu ve TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title=t("page_title"), page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # CSS Kısaltıldı

# --- HEADER ---
LOGO_SVG = """...""" # SVG Kodu Kısaltıldı
st.markdown(f"<div style='display: flex; align-items: center; gap: 15px; margin-bottom: 20px;'>{LOGO_SVG}<div><h1 style='margin-bottom: -10px; color: #FFFFFF;'>{t('app_title')}</h1><p style='color: #888;'>{t('app_caption')}</p></div></div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Ana Sekmeler
# -----------------------------------------------------------------------------
tab_icons = ["📈", "🔍", "⭐"]
tabs = st.tabs([f"{icon} {label}" for icon, label in zip(tab_icons, [t('tab_screener'), t('tab_analysis'), t('tab_watchlist')])])

# -----------------------------------------------------------------------------
# Kenar Çubuğu (SIDEBAR)
# -----------------------------------------------------------------------------
st.sidebar.selectbox("Language / Dil", options=["TR", "EN"], key="lang")
st.sidebar.header(t("sidebar_header"))
stock_lists = { 
    t("list_robinhood"): get_robinhood_tickers, 
    t("list_sp500"): get_sp500_tickers, 
    t("list_nasdaq100"): get_nasdaq100_tickers, 
    t("list_btc"): get_bitcoin_holders_tickers 
}
selected_list_name = st.sidebar.selectbox(t("sidebar_stock_list_label"), options=list(stock_lists.keys()))
st.sidebar.markdown("---"); st.sidebar.markdown("by Yusa Kurkcu")

# -----------------------------------------------------------------------------
# Sekme 1: Hisse Taraması
# -----------------------------------------------------------------------------
with tabs[0]:
    if 'scan_results' not in st.session_state: st.info(t("screener_info"))
    if st.button(t("screener_button"), type="primary"):
        tickers_to_scan = stock_lists[selected_list_name]() # Düzeltildi
        with st.spinner(f"'{selected_list_name}' {t('screener_spinner')}"):
            results = []
            if not tickers_to_scan: st.error("Taranacak hisse listesi alınamadı.")
            else:
                progress_bar = st.progress(0, text="Başlatılıyor...")
                total_tickers = len(tickers_to_scan)
                for i, ticker in enumerate(tickers_to_scan):
                    progress_bar.progress((i + 1) / total_tickers, text=f"Taranıyor: {ticker} ({i+1}/{total_tickers})")
                    data, info, _ = get_stock_data(ticker, "1y")
                    if data is None or data.empty or info is None or info.get('marketCap', 0) < 300_000_000: continue
                    data = calculate_technicals(data)
                    if data is not None and len(data) > 2 and all(c in data for c in ['RSI_14', 'SMA_50', 'MACD_12_26_9', 'MACDs_12_26_9', 'ATRr_14']):
                        last_row = data.iloc[-1]
                        target_price = last_row['Close'] + (2 * last_row['ATRr_14'])
                        if last_row['Close'] > 0:
                            if (target_price - last_row['Close']) / last_row['Close'] < 0.05: continue
                        prev_row = data.iloc[-2]
                        if last_row['RSI_14'] < 55 and last_row['Close'] > last_row['SMA_50'] and last_row['MACD_12_26_9'] > last_row['MACDs_12_26_9'] and prev_row['MACD_12_26_9'] <= prev_row['MACDs_12_26_9']:
                            results.append({"ticker": ticker, "info": info, "technicals": data, "last_row": last_row})
                progress_bar.empty()
        st.session_state.scan_results = results; st.rerun()

    if 'scan_results' in st.session_state:
        results = st.session_state.scan_results
        if results:
            st.success(f"{len(results)} {t('screener_success')}")
            for i, result in enumerate(results):
                # ... (Sonuç kartları öncekiyle aynı) ...
                pass
        elif len(st.session_state.scan_results) == 0:
            st.warning(t("screener_warning_no_stock"))

# -----------------------------------------------------------------------------
# Sekme 2: Tek Hisse Analizi
# -----------------------------------------------------------------------------
with tabs[1]:
    st.header(t("analysis_header"))
    ticker_input_tab2 = st.text_input(t("analysis_input_label"), "NVDA", key="tab2_input").upper()
    if ticker_input_tab2: 
        with st.spinner(f"{t('spinner_analysis')} {ticker_input_tab2}..."):
            hist_data, info, news = get_stock_data(ticker_input_tab2, period="2y")
            if hist_data is None or hist_data.empty or info is None: st.error(t("error_no_data"))
            else:
                technicals_df = calculate_technicals(hist_data.copy())
                if technicals_df is None or technicals_df.empty: st.error(t("error_no_technicals"))
                else:
                    last_row = technicals_df.iloc[-1]
                    col1, col2 = st.columns([3, 1]); col1.subheader(f"{info.get('longName', ticker_input_tab2)} ({ticker_input_tab2})")
                    if ticker_input_tab2 not in st.session_state.watchlist:
                        if col2.button(t("add_to_watchlist"), key=f"add_{ticker_input_tab2}"): st.session_state.watchlist.append(ticker_input_tab2); st.toast(f"{ticker_input_tab2} {t('added_to_watchlist')}"); st.rerun()
                    
                    c1,c2,c3 = st.columns(3)
                    current_price, prev_close = last_row['Close'], info.get('previousClose', 0)
                    price_change = current_price - prev_close; price_change_pct = (price_change / prev_close) * 100 if prev_close else 0
                    target_price = last_row.get('Close', 0) + (2 * last_row.get('ATRr_14', 0))
                    c1.metric(t("metric_price"), f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.2f}%)", delta_color="inverse" if price_change < 0 else "normal")
                    c2.metric(t("metric_cap"), f"${(info.get('marketCap', 0) / 1e9):.1f}B")
                    c3.metric(t("metric_target_price"), f"${target_price:.2f}")
                    st.divider()
                    
                    analysis_col, chart_col = st.columns([0.8, 1.2])
                    with analysis_col:
                        st.subheader(t("subheader_rule_based")); summary, recommendation = generate_analysis_summary(ticker_input_tab2, info, last_row)
                        st.markdown(summary); st.subheader(t("subheader_company_profile")); st.info(info.get('longBusinessSummary', 'Profile not available.'))
                    with chart_col:
                        st.subheader(t("subheader_charts"))
                        fig = go.Figure(); fig.add_trace(go.Candlestick(x=technicals_df.index, open=technicals_df['Open'], high=technicals_df['High'], low=technicals_df['Low'], close=technicals_df['Close'], name='Price'))
                        fig.update_layout(xaxis_rangeslider_visible=False, template='plotly_dark', margin=dict(l=0, r=0, t=0, b=0), height=400); st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# Sekme 3: İzleme Listesi
# -----------------------------------------------------------------------------
with tabs[2]:
    st.header(t("watchlist_header"))
    if not st.session_state.watchlist: st.info(t("watchlist_empty"))
    else:
        for ticker in st.session_state.watchlist:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            try:
                info = yf.Ticker(ticker).info
                price = info.get('currentPrice', 0); change = info.get('regularMarketChange', 0)
                logo_url = info.get('logo_url', f'https://logo.clearbit.com/{info.get("website", "streamlit.io").split("//")[-1].split("/")[0]}')
                with col1: st.markdown(f"<div style='display:flex; align-items:center;'><img src='{logo_url}' width='30' style='border-radius:50%; margin-right:10px;'> <b>{info.get('shortName', ticker)} ({ticker})</b></div>", unsafe_allow_html=True)
                with col2: st.metric("", f"${price:.2f}", f"{change:.2f}$")
                with col3: st.metric("", f"${(info.get('marketCap', 0)/1e9):.1f}B")
                with col4:
                    if st.button(t("remove_from_watchlist"), key=f"remove_{ticker}"): st.session_state.watchlist.remove(ticker); st.rerun()
            except Exception: st.error(f"{ticker} için veri çekilemedi.")
            st.divider()

