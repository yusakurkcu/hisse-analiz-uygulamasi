import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- YARDIMCI FONKSİYONLAR ---
@st.cache_data(ttl=86400)
def get_ticker_list(list_name_key):
    try:
        if list_name_key == "Tüm ABD Hisseleri":
            url = "https://pkgstore.datahub.io/core/nasdaq-listings/nasdaq-listed_csv/data/7665719fb51081ba0bd834fde7cde094/nasdaq-listed_csv.csv"
            df = pd.read_csv(url)
            return df[~df['Symbol'].str.contains(r'\$|\.', na=False)]['Symbol'].dropna().unique().tolist()
        elif list_name_key == "S&P 500 Hisseleri":
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            df = pd.read_html(url, header=0)[0]
            return df['Symbol'].tolist()
        elif list_name_key == "Nasdaq 100 Hisseleri":
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            df = pd.read_html(url, header=0)[4]
            return df['Ticker'].tolist()
        elif list_name_key == "Bitcoin Tutan Şirketler":
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
        if 'volume' in df.columns:
            df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
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
    if rsi < 30: summary_points.append(f"RSI ({rsi:.2f}) aşırı satım bölgesinde, tepki alımı potansiyeli olabilir."); buy_signals += 2
    elif rsi > 70: summary_points.append(f"RSI ({rsi:.2f}) aşırı alım bölgesinde, düzeltme riski olabilir."); sell_signals += 2
    else: summary_points.append(f"RSI ({rsi:.2f}) nötr bölgede.")

    if last_row.get('macd_12_26_9', 0) > last_row.get('macds_12_26_9', 0): summary_points.append("MACD, sinyal çizgisini yukarı keserek 'Al' sinyali üretiyor."); buy_signals += 1
    else: summary_points.append("MACD, sinyal çizgisini aşağı keserek 'Sat' sinyali üretiyor."); sell_signals += 1

    current_price = last_row.get('close', 0); sma_50 = last_row.get('sma_50', 0); sma_200 = last_row.get('sma_200', 0)
    if sma_50 > 0 and sma_200 > 0:
        if current_price > sma_50 and sma_50 > sma_200: summary_points.append("Fiyat, 50 ve 200 günlük ortalamaların üzerinde (Golden Cross). Güçlü yükseliş trendi."); buy_signals += 2
        elif current_price < sma_50 and current_price < sma_200: summary_points.append("Fiyat, 50 ve 200 günlük ortalamaların altında (Death Cross). Düşüş trendi."); sell_signals += 2
        elif current_price > sma_50: summary_points.append("Fiyat, 50 günlük ortalamanın üzerinde, kısa vadeli görünüm pozitif."); buy_signals += 1
        else: summary_points.append("Fiyat, 50 günlük ortalamanın altında, kısa vadede baskı olabilir."); sell_signals += 1
    
    recommendation = "NÖTR"
    if buy_signals > sell_signals + 1: recommendation = "AL"
    elif sell_signals > buy_signals + 1: recommendation = "SAT"
    
    final_summary = f"**{info.get('longName', ticker)} ({ticker})**: \n" + "- " + "\n- ".join(summary_points)
    return final_summary, recommendation

