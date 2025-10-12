import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- UYGULAMA AYARLARI ---
st.set_page_config(layout="wide", page_title="AI Hisse Strateji Motoru")

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
    except Exception as e:
        st.error(f"Hisse senedi listesi yüklenirken bir hata oluştu: {e}")
        return None

@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()

def analyze_for_ai_screener(data):
    """
    Tarayıcı için "AI" puanlama sistemi ile analiz yapar.
    """
    if data is None or len(data) < 200: return None # 200 günlük veri yoksa analize başlama
    
    # Tüm göstergeleri hesapla
    data.ta.rsi(length=14, append=True)
    data.ta.bbands(length=20, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.sma(length=200, append=True)
    
    last = data.iloc[-1]
    score = 0
    signals = []

    # Puanlama Kriterleri
    if last['Close'] > last['SMA_200']:
        score += 1
        signals.append("Uzun Vadeli Trend Pozitif")
    if 'RSI_14' in last and last['RSI_14'] < 35:
        score += 1
        signals.append("RSI Aşırı Satım")
    if 'BBL_20_2.0' in last and last['Close'] <= last['BBL_20_2.0']:
        score += 1
        signals.append("Bollinger Alt Bandı")
    if 'MACD_12_26_9' in data.columns and len(data) > 2 and (data['MACD_12_26_9'].iloc[-1] > data['MACDs_12_26_9'].iloc[-1]) and (data['MACD_12_26_9'].iloc[-2] < data['MACDs_12_26_9'].iloc[-2]):
        score += 1
        signals.append("Yeni MACD Al Sinyali")

    # Sadece puanı 2 veya daha yüksek olan güçlü sinyalleri raporla
    if score >= 2:
        target_price = last.get('BBM_20_2.0', 0)
        current_price = last['Close']
        if target_price > current_price:
            return {
                "signals": ", ".join(signals),
                "score": f"{score}/4",
                "current_price": current_price,
                "target_price": target_price,
                "potential_profit_pct": ((target_price - current_price) / current_price) * 100
            }
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
    # Bu fonksiyon tekli analiz için aynı kalıyor
    if data is None or len(data) < 50: return {}
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=50, append=True); data.ta.sma(length=200, append=True)
    last = data.iloc[-1]
    signals = {'bullish': [], 'bearish': []}
    # Sinyal yorumları... (önceki versiyon ile aynı)
    if 'RSI_14' in last:
        if last['RSI_14'] < 30: signals['bullish'].append(f"**RSI Aşırı Satım:** Değer ({last['RSI_14']:.2f}) 30'un altında.")
        elif last['RSI_14'] > 70: signals['bearish'].append(f"**RSI Aşırı Alım:** Değer ({last['RSI_14']:.2f}) 70'in üzerinde.")
    if 'BBL_20_2.0' in last and 'BBU_20_2.0' in last:
        if last['Close'] <= last['BBL_20_2.0']: signals['bullish'].append(f"**Bollinger Alt Bandı:** Fiyat ({last['Close']:.2f}) alt banda temas ediyor.")
        elif last['Close'] >= last['BBU_20_2.0']: signals['bearish'].append(f"**Bollinger Üst Bandı:** Fiyat ({last['Close']:.2f}) üst banda temas ediyor.")
    if 'MACD_12_26_9' in last and 'MACDs_12_26_9' in last:
        if last['MACD_12_26_9'] > last['MACDs_12_26_9']: signals['bullish'].append("**MACD Pozitif:** MACD çizgisi sinyal çizgisinin üzerinde.")
        else: signals['bearish'].append("**MACD Negatif:** MACD çizgisi sinyal çizgisinin altında.")
    if 'SMA_50' in last and 'SMA_200' in last:
        if last['Close'] > last['SMA_50'] and last['Close'] > last['SMA_200']:
            signals['bullish'].append("**Güçlü Yükseliş Trendi:** Fiyat 50 ve 200 günlük ortalamaların üzerinde.")
        elif last['Close'] < last['SMA_50'] and last['Close'] < last['SMA_200']:
            signals['bearish'].append("**Güçlü Düşüş Trendi:** Fiyat 50 ve 200 günlük ortalamaların altında.")
    return signals


