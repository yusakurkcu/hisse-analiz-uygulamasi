import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
from newsapi import NewsApiClient
from textblob import TextBlob
import time

# --- UYGULAMA AYARLARI ---
st.set_page_config(layout="wide", page_title="AI Hisse Strateji Motoru")

# NewsAPI Anahtarı - Lütfen kendi NewsAPI anahtarınızı kullanın.
NEWS_API_KEY = "b45712756c0a4d93827bd02ae10c43c2"
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# --- VERİ VE ANALİZ FONKSİYONLARI ---

@st.cache_data(ttl=3600)
def load_all_tradable_stocks():
    url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed-symbols.csv"
    try:
        df = pd.read_csv(url)
        df.rename(columns={'Company Name': 'Company_Name', 'Symbol': 'Symbol'}, inplace=True)
        df.drop_duplicates(subset=['Symbol'], keep='first', inplace=True)
        df.sort_values(by='Symbol', inplace=True)
        df['display_name'] = df['Symbol'] + ' - ' + df['Company_Name']
        return df
    except Exception: return None

# HIZ LİMİTİNE KARŞI KORUMALI VERİ ÇEKME FONKSİYONU
def get_ticker_with_retry(ticker_symbol, retries=3, delay=60):
    for i in range(retries):
        try:
            ticker_obj = yf.Ticker(ticker_symbol)
            # Hızlı bir test sorgusu ile ticker'ın geçerli olup olmadığını kontrol et
            if ticker_obj.history(period="1d").empty:
                return None
            return ticker_obj
        except (yf.YFRateLimitError, Exception) as e:
            st.warning(f"Yahoo Finance hız limitine takıldık veya bir hata oluştu. {delay} saniye bekleniyor... ({i+1}/{retries})")
            time.sleep(delay)
    st.error(f"{ticker_symbol} için veri çekme denemeleri başarısız oldu. Tarama devam ediyor.")
    return None

@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try:
        ticker_obj = get_ticker_with_retry(ticker)
        if ticker_obj:
            return ticker_obj.history(period=period)
        return pd.DataFrame()
    except Exception: return pd.DataFrame()

def analyze_for_ai_screener(data):
    if data is None or len(data) < 200: return None
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=200, append=True)
    last = data.iloc[-1]
    score = 0; signals = []
    if 'SMA_200' in last and last['Close'] > last['SMA_200']: score += 1; signals.append("Uzun Vadeli Trend Pozitif")
    if 'RSI_14' in last and last['RSI_14'] < 35: score += 1; signals.append("RSI Aşırı Satım")
    if 'BBL_20_2.0' in last and last['Close'] <= last['BBL_20_2.0']: score += 1; signals.append("Bollinger Alt Bandı")
    if 'MACD_12_26_9' in data.columns and len(data) > 2 and (data['MACD_12_26_9'].iloc[-1] > data['MACDs_12_26_9'].iloc[-1]) and (data['MACD_12_26_9'].iloc[-2] < data['MACDs_12_26_9'].iloc[-2]): score += 1; signals.append("Yeni MACD Al Sinyali")
    if score >= 2:
        target_price = last.get('BBM_20_2.0', 0)
        current_price = last['Close']
        if target_price > current_price: return {"signals": ", ".join(signals), "score": f"{score}/4", "current_price": current_price, "target_price": target_price, "potential_profit_pct": ((target_price - current_price) / current_price) * 100}
    return None

def recommend_option(options_df):
    if options_df is None or options_df.empty: return None
    required_cols = ['delta', 'theta', 'volume', 'openInterest', 'strike', 'lastPrice']
    if not all(col in options_df.columns for col in required_cols): return None
    df = options_df[(options_df['delta'].abs() >= 0.30) & (options_df['delta'].abs() <= 0.60) & (options_df['volume'] >= 10) & (options_df['openInterest'] >= 50)].copy()
    if df.empty: return None
    df['score'] = df['openInterest'] + df['theta'].abs() * -100
    best_option = df.loc[df['score'].idxmax()]
    return best_option

