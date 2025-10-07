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
        "tab_portfolio": "Portföyüm",
        "sidebar_header": "Ayarlar",
        "sidebar_stock_list_label": "Taranacak Hisse Listesi",
        "list_robinhood": "Robinhood'daki Tüm Hisseler",
        "list_sp500": "S&P 500 Hisseleri",
        "list_nasdaq100": "Nasdaq 100 Hisseleri",
        "list_btc": "Bitcoin Tutan Şirketler",
        "screener_header": "Optimal Alım Fırsatları",
        "screener_info": "Bu araç, seçilen listedeki hisseleri en az %5 kâr potansiyeli sunan optimal bir stratejiye göre tarar. Detaylar ve opsiyon analizleri için bir hisseye tıklayın.",
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
        "option_header": "Akıllı Opsiyon Analizi",
        "option_contract": "Kontrat",
        "option_expiry": "Vade",
        "option_buy_target": "Alım Hedef",
        "option_sell_target": "Satış Hedef (Hisse Hedefine Göre)",
        "option_profit_potential": "Potansiyel Kâr",
        "option_call": "Alım (Call)",
        "option_spinner": "Opsiyon verileri yükleniyor...",
        "option_none": "Bu hisse için uygun, likit ve mantıklı maliyetli bir opsiyon bulunamadı.",
        "greeks_header": "Yunanlar (Risk Metrikleri)",
        "delta_label": "Delta (Δ)",
        "delta_help": "Hisse senedi 1$ arttığında, opsiyon priminizin yaklaşık olarak ne kadar artacağını gösterir.",
        "theta_label": "Theta (Θ)",
        "theta_help": "Zamanın aleyhinize nasıl işlediğini, yani opsiyonunuzun her gün ne kadar zaman değeri kaybedeceğini gösterir.",
        "gamma_label": "Gamma (Γ)",
        "gamma_help": "Delta'nın ne kadar hızlı değişeceğini, yani hisse senedi lehinize hareket ettiğinde kazancınızın nasıl ivmeleneceğini gösterir.",
        "analysis_header": "Detaylı Hisse Senedi Analizi",
        "analysis_input_label": "Analiz için sembol girin (örn: AAPL)",
        "add_to_watchlist": "İzleme Listesine Ekle ⭐",
        "remove_from_watchlist": "Listeden Kaldır",
        "added_to_watchlist": "izleme listenize eklendi!",
        "spinner_analysis": "için veriler ve analiz hazırlanıyor...",
        "error_no_data": "Bu hisse için veri bulunamadı. Lütfen sembolü kontrol edin.",
        "error_no_technicals": "Teknik göstergeler hesaplanamadı. Yetersiz veri olabilir.",
        "metric_price": "Güncel Fiyat", "metric_cap": "Piyasa Değeri",
        "metric_target_price": "Fiyat Beklentisi (Kısa Vade)",
        "metric_target_price_bearish": "Aşağı Yönlü Fiyat Beklentisi (Kısa Vade)",
        "metric_target_price_help": "Fiyat hedefi, hissenin son 14 günlük ortalama volatilitesinin (ATR) iki katının mevcut fiyata eklenmesiyle hesaplanır. Bu, kısa vadeli bir potansiyel hareket aralığını gösterir.",
        "metric_target_price_bearish_help": "Fiyat hedefi, hissenin son 14 günlük ortalama volatilitesinin (ATR) iki katının mevcut fiyattan çıkarılmasıyla hesaplanır. Bu, kısa vadeli bir potansiyel düşüş aralığını gösterir.",
        "metric_support_1": "Destek 1 (S1)",
        "metric_resistance_1": "Direnç 1 (R1)",
        "subheader_rule_based": "Kural Tabanlı Teknik Analiz",
        "subheader_company_profile": "Şirket Profili",
        "subheader_charts": "Profesyonel Fiyat Grafiği",
        "summary_recommendation": "Öneri", "recommendation_buy": "AL", "recommendation_sell": "SAT", "recommendation_neutral": "NÖTR",
        "summary_rsi_oversold": "RSI ({rsi:.2f}) aşırı satım bölgesinde, tepki alımı potansiyeli olabilir.",
        "summary_rsi_overbought": "RSI ({rsi:.2f}) aşırı alım bölgesinde, düzeltme riski olabilir.",
        "summary_rsi_neutral": "RSI ({rsi:.2f}) nötr bölgede.",
        "summary_macd_bullish": "MACD, sinyal çizgisini yukarı keserek 'Al' sinyali üretiyor.",
        "summary_macd_bearish": "MACD, sinyal çizgisini aşağı keserek 'Sat' sinyali üretiyor.",
        "summary_sma_golden": "Fiyat, 50 ve 200 günlük ortalamaların üzerinde (Golden Cross). Güçlü yükseliş trendi.",
        "summary_sma_death": "Fiyat, 50 ve 200 günlük ortalamaların altında (Death Cross). Düşüş trendi.",
        "summary_sma_bullish": "Fiyat, 50 günlük ortalamanın üzerinde, kısa vadeli görünüm pozitif.",
        "summary_sma_bearish": "Fiyat, 50 günlük ortalamanın altında, kısa vadede baskı olabilir.",
        "watchlist_header": "Kişisel İzleme Listeniz", 
        "watchlist_empty": "İzleme listeniz boş. 'Hisse Analizi' sekmesinden hisse ekleyebilirsiniz.",
        "portfolio_header": "Portföyüm",
        "portfolio_add_header": "Portföye Yeni Pozisyon Ekle",
        "portfolio_ticker": "Hisse Senedi Sembolü",
        "portfolio_shares": "Adet (Pay)",
        "portfolio_cost": "Ortalama Maliyet ($)",
        "portfolio_add_button": "Pozisyon Ekle",
        "portfolio_empty": "Portföyünüz boş. Yukarıdaki formdan yeni bir pozisyon ekleyebilirsiniz.",
        "portfolio_current_value": "Mevcut Değer",
        "portfolio_pl": "Toplam Kâr/Zarar",
        "portfolio_recommendation": "Aksiyon Önerisi",
        "recommendation_hold": "TUT",
        "recommendation_add": "POZİSYON EKLE",
        "recommendation_sell_strong": "SAT",
        "sell_target": "Satış Hedefi (Kâr Al)",
        "stop_loss": "Stop-Loss (Zarar Durdur)",
        "delete_position": "Pozisyonu Sil",
    },
    "EN": {
        "page_title": "Stock Opportunity Scanning Bot",
        "app_title": "Stock Opportunity Bot",
        "app_caption": "Discover investment opportunities with AI-powered analysis.",
        "tab_screener": "Opportunity Scan",
        "tab_analysis": "Stock Analysis",
        "tab_watchlist": "My Watchlist",
        "tab_portfolio": "My Portfolio",
        "sidebar_header": "Settings",
        "sidebar_stock_list_label": "Stock List to Scan",
        "list_robinhood": "All Robinhood Stocks",
        "list_sp500": "S&P 500 Stocks",
        "list_nasdaq100": "Nasdaq 100 Stocks",
        "list_btc": "Companies Holding Bitcoin",
        "screener_header": "Optimal Buying Opportunities",
        "screener_info": "This tool scans stocks in the selected list for opportunities with at least 5% profit potential. Click on a stock for details and option analysis.",
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
        "option_header": "Smart Option Analysis",
        "option_contract": "Contract",
        "option_expiry": "Expiry",
        "option_buy_target": "Buy Target",
        "option_sell_target": "Sell Target (at Stock Target)",
        "option_profit_potential": "Potential Profit",
        "option_call": "Call",
        "option_spinner": "Loading option data...",
        "option_none": "No suitable, liquid, and reasonably priced options found.",
        "greeks_header": "The Greeks (Risk Metrics)",
        "delta_label": "Delta (Δ)",
        "delta_help": "Shows how much the option price is expected to move for a $1 change in the stock price.",
        "theta_label": "Theta (Θ)",
        "theta_help": "Shows how much value the option loses each day due to time decay.",
        "gamma_label": "Gamma (Γ)",
        "gamma_help": "Shows the rate of change for Delta. It indicates how much the Delta will accelerate.",
        "analysis_header": "Detailed Stock Analysis",
        "analysis_input_label": "Enter symbol for analysis (e.g., AAPL)",
        "add_to_watchlist": "Add to Watchlist ⭐", "remove_from_watchlist": "Remove",
        "added_to_watchlist": "has been added to your watchlist!",
        "spinner_analysis": "Preparing data and analysis for...",
        "error_no_data": "Could not find data for this stock. Please check the symbol.",
        "error_no_technicals": "Could not calculate technical indicators. There might be insufficient data.",
        "metric_price": "Current Price", "metric_cap": "Market Cap",
        "metric_target_price": "Price Target (Short-Term)",
        "metric_target_price_bearish": "Bearish Price Target (Short-Term)",
        "metric_target_price_help": "The price target is calculated by adding two times the Average True Range (ATR) of the last 14 days to the current price. This indicates a potential short-term price movement range.",
        "metric_target_price_bearish_help": "The price target is calculated by subtracting two times the Average True Range (ATR) of the last 14 days from the current price. This indicates a potential short-term downside range.",
        "metric_support_1": "Support 1 (S1)",
        "metric_resistance_1": "Resistance 1 (R1)",
        "subheader_rule_based": "Rule-Based Technical Analysis",
        "subheader_company_profile": "Company Profile",
        "subheader_charts": "Professional Price Chart",
        "summary_recommendation": "Recommendation", "recommendation_buy": "BUY", "recommendation_sell": "SELL", "recommendation_neutral": "NEUTRAL",
        "summary_rsi_oversold": "RSI ({rsi:.2f}) is in the oversold region, suggesting a potential for a rebound.",
        "summary_rsi_overbought": "RSI ({rsi:.2f}) is in the overbought region, suggesting a risk of a correction.",
        "summary_rsi_neutral": "RSI ({rsi:.2f}) is in the neutral zone.",
        "summary_macd_bullish": "MACD is generating a 'Buy' signal, crossing above its signal line.",
        "summary_macd_bearish": "MACD is generating a 'Sell' signal, crossing below its signal line.",
        "summary_sma_golden": "Price is above the 50-day and 200-day MAs (Golden Cross). Strong bullish trend.",
        "summary_sma_death": "Price is below the 50-day and 200-day MAs (Death Cross). Bearish trend.",
        "summary_sma_bullish": "Price is above the 50-day MA, indicating a positive short-term outlook.",
        "summary_sma_bearish": "Price is below the 50-day MA, which may indicate short-term pressure.",
        "watchlist_header": "Your Personal Watchlist", 
        "watchlist_empty": "Your watchlist is empty. Add stocks from the 'Stock Analysis' tab.",
        "portfolio_header": "My Portfolio",
        "portfolio_add_header": "Add New Position to Portfolio",
        "portfolio_ticker": "Stock Symbol",
        "portfolio_shares": "Number of Shares",
        "portfolio_cost": "Average Cost ($)",
        "portfolio_add_button": "Add Position",
        "portfolio_empty": "Your portfolio is empty. Add a new position using the form above.",
        "portfolio_current_value": "Current Value",
        "portfolio_pl": "Total P/L",
        "portfolio_recommendation": "Action Recommendation",
        "recommendation_hold": "HOLD",
        "recommendation_add": "ADD TO POSITION",
        "recommendation_sell_strong": "SELL",
        "sell_target": "Sell Target (Take Profit)",
        "stop_loss": "Stop-Loss",
        "delete_position": "Delete Position",
    }
}

