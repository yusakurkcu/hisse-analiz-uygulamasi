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
    except Exception: return None

@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    try: return yf.Ticker(ticker).history(period=period)
    except Exception: return pd.DataFrame()

def analyze_for_ai_screener(data):
    if data is None or len(data) < 200: return None
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=200, append=True)
    last = data.iloc[-1]
    score = 0; signals = []
    if last['Close'] > last['SMA_200']: score += 1; signals.append("Uzun Vadeli Trend Pozitif")
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
    if data is None or len(data) < 50: return {}, None
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=50, append=True); data.ta.sma(length=200, append=True)
    last = data.iloc[-1]
    signals = {'bullish': [], 'bearish': []}
    if 'RSI_14' in last:
        if last['RSI_14'] < 30: signals['bullish'].append("RSI Aşırı Satım")
        elif last['RSI_14'] > 70: signals['bearish'].append("RSI Aşırı Alım")
    if 'BBL_20_2.0' in last and last['Close'] <= last['BBL_20_2.0']: signals['bullish'].append("Bollinger Alt Bandı")
    elif 'BBU_20_2.0' in last and last['Close'] >= last['BBU_20_2.0']: signals['bearish'].append("Bollinger Üst Bandı")
    if 'MACD_12_26_9' in last and last['MACD_12_26_9'] > last['MACDs_12_26_9']: signals['bullish'].append("MACD Pozitif")
    else: signals['bearish'].append("MACD Negatif")
    if 'SMA_50' in last and 'SMA_200' in last and last['Close'] > last['SMA_50'] and last['Close'] > last['SMA_200']:
        signals['bullish'].append("Güçlü Yükseliş Trendi")
    elif 'SMA_50' in last and 'SMA_200' in last and last['Close'] < last['SMA_50'] and last['Close'] < last['SMA_200']:
        signals['bearish'].append("Güçlü Düşüş Trendi")
    return signals, last

@st.cache_data(ttl=1800)
def get_market_health():
    try:
        spy_data = yf.Ticker("SPY").history(period="3mo")
        spy_data.ta.sma(length=50, append=True)
        last_price = spy_data['Close'].iloc[-1]
        sma_50 = spy_data['SMA_50'].iloc[-1]
        if last_price > sma_50:
            return "Boğa Piyasası (Olumlu)", "S&P 500 (SPY) 50 günlük hareketli ortalamasının üzerinde. Genel piyasa trendi kısa ve orta vadede olumlu.", "success"
        else:
            return "Dikkatli Olunmalı (Nötr/Olumsuz)", "S&P 500 (SPY) 50 günlük hareketli ortalamasının altında. Piyasa genelinde zayıflık mevcut.", "warning"
    except Exception:
        return "Belirlenemedi", "Piyasa endeksi verisi alınamadı.", "error"

def analyze_portfolio_position(position, market_health_status):
    try:
        data = get_stock_data(position['Hisse'])
        if data.empty: return "Veri Alınamadı"
        signals, last = get_detailed_analysis(data)
        current_price = last['Close']
        profit_pct = ((current_price - position['Maliyet']) / position['Maliyet']) * 100 if position['Maliyet'] > 0 else 0
        is_bullish_trend = "Güçlü Yükseliş Trendi" in signals['bullish']
        is_bearish_trend = "Güçlü Düşüş Trendi" in signals['bearish']
        
        if profit_pct > 25 and "RSI Aşırı Alım" in signals['bearish']:
            return f"📈 **Kâr Almayı Değerlendir:** %{profit_pct:.2f} kârda ve hisse teknik olarak 'pahalı' görünüyor. Kârın bir kısmını realize etmek düşünülebilir."
        elif profit_pct < -15 and is_bearish_trend:
            return f"📉 **Zararı Durdurmayı Düşün:** %{profit_pct:.2f} zararda ve hisse ana trendini aşağı çevirmiş. Daha fazla kaybı önlemek için pozisyonu gözden geçirin."
        elif is_bullish_trend and market_health_status == "Boğa Piyasası (Olumlu)":
            return f"💪 **Pozisyonu Koru ve Büyüt:** %{profit_pct:.2f} kâr/zararda. Hem hissenin hem de genel piyasanın trendi olumlu. Geri çekilmeler alım fırsatı olabilir."
        elif is_bullish_trend and "RSI Aşırı Satım" in signals['bullish']:
            return f"🔍 **Pozisyona Ekleme Fırsatı:** %{profit_pct:.2f} kâr/zararda. Ana trendi yukarı olan hissede kısa vadeli bir geri çekilme yaşanıyor. Ortalama düşürmek için iyi bir zaman olabilir."
        else:
            return f"🤔 **Tut/Gözlemle:** %{profit_pct:.2f} kâr/zararda. Belirgin bir stratejik sinyal yok, pozisyonu izlemeye devam edin."
    except Exception:
        return "Analiz Başarısız"

# --- ANA ARAYÜZ ---
st.title('🤖 AI Hisse Senedi Strateji Motoru')
st.caption('Portföy Optimizasyonu, AI Fırsat Tarama ve Derinlemesine Analiz')
st.error(
    "**YASAL UYARI: BU BİR FİNANSAL DANIŞMANLIK ARACI DEĞİLDİR!**\n\n"
    "Bu uygulama tarafından üretilen tüm veriler, analizler ve öneriler tamamen **eğitim ve simülasyon amaçlıdır.** "
    "Yatırım kararlarınızı profesyonel bir danışmana başvurmadan almayınız. Tüm işlemlerin riski ve sorumluluğu tamamen size aittir.", 
    icon="🚨"
)
full_stock_list = load_all_tradable_stocks()
if full_stock_list is None:
    st.error("Hisse senedi listesi yüklenemedi. Lütfen internet bağlantınızı kontrol edip sayfayı yenileyin.")
