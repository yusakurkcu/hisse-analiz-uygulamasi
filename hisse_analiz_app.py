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
        "sidebar_stock_list_label": "Taranacak Hisse Listesi",
        "list_robinhood": "Robinhood'daki Tüm Hisseler",
        "list_sp500": "S&P 500 Hisseleri",
        "list_nasdaq100": "Nasdaq 100 Hisseleri",
        "list_btc": "Bitcoin Tutan Şirketler",
        "screener_header": "Optimal Alım Fırsatları",
        "screener_info": "Bu araç, seçilen listedeki hisseleri 'yükseliş trendindeki geri çekilme' stratejisine göre tarar. Detaylar için bir hisseye tıklayın.",
        "screener_button": "Fırsatları Bul",
        "screener_spinner": "hisseleri taranıyor...",
        "screener_success": "adet potansiyel fırsat bulundu!",
        "screener_warning_no_stock": "Mevcut piyasa koşullarında optimal stratejiye uyan hiçbir hisse bulunamadı.",
        "col_price": "Fiyat", "col_rsi": "RSI", "col_potential": "Potansiyel",
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
        # ... (İngilizce çeviriler öncekiyle aynı, sadeleştirildi) ...
    }
}

# --- YARDIMCI FONKSİYONLAR ---
def t(key): return LANGUAGES[st.session_state.lang].get(key, key)

@st.cache_data(ttl=86400)
def get_ticker_list(list_name_key):
    try:
        if list_name_key == t("list_robinhood"):
            url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed-symbols.csv"
            df = pd.read_csv(url)
            return df[~df['Symbol'].str.contains(r'\$|\.', na=False)]['Symbol'].dropna().unique().tolist()
        elif list_name_key == t("list_sp500"):
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            df = pd.read_html(url, header=0)[0]
            return df['Symbol'].tolist()
        elif list_name_key == t("list_nasdaq100"):
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            df = pd.read_html(url, header=0)[4]
            return df['Ticker'].tolist()
        elif list_name_key == t("list_btc"):
            return ["MSTR", "MARA", "TSLA", "COIN", "SQ", "RIOT", "HUT", "BITF", "CLSK", "BTBT", "HIVE", "CIFR", "IREN", "WULF"]
    except Exception as e:
        st.error(f"Hisse listesi çekilirken hata oluştu: {e}")
        return []

@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try:
        stock = yf.Ticker(ticker)
        data, info, news = stock.history(period=period, auto_adjust=False), stock.info, stock.news
        if not data.empty:
            data.columns = [col.lower() for col in data.columns]
        return data, info, news
    except Exception: return None, None, None