# -----------------------------------------------------------------------------
# Oturum Durumu Başlatma
# -----------------------------------------------------------------------------
if 'watchlist' not in st.session_state: st.session_state.watchlist = []
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'scan_results' not in st.session_state: st.session_state.scan_results = []

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu ve TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Borsa Fırsat Tarama Botu", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-16txtl3 { display: none; }
</style>""", unsafe_allow_html=True)

# --- HEADER ---
LOGO_SVG = """<svg width="60" height="60" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 12.25C8.48528 12.25 9.75 11.1688 9.75 9.875C9.75 8.58125 8.48528 7.5 7 7.5C5.51472 7.5 4.25 8.58125 4.25 9.875C4.25 11.1688 5.51472 12.25 7 12.25Z" stroke="#00C805" stroke-width="1.5"/><path d="M17 16.5C18.4853 16.5 19.75 15.4187 19.75 14.125C19.75 12.8312 18.4853 11.75 17 11.75C15.5147 11.75 14.25 12.8312 14.25 14.125C14.25 15.4187 15.5147 16.5 17 16.5Z" stroke="#00C805" stroke-width="1.5"/><path d="M9.75 9.875H14.25L14.25 14.125" stroke="#00C805" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 21.25C4 18.3505 6.35051 16 9.25 16H14.75C17.6495 16 20 18.3505 20 21.25" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/><path d="M18.5 7.75L19.25 7" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/><path d="M21.25 5L20.5 5.75" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/><path d="M16 4.25L15.25 3.5" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"/></svg>"""
header_cols = st.columns([1, 4])
with header_cols[0]: st.markdown(f"<div style='display: flex; align-items: center; height: 100%;'>{LOGO_SVG}</div>", unsafe_allow_html=True)
with header_cols[1]: st.markdown(f"<div><h1 style='margin-bottom: -10px; color: #FFFFFF;'>Borsa Fırsat Tarama Botu</h1><p style='color: #888;'>Profesyonel stratejilerle yatırım fırsatlarını keşfedin.</p></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Ana Sekmeler
# -----------------------------------------------------------------------------
tab_icons = ["📈", "🔍", "⭐", "💼"]
tabs = st.tabs([f"{tab_icons[0]} Fırsat Taraması", f"{tab_icons[1]} Hisse Analizi", f"{tab_icons[2]} İzleme Listem", f"{tab_icons[3]} Portföyüm"])

# -----------------------------------------------------------------------------
# Sekme 1: Hisse Taraması
# -----------------------------------------------------------------------------
with tabs[0]:
    col1, col2 = st.columns([2,1])
    with col1:
        list_options = ["Tüm ABD Hisseleri", "S&P 500 Hisseleri", "Nasdaq 100 Hisseleri", "Bitcoin Tutan Şirketler"]
        selected_list_name = st.selectbox("Taranacak Hisse Listesi", options=list_options)
    with col2:
        st.write(""); st.write("") # Boşluk
        scan_button = st.button("Fırsatları Bul", type="primary", use_container_width=True)

    if not st.session_state.scan_results:
        st.info("Bu araç, seçilen listedeki hisseleri 'yükseliş trendindeki geri çekilme' stratejisine göre tarar. Detaylar için bir hisseye tıklayın.")

    if scan_button:
        tickers_to_scan = get_ticker_list(selected_list_name)
        with st.spinner(f"'{selected_list_name}' hisseleri taranıyor..."):
            results = []
            if not tickers_to_scan: st.error("Taranacak hisse listesi alınamadı.")
            else:
                progress_bar = st.progress(0, text="Başlatılıyor...")
                for i, ticker in enumerate(tickers_to_scan):
                    progress_bar.progress((i + 1) / len(tickers_to_scan), text=f"Taranıyor: {ticker} ({i+1}/{len(tickers_to_scan)})")
                    data, info, _ = get_stock_data(ticker, "1y")
                    if data is None or data.empty or info is None or info.get('marketCap', 0) < 500_000_000: continue
                    data = calculate_technicals(data)
                    if data is not None and len(data) > 21 and all(c in data.columns for c in ['close', 'high', 'low', 'sma_50', 'sma_200', 'volume', 'volume_sma_20']):
                        last_row = data.iloc[-1]
                        
                        is_in_uptrend = last_row['close'] > last_row['sma_200']
                        recent_range = data.tail(20)
                        consolidation_high = recent_range['high'].max()
                        consolidation_low = recent_range['low'].min()
                        is_consolidating = (consolidation_high - consolidation_low) / consolidation_low < 0.15 
                        
                        is_breakout = last_row['close'] > consolidation_high
                        is_volume_confirmed = last_row['volume'] > last_row['volume_sma_20'] * 1.5
                        
                        if is_in_uptrend and is_consolidating and is_breakout and is_volume_confirmed:
                            results.append({"ticker": ticker, "info": info, "technicals": data, "last_row": last_row})
                progress_bar.empty()
        st.session_state.scan_results = results; st.rerun()

    if 'scan_results' in st.session_state:
        results = st.session_state.scan_results
        if results:
            st.success(f"{len(results)} adet potansiyel fırsat bulundu!")
            for i, result in enumerate(results):
                # ... Sonuç kartları ...
                pass
        elif len(st.session_state.scan_results) == 0:
            st.warning("Mevcut piyasa koşullarında bu stratejiye uyan hiçbir hisse bulunamadı.")

# -----------------------------------------------------------------------------
# Sekme 2: Tek Hisse Analizi
# -----------------------------------------------------------------------------
with tabs[1]:
    st.header("Detaylı Hisse Senedi Analizi")
    ticker_input_tab2 = st.text_input("Analiz için sembol girin (örn: AAPL)", "NVDA", key="tab2_input").upper()
    if ticker_input_tab2: 
        with st.spinner(f"{ticker_input_tab2} için veriler ve analiz hazırlanıyor..."):
            hist_data, info, news = get_stock_data(ticker_input_tab2, period="2y")
            if hist_data is None or hist_data.empty or info is None: st.error("Bu hisse için veri bulunamadı. Lütfen sembolü kontrol edin.")
            else:
                technicals_df = calculate_technicals(hist_data.copy())
                if technicals_df is None or technicals_df.empty: st.error("Teknik göstergeler hesaplanamadı. Yetersiz veri olabilir.")
                else:
                    last_row = technicals_df.iloc[-1]
                    summary, recommendation = generate_analysis_summary(ticker_input_tab2, info, last_row)
                    
                    st.subheader(f"{info.get('longName', ticker_input_tab2)} ({ticker_input_tab2})")
                    
                    c1,c2,c3 = st.columns(3)
                    current_price = last_row.get('close', 0); prev_close = info.get('previousClose', 0)
                    price_change = current_price - prev_close; price_change_pct = (price_change / prev_close) * 100 if prev_close else 0
                    
                    c1.metric("Güncel Fiyat", f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.2f}%)", delta_color="inverse" if price_change < 0 else "normal")
                    c2.metric("Piyasa Değeri", f"${(info.get('marketCap', 0) / 1e9):.1f}B")

                    atr_val = last_row.get('atrr_14', 0)
                    if recommendation == "SAT":
                        target_price = last_row.get('close', 0) - (2 * atr_val)
                        c3.metric("Aşağı Yönlü Fiyat Beklentisi (Kısa Vade)", f"${target_price:.2f}", help="Fiyat hedefi, hissenin son 14 günlük ortalama volatilitesinin (ATR) iki katının mevcut fiyattan çıkarılmasıyla hesaplanır.")
                    else:
                        target_price = last_row.get('close', 0) + (2 * atr_val)
                        c3.metric("Fiyat Beklentisi (Kısa Vade)", f"${target_price:.2f}", help="Fiyat hedefi, hissenin son 14 günlük ortalama volatilitesinin (ATR) iki katının mevcut fiyata eklenmesiyle hesaplanır.")

                    recent_data = technicals_df.tail(90)
                    support1 = recent_data['low'].min()
                    resistance1 = recent_data['high'].max()
                    c4, c5 = st.columns(2)
                    c4.metric("Destek 1 (S1)", f"${support1:.2f}")
                    c5.metric("Direnç 1 (R1)", f"${resistance1:.2f}")
                    st.divider()
                    
                    analysis_col, chart_col = st.columns([1, 1])
                    with analysis_col:
                        st.subheader("Kural Tabanlı Teknik Analiz")
                        st.markdown(summary); st.subheader("Şirket Profili"); st.info(info.get('longBusinessSummary', 'Profile not available.'))
                        
                        st.subheader(f"📜 Akıllı Opsiyon Analizi")
                        with st.spinner("Opsiyon verileri yükleniyor..."): option = get_option_suggestion(ticker_input_tab2, last_row['close'], target_price)
                        if option:
                            st.metric(label=f"Kontrat (Alım (Call))", value=f"${option['strike']:.2f}")
                            st.text(f"Vade: {option['expiry']}")
                            st.metric(label="Alım Hedef", value=f"${option['buy_target']:.2f}")
                        else: st.info("Bu hisse için uygun, likit ve mantıklı maliyetli bir opsiyon bulunamadı.")

                    with chart_col:
                        st.subheader("Profesyonel Fiyat Grafiği")
                        fig = go.Figure(); fig.add_trace(go.Candlestick(x=technicals_df.index, open=technicals_df['open'], high=technicals_df['high'], low=technicals_df['low'], close=technicals_df['close'], name='Price'))
                        fig.add_hline(y=support1, line_dash="dash", line_color="green", annotation_text="Destek 1 (S1)", annotation_position="bottom right")
                        fig.add_hline(y=resistance1, line_dash="dash", line_color="red", annotation_text="Direnç 1 (R1)", annotation_position="top right")
                        fig.update_layout(xaxis_rangeslider_visible=False, template='plotly_dark', margin=dict(l=0, r=0, t=0, b=0), height=450); st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# Sekme 3: İzleme Listesi
