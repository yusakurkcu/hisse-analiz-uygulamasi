import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- UYGULAMA AYARLARI ---
st.set_page_config(layout="wide", page_title="Hisse Senedi Strateji Motoru")

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

def analyze_for_screener(data):
    if data is None or len(data) < 50: return None
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=20, append=True)
    last_row = data.iloc[-1]
    opportunity_type = None
    if ('RSI_14' in last_row and last_row['RSI_14'] < 35) or ('BBL_20_2.0' in last_row and last_row['Close'] <= last_row['BBL_20_2.0']):
        opportunity_type = "Dipten Alım Sinyali"
    elif 'SMA_20' in data.columns and len(data) > 2 and (data['Close'].iloc[-1] > data['SMA_20'].iloc[-1]) and (data['Close'].iloc[-2] < data['SMA_20'].iloc[-2]):
        opportunity_type = "Momentum Başlangıcı"
    if opportunity_type:
        target_price = last_row.get('BBM_20_2.0', 0)
        current_price = last_row['Close']
        if target_price > current_price:
            return {"type": opportunity_type, "current_price": current_price, "target_price": target_price, "potential_profit_pct": ((target_price - current_price) / current_price) * 100}
    return None

def get_detailed_analysis(data):
    if data is None or len(data) < 50: return {}
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=50, append=True); data.ta.sma(length=200, append=True)
    last = data.iloc[-1]
    signals = {'bullish': [], 'bearish': []}
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

def recommend_option(options_df, sentiment):
    """Verilen opsiyon listesini ve teknik sentimenti analiz ederek en uygun kontratı önerir."""
    if options_df is None or options_df.empty:
        return None
    
    # Alıcı için temel kriterler
    # Delta: 0.30 - 0.60 arası (Denge)
    # Likidite: Yüksek Hacim ve Açık Pozisyon
    # Theta: Mümkün olduğunca düşük (negatif olduğu için mutlak değeri küçük olan)
    
    # Gerekli Greek sütunlarının varlığını kontrol et
    required_cols = ['delta', 'theta', 'volume', 'openInterest', 'strike']
    if not all(col in options_df.columns for col in required_cols):
        return None

    # Kriterlere göre filtrele
    df = options_df[
        (options_df['delta'].abs() >= 0.30) &
        (options_df['delta'].abs() <= 0.60) &
        (options_df['volume'] >= 10) &
        (options_df['openInterest'] >= 50)
    ].copy()

    if df.empty:
        return None

    # En iyi adayı seç: En düşük zaman kaybı (theta) ve en yüksek açık pozisyona (likidite) sahip olanı bul
    df['score'] = df['openInterest'] + df['theta'].abs() * -100 # Theta'yı cezalandır
    best_option = df.loc[df['score'].idxmax()]
    
    return best_option

# --- ANA ARAYÜZ ---
st.title('📈 ABD Hisse Piyasası Strateji Motoru')
st.caption('Otomatik Fırsat Tarama, Derinlemesine Analiz ve Akıllı Opsiyon Önerileri')
st.warning("Bu araç yalnızca eğitim amaçlıdır ve yatırım tavsiyesi değildir. Finansal piyasalar risk içerir.", icon="⚠️")

full_stock_list = load_all_tradable_stocks()

if full_stock_list is None:
    st.error("Hisse senedi listesi yüklenemedi. Lütfen internet bağlantınızı kontrol edip sayfayı yenileyin.")