# --- ANA ARAYÜZ ---
st.title('🤖 AI Hisse Senedi Strateji Motoru')
st.caption('AI Puanlaması, Otomatik Fırsat Tarama ve Derinlemesine Analiz')
st.warning("Bu araç yalnızca eğitim amaçlıdır ve yatırım tavsiyesi değildir. Finansal piyasalar risk içerir.", icon="⚠️")

full_stock_list = load_all_tradable_stocks()

if full_stock_list is None:
    st.error("Hisse senedi listesi yüklenemedi. Lütfen internet bağlantınızı kontrol edip sayfayı yenileyin.")
else:
    tab1, tab2 = st.tabs(["🚀 AI Fırsat Tarayıcısı", "🔍 Detaylı Hisse Analizi"])

    # --- SEKME 1: AI FIRSAT TARAYICISI ---
    with tab1:
        st.header("Yüksek Potansiyelli Hisse ve Opsiyon Fırsatlarını Keşfedin")
        st.warning(
            """
            **ÇOK ÖNEMLİ:** Bu tarayıcı, binlerce hisseyi ve potansiyel opsiyonlarını **derinlemesine** analiz eder. 
            Tarama süresi **15 ila 40 dakika** veya daha uzun olabilir. 
            Lütfen sabırlı olun ve işlem bitene kadar sekmeyi kapatmayın.
            """, 
            icon="⏳"
        )
        
        if st.button('🧠 TÜM PİYASAYI DERİNLEMESİNE TARA!', type="primary"):
            opportunities = []
            ticker_symbols = full_stock_list['Symbol'].tolist()
            total_tickers = len(ticker_symbols)
            
            progress_bar = st.progress(0, text="AI Motoru Başlatılıyor...")
            
            for i, ticker in enumerate(ticker_symbols):
                stock_data = get_stock_data(ticker)
                opportunity = analyze_for_ai_screener(stock_data)
                
                if opportunity:
                    opportunity['ticker'] = ticker
                    
                    # Opsiyon Fırsatını Ara
                    try:
                        ticker_obj = yf.Ticker(ticker)
                        if ticker_obj.options:
                            exp_date = ticker_obj.options[0]
                            options_chain = ticker_obj.option_chain(exp_date)
                            recommended_call = recommend_option(options_chain.calls)
                            if recommended_call is not None:
                                opportunity['option_strike'] = recommended_call['strike']
                                opportunity['option_price'] = recommended_call['lastPrice']
                                opportunity['option_expiry'] = exp_date
                    except Exception:
                        pass # Opsiyon bulunamazsa veya hata olursa sessizce geç
                    
                    opportunities.append(opportunity)
                
                progress_text = f"Analiz Ediliyor: {ticker} ({i+1}/{total_tickers}) - Yüksek Puanlı Fırsatlar: {len(opportunities)}"
                progress_bar.progress((i + 1) / total_tickers, text=progress_text)
            
            progress_bar.empty()

            if not opportunities:
                st.success("✅ Tarama Tamamlandı! Bugün AI kriterlerine uyan yüksek puanlı bir fırsat tespit edilmedi.", icon="👍")
            else:
                st.success(f"✅ Tarama Tamamlandı! {len(opportunities)} adet yüksek puanlı fırsat bulundu.", icon="🎯")
                df = pd.DataFrame(opportunities)
                
                # Opsiyon bilgilerini formatla
                df['Önerilen Opsiyon'] = df.apply(lambda row: f"${row['option_strike']} CALL ({datetime.strptime(row['option_expiry'], '%Y-%m-%d').strftime('%d %b')})" if pd.notna(row.get('option_strike')) else "N/A", axis=1)
                df['Opsiyon Fiyatı'] = df['option_price'].map('${:,.2f}'.format).fillna("N/A")

                # Sonuçları formatla
                df['current_price'] = df['current_price'].map('${:,.2f}'.format)
                df['target_price'] = df['target_price'].map('${:,.2f}'.format)
                df['potential_profit_pct'] = df['potential_profit_pct'].map('{:.2f}%'.format)
                
                st.subheader("AI Tarafından Belirlenen Yüksek Potansiyelli Fırsatlar")
                display_df = df[['ticker', 'signals', 'score', 'current_price', 'target_price', 'potential_profit_pct', 'Önerilen Opsiyon', 'Opsiyon Fiyatı']] \
                    .rename(columns={'ticker': 'Hisse', 'signals': 'Onaylanan Sinyaller', 'score': 'Sinyal Gücü', 'current_price': 'Mevcut Fiyat', 'target_price': 'Hedef Fiyat', 'potential_profit_pct': 'Potansiyel Kâr (%)'}) \
                    .set_index('Hisse')
                
                st.dataframe(display_df, use_container_width=True)

    # --- SEKME 2: DETAYLI HİSSE ANALİZİ (Değişiklik yok) ---
    with tab2:
        # Bu sekmenin kodu önceki versiyon ile aynı, tamamen işlevsel.
        st.header("İstediğiniz Hisseyi Derinlemesine İnceleyin")
        selected_display_name = st.selectbox('Analiz edilecek hisseyi seçin veya yazarak arayın:', full_stock_list['display_name'], index=None, placeholder="Piyasadaki herhangi bir hisseyi arayın...")
        if selected_display_name:
            selected_ticker = selected_display_name.split(' - ')[0]
            ticker_obj = yf.Ticker(selected_ticker)
            data = get_stock_data(selected_ticker, period="1y")
            if data.empty:
                st.error("Bu hisse için veri alınamadı. Lütfen başka bir hisse seçin.")
            else:
                info = ticker_obj.info
                st.subheader(f"{info.get('longName', selected_ticker)} ({selected_ticker}) Strateji Paneli")
                st.markdown("#### 📈 Stratejik Fiyat Seviyeleri")
                current_price = data['Close'].iloc[-1]
                analyst_target = info.get('targetMeanPrice', None)
                support_level = data['Low'].tail(90).min()
                resistance_level = data['High'].tail(90).max()
                daily_change = data['Close'].iloc[-1] - data['Close'].iloc[-2] if len(data) >= 2 else 0.0
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Mevcut Fiyat", f"${current_price:,.2f}", f"{daily_change:.2f}$")
                col2.metric("Analist Hedefi", f"${analyst_target:,.2f}" if analyst_target else "N/A", help="Analistlerin ortalama 12 aylık fiyat hedefi.")
                col3.metric("Destek Seviyesi", f"${support_level:,.2f}", help="Son 3 ayın en düşük fiyatı.")
                col4.metric("Direnç Seviyesi", f"${resistance_level:,.2f}", help="Son 3 ayın en yüksek fiyatı.")
                st.divider()
                fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Fiyat')])
                fig.update_layout(title=f'{selected_ticker} Fiyat Grafiği', xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                st.divider()
                st.markdown("#### 📊 Teknik Sinyal Özeti")
                signals = get_detailed_analysis(data)
                col1_sig, col2_sig = st.columns(2)
                with col1_sig:
                    st.markdown("##### Olumlu Sinyaller (Bullish)")
                    if signals['bullish']:
                        for signal in signals['bullish']: st.success(signal, icon="🔼")
                    else:
                        st.info("Belirgin bir olumlu sinyal yok.", icon="😐")
                with col2_sig:
                    st.markdown("##### Olumsuz/Nötr Sinyaller (Bearish)")
                    if signals['bearish']:
                        for signal in signals['bearish']: st.error(signal, icon="🔽")
                    else:
                        st.info("Belirgin bir olumsuz sinyal yok.", icon="😐")
                st.divider()
                st.markdown("#### 🧠 Akıllı Opsiyon Stratejisi ve Verileri")
                available_dates = ticker_obj.options
                if not available_dates:
                    st.warning("Bu hisse senedi için listelenmiş herhangi bir opsiyon vadesi bulunamadı.", icon="⚠️")
                else:
                    try:
                        exp_date = available_dates[0]
                        options = ticker_obj.option_chain(exp_date)
                        sentiment = 'bullish' if len(signals['bullish']) > len(signals['bearish']) else 'bearish'
                        recommended_option = None
                        if sentiment == 'bullish':
                            recommended_option = recommend_option(options.calls)
                            option_type = "ALIM (CALL)"
                        else:
                            recommended_option = recommend_option(options.puts)
                            option_type = "SATIM (PUT)"
                        if recommended_option is not None:
                            st.success(f"**Teknik Analiz Önerisi:** Hissenin genel teknik görünümü **{sentiment.capitalize()}** olduğu için, bir **{option_type}** opsiyonu stratejisi daha uygun olabilir.", icon="💡")
                            st.markdown(f"##### 🎯 Önerilen Kontrat: **{selected_ticker} {datetime.strptime(exp_date, '%Y-%m-%d').strftime('%d %b %Y')} ${recommended_option['strike']} {option_type}**")
                            col1_rec, col2_rec, col3_rec, col4_rec = st.columns(4)
                            col1_rec.metric("Opsiyon Fiyatı (Prim)", f"${recommended_option['lastPrice']:.2f}")
                            col2_rec.metric("Delta", f"{recommended_option['delta']:.3f}", help="Hisse 1$ arttığında opsiyonun ne kadar değer kazanacağını gösterir.")
                            col3_rec.metric("Theta", f"{recommended_option['theta']:.3f}", help="Opsiyonun her gün ne kadar zaman değeri kaybedeceğini gösterir.")
                            col4_rec.metric("Hacim / Açık Poz.", f"{int(recommended_option['volume'])} / {int(recommended_option['openInterest'])}", help="Kontratın likiditesini gösterir.")
                            st.caption(f"**Neden Bu Kontrat?** İdeal **Delta** aralığında, zaman kaybı (**Theta**) görece düşük ve yüksek likiditeye sahip olduğu için seçilmiştir.")
                        else:
                            st.info("Mevcut teknik görünüme ve likiditeye uygun, net bir opsiyon stratejisi bulunamadı.", icon="🤔")
                        st.markdown("---")
                        st.markdown(f"##### ⛓️ Tüm Opsiyon Zinciri ({datetime.strptime(exp_date, '%Y-%m-%d').strftime('%d %B %Y')} Vade)")
                        atm_strike = min(options.calls['strike'], key=lambda x:abs(x-current_price))
                        filtered_calls = options.calls[(options.calls['strike'] >= atm_strike - 10) & (options.calls['strike'] <= atm_strike + 10)]
                        filtered_puts = options.puts[(options.puts['strike'] >= atm_strike - 10) & (options.puts['strike'] <= atm_strike + 10)]
                        display_cols = {'strike':'Kullanım F.', 'lastPrice':'Son Fiyat', 'delta':'Delta', 'theta':'Theta', 'volume':'Hacim', 'openInterest':'Açık Poz.'}
                        col1_opt, col2_opt = st.columns(2)
                        with col1_opt:
                            st.markdown("###### ALIM (CALL) Opsiyonları")
                            st.dataframe(filtered_calls[list(display_cols.keys())].rename(columns=display_cols).set_index('Kullanım F.'), height=300)
                        with col2_opt:
                            st.markdown("###### SATIM (PUT) Opsiyonları")
                            st.dataframe(filtered_puts[list(display_cols.keys())].rename(columns=display_cols).set_index('Kullanım F.'), height=300)
                    except Exception as e:
                        st.warning(f"Opsiyon verileri çekilirken bir sorun oluştu: {e}", icon="⚠️")
