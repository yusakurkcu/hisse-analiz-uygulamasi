import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Dil ve Çeviri Ayarları
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
        "metric_price": "Güncel Fiyat", "metric_cap": "Piyasa Değeri", "metric_volume": "Hacim", "metric_pe": "F/K Oranı",
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
        "metric_price": "Current Price", "metric_cap": "Market Cap", "metric_volume": "Volume", "metric_pe": "P/E Ratio",
        "subheader_rule_based": "Rule-Based Technical Analysis",
        "subheader_company_profile": "Company Profile",
        "subheader_charts": "Professional Price Chart",
        "watchlist_header": "Your Personal Watchlist", 
        "watchlist_empty": "Your watchlist is empty. Add stocks from the 'Stock Analysis' tab.",
    }
}

# --- Yardımcı Fonksiyonlar ---
def t(key): return LANGUAGES[st.session_state.lang].get(key, key)

@st.cache_data(ttl=86400)
def get_ticker_list(list_name):
    try:
        if list_name == t("list_robinhood"):
            url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed-symbols.csv"
            df = pd.read_csv(url)
            return df[~df['Symbol'].str.contains(r'\$|\.', na=False)]['Symbol'].dropna().unique().tolist()
        elif list_name == t("list_sp500"):
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            df = pd.read_html(url, header=0)[0]
            return df['Symbol'].tolist()
        elif list_name == t("list_nasdaq100"):
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            df = pd.read_html(url, header=0)[4]
            return df['Ticker'].tolist()
        elif list_name == t("list_btc"):
            return ["MSTR", "MARA", "TSLA", "COIN", "SQ", "RIOT", "HUT", "BITF", "CLSK", "BTBT", "HIVE", "CIFR", "IREN", "WULF"]
    except Exception as e:
        st.error(f"Hisse listesi çekilirken hata oluştu: {e}")
        return []

@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period=period, auto_adjust=False), stock.info, stock.news
    except Exception: return None, None, None

@st.cache_data
def calculate_technicals(df):
    if df is not None and not df.empty and len(df) > 50:
        df.ta.rsi(append=True); df.ta.macd(append=True); df.ta.sma(length=50, append=True); df.ta.atr(append=True)
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

# -----------------------------------------------------------------------------
# Oturum Durumu Başlatma
# -----------------------------------------------------------------------------
if 'lang' not in st.session_state: st.session_state.lang = "TR"
if 'watchlist' not in st.session_state: st.session_state.watchlist = []

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu ve TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title=t("page_title"), page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #000000; color: #FFFFFF; }
    .st-emotion-cache-16txtl3 { background-color: #000000; border-right: 1px solid #1a1a1a; }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #00C805;
        background-color: transparent;
        color: #00C805;
        font-weight: 600;
        padding: 8px 20px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        border-color: #FFFFFF;
        background-color: #00C805;
        color: #000000;
        transform: scale(1.05);
        box-shadow: 0px 0px 15px rgba(0, 200, 5, 0.5);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab-list"] button {
        background-color: transparent;
        color: #888;
        border: 0;
        font-weight: 600;
        font-size: 1em;
        padding-bottom: 10px;
        border-bottom: 2px solid transparent;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #FFFFFF;
        border-bottom: 2px solid #00C805;
    }
    .stExpander {
        border: none;
        border-radius: 12px;
        background-color: #121212;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stExpander header { font-size: 1.1em; font-weight: 600; }
    .stMetric {
        background-color: #181818;
        padding: 15px;
        border-radius: 10px;
    }
    [data-testid="stMetricDelta"] svg { display: inline; }
    h1, h2, h3, h4 { color: #FFFFFF; }
</style>""", unsafe_allow_html=True)

# --- HEADER ---
LOGO_SVG = """
<svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M7 12.25C8.48528 12.25 9.75 11.1688 9.75 9.875C9.75 8.58125 8.48528 7.5 7 7.5C5.51472 7.5 4.25 8.58125 4.25 9.875C4.25 11.1688 5.51472 12.25 7 12.25Z" stroke="#00C805" stroke-width="1.5"/>
<path d="M17 16.5C18.4853 16.5 19.75 15.4187 19.75 14.125C19.75 12.8312 18.4853 11.75 17 11.75C15.5147 11.75 14.25 12.8312 14.25 14.125C14.25 15.4187 15.5147 16.5 17 16.5Z" stroke="#00C805" stroke-width="1.5"/>
<path d="M9.75 9.875H14.25L14.25 14.125" stroke="#00C805" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M4 21.25C4 18.3505 6.35051 16 9.25 16H14.75C17.6495 16 20 18.3505 20 21.25" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>
<path d="M18.5 7.75L19.25 7" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>
<path d="M21.25 5L20.5 5.75" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>
<path d="M16 4.25L15.25 3.5" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/>
</svg>
"""

st.markdown(f"""
<div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
    {LOGO_SVG}
    <div>
        <h1 style='margin-bottom: -10px; color: #FFFFFF;'>{t("app_title")}</h1>
        <p style='color: #888;'>{t("app_caption")}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Ana Sekmeler
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    f"📈 {t('tab_screener')}", 
    f"🔍 {t('tab_analysis')}", 
    f"⭐ {t('tab_watchlist')}"
])