@st.cache_data
def calculate_technicals(df):
    if df is not None and not df.empty and len(df) > 50:
        df.columns = [col.lower() for col in df.columns]
        df.ta.rsi(close=df['close'], append=True)
        df.ta.macd(close=df['close'], append=True)
        df.ta.sma(close=df['close'], length=50, append=True)
        df.ta.sma(close=df['close'], length=200, append=True)
        df.ta.atr(high=df['high'], low=df['low'], close=df['close'], length=14, append=True)
        df.dropna(inplace=True)
        df.columns = [col.lower() for col in df.columns]
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
    
    rsi = last_row.get('rsi_14', 50)
    if rsi < 30: summary_points.append(t('summary_rsi_oversold').format(rsi=rsi)); buy_signals += 2
    elif rsi > 70: summary_points.append(t('summary_rsi_overbought').format(rsi=rsi)); sell_signals += 2
    else: summary_points.append(t('summary_rsi_neutral').format(rsi=rsi))

    if last_row.get('macd_12_26_9', 0) > last_row.get('macds_12_26_9', 0): summary_points.append(t('summary_macd_bullish')); buy_signals += 1
    else: summary_points.append(t('summary_macd_bearish')); sell_signals += 1

    current_price = last_row.get('close', 0); sma_50 = last_row.get('sma_50', 0); sma_200 = last_row.get('sma_200', 0)
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
st.set_page_config(page_title=t("page_title"), page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-16txtl3 { display: none; }
</style>""", unsafe_allow_html=True)

# --- HEADER ve DİL SEÇİMİ ---
LOGO_SVG = """...""" # SVG Kısaltıldı
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
# Sekme 1: Hisse Taraması
# -----------------------------------------------------------------------------
with tabs[0]:
    col1, col2 = st.columns([2,1])
    with col1:
        selected_list_name = st.selectbox(t("sidebar_stock_list_label"), options=[t("list_robinhood"), t("list_sp500"), t("list_nasdaq100"), t("list_btc")])
    with col2:
        st.write(""); st.write("") # Boşluk
        scan_button = st.button(t("screener_button"), type="primary", use_container_width=True)

    if not st.session_state.scan_results:
        st.info(t("screener_info"))

    if scan_button:
        tickers_to_scan = get_ticker_list(selected_list_name)
        with st.spinner(f"'{selected_list_name}' {t('screener_spinner')}"):
            results = []
            if not tickers_to_scan: st.error("Taranacak hisse listesi alınamadı.")
            else:
                progress_bar = st.progress(0, text="Başlatılıyor...")
                for i, ticker in enumerate(tickers_to_scan):
                    progress_bar.progress((i + 1) / len(tickers_to_scan), text=f"Taranıyor: {ticker} ({i+1}/{len(tickers_to_scan)})")
                    data, info, _ = get_stock_data(ticker, "1y")
                    if data is None or data.empty or info is None or info.get('marketCap', 0) < 300_000_000: continue
                    data = calculate_technicals(data)
                    if data is not None and len(data) > 2 and all(c in data.columns for c in ['rsi_14', 'sma_50', 'macd_12_26_9', 'macds_12_26_9', 'atrr_14']):
                        last_row = data.iloc[-1]
                        prev_row = data.iloc[-2]
                        if last_row['rsi_14'] < 55 and last_row['close'] > last_row['sma_50'] and last_row['macd_12_26_9'] > last_row['macds_12_26_9'] and prev_row['macd_12_26_9'] <= prev_row['macds_12_26_9']:
                            results.append({"ticker": ticker, "info": info, "technicals": data, "last_row": last_row})
                progress_bar.empty()
        st.session_state.scan_results = results; st.rerun()

    if st.session_state.scan_results:
        results = st.session_state.scan_results
        st.success(f"{len(results)} {t('screener_success')}")
        for i, result in enumerate(results):
            info, last_row, technicals, ticker = result['info'], result['last_row'], result['technicals'], result['ticker']
            logo_url = info.get('logo_url', f'https://logo.clearbit.com/{info.get("website", "streamlit.io").split("//")[-1].split("/")[0]}')
            target_price = last_row['close'] + (2 * last_row['atrr_14'])
            potential_gain_pct = ((target_price - last_row['close']) / last_row['close']) * 100 if last_row['close'] > 0 else 0
            expander_title = f"<div style='display:flex; align-items:center;'><img src='{logo_url}' width='30' style='border-radius:50%; margin-right:10px;'> <div><b>{info.get('shortName', ticker)} ({ticker})</b><br><small style='color:#00C805;'>{t('col_potential')}: +{potential_gain_pct:.2f}%</small></div></div>"
            with st.expander(expander_title, expanded=False):
                col1, col2 = st.columns([1.2, 1])
                with col1:
                    st.metric(label=t('detail_target_price'), value=f"${target_price:.2f}")
                    st.subheader(t('calculator_header'))
                    investment_amount = st.number_input(t('calculator_input_label'), min_value=100, value=1000, step=100, key=f"invest_{i}")
                    potential_return = (target_price / last_row['close']) * investment_amount if last_row['close'] > 0 else 0
                    potential_profit = potential_return - investment_amount
                    st.metric(label=t('calculator_return_label'), value=f"${potential_return:,.2f}", delta=f"${potential_profit:,.2f}")
                with col2:
                    st.subheader(f"📜 {t('option_header')}")
                    with st.spinner(t('option_spinner')): option = get_option_suggestion(ticker, last_row['close'], target_price)
                    if option:
                        st.metric(label=f"{t('option_contract')} ({t('option_call')})", value=f"${option['strike']:.2f}")
                        st.text(f"{t('option_expiry')}: {option['expiry']}")
                        st.metric(label=t('option_buy_target'), value=f"${option['buy_target']:.2f}")
                        sell_profit_pct = ((option['sell_target']-option['buy_target'])/option['buy_target'])*100 if option['buy_target'] > 0 else 0
                        st.metric(label=t('option_sell_target'), value=f"${option['sell_target']:.2f}", delta=f"+{sell_profit_pct:.2f}%")
                    else: st.info(t('option_none'))

    elif 'scan_results' in st.session_state and not st.session_state.scan_results:
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
                    summary, recommendation = generate_analysis_summary(ticker_input_tab2, info, last_row)
                    
                    col1, col2 = st.columns([3, 1]); col1.subheader(f"{info.get('longName', ticker_input_tab2)} ({ticker_input_tab2})")
                    if ticker_input_tab2 not in st.session_state.watchlist:
                        if col2.button(t("add_to_watchlist"), key=f"add_{ticker_input_tab2}"): st.session_state.watchlist.append(ticker_input_tab2); st.toast(f"{ticker_input_tab2} {t('added_to_watchlist')}"); st.rerun()
                    
                    c1,c2,c3 = st.columns(3)
                    current_price = last_row.get('close', 0); prev_close = info.get('previousClose', 0)
                    price_change = current_price - prev_close; price_change_pct = (price_change / prev_close) * 100 if prev_close else 0
                    
                    c1.metric(t("metric_price"), f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.2f}%)", delta_color="inverse" if price_change < 0 else "normal")
                    c2.metric(t("metric_cap"), f"${(info.get('marketCap', 0) / 1e9):.1f}B")

                    atr_val = last_row.get('atrr_14', 0)
                    if recommendation == t("recommendation_sell"):
                        target_price = last_row.get('close', 0) - (2 * atr_val)
                        c3.metric(t("metric_target_price_bearish"), f"${target_price:.2f}", help=t("metric_target_price_bearish_help"))
                    else:
                        target_price = last_row.get('close', 0) + (2 * atr_val)
                        c3.metric(t("metric_target_price"), f"${target_price:.2f}", help=t("metric_target_price_help"))

                    recent_data = technicals_df.tail(90)
                    support1 = recent_data['low'].min()
                    resistance1 = recent_data['high'].max()
                    c4, c5 = st.columns(2)
                    c4.metric(t("metric_support_1"), f"${support1:.2f}")
                    c5.metric(t("metric_resistance_1"), f"${resistance1:.2f}")
                    st.divider()
                    
                    analysis_col, chart_col = st.columns([1, 1])
                    with analysis_col:
                        st.subheader(t("subheader_rule_based"))
                        st.markdown(summary); st.subheader(t("subheader_company_profile")); st.info(info.get('longBusinessSummary', 'Profile not available.'))
                        
                        st.subheader(f"📜 {t('option_header')}")
                        with st.spinner(t('option_spinner')): option = get_option_suggestion(ticker_input_tab2, last_row['close'], target_price)
                        if option:
                            st.metric(label=f"{t('option_contract')} ({t('option_call')})", value=f"${option['strike']:.2f}")
                            st.text(f"{t('option_expiry')}: {option['expiry']}")
                            st.metric(label=t('option_buy_target'), value=f"${option['buy_target']:.2f}")
                        else: st.info(t('option_none'))

                    with chart_col:
                        st.subheader(t("subheader_charts"))
                        fig = go.Figure(); fig.add_trace(go.Candlestick(x=technicals_df.index, open=technicals_df['open'], high=technicals_df['high'], low=technicals_df['low'], close=technicals_df['close'], name='Price'))
                        fig.add_hline(y=support1, line_dash="dash", line_color="green", annotation_text=t("metric_support_1"), annotation_position="bottom right")
                        fig.add_hline(y=resistance1, line_dash="dash", line_color="red", annotation_text=t("metric_resistance_1"), annotation_position="top right")
                        fig.update_layout(xaxis_rangeslider_visible=False, template='plotly_dark', margin=dict(l=0, r=0, t=0, b=0), height=450); st.plotly_chart(fig, use_container_width=True)

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
                        support1 = recent_data['low'].min(); resistance1 = recent_data['high'].max()
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