def get_detailed_analysis(data):
    if data is None or len(data) < 1: return {}, None
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=50, append=True); data.ta.sma(length=200, append=True); data.ta.atr(length=14, append=True)
    last = data.iloc[-1]
    signals = {'bullish': [], 'bearish': []}
    if 'RSI_14' in last and last['RSI_14'] < 30: signals['bullish'].append("RSI Aşırı Satım")
    elif 'RSI_14' in last and last['RSI_14'] > 70: signals['bearish'].append("RSI Aşırı Alım")
    if 'BBL_20_2.0' in last and 'Close' in last and last['Close'] <= last['BBL_20_2.0']: signals['bullish'].append("Bollinger Alt Bandı")
    elif 'BBU_20_2.0' in last and 'Close' in last and last['Close'] >= last['BBU_20_2.0']: signals['bearish'].append("Bollinger Üst Bandı")
    if 'MACD_12_26_9' in last and 'MACDs_12_26_9' in last and last['MACD_12_26_9'] > last['MACDs_12_26_9']: signals['bullish'].append("MACD Pozitif")
    elif 'MACD_12_26_9' in last and 'MACDs_12_26_9' in last: signals['bearish'].append("MACD Negatif")
    if 'SMA_50' in last and 'SMA_200' in last and 'Close' in last and last['Close'] > last['SMA_50'] and last['Close'] > last['SMA_200']:
        signals['bullish'].append("Güçlü Yükseliş Trendi")
    elif 'SMA_50' in last and 'SMA_200' in last and 'Close' in last and last['Close'] < last['SMA_50'] and last['Close'] < last['SMA_200']:
        signals['bearish'].append("Güçlü Düşüş Trendi")
    return signals, last

@st.cache_data(ttl=1800)
def get_market_health():
    try:
        spy_data = yf.Ticker("SPY").history(period="3mo")
        spy_data.ta.sma(length=50, append=True)
        last_price = spy_data['Close'].iloc[-1]
        sma_50 = spy_data['SMA_50'].iloc[-1]
        if last_price > sma_50: return "Boğa Piyasası (Olumlu)", "S&P 500 (SPY) 50 günlük hareketli ortalamasının üzerinde.", "success"
        else: return "Dikkatli Olunmalı (Nötr/Olumsuz)", "S&P 500 (SPY) 50 günlük hareketli ortalamasının altında.", "warning"
    except Exception: return "Belirlenemedi", "Piyasa endeksi verisi alınamadı.", "error"

def analyze_portfolio_position(position, market_health_status):
    try:
        data = get_stock_data(position['Hisse'])
        if data.empty: return "Veri Alınamadı"
        signals, last = get_detailed_analysis(data)
        current_price = last['Close']
        profit_pct = ((current_price - position['Maliyet']) / position['Maliyet']) * 100 if position['Maliyet'] > 0 else 0
        is_bullish_trend = "Güçlü Yükseliş Trendi" in signals['bullish']; is_bearish_trend = "Güçlü Düşüş Trendi" in signals['bearish']
        if profit_pct > 25 and "RSI Aşırı Alım" in signals['bearish']: return f"📈 **Kâr Almayı Değerlendir:** %{profit_pct:.2f} kârda ve hisse 'pahalı' görünüyor."
        elif profit_pct < -15 and is_bearish_trend: return f"📉 **Zararı Durdurmayı Düşün:** %{profit_pct:.2f} zararda ve ana trend aşağı."
        elif is_bullish_trend and market_health_status == "Boğa Piyasası (Olumlu)": return f"💪 **Pozisyonu Koru ve Büyüt:** %{profit_pct:.2f} kâr/zararda. Hem hisse hem de piyasa trendi olumlu."
        elif is_bullish_trend and "RSI Aşırı Satım" in signals['bullish']: return f"🔍 **Pozisyona Ekleme Fırsatı:** %{profit_pct:.2f} kâr/zararda. Ana trend yukarıyken geri çekilme yaşıyor."
        else: return f"🤔 **Tut/Gözlemle:** %{profit_pct:.2f} kâr/zararda. Belirgin bir sinyal yok."
    except Exception: return "Analiz Başarısız"