# -----------------------------------------------------------------------------
# Kenar Çubuğu (SIDEBAR)
# -----------------------------------------------------------------------------
st.sidebar.selectbox("Language / Dil", options=["TR", "EN"], key="lang")
st.sidebar.header(t("sidebar_header"))
stock_lists = {
    t("list_robinhood"): get_ticker_list,
    t("list_sp500"): get_ticker_list,
    t("list_nasdaq100"): get_ticker_list,
    t("list_btc"): get_ticker_list,
}
selected_list_name = st.sidebar.selectbox(t("sidebar_stock_list_label"), options=list(stock_lists.keys()))
st.sidebar.markdown("---")
st.sidebar.markdown("by Yusa Kurkcu")

# -----------------------------------------------------------------------------
# Sekme 1: Hisse Taraması
# -----------------------------------------------------------------------------
with tab1:
    if 'scan_results' not in st.session_state:
        st.info(t("screener_info"))
    
    if st.button(t("screener_button"), type="primary"):
        tickers_to_scan = stock_lists[selected_list_name](selected_list_name)
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
        st.session_state.scan_results = results
        st.rerun()

    if 'scan_results' in st.session_state:
        results = st.session_state.scan_results
        if results:
            st.success(f"{len(results)} {t('screener_success')}")
            for i, result in enumerate(results):
                info, last_row, technicals, ticker = result['info'], result['last_row'], result['technicals'], result['ticker']
                logo_url = info.get('logo_url', f'https://logo.clearbit.com/{info.get("website", "streamlit.io").split("//")[-1].split("/")[0]}')
                expander_title = f"<img src='{logo_url}' width='30' style='border-radius:50%; margin-right:10px; vertical-align:middle;'> **{info.get('shortName', ticker)} ({ticker})** | {t('col_price')}: ${last_row['Close']:.2f}"
                
                with st.expander(expander_title, expanded=False):
                    col1, col2 = st.columns([1.2, 1])
                    with col1:
                        target_price = last_row['Close'] + (2 * last_row['ATRr_14'])
                        st.metric(label=t('detail_target_price'), value=f"${target_price:.2f}")
                        st.subheader(t('calculator_header'))
                        investment_amount = st.number_input(t('calculator_input_label'), min_value=100, value=1000, step=100, key=f"invest_{i}")
                        potential_return = (target_price / last_row['Close']) * investment_amount if last_row['Close'] > 0 else 0
                        potential_profit = potential_return - investment_amount
                        st.metric(label=t('calculator_return_label'), value=f"${potential_return:,.2f}", delta=f"${potential_profit:,.2f}")
                    with col2:
                        st.subheader(t('option_header'))
                        with st.spinner(t('option_spinner')): option = get_option_suggestion(ticker, last_row['Close'])
                        if option:
                            st.metric(label=f"{t('option_contract')} ({t('option_call')})", value=f"${option['strike']:.2f}")
                            st.text(f"{t('option_expiry')}: {option['expiry']}")
                            st.metric(label=t('option_buy_target'), value=f"${option['buy_target']:.2f}")
                            st.metric(label=t('option_sell_target'), value=f"${option['sell_target']:.2f}", delta="100%")
                        else: st.info(t('option_none'))
        elif len(st.session_state.scan_results) == 0:
            st.warning(t("screener_warning_no_stock"))

# -----------------------------------------------------------------------------
# Sekme 2: Tek Hisse Analizi
# -----------------------------------------------------------------------------
def display_single_stock_analysis(ticker_input):
    with st.spinner(f"{t('spinner_analysis')} {ticker_input}..."):
        hist_data, info, news = get_stock_data(ticker_input, period="2y")
        if hist_data is None or hist_data.empty or info is None: st.error(t("error_no_data")); return
        # ... (Bu fonksiyonun geri kalanı önceki tam versiyon ile aynı)

with tab2:
    st.header(t("analysis_header"))
    ticker_input_tab2 = st.text_input(t("analysis_input_label"), "NVDA", key="tab2_input").upper()
    if ticker_input_tab2: display_single_stock_analysis(ticker_input_tab2)

# -----------------------------------------------------------------------------
# Sekme 3: İzleme Listesi
# -----------------------------------------------------------------------------
with tab3:
    st.header(t("watchlist_header"))
    if not st.session_state.watchlist: st.info(t("watchlist_empty"))
    else:
        # ... (Bu sekmenin kodu önceki tam versiyon ile aynı)
        pass