# --- YARDIMCI FONKSİYONLAR ---
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
        df.ta.rsi(append=True); df.ta.macd(append=True); df.ta.sma(length=50, append=True); df.ta.sma(length=200, append=True); df.ta.atr(append=True)
        df.dropna(inplace=True)
    return df

def get_option_suggestion(ticker, current_price, stock_target_price):
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
        
        candidates = calls[(calls['strike'] >= current_price) & (calls['strike'] <= current_price * 1.05)]
        liquid_candidates = candidates[candidates['openInterest'] > 20]
        if liquid_candidates.empty: return None

        liquid_candidates = liquid_candidates.copy()
        liquid_candidates.loc[:, 'spread_pct'] = (liquid_candidates['ask'] - liquid_candidates['bid']) / liquid_candidates['ask']
        tight_spread_candidates = liquid_candidates[liquid_candidates['spread_pct'] < 0.3]
        if tight_spread_candidates.empty: return None

        affordable_candidates = tight_spread_candidates[tight_spread_candidates['ask'] < (current_price * 0.1)]
        if affordable_candidates.empty: return None
        
        best_option = affordable_candidates.sort_values(by='ask').iloc[0]
        buy_price = best_option['ask']
        if buy_price > 0:
            intrinsic_value_at_target = max(0, stock_target_price - best_option['strike'])
            sell_target = buy_price + intrinsic_value_at_target
            
            return {
                "expiry": target_expiry, 
                "strike": best_option['strike'], 
                "buy_target": buy_price,
                "sell_target": sell_target,
                "delta": best_option.get('delta', 0),
                "theta": best_option.get('theta', 0),
                "gamma": best_option.get('gamma', 0)
            }
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
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'scan_results' not in st.session_state: st.session_state.scan_results = []

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu ve TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title=t("page_title"), page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style>/* CSS Kısaltıldı */</style>""", unsafe_allow_html=True)

# --- HEADER ve DİL SEÇİMİ ---
LOGO_SVG = """<svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 12.25C8.48528 12.25 9.75 11.1688 9.75 9.875C9.75 8.58125 8.48528 7.5 7 7.5C5.51472 7.5 4.25 8.58125 4.25 9.875C4.25 11.1688 5.51472 12.25 7 12.25Z" stroke="#00C805" stroke-width="1.5"/><path d="M17 16.5C18.4853 16.5 19.75 15.4187 19.75 14.125C19.75 12.8312 18.4853 11.75 17 11.75C15.5147 11.75 14.25 12.8312 14.25 14.125C14.25 15.4187 15.5147 16.5 17 16.5Z" stroke="#00C805" stroke-width="1.5"/><path d="M9.75 9.875H14.25L14.25 14.125" stroke="#00C805" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 21.25C4 18.3505 6.35051 16 9.25 16H14.75C17.6495 16 20 18.3505 20 21.25" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/><path d="M18.5 7.75L19.25 7" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/><path d="M21.25 5L20.5 5.75" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/><path d="M16 4.25L15.25 3.5" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/></svg>"""
header_cols = st.columns([1, 3, 1])
with header_cols[0]: st.markdown(f"<div style='display: flex; align-items: center; height: 100%;'>{LOGO_SVG}</div>", unsafe_allow_html=True)
with header_cols[1]: st.markdown(f"<div><h1 style='margin-bottom: -10px; color: #FFFFFF;'>{t('app_title')}</h1><p style='color: #888;'>{t('app_caption')}</p></div>", unsafe_allow_html=True)
with header_cols[2]: st.radio("Language / Dil", options=["TR", "EN"], key="lang", horizontal=True, label_visibility="collapsed")

