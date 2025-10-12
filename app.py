import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from newsapi import NewsApiClient
from textblob import TextBlob
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- GÜVENLİK VE API AYARLARI ---
NEWS_API_KEY = "b45712756c0a4d93827bd02ae10c43c2"
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# --- VERİ YÜKLEME VE ÖNBELLEKLEME (GÜNCELLENMİŞ VERSİYON) ---
@st.cache_data
def load_nasdaq_tickers():
    """NASDAQ hisse senedi listesini doğrudan internetten yükler ve önbelleğe alır."""
    url = "https://pkgstore.datahub.io/core/nasdaq-listings/nasdaq-listed_csv/data/7665719fb51081ba0bd834fde71ce822/nasdaq-listed_csv.csv"
    try:
        df = pd.read_csv(url)
        # Sütun isimlerinde boşluk varsa temizle
        df.rename(columns={'Company Name': 'Company_Name'}, inplace=True)
        # Kullanıcı dostu bir görüntü için Sembol ve Şirket Adını birleştir
        df['display_name'] = df['Symbol'] + ' - ' + df['Company_Name']
        return df
    except Exception as e:
        st.error(f"Hisse senedi listesi yüklenirken bir hata oluştu: {e}")
        return None

# --- ANALİZ FONKSİYONLARI ---

def analyze_trade_signals(data):
    """
    Hisse senedi verilerini analiz eder ve alım fırsatları ile genel trend üzerine yorumlar üretir.
    """
    signals = {'opportunities': [], 'trend': []}
    
    # Veri setinin yeterli uzunlukta olduğundan emin ol
    if len(data) < 20: # En uzun periyotlu indikatörümüz 20 (Bollinger)
        return signals # Yeterli veri yoksa boş sinyal listesi döndür

    # Gerekli tüm teknik göstergeleri hesapla
    data.ta.rsi(length=14, append=True)
    data.ta.bbands(length=20, append=True) # Bollinger Bands
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    data.ta.sma(length=50, append=True)
    data.ta.sma(length=200, append=True)
    
    # En son (bugünün) verilerini al
    last_row = data.iloc[-1]
    
    # --- Alım Fırsatı Sinyalleri ---
    
    # 1. RSI Aşırı Satım Analizi (Güvenlik Kontrollü)
    if 'RSI_14' in last_row.index and not pd.isna(last_row['RSI_14']):
        if last_row['RSI_14'] < 35:
            signals['opportunities'].append({
                'title': 'Aşırı Satım Bölgesi (RSI)',
                'description': f"RSI değeri ({last_row['RSI_14']:.2f}) kritik 35 seviyesinin altında. Bu durum, hissenin aşırı satıldığını ve bir tepki alımı için potansiyel oluşturduğunu gösterebilir.",
                'sentiment': 'pozitif'
            })

    # 2. Bollinger Alt Bandı Analizi (Güvenlik Kontrollü)
    if 'BBL_20_2.0' in last_row.index and not pd.isna(last_row['BBL_20_2.0']):
        if last_row['Close'] <= last_row['BBL_20_2.0']:
            signals['opportunities'].append({
                'title': 'Bollinger Alt Bandı Teması',
                'description': f"Fiyat ({last_row['Close']:.2f} $), Bollinger alt bandına ({last_row['BBL_20_2.0']:.2f} $) temas etti veya altına düştü. Bu, hissenin istatistiksel olarak 'ucuz' olduğunu ve bir sıçrama potansiyeli taşıdığını işaret edebilir.",
                'sentiment': 'pozitif'
            })
        
    # 3. MACD Alım Sinyali Analizi (Güvenlik Kontrollü)
    if 'MACD_12_26_9' in data.columns and 'MACDs_12_26_9' in data.columns:
        recent_data = data.tail(3)
        if len(recent_data) > 2: # En az 3 veri noktası olduğundan emin ol
            if (recent_data['MACD_12_26_9'].iloc[-1] > recent_data['MACDs_12_26_9'].iloc[-1]) and \
               (recent_data['MACD_12_26_9'].iloc[-2] < recent_data['MACDs_12_26_9'].iloc[-2]):
                signals['opportunities'].append({
                    'title': 'Yeni MACD Al Sinyali',
                    'description': 'MACD çizgisi, sinyal çizgisini son 3 gün içinde yukarı yönlü kesti. Bu, yükseliş momentumunun başladığına dair güçlü bir teknik işarettir.',
                    'sentiment': 'pozitif'
                })

    # --- Genel Trend Durumu ---
    
    # 1. Uzun Vadeli Trend (200 Günlük Ortalama) (Güvenlik Kontrollü)
    if 'SMA_200' in last_row.index and not pd.isna(last_row['SMA_200']):
        if last_row['Close'] > last_row['SMA_200']:
            signals['trend'].append({
                'title': 'Uzun Vadeli Yükseliş Trendi',
                'description': f"Fiyat ({last_row['Close']:.2f} $), 200 günlük ortalamanın ({last_row['SMA_200']:.2f} $) üzerinde. Bu, hissenin ana trendinin YUKARI olduğunu gösterir.",
                'sentiment': 'pozitif'
            })
        else:
            signals['trend'].append({
                'title': 'Uzun Vadeli Düşüş Trendi',
                'description': f"Fiyat ({last_row['Close']:.2f} $), 200 günlük ortalamanın ({last_row['SMA_200']:.2f} $) altında. Bu, hissenin ana trendinin AŞAĞI olduğunu gösterir.",
                'sentiment': 'negatif'
            })
        
    # 2. Kısa/Orta Vadeli Trend (Golden/Death Cross) (Güvenlik Kontrollü)
    if 'SMA_50' in last_row.index and 'SMA_200' in last_row.index and not pd.isna(last_row['SMA_50']) and not pd.isna(last_row['SMA_200']):
        if last_row['SMA_50'] > last_row['SMA_200']:
            signals['trend'].append({
                'title': 'Golden Cross Aktif',
                'description': '50 günlük ortalama, 200 günlük ortalamanın üzerinde. Bu, orta ve uzun vadede güçlü bir yükseliş sinyali olarak kabul edilir.',
                'sentiment': 'pozitif'
            })
        else:
            signals['trend'].append({
                'title': 'Death Cross Aktif',
                'description': '50 günlük ortalama, 200 günlük ortalamanın altında. Bu, orta ve uzun vadede bir zayıflık işareti olarak kabul edilir.',
                'sentiment': 'negatif'
            })
            
    return signals