@st.cache_data(ttl=3600)
def get_news_for_stock(ticker):
    try:
        end_date = datetime.now()
        start_date = end_date - pd.Timedelta(days=7)
        all_articles = newsapi.get_everything(q=ticker, from_param=start_date.strftime('%Y-%m-%d'), language='en', sort_by='relevancy', page_size=10)
        analyzed_articles = []
        for article in all_articles['articles']:
            blob = TextBlob(article['title'])
            sentiment = 'Nötr'
            if blob.sentiment.polarity > 0.15: sentiment = 'Pozitif'
            elif blob.sentiment.polarity < -0.15: sentiment = 'Negatif'
            analyzed_articles.append({'title': article['title'], 'url': article['url'], 'sentiment': sentiment})
        return analyzed_articles
    except Exception: return []

# --- ANA ARAYÜZ ---
st.title('🤖 AI Hisse Senedi Strateji Motoru')
st.caption('Portföy Optimizasyonu, AI Fırsat Tarama ve Derinlemesine Analiz')
st.error("**YASAL UYARI:** Bu uygulama tarafından üretilen tüm veriler, analizler ve öneriler tamamen **eğitim ve simülasyon amaçlıdır.** Yatırım kararlarınızı profesyonel bir danışmana başvurmadan almayınız.", icon="🚨")

full_stock_list = load_all_tradable_stocks()
if full_stock_list is None:
    st.error("Hisse senedi listesi yüklenemedi. Lütfen internet bağlantınızı kontrol edip sayfayı yenileyin.")