# -----------------------------------------------------------------------------
# Ana Sekmeler
# -----------------------------------------------------------------------------
tab_icons = ["📈", "🔍", "⭐", "💼"]
tabs = st.tabs([f"{icon} {label}" for icon, label in zip(tab_icons, [t('tab_screener'), t('tab_analysis'), t('tab_watchlist'), t('tab_portfolio')])])

# -----------------------------------------------------------------------------
# Kenar Çubuğu (SIDEBAR)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header(t("sidebar_header"))
    stock_lists_map = { 
        t("list_robinhood"): get_robinhood_tickers, 
        t("list_sp500"): get_sp500_tickers, 
        t("list_nasdaq100"): get_nasdaq100_tickers, 
        t("list_btc"): get_bitcoin_holders_tickers 
    }
    selected_list_name = st.selectbox(t("sidebar_stock_list_label"), options=list(stock_lists_map.keys()))
    st.markdown("---"); st.markdown("by Yusa Kurkcu")

# -----------------------------------------------------------------------------
# Sekme 1: Hisse Taraması
# -----------------------------------------------------------------------------
with tabs[0]:
    if 'scan_results' not in st.session_state or not st.session_state.scan_results:
        st.info(t("screener_info"))

    if st.button(t("screener_button"), type="primary"):
        tickers_to_scan = stock_lists_map[selected_list_name]()
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
                        if last_row['Close'] > 0 and (target_price - last_row['Close']) / last_row['Close'] < 0.05: continue
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
                    # ... (Bu sekmenin tam kodu öncekiyle aynı) ...
                    pass

