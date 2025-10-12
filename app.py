import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time

# --- UYGULAMA AYARLARI VE HİSSE LİSTESİ ---

st.set_page_config(layout="wide", page_title="NASDAQ Strateji Motoru")

# Performans ve anlamlı sonuçlar için NASDAQ'ın en popüler hisselerinden oluşan bir liste.
# Bu liste kolayca genişletilebilir.
TICKER_LIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'COST', 'PEP',
    'ADBE', 'CSCO', 'TMUS', 'NFLX', 'AMD', 'INTC', 'CMCSA', 'INTU', 'AMGN', 'TXN',
    'QCOM', 'HON', 'AMAT', 'ISRG', 'BKNG', 'SBUX', 'ADP', 'MDLZ', 'GILD', 'ADI',
    'PYPL', 'REGN', 'VRTX', 'LRCX', 'PANW', 'MU', 'CSX', 'MAR', 'SNPS', 'ORLY',
    'CDNS', 'KLAC', 'ASML', 'CTAS', 'EXC', 'FTNT', 'AEP', 'DXCM', 'MNST', 'MCHP',
    'PCAR', 'PAYX', 'ROST', 'XEL', 'IDXX', 'WDAY', 'EA', 'KDP', 'FAST', 'BIIB',
    'ODFL', 'CSGP', 'CPRT', 'DDOG', 'TEAM', 'ILMN', 'SIRI', 'CHTR', 'WBD', 'GEHC',
    'BKR', 'CTSH', 'FANG', 'MRVL', 'ON', 'WBA', 'ZM', 'CRWD', 'DLTR', 'ANSS',
    'VRSK', 'ENPH', 'MRNA', 'ALGN', 'CEG', 'DASH', 'SGEN', 'ZS', 'EBAY', 'LULU',
    'JD', 'LCID', 'RIVN', 'AFRM', 'PLTR', 'SNOW', 'U', 'UBER', 'LYFT', 'HOOD',
    'SOFI', 'ETSY', 'PTON', 'COIN', 'RBLX', 'DOCN', 'MDB', 'OKTA', 'SHOP', 'SQ',
    'TWLO', 'ZI', 'NET', 'DOCS', 'ABNB', 'GTLB', 'PATH', 'BILL', 'DDOG'
]

# --- ANALİZ FONKSİYONLARI ---

@st.cache_data(ttl=3600) # Verileri 1 saat boyunca önbellekte tut
def get_stock_data(ticker):
    """Bir hissenin son 1 yıllık verisini çeker."""
    return yf.Ticker(ticker).history(period="1y")