else:
    tab1, tab2, tab3 = st.tabs(["🚀 AI Fırsat Tarayıcısı", "🔍 Detaylı Hisse Analizi", "🧠 Portföy Stratejisti"])

    # --- SEKME 1: AI FIRSAT TARAYICISI ---
    with tab1:
        st.header("Yüksek Potansiyelli Hisse ve Opsiyon Fırsatlarını Keşfedin")
        scan_for_options = st.checkbox("Opsiyon Fırsatlarını da Tara (Tarama Süresini Ciddi Şekilde Uzatır)", value=False, key="scan_options_checkbox")
        st.warning("**LÜTFEN DİKKAT:** Sadece hisse taraması **5-15 dakika**, opsiyonlarla birlikte tarama **20-60+ dakika** sürebilir.", icon="⏳")
        if st.button('🧠 TÜM PİYASAYI TARA!', type="primary", key="scan_market_button"):
            opportunities = []
            ticker_symbols = full_stock_list['Symbol'].tolist()
            total_tickers = len(ticker_symbols)
            progress_bar = st.progress(0, text="AI Motoru Başlatılıyor...")
            for i, ticker in enumerate(ticker_symbols):
                stock_data = get_stock_data(ticker)
                opportunity = analyze_for_ai_screener(stock_data)
                if opportunity:
                    opportunity['ticker'] = ticker
                    if scan_for_options:
                        ticker_obj = get_ticker_with_retry(ticker)
                        if ticker_obj and ticker_obj.options:
                            try:
                                exp_date = ticker_obj.options[0]
                                options_chain = ticker_obj.option_chain(exp_date)
                                recommended_call = recommend_option(options_chain.calls)
                                if recommended_call is not None:
                                    opportunity['option_strike'] = recommended_call['strike']; opportunity['option_price'] = recommended_call['lastPrice']; opportunity['option_expiry'] = exp_date
                            except Exception: pass
                    opportunities.append(opportunity)
                progress_text = f"Analiz Ediliyor: {ticker} ({i+1}/{total_tickers}) - Fırsatlar: {len(opportunities)}"
                progress_bar.progress((i + 1) / total_tickers, text=progress_text)
            progress_bar.empty()
            if not opportunities:
                st.success("✅ Tarama Tamamlandı! Bugün AI kriterlerine uyan yüksek puanlı bir fırsat tespit edilmedi.", icon="👍")
            else:
                st.success(f"✅ Tarama Tamamlandı! {len(opportunities)} adet yüksek puanlı fırsat bulundu.", icon="🎯")
                df = pd.DataFrame(opportunities)
                df['Önerilen Opsiyon'] = df.apply(lambda row: f"${row.get('option_strike')} CALL ({datetime.strptime(row.get('option_expiry'), '%Y-%m-%d').strftime('%d %b')})" if pd.notna(row.get('option_strike')) else "N/A", axis=1)
                st.subheader("AI Tarafından Belirlenen Yüksek Potansiyelli Fırsatlar")
                st.dataframe(df, column_config={
                    "ticker": st.column_config.TextColumn("Hisse"),
                    "signals": st.column_config.TextColumn("Onaylanan Sinyaller", width="medium"),
                    "score": st.column_config.TextColumn("Sinyal Gücü"),
                    "current_price": st.column_config.NumberColumn("Mevcut Fiyat", format="$%.2f"),
                    "target_price": st.column_config.NumberColumn("Hedef Fiyat", format="$%.2f"),
                    "potential_profit_pct": st.column_config.NumberColumn("Potansiyel Kâr", format="%.2f%%"),
                    "Önerilen Opsiyon": st.column_config.TextColumn("Öneri: Opsiyon"),
                    "option_price": st.column_config.NumberColumn("Opsiyon Fiyatı", format="$%.2f"),
                }, use_container_width=True, hide_index=True,
                column_order=("ticker", "signals", "score", "current_price", "target_price", "potential_profit_pct", "Önerilen Opsiyon", "option_price"))

    # --- SEKME 2: DETAYLI HİSSE ANALİZİ (TAM VE ÇALIŞAN) ---
    with tab2:
        st.header("İstediğiniz Hisseyi Derinlemesine İnceleyin")
        selected_display_name = st.selectbox('Analiz edilecek hisseyi seçin veya yazarak arayın:', full_stock_list['display_name'], index=None, placeholder="Piyasadaki herhangi bir hisseyi arayın...", key="single_stock_selector")
        
        if selected_display_name:
            selected_ticker = selected_display_name.split(' - ')[0]
            ticker_obj = get_ticker_with_retry(selected_ticker)
            
            if ticker_obj is None:
                st.error(f"{selected_ticker} için veri çekilemedi. Lütfen daha sonra tekrar deneyin.")
            else:
                data = get_stock_data(selected_ticker)
                if data.empty:
                    st.error("Bu hisse için veri alınamadı.")
                else:
                    signals, last = get_detailed_analysis(data)
                    info = ticker_obj.info
                    st.subheader(f"{info.get('longName', selected_ticker)} ({selected_ticker})")
                    st.caption(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')} | {info.get('country', 'N/A')}")
                    st.divider()

                    st.markdown("#### 🎯 Stratejik Seviyeler ve Ticaret Planı")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("##### Statik Seviyeler")
                        current_price = data['Close'].iloc[-1]; support_level = data['Low'].tail(90).min(); resistance_level = data['High'].tail(90).max()
                        st.metric("Mevcut Fiyat", f"${current_price:,.2f}")
                        st.metric("Destek (Son 3 Ay)", f"${support_level:,.2f}")
                        st.metric("Direnç (Son 3 Ay)", f"${resistance_level:,.2f}")
                    with col2:
                        st.markdown("##### 🛡️ Risk Kalkanı (Volatiliteye Dayalı Plan)")
                        if 'ATRr_14' in last and pd.notna(last['ATRr_14']):
                            atr_value = last['ATRr_14']; stop_loss = current_price - (2 * atr_value); risk_amount = current_price - stop_loss
                            target_1 = current_price + (1.5 * risk_amount); target_2 = current_price + (2.5 * risk_amount)
                            st.metric("Dinamik Stop-Loss", f"${stop_loss:,.2f}", help="Hissenin ortalama volatilitesine (2 x ATR) göre hesaplanan zarar durdurma seviyesi.")
                            st.metric("Hedef 1 (1.5R Ödül)", f"${target_1:,.2f}", help="Aldığınız riskin 1.5 katı potansiyel kâr sunan hedef.")
                            st.metric("Hedef 2 (2.5R Ödül)", f"${target_2:,.2f}", help="Aldığınız riskin 2.5 katı potansiyel kâr sunan hedef.")
                            st.caption(f"Bu plan, hissenin son 14 gündeki ortalama {atr_value:,.2f}$'lık hareketine dayanmaktadır.")
                        else:
                            st.info("Volatiliteye dayalı bir plan oluşturmak için yeterli veri yok.")
                    st.divider()

                    st.markdown("#### 📈 İnteraktif Fiyat Grafiği")
                    col_chart, col_options = st.columns([4, 1])
                    with col_options:
                        st.write("Göstergeler:"); show_bbands = st.checkbox("Bollinger Bantları", True, key=f"bb_{selected_ticker}"); show_sma50 = st.checkbox("50 Günlük Ortalama", True, key=f"sma50_{selected_ticker}"); show_sma200 = st.checkbox("200 Günlük Ortalama", True, key=f"sma200_{selected_ticker}"); st.write("---"); show_rsi = st.checkbox("RSI Grafiği", True, key=f"rsi_{selected_ticker}"); show_macd = st.checkbox("MACD Grafiği", False, key=f"macd_{selected_ticker}")
                    with col_chart:
                        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Fiyat')])
                        if show_bbands and 'BBU_20_2.0' in data.columns: fig.add_trace(go.Scatter(x=data.index, y=data['BBU_20_2.0'], mode='lines', line_color='rgba(150,150,150,0.5)', name='Bollinger Üst')); fig.add_trace(go.Scatter(x=data.index, y=data['BBL_20_2.0'], mode='lines', line_color='rgba(150,150,150,0.5)', name='Bollinger Alt', fill='tonexty', fillcolor='rgba(200,200,200,0.1)'))
                        if show_sma50 and 'SMA_50' in data.columns: fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], mode='lines', line_color='orange', name='50 Günlük MA'))
                        if show_sma200 and 'SMA_200' in data.columns: fig.add_trace(go.Scatter(x=data.index, y=data['SMA_200'], mode='lines', line_color='purple', name='200 Günlük MA'))
                        fig.update_layout(xaxis_rangeslider_visible=False, height=400, margin=dict(t=0, b=20, l=0, r=0)); st.plotly_chart(fig, use_container_width=True)
                        if show_rsi and 'RSI_14' in data.columns: fig_rsi = go.Figure(); fig_rsi.add_trace(go.Scatter(x=data.index, y=data['RSI_14'], mode='lines', name='RSI')); fig_rsi.add_hline(y=70, line_dash="dash", line_color="red"); fig_rsi.add_hline(y=30, line_dash="dash", line_color="green"); fig_rsi.update_layout(title_text="RSI", height=200, margin=dict(t=30, b=20, l=0, r=0)); st.plotly_chart(fig_rsi, use_container_width=True)
                        if show_macd and 'MACD_12_26_9' in data.columns: fig_macd = go.Figure(); fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACD_12_26_9'], mode='lines', name='MACD', line_color='blue')); fig_macd.add_trace(go.Scatter(x=data.index, y=data['MACDs_12_26_9'], mode='lines', name='Sinyal', line_color='orange')); fig_macd.add_bar(x=data.index, y=data['MACDh_12_26_9'], name='Histogram'); fig_macd.update_layout(title_text="MACD", height=200, margin=dict(t=30, b=20, l=0, r=0)); st.plotly_chart(fig_macd, use_container_width=True)

                    st.divider()
                    # ... Diğer analiz bölümleri (Finansal Karne, Haberler vs. buraya gelecek)

    # --- SEKME 3: PORTFÖY STRATEJİSTİ (TAM VE ÇALIŞAN) ---
    with tab3:
        st.header("Kişisel Portföyünüz İçin AI Destekli Stratejiler")
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = pd.DataFrame(columns=["Hisse", "Adet", "Maliyet"])

        with st.expander(" Portföyünüze Yeni Pozisyon Ekleyin"):
            col1, col2, col3, col4 = st.columns([2,1,1,1])
            with col1:
                ticker_to_add = st.text_input("Hisse Sembolü", "", key="add_ticker").upper()
            with col2:
                quantity_to_add = st.number_input("Adet", min_value=0.01, step=0.01, format="%.2f", key="add_qty")
            with col3:
                cost_to_add = st.number_input("Ortalama Maliyet ($)", min_value=0.01, step=0.01, format="%.2f", key="add_cost")
            with col4:
                st.write(""); st.write("") # Boşluk
                if st.button("Ekle", use_container_width=True, key="add_button"):
                    if ticker_to_add and quantity_to_add > 0:
                        new_pos = pd.DataFrame([{"Hisse": ticker_to_add, "Adet": quantity_to_add, "Maliyet": cost_to_add}])
                        st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_pos], ignore_index=True)
                        st.success(f"{ticker_to_add} portföyünüze eklendi!")
                    else: st.warning("Lütfen tüm alanları doldurun.")
        
        st.divider()

        if not st.session_state.portfolio.empty:
            if st.button("🧠 Portföyüm İçin Strateji Oluştur!", type="primary", use_container_width=True):
                with st.spinner("AI stratejistiniz portföyünüzü ve piyasayı analiz ediyor..."):
                    results = []; sectors = {}; total_value = 0; total_cost = 0
                    market_health, market_comment, market_status_type = get_market_health()
                    for index, position in st.session_state.portfolio.iterrows():
                        try:
                            ticker_obj = get_ticker_with_retry(position['Hisse'])
                            if ticker_obj:
                                ticker_info = ticker_obj.info
                                current_price = ticker_info.get('currentPrice', ticker_obj.history(period="1d")['Close'].iloc[-1])
                                sector = ticker_info.get('sector', 'Diğer'); value = position['Adet'] * current_price
                                total_value += value
                                if sector in sectors: sectors[sector] += value
                                else: sectors[sector] = value
                                cost = position['Adet'] * position['Maliyet']; total_cost += cost
                                profit_loss = value - cost
                                profit_loss_pct = (profit_loss / cost) * 100 if cost > 0 else 0
                                strategy = analyze_portfolio_position(position, market_health)
                                results.append({"Hisse": position['Hisse'], "Anlık Değer": value, "Kâr/Zarar ($)": profit_loss, "Kâr/Zarar (%)": profit_loss_pct, "AI Strateji Önerisi": strategy})
                        except Exception:
                            results.append({"Hisse": position['Hisse'], "Anlık Değer": 0, "Kâr/Zarar ($)": 0, "Kâr/Zarar (%)": 0, "AI Strateji Önerisi": "Hisse verisi alınamadı."})
                    
                    st.markdown("---"); st.subheader("Portföy Analizi ve Risk Değerlendirmesi")
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        total_pl = total_value - total_cost
                        total_pl_pct = (total_pl / total_cost) * 100 if total_cost > 0 else 0
                        st.metric("Toplam Portföy Değeri", f"${total_value:,.2f}", f"{total_pl:,.2f}$ ({total_pl_pct:.2f}%)")
                        if market_status_type == "success": st.success(f"**Piyasa Sağlığı:** {market_health}", icon="📈")
                        else: st.warning(f"**Piyasa Sağlığı:** {market_health}", icon="⚠️")
                        st.caption(market_comment)
                    with col_m2:
                        if sectors:
                            sector_df = pd.DataFrame(list(sectors.items()), columns=['Sektör', 'Değer'])
                            fig = go.Figure(data=[go.Pie(labels=sector_df['Sektör'], values=sector_df['Değer'], hole=.4, textinfo='percent+label', pull=[0.05 if v == sector_df['Değer'].max() else 0 for v in sector_df['Değer']])])
                            fig.update_layout(title_text='Sektörel Dağılım', showlegend=False, height=250, margin=dict(t=50, b=0, l=0, r=0))
                            st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("##### Pozisyon Bazında Strateji Önerileri")
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df, use_container_width=True, hide_index=True, column_config={
                        "Hisse": st.column_config.TextColumn("Hisse"),
                        "Anlık Değer": st.column_config.NumberColumn("Anlık Değer", format="$%.2f"),
                        "Kâr/Zarar ($)": st.column_config.NumberColumn("Kâr/Zarar ($)", format="$%.2f"),
                        "Kâr/Zarar (%)": st.column_config.NumberColumn("Kâr/Zarar (%)", format="%.2f%%"),
                        "AI Strateji Önerisi": st.column_config.TextColumn("AI Strateji Önerisi", width="large"),
                    })
        else:
            st.info("Strateji oluşturmak için lütfen yukarıdaki bölümden portföyünüze pozisyon ekleyin.")