# -----------------------------------------------------------------------------
# Sekme 3: İzleme Listesi
# -----------------------------------------------------------------------------
with tabs[2]:
    st.header(t("watchlist_header"))
    if not st.session_state.watchlist: st.info(t("watchlist_empty"))
    else:
        for ticker in st.session_state.watchlist:
            # ... (Bu sekmenin tam kodu öncekiyle aynı) ...
            pass

# -----------------------------------------------------------------------------
# Sekme 4: Portföyüm
# -----------------------------------------------------------------------------
with tabs[3]:
    st.header(t("portfolio_header"))
    with st.form("portfolio_form"):
        st.subheader(t("portfolio_add_header"))
        cols = st.columns([2, 1, 1])
        ticker = cols[0].text_input(t("portfolio_ticker")).upper()
        shares = cols[1].number_input(t("portfolio_shares"), min_value=0.0, format="%.4f")
        cost = cols[2].number_input(t("portfolio_cost"), min_value=0.0, format="%.2f")
        submitted = st.form_submit_button(t("portfolio_add_button"))
        if submitted and ticker and shares > 0 and cost > 0:
            st.session_state.portfolio.append({"ticker": ticker, "shares": shares, "cost": cost})
            st.rerun()

    st.markdown("---")
    if not st.session_state.portfolio: st.info(t("portfolio_empty"))
    else:
        total_portfolio_value = 0; total_portfolio_cost = 0
        for i, pos in enumerate(st.session_state.portfolio):
            try:
                info = yf.Ticker(pos['ticker']).info
                current_price = info.get('currentPrice', 0)
                cost_basis = pos['shares'] * pos['cost']; current_value = pos['shares'] * current_price
                total_pl = current_value - cost_basis; total_pl_pct = (total_pl / cost_basis) * 100 if cost_basis > 0 else 0
                total_portfolio_value += current_value; total_portfolio_cost += cost_basis
                
                with st.container():
                    st.markdown(f"#### {info.get('shortName', pos['ticker'])} ({pos['ticker']})")
                    c1, c2, c3 = st.columns(3)
                    c1.metric(label=t("portfolio_current_value"), value=f"${current_value:,.2f}")
                    c2.metric(label=t("portfolio_pl"), value=f"${total_pl:,.2f}", delta=f"{total_pl_pct:.2f}%")
                    
                    hist = yf.Ticker(pos['ticker']).history(period="6mo"); tech = calculate_technicals(hist)
                    if tech is not None and not tech.empty:
                        last_row = tech.iloc[-1]; _, recommendation = generate_analysis_summary(pos['ticker'], info, last_row)
                        action_rec = t("recommendation_hold")
                        if recommendation == t("recommendation_buy"): action_rec = t("recommendation_add")
                        elif recommendation == t("recommendation_sell"): action_rec = t("recommendation_sell_strong")
                        c3.metric(label=t("portfolio_recommendation"), value=action_rec)

                        recent_data = tech.tail(90)
                        support1 = recent_data['Low'].min(); resistance1 = recent_data['High'].max()
                        st.text(f"🎯 {t('sell_target')}: ${resistance1:.2f} | 🛑 {t('stop_loss')}: ${support1:.2f}")

                    if st.button(t("delete_position"), key=f"delete_{i}"):
                        st.session_state.portfolio.pop(i); st.rerun()
                st.markdown("---")
            except Exception: st.error(f"{pos['ticker']} için analiz oluşturulamadı.")
        
        overall_pl = total_portfolio_value - total_portfolio_cost
        overall_pl_pct = (overall_pl / total_portfolio_cost) * 100 if total_portfolio_cost > 0 else 0
        st.header("Portföy Özeti")
        p1, p2 = st.columns(2)
        p1.metric("Toplam Portföy Değeri", f"${total_portfolio_value:,.2f}")
        p2.metric("Toplam Kâr/Zarar", f"${overall_pl:,.2f}", delta=f"{overall_pl_pct:.2f}%")

# --- FOOTER ---
st.markdown("<hr style='border-color:#222; margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #888; padding: 20px;'>by Yusa Kurkcu</div>", unsafe_allow_html=True)