else:
    tab1, tab2, tab3 = st.tabs(["🚀 AI Fırsat Tarayıcısı", "🔍 Detaylı Hisse Analizi", "🧠 Portföy Stratejisti"])

    # --- SEKME 1 & 2 (Değişiklik yok) ---
    with tab1:
        st.header("Yüksek Potansiyelli Hisse ve Opsiyon Fırsatlarını Keşfedin")
        st.warning("**ÇOK ÖNEMLİ:** Tarama süresi **15 ila 40 dakika** veya daha uzun olabilir.", icon="⏳")
        if st.button('🧠 TÜM PİYASAYI DERİNLEMESİNE TARA!', type="primary"):
            pass # Önceki versiyondaki kod burada olacak
    with tab2:
        st.header("İstediğiniz Hisseyi Derinlemesine İnceleyin")
        selected_display_name = st.selectbox('...', full_stock_list['display_name'], index=None, placeholder="...", key="single_stock_selector")
        if selected_display_name:
            pass # Önceki versiyondaki kod burada olacak

    # --- SEKME 3: PORTFÖY STRATEJİSTİ (YENİLENMİŞ) ---
    with tab3:
        st.header("Kişisel Portföyünüz İçin AI Destekli Stratejiler")

        # *** DÜZELTME BURADA: Portföyü her zaman DataFrame olarak başlat ***
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = pd.DataFrame(columns=["Hisse", "Adet", "Maliyet"])

        with st.expander(" Portföyünüze Yeni Pozisyon Ekleyin"):
            col1, col2, col3, col4 = st.columns([2,1,1,1])
            with col1:
                ticker_to_add = st.text_input("Hisse Sembolü", "").upper()
            with col2:
                quantity_to_add = st.number_input("Adet", min_value=0.01, step=0.01, format="%.2f")
            with col3:
                cost_to_add = st.number_input("Ortalama Maliyet ($)", min_value=0.01, step=0.01, format="%.2f")
            with col4:
                st.write("")
                if st.button("Ekle", use_container_width=True):
                    if ticker_to_add and quantity_to_add > 0:
                        new_pos = pd.DataFrame([{"Hisse": ticker_to_add, "Adet": quantity_to_add, "Maliyet": cost_to_add}])
                        st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_pos], ignore_index=True)
                        st.success(f"{ticker_to_add} portföyünüze eklendi!")
                    else:
                        st.warning("Lütfen tüm alanları doldurun.")
        
        st.divider()

        if not st.session_state.portfolio.empty:
            st.markdown("#### Mevcut Portföy Durumunuz ve Stratejiniz")
            
            with st.spinner("AI stratejistiniz portföyünüzü ve piyasayı analiz ediyor..."):
                results = []
                sectors = {}
                total_value = 0
                
                market_health, market_comment, market_status_type = get_market_health()

                for index, position in st.session_state.portfolio.iterrows():
                    try:
                        ticker_info = yf.Ticker(position['Hisse']).info
                        current_price = ticker_info.get('currentPrice', yf.Ticker(position['Hisse']).history(period="1d")['Close'].iloc[-1])
                        sector = ticker_info.get('sector', 'Diğer')
                        value = position['Adet'] * current_price
                        total_value += value
                        if sector in sectors: sectors[sector] += value
                        else: sectors[sector] = value
                        cost = position['Adet'] * position['Maliyet']
                        profit_loss = value - cost
                        profit_loss_pct = (profit_loss / cost) * 100 if cost > 0 else 0
                        strategy = analyze_portfolio_position(position, market_health)
                        results.append({"Hisse": position['Hisse'], "Anlık Değer": value, "Kâr/Zarar ($)": profit_loss, "Kâr/Zarar (%)": profit_loss_pct, "AI Strateji Önerisi": strategy})
                    except Exception:
                        results.append({"Hisse": position['Hisse'], "Anlık Değer": 0, "Kâr/Zarar ($)": 0, "Kâr/Zarar (%)": 0, "AI Strateji Önerisi": "Hisse verisi alınamadı."})

                st.markdown("##### Portföy Genel Bakış")
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("Toplam Portföy Değeri", f"${total_value:,.2f}")
                    if market_status_type == "success":
                        st.success(f"**Piyasa Sağlığı:** {market_health}", icon="📈")
                    else:
                        st.warning(f"**Piyasa Sağlığı:** {market_health}", icon="⚠️")
                    st.caption(market_comment)
                with col_m2:
                    if sectors:
                        sector_df = pd.DataFrame(list(sectors.items()), columns=['Sektör', 'Değer'])
                        fig = go.Figure(data=[go.Pie(labels=sector_df['Sektör'], values=sector_df['Değer'], hole=.3, textinfo='percent+label')])
                        fig.update_layout(title_text='Sektörel Dağılım', showlegend=False, height=250, margin=dict(t=50, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("##### Pozisyon Bazında Strateji Önerileri")
                results_df = pd.DataFrame(results)
                results_df['Anlık Değer'] = results_df['Anlık Değer'].map('${:,.2f}'.format)
                results_df['Kâr/Zarar ($)'] = results_df['Kâr/Zarar ($)'].map('${:,.2f}'.format)
                results_df['Kâr/Zarar (%)'] = results_df['Kâr/Zarar (%)'].map('{:.2f}%'.format)
                st.dataframe(results_df.set_index("Hisse"), use_container_width=True)
        else:
            st.info("Strateji oluşturmak için lütfen yukarıdaki bölümden portföyünüze pozisyon ekleyin.")