else:
    tab1, tab2 = st.tabs(["🚀 Kapsamlı Fırsat Tarayıcısı", "🔍 Detaylı Hisse Analizi"])

    # SEKME 1: OTOMATİK TARAYICI (Değişiklik yok)
    with tab1:
        st.header("Tüm Piyasayı Fırsatlar İçin Tarayın")
        st.warning("**LÜTFEN DİKKAT:** Bu işlem **binlerce** hisseyi analiz edecektir. Taramanın tamamlanması **5 ila 20 dakika** sürebilir.", icon="⏳")
        user_cash = st.number_input('Strateji için ne kadar nakit ($) kullanmak istersiniz?', min_value=100, max_value=1000000, value=1000, step=100, key='screener_cash_input')
        if st.button('🚀 TÜM PİYASAYI ŞİMDİ TARA!', type="primary"):
            # Tarama kodları burada... (değişiklik yok)
            opportunities = []
            ticker_symbols = full_stock_list['Symbol'].tolist()
            total_tickers = len(ticker_symbols)
            progress_bar = st.progress(0, text="Tarama Başlatılıyor...")
            for i, ticker in enumerate(ticker_symbols):
                stock_data = get_stock_data(ticker, period="1y")
                opportunity = analyze_for_screener(stock_data)
                if opportunity:
                    opportunity['ticker'] = ticker
                    opportunities.append(opportunity)
                progress_text = f"Taranıyor: {ticker} ({i+1}/{total_tickers}) - Fırsatlar Bulundu: {len(opportunities)}"
                progress_bar.progress((i + 1) / total_tickers, text=progress_text)
            progress_bar.empty()
            if not opportunities:
                st.success("✅ Tarama Tamamlandı! Şu anda belirgin bir fırsat tespit edilmedi.", icon="👍")
            else:
                st.success(f"✅ Tarama Tamamlandı! {len(opportunities)} adet potansiyel fırsat bulundu.", icon="🎯")
                df = pd.DataFrame(opportunities)
                df['buyable_shares'] = (user_cash // df['current_price']).astype(int)
                df['investment_cost'] = df['buyable_shares'] * df['current_price']
                df['potential_profit_usd'] = (df['target_price'] - df['current_price']) * df['buyable_shares']
                df_filtered = df[df['buyable_shares'] > 0].copy()
                df_filtered['current_price'] = df_filtered['current_price'].map('${:,.2f}'.format)
                df_filtered['target_price'] = df_filtered['target_price'].map('${:,.2f}'.format)
                df_filtered['potential_profit_pct'] = df_filtered['potential_profit_pct'].map('{:.2f}%'.format)
                df_filtered['investment_cost'] = df_filtered['investment_cost'].map('${:,.2f}'.format)
                df_filtered['potential_profit_usd'] = df_filtered['potential_profit_usd'].map('${:,.2f}'.format)
                st.subheader(f"Sizin için Oluşturulan Strateji Önerileri ({user_cash:,.0f} $ Nakit ile)")
                display_df = df_filtered[['ticker', 'type', 'current_price', 'target_price', 'potential_profit_pct', 'buyable_shares', 'investment_cost', 'potential_profit_usd']].rename(columns={'ticker': 'Hisse', 'type': 'Fırsat Tipi', 'current_price': 'Mevcut Fiyat', 'target_price': 'Hedef Fiyat', 'potential_profit_pct': 'Potansiyel Kâr (%)', 'buyable_shares': 'Alınabilir Adet', 'investment_cost': 'Yatırım Maliyeti', 'potential_profit_usd': 'Potansiyel Kâr ($)'}).set_index('Hisse')
                st.dataframe(display_df, use_container_width=True)


    # SEKME 2: DETAYLI HİSSE ANALİZİ (GÜNCELLENMİŞ)
    with tab2:
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

                # BÖLÜM 1: STRATEJİK FİYAT SEVİYELERİ (Değişiklik yok)
                st.markdown("#### 📈 Stratejik Fiyat Seviyeleri")
                current_price = data['Close'].iloc[-1]
                analyst_target = info.get('targetMeanPrice', None)
                support_level = data['Low'].tail(90).min()
                resistance_level = data['High'].tail(90).max()
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Mevcut Fiyat", f"${current_price:,.2f}", f"{data['Close'].iloc[-1] - data['Close'].iloc[-2]:.2f}$")
                col2.metric("Analist Hedefi", f"${analyst_target:,.2f}" if analyst_target else "N/A", help="Analistlerin ortalama 12 aylık fiyat hedefi.")
                col3.metric("Destek Seviyesi", f"${support_level:,.2f}", help="Son 3 ayın en düşük fiyatı.")
                col4.metric("Direnç Seviyesi", f"${resistance_level:,.2f}", help="Son 3 ayın en yüksek fiyatı.")
                st.divider()

                # BÖLÜM 2: FİYAT GRAFİĞİ (Değişiklik yok)
                fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Fiyat')])
                fig.update_layout(title=f'{selected_ticker} Fiyat Grafiği', xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                st.divider()

                # BÖLÜM 3: TEKNİK SİNYAL ÖZETİ (Değişiklik yok)
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

                # BÖLÜM 4: AKILLI OPSİYON ÖNERİSİ VE ZİNCİRİ
                st.markdown("#### 🧠 Akıllı Opsiyon Stratejisi ve Verileri")
                try:
                    exp_date = ticker_obj.options[0]
                    options = ticker_obj.option_chain(exp_date)
                    sentiment = 'bullish' if len(signals['bullish']) > len(signals['bearish']) else 'bearish'
                    
                    recommended_option = None
                    if sentiment == 'bullish':
                        recommended_option = recommend_option(options.calls, sentiment)
                        option_type = "ALIM (CALL)"
                    else: # bearish or neutral
                        recommended_option = recommend_option(options.puts, sentiment)
                        option_type = "SATIM (PUT)"

                    if recommended_option is not None:
                        st.success(f"**Teknik Analiz Önerisi:** Hissenin genel teknik görünümü **{sentiment.capitalize()}** olduğu için, bir **{option_type}** opsiyonu stratejisi daha uygun olabilir.", icon="💡")
                        
                        st.markdown(f"##### 🎯 Önerilen Kontrat: **{selected_ticker} {datetime.strptime(exp_date, '%Y-%m-%d').strftime('%d %b %Y')} ${recommended_option['strike']} {option_type}**")
                        
                        col1_rec, col2_rec, col3_rec, col4_rec = st.columns(4)
                        col1_rec.metric("Opsiyon Fiyatı (Prim)", f"${recommended_option['lastPrice']:.2f}")
                        col2_rec.metric("Delta", f"{recommended_option['delta']:.3f}", help="Hisse 1$ arttığında opsiyonun ne kadar değer kazanacağını gösterir.")
                        col3_rec.metric("Theta", f"{recommended_option['theta']:.3f}", help="Opsiyonun her gün ne kadar zaman değeri kaybedeceğini gösterir (düşük olması iyidir).")
                        col4_rec.metric("Hacim / Açık Poz.", f"{int(recommended_option['volume'])} / {int(recommended_option['openInterest'])}", help="Kontratın ne kadar popüler ve likit olduğunu gösterir.")
                        
                        st.caption(f"**Neden Bu Kontrat?** Bu opsiyon, alıcılar için ideal kabul edilen **Delta** aralığında, zaman kaybı (**Theta**) görece düşük ve yüksek likiditeye (**Hacim/Açık Poz.**) sahip olduğu için seçilmiştir.")
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
                    st.warning("Bu hisse senedi için opsiyon verisi bulunamadı veya alınamadı.", icon="⚠️")