# -----------------------------------------------------------------------------
with tabs[2]:
    st.header("Kişisel İzleme Listeniz")
    if not st.session_state.watchlist: st.info("İzleme listeniz boş. 'Hisse Analizi' sekmesinden hisse ekleyebilirsiniz.")
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
                    if st.button("Listeden Kaldır", key=f"remove_{ticker}"): st.session_state.watchlist.remove(ticker); st.rerun()
            except Exception: st.error(f"{ticker} için veri çekilemedi.")
            st.divider()

# -----------------------------------------------------------------------------
# Sekme 4: Portföyüm
# -----------------------------------------------------------------------------
with tabs[3]:
    st.header("Portföyüm")
    with st.form("portfolio_form"):
        st.subheader("Portföye Yeni Pozisyon Ekle")
        cols = st.columns([2, 1, 1])
        ticker = cols[0].text_input("Hisse Senedi Sembolü").upper()
        shares = cols[1].number_input("Adet (Pay)", min_value=0.0, format="%.4f")
        cost = cols[2].number_input("Ortalama Maliyet ($)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Pozisyon Ekle")
        if submitted and ticker and shares > 0 and cost > 0:
            st.session_state.portfolio.append({"ticker": ticker, "shares": shares, "cost": cost})
            st.rerun()

    st.markdown("---")
    if not st.session_state.portfolio: st.info("Portföyünüz boş. Yukarıdaki formdan yeni bir pozisyon ekleyebilirsiniz.")
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
                    c1.metric(label="Mevcut Değer", value=f"${current_value:,.2f}")
                    c2.metric(label="Toplam Kâr/Zarar", value=f"${total_pl:,.2f}", delta=f"{total_pl_pct:.2f}%")
                    
                    hist = yf.Ticker(pos['ticker']).history(period="6mo"); tech = calculate_technicals(hist)
                    if tech is not None and not tech.empty:
                        last_row = tech.iloc[-1]; _, recommendation = generate_analysis_summary(pos['ticker'], info, last_row)
                        action_rec = "TUT"
                        if recommendation == "AL": action_rec = "POZİSYON EKLE"
                        elif recommendation == "SAT": action_rec = "SAT"
                        c3.metric(label="Aksiyon Önerisi", value=action_rec)

                        recent_data = tech.tail(90)
                        support1 = recent_data['low'].min(); resistance1 = recent_data['high'].max()
                        st.text(f"🎯 Satış Hedefi (Kâr Al): ${resistance1:.2f} | 🛑 Stop-Loss (Zarar Durdur): ${support1:.2f}")

                    if st.button("Pozisyonu Sil", key=f"delete_{i}"):
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

