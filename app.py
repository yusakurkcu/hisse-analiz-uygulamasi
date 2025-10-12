import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
from newsapi import NewsApiClient
from textblob import TextBlob

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
    # ATR HESAPLAMASI EKLENDİ
    data.ta.rsi(length=14, append=True); data.ta.bbands(length=20, append=True); data.ta.macd(fast=12, slow=26, signal=9, append=True); data.ta.sma(length=50, append=True); data.ta.sma(length=200, append=True); data.ta.atr(length=14, append=True)
    last = data.iloc[-1]
    signals = {'bullish': [], 'bearish': []}
    # ... (sinyal mantığı aynı)
    if 'RSI_14' in last and last['RSI_14'] < 30: signals['bullish'].append("RSI Aşırı Satım")
    elif 'RSI_14' in last and last['RSI_14'] > 70: signals['bearish'].append("RSI Aşırı Alım")
    # ... (diğer sinyaller)
    return signals, last

@st.cache_data(ttl=1800)
def get_market_health():
    # ... (aynı)
    pass

def analyze_portfolio_position(position, market_health_status):
    # ... (aynı)
    pass

@st.cache_data(ttl=3600)
def get_news_for_stock(ticker):
    # ... (aynı)
    pass

# --- ANA ARAYÜZ ---
st.title('🤖 AI Hisse Senedi Strateji Motoru')
# ... (Yasal Uyarı vb. aynı)
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

    # --- SEKME 1 ---
    with tab1:
        # ... (Önceki versiyon ile aynı, değişiklik yok)
        pass

    # --- SEKME 2 (YENİ "RİSK KALKANI" ÖZELLİĞİ İLE GÜNCELLENDİ) ---
    with tab2:
        st.header("İstediğiniz Hisseyi Derinlemesine İnceleyin")
        selected_display_name = st.selectbox('Analiz edilecek hisseyi seçin veya yazarak arayın:', full_stock_list['display_name'], index=None, placeholder="Piyasadaki herhangi bir hisseyi arayın...", key="single_stock_selector")
        
        if selected_display_name:
            selected_ticker = selected_display_name.split(' - ')[0]
            ticker_obj = yf.Ticker(selected_ticker)
            data = get_stock_data(selected_ticker)
            
            if data.empty:
                st.error("Bu hisse için veri alınamadı.")
            else:
                signals, last = get_detailed_analysis(data)
                info = ticker_obj.info
                st.subheader(f"{info.get('longName', selected_ticker)} ({selected_ticker})")
                st.caption(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')} | {info.get('country', 'N/A')}")
                st.divider()

                # BÖLÜM 1: STRATEJİK SEVİYELER
                st.markdown("#### 🎯 Stratejik Seviyeler ve Ticaret Planı")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### Statik Seviyeler")
                    current_price = data['Close'].iloc[-1]
                    support_level = data['Low'].tail(90).min()
                    resistance_level = data['High'].tail(90).max()
                    st.metric("Mevcut Fiyat", f"${current_price:,.2f}")
                    st.metric("Destek (Son 3 Ay)", f"${support_level:,.2f}")
                    st.metric("Direnç (Son 3 Ay)", f"${resistance_level:,.2f}")
                
                with col2:
                    st.markdown("##### 🛡️ Risk Kalkanı (Volatiliteye Dayalı Plan)")
                    if 'ATRr_14' in last and pd.notna(last['ATRr_14']):
                        atr_value = last['ATRr_14']
                        stop_loss = current_price - (2 * atr_value)
                        risk_amount = current_price - stop_loss
                        target_1 = current_price + (1.5 * risk_amount)
                        target_2 = current_price + (2.5 * risk_amount)

                        st.metric("Dinamik Stop-Loss", f"${stop_loss:,.2f}", help="Hissenin ortalama volatilitesine (2 x ATR) göre hesaplanan, duygusal olmayan bir zarar durdurma seviyesi.")
                        st.metric("Hedef 1 (1.5R Ödül)", f"${target_1:,.2f}", help="Aldığınız riskin 1.5 katı potansiyel kâr sunan, daha temkinli bir kâr alma hedefi.")
                        st.metric("Hedef 2 (2.5R Ödül)", f"${target_2:,.2f}", help="Aldığınız riskin 2.5 katı potansiyel kâr sunan, daha iddialı bir kâr alma hedefi.")
                        st.caption(f"Bu plan, hissenin son 14 gündeki ortalama {atr_value:,.2f}$'lık hareketine dayanmaktadır.")
                    else:
                        st.info("Volatiliteye dayalı bir plan oluşturmak için yeterli veri yok.")
                st.divider()

                # BÖLÜM 2: İNTERAKTİF GRAFİK
                # ... (Önceki versiyon ile aynı, değişiklik yok)
                st.markdown("#### 📈 İnteraktif Fiyat Grafiği")
                # ... (Grafik kodu burada)
                
                # Diğer bölümler...
                # ... (Finansal Karne, Analist Görüşü, Haberler, Opsiyonlar vb.)
                # Bu kısımlar önceki versiyon ile aynı olduğu için kodun kısalığı açısından eklenmemiştir.
                # Lütfen bir önceki tam koddan bu bölümleri buraya kopyalayın.

    # --- SEKME 3 ---
    with tab3:
        # ... (Önceki versiyon ile aynı, değişiklik yok)
        pass
