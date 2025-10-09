import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

# --- NLTK Kurulumu ve Sentiment Analyzer ---
@st.cache_resource
def setup_nltk():
    """NLTK için gerekli olan vader_lexicon'u indirir."""
    import nltk
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        st.info("Gerekli dil verileri indiriliyor (yalnızca ilk çalıştırmada)...")
        nltk.download('vader_lexicon')
setup_nltk()

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- Streamlit Sayfa Yapılandırması ---
st.set_page_config(
    page_title="Profesyonel Hisse Senedi Analiz Aracı",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Stil Tanımlamaları ---
st.markdown("""
<style>
    .stMetric { border-radius: 10px; padding: 15px; background-color: #262730; border: 1px solid #262730; }
    .stMetric .st-ae { font-size: 1.1em; font-weight: bold; color: #fafafa; }
    .stMetric .st-af { font-size: 1.5em; font-weight: bold; }
    .risk-low { color: #28a745; }
    .risk-medium { color: #ffc107; }
    .risk-high { color: #dc3545; }
    .stButton>button { width: 100%; }
    .sidebar .stButton>button { text-align: left; }
</style>
""", unsafe_allow_html=True)

# --- ÖNBELLEKLEME FONKSİYONLARI (DAHA DAYANIKLI) ---
@st.cache_data(ttl=300)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty or len(hist) < 20: return None # Teknik analiz için yetersiz veri
        hist = add_technical_indicators(hist)
        return hist
    except Exception: return None

@st.cache_data(ttl=300)
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or info.get('regularMarketPrice') is None: return None, None
        return info, stock.calendar
    except Exception: return None, None

@st.cache_data(ttl=300)
def get_advanced_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.recommendations, stock.insider_transactions, stock.news
    except Exception: return None, None, None

@st.cache_data(ttl=300)
def get_option_chain(ticker):
    try:
        stock = yf.Ticker(ticker)
        exp_dates = stock.options
        if not exp_dates: return None, None, None
        today = datetime.now().date()
        valid_dates = [d for d in exp_dates if (datetime.strptime(d, '%Y-%m-%d').date() - today).days >= 30]
        exp_date = valid_dates[0] if valid_dates else exp_dates[-1] # En azından son tarihi al
        options = stock.option_chain(exp_date)
        return options.calls, options.puts, exp_date
    except Exception: return None, None, None

@st.cache_data(ttl=3600)
def get_risk_free_rate():
    try:
        hist = yf.Ticker("^TNX").history(period="5d")
        return hist['Close'].iloc[-1] / 100 if not hist.empty else 0.04
    except Exception: return 0.04

# --- ANALİZ FONKSİYONLARI (İYİLEŞTİRİLDİ) ---
def add_technical_indicators(df):
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    delta_val = df['Close'].diff()
    gain = delta_val.where(delta_val > 0, 0).rolling(window=14).mean()
    loss = -delta_val.where(delta_val < 0, 0).rolling(window=14).mean()
    rs = gain / loss.replace(0, 1e-9) # Sıfıra bölme hatasını önle
    df['RSI'] = 100 - (100 / (1 + rs))
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def find_support_resistance(df):
    recent_df = df.tail(180)
    if len(recent_df) < 11: return None, None
    current_price = recent_df['Close'].iloc[-1]
    support_levels = [recent_df['Low'][i] for i in range(5, len(recent_df) - 5) if recent_df['Low'][i] <= min(recent_df['Low'][i-5:i+6])]
    resistance_levels = [recent_df['High'][i] for i in range(5, len(recent_df) - 5) if recent_df['High'][i] >= max(recent_df['High'][i-5:i+6])]
    valid_supports = list(set([s for s in support_levels if s < current_price]))
    valid_resistances = list(set([r for r in resistance_levels if r > current_price]))
    closest_support = max(valid_supports) if valid_supports else (recent_df['Low'].min() if recent_df['Low'].min() < current_price else None)
    closest_resistance = min(valid_resistances) if valid_resistances else (recent_df['High'].max() if recent_df['High'].max() > current_price else None)
    return closest_support, closest_resistance

def analyze_sentiment(news_list):
    if not news_list: return 0, []
    sia = SentimentIntensityAnalyzer()
    for item in news_list:
        title = item.get('title')
        item['sentiment'] = sia.polarity_scores(title)['compound'] if title and isinstance(title, str) else 0.0
    avg_sentiment = sum(n.get('sentiment', 0) for n in news_list) / len(news_list) if news_list else 0
    return avg_sentiment, news_list

def calculate_greeks(df, stock_price, risk_free_rate, exp_date_str, option_type='c'):
    if df is None or df.empty or 'strike' not in df.columns or 'impliedVolatility' not in df.columns: return df
    today = datetime.now().date()
    exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
    time_to_expiry = (exp_date - today).days / 365.0
    if time_to_expiry <= 0: return df
    
    # NaN değerleri olan satırları atla
    df_valid = df.dropna(subset=['strike', 'impliedVolatility'])
    if df_valid.empty: return df

    greeks = df_valid.apply(
        lambda r: pd.Series([
            delta(option_type, stock_price, r['strike'], time_to_expiry, risk_free_rate, r['impliedVolatility']),
            gamma(option_type, stock_price, r['strike'], time_to_expiry, risk_free_rate, r['impliedVolatility']),
            theta(option_type, stock_price, r['strike'], time_to_expiry, risk_free_rate, r['impliedVolatility']),
            vega(option_type, stock_price, r['strike'], time_to_expiry, risk_free_rate, r['impliedVolatility'])
        ], index=['delta', 'gamma', 'theta', 'vega']),
        axis=1
    )
    return df.join(greeks)

def analyze_buying_opportunity(df, info):
    signals, score = [], 0
    last, prev = df.iloc[-1], df.iloc[-2]
    if pd.notna(last['RSI']) and pd.notna(prev['RSI']):
        if last['RSI'] > 30 and prev['RSI'] <= 30: signals.append("✅ RSI aşırı satım bölgesinden yukarı döndü."); score += 2
        elif last['RSI'] < 30: signals.append("⚠️ RSI aşırı satım bölgesinde, dönüş bekleniyor."); score += 1
        else: signals.append("➖ RSI nötr veya aşırı alım bölgesinde.")
    if pd.notna(last['MA20']) and pd.notna(last['MA50']) and pd.notna(prev['MA20']) and pd.notna(prev['MA50']):
        if last['MA20'] > last['MA50'] and prev['MA20'] <= prev['MA50']: signals.append("✅ Golden Cross sinyali oluştu (MA20 > MA50)."); score += 2
        elif last['MA20'] > last['MA50']: signals.append("➖ Kısa vadeli ortalama, uzun vadelinin üzerinde (Pozitif)."); score += 1
        else: signals.append("➖ Death Cross aktif (MA20 < MA50).")
    if last['Volume'] > df['Volume'].rolling(window=20).mean().iloc[-1] and last['Close'] > prev['Close']: signals.append("✅ Yükseliş, ortalamanın üzerinde bir hacimle destekleniyor."); score += 1
    else: signals.append("➖ Hacim, yükselişi belirgin şekilde desteklemiyor.")
    pe = info.get('trailingPE'); d_to_e = info.get('debtToEquity')
    if pe and pe > 0 and pe < 25: signals.append(f"✅ F/K oranı ({pe:.2f}) makul seviyede."); score += 1
    elif pe: signals.append(f"⚠️ F/K oranı ({pe:.2f}) sektör ortalamasına göre değerlendirilmeli.")
    if d_to_e is not None and d_to_e < 100: signals.append(f"✅ Borç/Özkaynak oranı ({d_to_e/100:.2f}) sağlıklı."); score += 1
    elif d_to_e is not None: signals.append(f"⚠️ Borç/Özkaynak oranı ({d_to_e/100:.2f}) yüksek.")
    
    if not signals: return ("Analiz için yeterli sinyal yok", "warning", [])
    if score >= 5: return ("Güçlü Alım Fırsatı", "success", signals)
    elif score >= 3: return ("Potansiyel Alım Fırsatı", "success", signals)
    else: return ("Alım İçin Henüz Erken", "warning", signals)

def analyze_option_suitability(df_hist, df_options, info, risk_free_rate, exp_date_str, option_type='call'):
    signals, suggestion, spread_suggestion = [], "Spesifik kontrat önerisi yapılamıyor.", None
    if df_options is None or df_options.empty: return "Opsiyon verisi bulunamadı.", signals, suggestion, None, None
    last = df_hist.iloc[-1]; current_price = last['Close']
    df_options = calculate_greeks(df_options, current_price, risk_free_rate, exp_date_str, 'c' if option_type == 'call' else 'p')
    is_bullish = pd.notna(last['MA20']) and pd.notna(last['MA50']) and last['MA20'] > last['MA50'] and last['RSI'] > 50
    is_bearish = pd.notna(last['MA20']) and pd.notna(last['MA50']) and last['MA20'] < last['MA50'] and last['RSI'] < 50
    if (option_type == 'call' and is_bullish) or (option_type == 'put' and is_bearish): signals.append(f"✅ Hisse, **{option_type.capitalize()}** alımı için uygun trendde.")
    else: signals.append(f"❌ Hisse, **{option_type.capitalize()}** alımı için uygun trendde değil.")
    df_options['liquidity_score'] = df_options.get('openInterest', 0).fillna(0) + df_options.get('volume', 0).fillna(0)
    if df_options['liquidity_score'].sum() > 500: signals.append("✅ Opsiyon zincirinde yeterli likidite mevcut.")
    else: signals.append("⚠️ Opsiyon zincirinde likidite düşük.")
    
    analysis_result = "N/A"
    atm_options = df_options[df_options['strike'] >= current_price].sort_values(by='strike').head(5) if option_type == 'call' else df_options[df_options['strike'] <= current_price].sort_values(by='strike', ascending=False).head(5)
    
    if not atm_options.empty and 'lastPrice' in atm_options.columns:
        best_option = atm_options.sort_values(by='liquidity_score', ascending=False).iloc[0]
        strike, last_price, oi = best_option.get('strike'), best_option.get('lastPrice'), best_option.get('openInterest')
        if strike is not None and last_price is not None and oi is not None:
            if (option_type == 'call' and is_bullish) or (option_type == 'put' and is_bearish):
                analysis_result = f"Beklentiyle **{option_type.capitalize()} Opsiyonu** düşünülebilir."
                strike_price_str, last_price_str = f"${strike:.2f}", f"${last_price:.2f}"
                suggestion = (f"**Öneri:** Vadesi **{exp_date_str}** olan, **{strike_price_str} kullanım fiyatlı** "
                              f"bir **{option_type.capitalize()}** kontratı incelenebilir. "
                              f"(Fiyat: {last_price_str}, Açık Pozisyon: {int(oi)})")

                if option_type == 'call' and len(atm_options) > 1 and 'strike' in atm_options.columns:
                    sell_option = atm_options.iloc[-1]
                    sell_strike_price_str = f"${sell_option.get('strike'):.2f}"
                    spread_suggestion = (f"**Daha Düşük Riskli Strateji (Bull Call Spread):** **{strike_price_str}** call alıp, "
                                         f"aynı anda **{sell_strike_price_str}** call satarak maliyeti düşürebilirsiniz.")
            else:
                analysis_result = f"Mevcut trend, **{option_type.capitalize()} Opsiyonu** alımını desteklemiyor."
    display_cols = ['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility', 'delta', 'gamma', 'theta', 'vega']
    existing_cols = [col for col in display_cols if col in df_options.columns]
    return analysis_result, signals, suggestion, df_options[existing_cols] if existing_cols else None, spread_suggestion

# --- ANA UYGULAMA ARAYÜZÜ ---
st.title("🚀 Profesyonel Hisse Senedi Analiz Aracı")

# --- KENAR ÇUBUĞU ---
if 'watchlist' not in st.session_state: st.session_state.watchlist = ['AAPL', 'NVDA', 'TSLA', 'GOOGL']
st.sidebar.header("Hisse Senedi Seçimi")
ticker_input = st.sidebar.text_input("Analiz için Hisse Senedi Sembolü Girin", "NVDA").upper()
st.sidebar.subheader("İzleme Listesi")
new_stock = st.sidebar.text_input("Listeye Ekle", placeholder="örn: MSFT").upper()
if st.sidebar.button("Ekle"):
    if new_stock and new_stock not in st.session_state.watchlist:
        st.session_state.watchlist.append(new_stock)
    st.rerun()
for stock_symbol in st.session_state.watchlist[:]:
    col1, col2 = st.sidebar.columns([3, 1])
    col1.markdown(f"**{stock_symbol}**")
    if col2.button("Kaldır", key=f"del_{stock_symbol}"):
        st.session_state.watchlist.remove(stock_symbol)
        st.rerun()

# --- ANA İÇERİK ---
if ticker_input:
    hist_data = get_stock_data(ticker_input)
    info, calendar = get_stock_info(ticker_input)
    if hist_data is None or info is None:
        st.error(f"'{ticker_input}' için analiz edilecek yeterli veri bulunamadı. Lütfen sembolü kontrol edin veya daha az bilinen bir hisse ise başka bir hisse deneyin.")
    else:
        recs, insider, news = get_advanced_stock_info(ticker_input)
        calls_df, puts_df, exp_date = get_option_chain(ticker_input)
        risk_free_rate = get_risk_free_rate()
        support, resistance = find_support_resistance(hist_data)
        buy_analysis = analyze_buying_opportunity(hist_data, info)
        
        st.header(f"{info.get('longName', ticker_input)} ({ticker_input}) Analizi")
        
        col_main, col_plan = st.columns([2, 1.5])
        with col_main:
            col_price, col_market, col_risk = st.columns(3)
            current_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
            prev_close = hist_data['Close'].iloc[-2]
            price_change = current_price - prev_close
            percent_change = (price_change / prev_close) * 100 if prev_close else 0
            col_price.metric("Güncel Fiyat", f"${current_price:.2f}", f"{price_change:+.2f} ({percent_change:+.2f}%)")
            market_cap = info.get('marketCap')
            col_market.metric("Piyasa Değeri", f"${market_cap / 1e9:.2f} Milyar" if market_cap else "N/A")
            beta = info.get('beta')
            risk_level, risk_color = ("Orta", "risk-medium")
            if beta:
                if beta < 1.0: risk_level, risk_color = "Düşük", "risk-low"
                elif beta > 1.5: risk_level, risk_color = "Yüksek", "risk-high"
            col_risk.markdown(f"**Risk Seviyesi**<br><span class='{risk_color}' style='font-size: 1.5em; font-weight:bold;'>{risk_level}</span>", unsafe_allow_html=True, help=f"Beta: {beta:.2f if beta else 'N/A'}\n\nBeta, hissenin piyasanın geneline göre ne kadar dalgalı olduğunu gösterir.")
        
        with col_plan:
            st.markdown("**Ticaret Planı Önerisi**")
            entry, stop, target = f"${current_price:.2f}", f"${support:.2f}" if support else "N/A", f"${resistance:.2f}" if resistance else "N/A"
            rr_ratio = "N/A"
            price_minus_support = current_price - support if support else 0
            if resistance and support and price_minus_support > 0:
                rr_ratio = f"{(resistance - current_price) / price_minus_support:.2f} : 1"
            st.markdown(f"- **Giriş:** {entry}\n- **Zarar Durdur (Stop):** {stop}\n- **Kâr Al (Hedef):** {target}\n- **Kazanç/Risk Oranı:** {rr_ratio}")
        
        st.subheader("Genel Alım Fırsatı Değerlendirmesi", divider='rainbow')
        st.markdown(f"**Sonuç:** <span style='color:{'#28a745' if buy_analysis[1]=='success' else '#ffc107'}; font-size: 1.2em;'>{buy_analysis[0]}</span>", unsafe_allow_html=True)
        with st.expander("Detaylı Sinyalleri Gör"):
            for signal in buy_analysis[2]: st.markdown(f"- {signal}")
        
        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Teknik Analiz", "🏢 Temel Analiz", "💡 Derinlemesine Analiz", "⛓️ Opsiyon Analizi"])
        
        with tab1:
            st.subheader("Fiyat Grafiği ve Teknik Göstergeler")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=hist_data.index, open=hist_data['Open'], high=hist_data['High'], low=hist_data['Low'], close=hist_data['Close'], name='Fiyat'), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA20'], mode='lines', name='MA20', line=dict(color='yellow', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA50'], mode='lines', name='MA50', line=dict(color='orange', width=1)), row=1, col=1)
            if support: fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text=f"Destek ${support:.2f}", row=1, col=1)
            if resistance: fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text=f"Direnç ${resistance:.2f}", row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['RSI'], mode='lines', name='RSI'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1); fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            fig.update_layout(title_text=f'{ticker_input} Fiyat Grafiği', xaxis_rangeslider_visible=False, height=600, template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Şirket Bilgileri ve Temel Veriler")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Sektör:** {info.get('sector', 'N/A')}")
                st.info(info.get('longBusinessSummary', 'N/A'))
            with col2:
                st.markdown("**Finansal Metrikler:**")
                st.metric("Fiyat/Kazanç (F/K)", f"{info.get('trailingPE'):.2f}" if info.get('trailingPE') else "N/A", help="Hisse fiyatının, hisse başına yıllık kârına oranıdır.")
                st.metric("Analistlerin Ortalama Hedef Fiyatı", f"${info.get('targetMeanPrice'):.2f}" if info.get('targetMeanPrice') else "N/A")
                st.metric("Açığa Satış Oranı (Short Ratio)", f"{info.get('shortRatio'):.2f}" if info.get('shortRatio') else "N/A", help="Piyasadaki açığa satılan hisse sayısının ortalama günlük işlem hacmine oranıdır.")
        
        with tab3:
            st.subheader("Piyasa Beklentileri ve Şirket İçi Gelişmeler")
            st.markdown("##### Haber Akışı ve Piyasa Duyarlılığı")
            if news:
                avg_sentiment, news_with_sentiment = analyze_sentiment(news)
                sentiment_text = "Nötr"
                if avg_sentiment > 0.1: sentiment_text = "Pozitif"
                elif avg_sentiment < -0.1: sentiment_text = "Negatif"
                st.metric("Ortalama Haber Duyarlılığı", sentiment_text)
                with st.expander("Son Haber Başlıkları"):
                    valid_news = [n for n in news_with_sentiment if n.get('title')]
                    if valid_news:
                        for n in valid_news[:5]:
                            st.markdown(f"- [{n.get('title')}]({n.get('link', '#')}) (Duygu: {n.get('sentiment', 0.0):.2f})")
                    else:
                        st.write("Başlıklı haber bulunamadı.")
            else: st.write("Haber bulunamadı.")
            
            st.markdown("##### Analist Tavsiyeleri")
            if recs is not None and not recs.empty:
                possible_cols = ['Firm', 'To Grade', 'From Grade', 'Action']
                existing_cols = [col for col in possible_cols if col in recs.columns]
                if existing_cols: st.dataframe(recs.tail(5).sort_index(ascending=False)[existing_cols], use_container_width=True)
                else: st.write("Analist tavsiye verisi uygun formatta değil.")
            else: st.write("Analist tavsiyesi verisi bulunamadı.")
            
            st.markdown("##### İçeriden Öğrenenlerin İşlemleri (Yönetici Alım/Satımları)")
            if insider is not None and not insider.empty:
                if 'Shares' in insider.columns and 'Price' in insider.columns: insider['Value ($)'] = insider['Shares'] * insider['Price']
                possible_cols = ['Insider', 'Shares', 'Value ($)', 'Price', 'Transaction']
                existing_cols = [col for col in possible_cols if col in insider.columns]
                if existing_cols: st.dataframe(insider[existing_cols], use_container_width=True)
                else: st.write("Yönetici işlemi verisi uygun formatta değil.")
            else: st.write("Yönetici işlemi verisi bulunamadı.")

        with tab4:
            st.subheader("Opsiyon Zinciri Analizi")
            if exp_date:
                st.info(f"Analiz, **{exp_date}** vadeli opsiyonlar için yapılmıştır.")
                call_analysis, call_signals, call_suggestion, call_df, spread_suggestion = analyze_option_suitability(hist_data, calls_df, info, risk_free_rate, exp_date, 'call')
                put_analysis, put_signals, put_suggestion, put_df, _ = analyze_option_suitability(hist_data, puts_df, info, risk_free_rate, exp_date, 'put')
                st.markdown("#### Yükseliş Beklentisi (Call Opsiyonu)")
                st.markdown(f"**Durum:** {call_analysis}")
                st.success(call_suggestion)
                if spread_suggestion: st.info(spread_suggestion)
                st.markdown("---")
                st.markdown("#### Düşüş Beklentisi (Put Opsiyonu)")
                st.markdown(f"**Durum:** {put_analysis}")
                st.warning(put_suggestion)
                with st.expander("Detaylı Opsiyon Zincirini Görüntüle"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Call Opsiyonları**")
                        st.dataframe(call_df.style.format(precision=2)) if call_df is not None else st.write("Veri yok.")
                    with col2:
                        st.markdown("**Put Opsiyonları**")
                        st.dataframe(put_df.style.format(precision=2)) if put_df is not None else st.write("Veri yok.")
            else:
                st.warning("Bu hisse senedi için opsiyon verisi bulunamadı.")
else:
    st.info("Lütfen analiz etmek için soldaki menüden bir hisse senedi sembolü girin.")

