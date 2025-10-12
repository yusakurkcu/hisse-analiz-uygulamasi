import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# --- UYGULAMA AYARLARI ---
st.set_page_config(layout="wide", page_title="Hisse Senedi Fırsat Motoru")

# --- VERİ VE ANALİZ FONKSİYONLARI ---

@st.cache_data(ttl=3600) # Hisse listesini 1 saat önbellekte tut
def load_all_tradable_stocks():
    """
    Robinhood'da işlem görmeye uygun tüm hisselerin listesini internetten yükler.
    Bu liste hem NASDAQ hem de NYSE gibi borsaları içerir.
    """
    # Topluluk tarafından derlenen ve güncel tutulan bir veri kaynağı kullanıyoruz.
    url = "https://raw.githubusercontent.com/datasets/nasdaq-listings/main/data/nasdaq-listed-symbols.csv"
    try:
        df = pd.read_csv(url)
        # Sütun isimlerini standart hale getirelim
        df.rename(columns={'Company Name': 'Company_Name', 'Symbol': 'Symbol'}, inplace=True)
        # Bazen aynı hisse farklı isimlerle listelenebiliyor, tekilleştirelim.
        df.drop_duplicates(subset=['Symbol'], keep='first', inplace=True)
        df.sort_values(by='Symbol', inplace=True)
        df['display_name'] = df['Symbol'] + ' - ' + df['Company_Name']
        return df
    except Exception as e:
        st.error(f"Hisse senedi listesi yüklenirken bir hata oluştu: {e}")
        return None

@st.cache_data(ttl=900) # Her bir hisse verisini 15 dakika önbellekte tut
def get_stock_data(ticker):
    """Bir hissenin son 1 yıllık verisini çeker."""
    try:
        return yf.Ticker(ticker).history(period="1y")
    except Exception:
        return pd.DataFrame()

def analyze_for_screener(data):
    """Tarayıcı için hisse senedi verilerini analiz eder."""
    if data is None or len(data) < 50: return None
    data.ta.rsi(length=14, append=True)
    data.ta.bbands(length=20, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.sma(length=20, append=True)
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
    """Tekli hisse analizi için tüm göstergeleri detaylı olarak yorumlar."""
    if data is None or len(data) < 50: return {}
    data.ta.rsi(length=14, append=True)
    data.ta.bbands(length=20, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.sma(length=200, append=True)
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

# --- ANA ARAYÜZ ---
st.title('📈 ABD Hisse Piyasası Fırsat Motoru')
st.caption('Otomatik Fırsat Tarama ve Detaylı Hisse Analizi Bir Arada')
st.warning("Bu araç yalnızca eğitim amaçlıdır ve yatırım tavsiyesi değildir. Finansal piyasalar risk içerir.", icon="⚠️")

full_stock_list = load_all_tradable_stocks()

if full_stock_list is None:
    st.error("Hisse senedi listesi yüklenemedi. Lütfen internet bağlantınızı kontrol edip sayfayı yenileyin.")
else:
    tab1, tab2 = st.tabs(["🚀 Kapsamlı Fırsat Tarayıcısı", "🔍 Tekli Hisse Analizi"])

    # --- SEKME 1: OTOMATİK TARAYICI ---
    with tab1:
        st.header("Tüm Piyasayı Fırsatlar İçin Tarayın")
        
        st.warning(
            "**LÜTFEN DİKKAT:** Bu işlem **binlerce** hisseyi analiz edecektir. Taramanın tamamlanması **5 ila 20 dakika** sürebilir. Lütfen işlem bitene kadar bu sekmeyi kapatmayın.", 
            icon="⏳"
        )
        
        user_cash = st.number_input('Strateji için ne kadar nakit ($) kullanmak istersiniz?', min_value=100, max_value=1000000, value=1000, step=100, key='screener_cash_input')
        
        if st.button('🚀 TÜM PİYASAYI ŞİMDİ TARA!', type="primary"):
            opportunities = []
            ticker_symbols = full_stock_list['Symbol'].tolist()
            total_tickers = len(ticker_symbols)
            
            progress_bar = st.progress(0, text="Tarama Başlatılıyor...")
            
            for i, ticker in enumerate(ticker_symbols):
                stock_data = get_stock_data(ticker)
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

    # --- SEKME 2: TEKLİ HİSSE ANALİZİ ---
    with tab2:
        st.header("İstediğiniz Hisseyi Derinlemesine İnceleyin")
        
        selected_display_name = st.selectbox(
            'Analiz edilecek hisseyi seçin veya yazarak arayın:',
            full_stock_list['display_name'],
            index=None,
            placeholder="Piyasadaki herhangi bir hisseyi arayın..."
        )

        if selected_display_name:
            selected_ticker = selected_display_name.split(' - ')[0]
            data = get_stock_data(selected_ticker)
            if data.empty:
                st.error("Bu hisse için veri alınamadı. Lütfen başka bir hisse seçin.")
            else:
                st.subheader(f"{selected_ticker} Detaylı Analizi")
                fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='Fiyat')])
                fig.update_layout(title=f'{selected_ticker} Fiyat Grafiği', xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Teknik Sinyal Özeti")
                signals = get_detailed_analysis(data)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### Olumlu Sinyaller (Bullish)")
                    if signals['bullish']:
                        for signal in signals['bullish']: st.success(signal, icon="🔼")
                    else:
                        st.info("Belirgin bir olumlu sinyal yok.", icon="😐")
                with col2:
                    st.markdown("##### Olumsuz/Nötr Sinyaller (Bearish)")
                    if signals['bearish']:
                        for signal in signals['bearish']: st.error(signal, icon="🔽")
                    else:
                        st.info("Belirgin bir olumsuz sinyal yok.", icon="😐")