def analyze_opportunity(data):
    """
    Hisse senedi verilerini analiz eder ve alım fırsatı varsa detayları döndürür.
    """
    # Yeterli veri yoksa analizi atla
    if data is None or len(data) < 50:
        return None

    # Teknik göstergeleri hesapla
    data.ta.rsi(length=14, append=True)
    data.ta.bbands(length=20, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.sma(length=200, append=True)

    last_row = data.iloc[-1]
    detected_signals = []

    # Sinyal 1: RSI Aşırı Satım
    if 'RSI_14' in last_row and last_row['RSI_14'] < 35:
        detected_signals.append("RSI Aşırı Satım")

    # Sinyal 2: Bollinger Alt Bandı
    if 'BBL_20_2.0' in last_row and last_row['Close'] <= last_row['BBL_20_2.0']:
        detected_signals.append("Bollinger Alt Bandı")

    # Sinyal 3: Yeni MACD Al Sinyali
    if 'MACD_12_26_9' in data.columns and 'MACDs_12_26_9' in data.columns:
        if len(data) > 2 and (data['MACD_12_26_9'].iloc[-1] > data['MACDs_12_26_9'].iloc[-1]) and \
           (data['MACD_12_26_9'].iloc[-2] < data['MACDs_12_26_9'].iloc[-2]):
            detected_signals.append("Yeni MACD Al Sinyali")

    # Eğer en az bir alım sinyali varsa, detayları hesapla
    if detected_signals:
        # Uzun vadeli trendi kontrol et
        long_term_trend = "Yükseliş" if 'SMA_200' in last_row and last_row['Close'] > last_row['SMA_200'] else "Düşüş"
        
        # Hedef fiyatı belirle (Bollinger orta bandı)
        target_price = last_row.get('BBM_20_2.0', 0)
        current_price = last_row['Close']

        # Sadece hedef fiyatı mevcut fiyattan yüksek olan mantıklı fırsatları tut
        if target_price > current_price:
            potential_profit_pct = ((target_price - current_price) / current_price) * 100
            
            return {
                "signal": ", ".join(detected_signals),
                "current_price": current_price,
                "target_price": target_price,
                "potential_profit_pct": potential_profit_pct,
                "long_term_trend": long_term_trend
            }
    return None

# --- STREAMLIT ARAYÜZÜ ---

st.title('🚀 NASDAQ Strateji Motoru')
st.caption('Otomatik Fırsat Tarama ve Sermaye Yönetimi Simülatörü')

st.info("""
**Bu Araç Nasıl Çalışır?**
1.  NASDAQ'ın en popüler hisselerini sizin için otomatik olarak tarar.
2.  Teknik göstergelere dayalı olarak **kısa vadeli alım fırsatları** arar (RSI, Bollinger Bantları vb.).
3.  Bir fırsat bulduğunda, potansiyel **hedef fiyatı** ve **kâr oranını** hesaplar.
4.  Girdiğiniz nakit miktarına göre size **kişiselleştirilmiş strateji önerileri** sunar.
""", icon="ℹ️")

st.warning("""
**Yasal Uyarı:** Bu araç yalnızca eğitim ve simülasyon amaçlıdır. Sunulan bilgiler yatırım tavsiyesi değildir. 
Finansal piyasalarda işlem yapmak ciddi riskler içerir.
""", icon="⚠️")

# Kullanıcıdan sermaye girişi al
user_cash = st.number_input(
    'Strateji oluşturmak için ne kadar nakit ($) kullanmak istersiniz?',
    min_value=100,
    max_value=1000000,
    value=1000,
    step=100,
    help="Bu miktar, potansiyel alım adetlerini ve kârı hesaplamak için kullanılacaktır."
)

if st.button('📈 Piyasayı Şimdi Tara!', type="primary"):
    
    opportunities = []
    
    progress_bar = st.progress(0, text="Tarama Başlatılıyor...")
    
    for i, ticker in enumerate(TICKER_LIST):
        try:
            stock_data = get_stock_data(ticker)
            opportunity = analyze_opportunity(stock_data)
            
            if opportunity:
                opportunity['ticker'] = ticker
                opportunities.append(opportunity)
                
            progress_text = f"Taranıyor: {ticker} ({i+1}/{len(TICKER_LIST)}) - Fırsatlar Bulundu: {len(opportunities)}"
            progress_bar.progress((i + 1) / len(TICKER_LIST), text=progress_text)
            
        except Exception as e:
            # Hata veren hisseleri atla ve devam et
            continue
            
    progress_bar.empty()

    if not opportunities:
        st.success("✅ Tarama Tamamlandı! Şu anda belirgin bir alım fırsatı tespit edilmedi.", icon="👍")
    else:
        st.success(f"✅ Tarama Tamamlandı! {len(opportunities)} adet potansiyel fırsat bulundu.", icon="🎯")
        
        # Sonuçları DataFrame'e çevir
        df = pd.DataFrame(opportunities)
        
        # Sermayeye göre hesaplamalar yap
        df['buyable_shares'] = (user_cash // df['current_price']).astype(int)
        df['investment_cost'] = df['buyable_shares'] * df['current_price']
        df['potential_profit_usd'] = (df['target_price'] - df['current_price']) * df['buyable_shares']
        
        # Sadece alınabilecek hisseleri göster
        df_filtered = df[df['buyable_shares'] > 0].copy()
        
        # Gösterim için sütunları düzenle
        df_filtered['current_price'] = df_filtered['current_price'].map('${:,.2f}'.format)
        df_filtered['target_price'] = df_filtered['target_price'].map('${:,.2f}'.format)
        df_filtered['potential_profit_pct'] = df_filtered['potential_profit_pct'].map('{:.2f}%'.format)
        df_filtered['investment_cost'] = df_filtered['investment_cost'].map('${:,.2f}'.format)
        df_filtered['potential_profit_usd'] = df_filtered['potential_profit_usd'].map('${:,.2f}'.format)
        
        st.subheader(f"Sizin için Oluşturulan Strateji Önerileri ({user_cash:,.0f} $ Nakit ile)")
        
        display_df = df_filtered[[
            'ticker', 
            'signal', 
            'current_price', 
            'target_price', 
            'potential_profit_pct',
            'buyable_shares',
            'investment_cost',
            'potential_profit_usd',
            'long_term_trend'
        ]].rename(columns={
            'ticker': 'Hisse',
            'signal': 'Tespit Edilen Sinyal',
            'current_price': 'Mevcut Fiyat',
            'target_price': 'Hedef Fiyat',
            'potential_profit_pct': 'Potansiyel Kâr (%)',
            'buyable_shares': 'Alınabilir Adet',
            'investment_cost': 'Yatırım Maliyeti',
            'potential_profit_usd': 'Potansiyel Kâr ($)',
            'long_term_trend': 'Uzun Vadeli Trend'
        }).set_index('Hisse')
        
        st.dataframe(display_df, use_container_width=True)