def get_news_and_sentiment(ticker_symbol):
    """Hisse ile ilgili haberleri çeker ve duygu analizi yapar."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        all_articles = newsapi.get_everything(q=ticker_symbol, from_param=start_date.strftime('%Y-%m-%d'), to=end_date.strftime('%Y-%m-%d'), language='en', sort_by='publishedAt', page_size=10)
        analyzed_articles = []
        for article in all_articles['articles']:
            blob = TextBlob(article['title'])
            sentiment = 'Nötr'
            if blob.sentiment.polarity > 0.15: sentiment = 'Pozitif'
            elif blob.sentiment.polarity < -0.15: sentiment = 'Negatif'
            analyzed_articles.append({'title': article['title'], 'url': article['url'], 'sentiment': sentiment})
        return analyzed_articles
    except Exception:
        return []

# --- STREAMLIT ARAYÜZÜ ---

st.set_page_config(layout="wide", page_title="NASDAQ Fırsat Tarayıcısı")
st.title('🎯 NASDAQ Fırsat Tarayıcısı')
st.caption('Yapay Zeka Destekli Alım Fırsatı Analizi')

nasdaq_tickers = load_nasdaq_tickers()

if nasdaq_tickers is None:
    st.error("NASDAQ hisse senedi listesi internetten yüklenemedi. Lütfen internet bağlantınızı kontrol edin veya daha sonra tekrar deneyin.")
else:
    selected_display_name = st.selectbox(
        'Analiz edilecek hisseyi seçin veya yazarak arayın:',
        nasdaq_tickers['display_name'],
        index=None, # Başlangıçta boş olsun
        placeholder="Bir hisse senedi seçin (Örn: AAPL - Apple Inc.)..."
    )

    if selected_display_name:
        ticker_symbol = selected_display_name.split(' - ')[0]
        
        with st.spinner(f'{ticker_symbol} için derinlemesine analiz yapılıyor...'):
            stock_data = yf.Ticker(ticker_symbol).history(period="2y") # Daha sağlam hesaplamalar için periyodu 2 yıla çıkardım

            if stock_data.empty or len(stock_data) < 50: # En az 50 günlük veri olsun
                st.error("Bu hisse için yeterli veri bulunamadı. Lütfen daha uzun bir geçmişi olan başka bir hisse seçin.")
            else:
                signals = analyze_trade_signals(stock_data)
                articles = get_news_and_sentiment(ticker_symbol)
                try:
                    info = yf.Ticker(ticker_symbol).info
                except:
                    info = {} # .info bazen hata verebiliyor, buna karşı da koruma ekledim

                st.header(f"{info.get('longName', ticker_symbol)} ({ticker_symbol}) Analizi")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Sektör", info.get('sector', 'N/A'))
                col2.metric("Piyasa Değeri", f"{info.get('marketCap', 0) / 1e9:.2f} Milyar $" if info.get('marketCap') else 'N/A')
                col3.metric("Son Fiyat", f"{stock_data['Close'].iloc[-1]:.2f} $", f"{stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2]:.2f} $")

                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Fiyat'))
                if 'BBU_20_2.0' in stock_data.columns:
                    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['BBU_20_2.0'], mode='lines', name='Bollinger Üst', line=dict(color='rgba(150, 150, 150, 0.5)')))
                    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['BBL_20_2.0'], mode='lines', name='Bollinger Alt', line=dict(color='rgba(150, 150, 150, 0.5)'), fill='tonexty', fillcolor='rgba(200, 200, 200, 0.1)'))
                if 'SMA_50' in stock_data.columns:
                    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA_50'], mode='lines', name='50 Günlük MA', line=dict(color='orange')))
                if 'SMA_200' in stock_data.columns:
                    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA_200'], mode='lines', name='200 Günlük MA', line=dict(color='purple')))
                fig.update_layout(title='Fiyat Grafiği ve Teknik Göstergeler', xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, use_container_width=True)

                st.divider()

                col_opp, col_trend = st.columns(2)
                with col_opp:
                    st.subheader('💡 Potansiyel Alım Fırsatı Sinyalleri')
                    if not signals['opportunities']:
                        st.info("Şu anda belirgin bir kısa vadeli alım fırsatı sinyali tespit edilmedi.", icon="🤔")
                    for signal in signals['opportunities']:
                        st.success(f"**{signal['title']}:** {signal['description']}", icon="🔼")

                with col_trend:
                    st.subheader('🧭 Genel Trend Durumu')
                    if not signals['trend']:
                        st.warning("Genel trendi belirlemek için yeterli uzun vadeli veri bulunmuyor.", icon="⏳")
                    for signal in signals['trend']:
                        if signal['sentiment'] == 'pozitif':
                            st.success(f"**{signal['title']}:** {signal['description']}", icon="✅")
                        else:
                            st.error(f"**{signal['title']}:** {signal['description']}", icon="⚠️")

                st.divider()
                
                st.subheader('📰 "News AI" - Son Haberler ve Duygu Analizi')
                if not articles:
                    st.info(f"{ticker_symbol} için son 7 günde önemli bir haber bulunamadı.")
                for article in articles:
                    icon = "😐"
                    if article['sentiment'] == 'Pozitif': icon = "🟢"
                    elif article['sentiment'] == 'Negatif': icon = "🔴"
                    st.markdown(f"{icon} [{article['title']}]({article['url']})")
