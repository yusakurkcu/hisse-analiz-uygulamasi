import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests

# ==================================================================================================
# TEMEL AYARLAR VE STİL YAPILANDIRMASI
# ==================================================================================================

st.set_page_config(
    page_title="Borsa Fırsat Tarama Botu",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Robinhood'dan ilham alan modern koyu tema için özel CSS
st.markdown("""
<style>
    /* Google Fonts'tan Inter yazı tipini yükle */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Genel Stil Ayarları */
    body, .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #000000;
        color: #FAFAFA;
    }
    
    /* Ana Başlık Stili */
    .stApp > header {
        background-color: transparent;
    }
    
    .css-18ni7ap {
        background: #000000;
    }

    /* Sekme Stilleri */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #262626;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 8px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: #101010;
        color: #22c55e; /* Vurgu Rengi - Canlı Yeşil */
        border-bottom: 2px solid #22c55e;
    }
    
    /* Kart (Expander) Stilleri */
    .st-expander, .streamlit-expander {
        border: 1px solid #262626;
        border-radius: 12px;
        background-color: #101010;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    .st-expander header, .streamlit-expander-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #FAFAFA;
        padding: 16px;
    }
    
    .st-expander:hover, .streamlit-expander:hover {
       border-color: #22c55e;
    }

    /* Buton Stilleri */
    .stButton>button {
        border-radius: 8px;
        background-color: #22c55e;
        color: #000000;
        border: none;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 1rem;
        box-shadow: 0 2px 8px rgba(34, 197, 94, 0.3);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #16a34a;
        transform: scale(1.02);
    }
    
    /* Metin Giriş Kutusu Stilleri */
    .stTextInput>div>div>input {
        border-radius: 8px;
        background-color: #101010;
        border: 1px solid #363636;
        color: #FAFAFA;
    }
    
    /* Metrik Kutuları Stili */
    div[data-testid="stMetric"] {
        background-color: #101010;
        border: 1px solid #262626;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    /* Logo ve Başlık Stili */
    .app-header {
        display: flex;
        align-items: center;
        gap: 15px;
        padding-bottom: 20px;
        border-bottom: 1px solid #262626;
        margin-bottom: 20px;
    }
    .app-header .logo {
        font-size: 2.5rem;
    }
    .app-header .title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FAFAFA;
    }

</style>
""", unsafe_allow_html=True)


# ==================================================================================================
# YARDIMCI FONKSİYONLAR
# ==================================================================================================

# yfinance'dan gelen verilerin sütun adlarını standartlaştırmak için
def standardize_columns(df):
    """Veri çerçevesindeki sütun adlarını küçük harfe çevirir."""
    df.columns = df.columns.str.lower()
    return df

@st.cache_data(ttl=3600)
def get_stock_info(ticker):
    """Bir hisse senedinin temel bilgilerini ve logosunu çeker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        logo_url = info.get('logo_url', '')
        # Logo URL'si yoksa veya boşsa, favicon kullanmayı dene
        if not logo_url:
            domain = info.get('website', '').split('//')[-1].split('/')[0]
            if domain:
                logo_url = f"https://logo.clearbit.com/{domain}"
        return info, logo_url
    except Exception as e:
        return None, ""

@st.cache_data(ttl=900)
def get_stock_data(ticker, period="1y"):
    """Belirtilen periyotta hisse senedi verilerini çeker ve standartlaştırır."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        return standardize_columns(df)
    except Exception as e:
        return None
        
@st.cache_data(ttl=3600)
def get_robinhood_stocks():
    """Robinhood'da işlem gören popüler hisselerin bir listesini çeker."""
    # Güvenilir bir kaynaktan alınmış statik liste.
    # Bu liste zamanla güncellenebilir.
    tickers = [
        'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'GOOG', 'TSLA', 'META', 'NVDA', 'BRK-B', 'JPM', 'JNJ', 'V', 'UNH',
        'WMT', 'PG', 'MA', 'HD', 'DIS', 'BAC', 'PYPL', 'NFLX', 'ADBE', 'CRM', 'PFE', 'KO', 'INTC', 'CMCSA',
        'PEP', 'XOM', 'CSCO', 'T', 'VZ', 'ABT', 'NKE', 'MCD', 'MDT', 'WFC', 'COST', 'AVGO', 'ACN', 'QCOM',
        'TMO', 'CVX', 'LLY', 'MRK', 'NEE', 'DHR', 'TXN', 'HON', 'UPS', 'PM', 'ORCL', 'UNP', 'LIN', 'SBUX',
        'LOW', 'AMD', 'IBM', 'BA', 'CAT', 'GS', 'RTX', 'MMM', 'GE', 'CVS', 'DE', 'AMGN', 'ISRG', 'BKNG',
        'GILD', 'AMT', 'SPGI', 'ZTS', 'MO', 'ANTM', 'C', 'CI', 'TJX', 'TGT', 'BDX', 'SYK', 'ADP', 'FIS',
        'SCHW', 'DUK', 'PLD', 'SO', 'USB', 'LMT', 'CB', 'NOW', 'FISV', 'AXP', 'ETN', 'MDLZ', 'PNC', 'CL',
        'INTU', 'ADI', 'NSC', 'ATVI', 'ICE', 'MMC', 'BIIB', 'BSX', 'GM', 'F'
    ]
    return tickers

def run_breakout_scan(tickers):
    """
    Belirtilen hisseler üzerinde yüksek hacimli kırılım stratejisini çalıştırır.
    """
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(tickers):
        try:
            status_text.text(f"🔎 {ticker} taranıyor... ({i+1}/{len(tickers)})")
            
            stock_info, _ = get_stock_info(ticker)
            if stock_info is None:
                continue
            
            # 1. Piyasa Değeri Filtresi
            market_cap = stock_info.get('marketCap', 0)
            if market_cap < 500_000_000:
                continue

            df = get_stock_data(ticker, period="250d")
            if df is None or len(df) < 200:
                continue

            # Teknik göstergeleri hesapla
            df.ta.sma(length=200, append=True)
            df.ta.atr(length=14, append=True)
            
            latest_price = df['close'].iloc[-1]
            latest_volume = df['volume'].iloc[-1]
            sma_200 = df['SMA_200'].iloc[-1]
            atr = df['ATRr_14'].iloc[-1]

            # 2. Uzun Vadeli Yükseliş Trendi
            if latest_price < sma_200:
                continue

            # Son 20 günlük veriyi al
            last_20_days = df.iloc[-21:-1]
            
            # 3. Sıkışma Dönemi
            max_20_days = last_20_days['high'].max()
            min_20_days = last_20_days['low'].min()
            
            if (max_20_days - min_20_days) / min_20_days > 0.15:
                continue
            
            # 4. Kırılım Anı
            if latest_price < max_20_days:
                continue
                
            # 5. Hacim Teyidi
            avg_volume_20_days = last_20_days['volume'].mean()
            if latest_volume < (avg_volume_20_days * 1.5):
                continue
            
            # Tüm koşullar sağlandı, sonucu listeye ekle
            potential = (df['ATR_14'].iloc[-1] * 2 / latest_price) * 100
            target_price = latest_price + (df['ATR_14'].iloc[-1] * 2)

            results.append({
                'ticker': ticker,
                'info': stock_info,
                'potential': potential,
                'target_price': target_price,
                'latest_price': latest_price
            })

        except Exception as e:
            # Hata oluşursa atla ve devam et
            continue
        finally:
            progress_bar.progress((i + 1) / len(tickers))

    status_text.success(f"✅ Tarama tamamlandı! {len(results)} fırsat bulundu.")
    progress_bar.empty()
    return results

def get_technical_analysis(df):
    """RSI, MACD ve SMA'ya dayalı basit bir teknik analiz önerisi oluşturur."""
    if df is None or len(df) < 50:
        return "NÖTR", "Yetersiz veri."

    # Göstergeleri hesapla
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.sma(length=200, append=True)
    
    latest = df.iloc[-1]
    score = 0
    
    # RSI
    if latest['RSI_14'] < 30: score += 2
    elif latest['RSI_14'] < 40: score += 1
    elif latest['RSI_14'] > 70: score -= 2
    elif latest['RSI_14'] > 60: score -= 1
        
    # MACD
    if latest['MACD_12_26_9'] > latest['MACDs_12_26_9']: score += 1
    else: score -=1
    
    # Hareketli Ortalamalar
    if latest['close'] > latest['SMA_50']: score += 1
    if latest['close'] > latest['SMA_200']: score += 1
    if latest['SMA_50'] > latest['SMA_200']: score += 1
    
    # Sonuç
    if score >= 3:
        return "AL", "Hisse, RSI, MACD ve hareketli ortalamalara dayalı olarak pozitif bir momentum sergiliyor. Yükseliş trendi sinyalleri güçlü."
    elif score <= -2:
        return "SAT", "Teknik göstergeler zayıflığa işaret ediyor. Düşüş momentumu ve negatif sinyaller mevcut."
    else:
        return "NÖTR", "Piyasa kararsız bir seyir izliyor. Belirgin bir alım veya satım sinyali şu an için gözlenmiyor."

@st.cache_data(ttl=900)
def get_smart_option(ticker, stock_price):
    """
    Belirtilen hisse için en mantıklı alım (Call) opsiyonunu bulur.
    """
    try:
        stock = yf.Ticker(ticker)
        exp_dates = stock.options
        
        today = datetime.now()
        min_exp = today + timedelta(days=30)
        max_exp = today + timedelta(days=45)

        suitable_contracts = []

        for date in exp_dates:
            exp_date = datetime.strptime(date, '%Y-%m-%d')
            if not (min_exp <= exp_date <= max_exp):
                continue

            option_chain = stock.option_chain(date)
            calls = option_chain.calls
            
            # Filtreleme
            calls = calls[calls['openInterest'] > 50] # Likidite
            calls['spread'] = calls['ask'] - calls['bid']
            calls = calls[calls['spread'] < 0.5] # Dar makas
            calls = calls[calls['ask'] < (stock_price * 0.10)] # Maliyet
            
            # Fiyata en yakın olanları seç
            calls = calls[(calls['strike'] > stock_price * 0.95) & (calls['strike'] < stock_price * 1.10)]
            
            if not calls.empty:
                suitable_contracts.append(calls)
        
        if not suitable_contracts:
            return None
            
        all_options = pd.concat(suitable_contracts)
        
        # En ucuz olanı seç
        best_option = all_options.loc[all_options['ask'].idxmin()]
        return best_option

    except Exception as e:
        return None

# ==================================================================================================
# UYGULAMA ARAYÜZÜ
# ==================================================================================================

# Header
st.markdown("""
<div class="app-header">
    <span class="logo">🐂</span>
    <span class="title">Borsa Fırsat Tarama Botu</span>
</div>
""", unsafe_allow_html=True)


# Sekmeler
tab1, tab2 = st.tabs(["📈 Fırsat Taraması", "🔍 Hisse Analizi"])

# --------------------------------------------------------------------------------------------------
# SEKME 1: FIRSAT TARAMASI
# --------------------------------------------------------------------------------------------------
with tab1:
    st.subheader("Yüksek Hacimli Kırılım Stratejisi")
    st.markdown("Bu araç, uzun vadeli yükseliş trendinde olan, bir süredir dar bir bantta sıkışmış ve bu sıkışmayı yüksek hacimle yukarı kırmış hisseleri tespit eder. Sadece piyasa değeri **500 Milyon Dolar**'dan büyük şirketler listelenir.")

    if 'scan_results' not in st.session_state:
        st.session_state.scan_results = None

    if st.button("🚀 Taramayı Başlat"):
        with st.spinner("Piyasalar taranıyor, lütfen bekleyin... Bu işlem birkaç dakika sürebilir."):
            tickers_to_scan = get_robinhood_stocks()
            st.session_state.scan_results = run_breakout_scan(tickers_to_scan)

    if st.session_state.scan_results is not None:
        results = st.session_state.scan_results
        
        if not results:
            st.info("Mevcut piyasa koşullarında stratejiye uygun hisse bulunamadı.")
        else:
            st.success(f"**{len(results)} adet potansiyel fırsat bulundu!**")
            
            for res in results:
                info = res['info']
                ticker = res['ticker']
                _, logo_url = get_stock_info(ticker)
                
                header_col1, header_col2 = st.columns([1, 5])
                with header_col1:
                    if logo_url:
                        st.image(logo_url, width=60)
                    else:
                        st.markdown(f'<div style="width:60px; height:60px; background-color:#333; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:1.5rem;">{ticker[0]}</div>', unsafe_allow_html=True)
                with header_col2:
                    st.write(f"**{info.get('shortName', ticker)} ({ticker})**")
                    st.markdown(f"**<span style='color:#22c55e;'>Potansiyel: +{res['potential']:.2f}%</span>**", unsafe_allow_html=True)
                
                with st.expander("Detayları Görüntüle", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("##### Teyit Sinyalleri")
                        st.success("✅ Fiyat > 200 Günlük Ortalama")
                        st.success("✅ Son 20 Günlük Sıkışma")
                        st.success("✅ Fiyat Kırılımı Gerçekleşti")
                        st.success("✅ Hacim Ortalamanın 1.5 Katı")
                        st.success("✅ Piyasa Değeri > $500M")

                    with col2:
                        st.markdown("##### Hedef ve Potansiyel Kazanç")
                        st.metric(
                            label="ATR (14) Bazlı Hedef Fiyat",
                            value=f"${res['target_price']:.2f}",
                            delta=f"+${res['target_price'] - res['latest_price']:.2f}"
                        )
                        
                        st.markdown("<hr style='border-color: #262626; margin-top: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

                        st.markdown("##### Yatırım Hesaplayıcı")
                        investment_amount = st.number_input("Yatırım Miktarı ($)", min_value=100, max_value=100000, value=1000, step=100, key=f"invest_{ticker}")
                        
                        num_shares = investment_amount / res['latest_price']
                        potential_profit = (res['target_price'] - res['latest_price']) * num_shares
                        
                        st.info(f"**{investment_amount}$** yatırım ile hedefe ulaşıldığında potansiyel kârınız **~${potential_profit:.2f}** olabilir.")

# --------------------------------------------------------------------------------------------------
# SEKME 2: HİSSE ANALİZİ
# --------------------------------------------------------------------------------------------------
with tab2:
    st.subheader("Detaylı Hisse Senedi Analizi")
    
    ticker_input = st.text_input(
        "Analiz etmek istediğiniz hisse senedi sembolünü girin (Örn: AAPL, TSLA, MSFT)",
        placeholder="Sembolü buraya yazın..."
    ).upper()

    if ticker_input:
        with st.spinner(f"{ticker_input} verileri analiz ediliyor..."):
            info, logo_url = get_stock_info(ticker_input)
            df = get_stock_data(ticker_input, "1y")

            if info is None or df is None:
                st.error("Hisse senedi bilgileri alınamadı. Lütfen sembolü kontrol edin.")
            else:
                st.markdown("---")
                
                # Başlık ve Logo
                col1, col2 = st.columns([1, 6])
                with col1:
                    if logo_url:
                        st.image(logo_url, width=80)
                    else:
                         st.markdown(f'<div style="width:80px; height:80px; background-color:#333; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:2rem;">{ticker_input[0]}</div>', unsafe_allow_html=True)
                with col2:
                    st.title(info.get('shortName', ticker_input))
                    st.subheader(f"{info.get('symbol', '')} - {info.get('exchange', '')}")

                st.markdown("---")
                
                # Temel Metrikler
                st.subheader("Genel Bakış")
                latest_price = df['close'].iloc[-1]
                prev_close = df['close'].iloc[-2]
                price_change = latest_price - prev_close
                price_change_pct = (price_change / prev_close) * 100
                
                # Teknik Analiz
                analysis_signal, analysis_text = get_technical_analysis(df)
                
                # Dinamik Fiyat Beklentisi
                atr_val = ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1]
                if analysis_signal == "SAT":
                    target_delta = -atr_val * 1.5
                    target_price = latest_price + target_delta
                else:
                    target_delta = atr_val * 2
                    target_price = latest_price + target_delta
                
                # Destek & Direnç
                last_90_days = df.tail(90)
                support_1 = last_90_days['low'].min()
                resistance_1 = last_90_days['high'].max()

                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                with m_col1:
                    st.metric(
                        label="Güncel Fiyat",
                        value=f"${latest_price:.2f}",
                        delta=f"{price_change:.2f} ({price_change_pct:.2f}%)"
                    )
                with m_col2:
                    market_cap = info.get('marketCap', 0)
                    st.metric(label="Piyasa Değeri", value=f"${market_cap/1e9:.2f} Milyar")
                with m_col3:
                    st.metric(
                        label="Dinamik Fiyat Beklentisi",
                        value=f"${target_price:.2f}",
                        delta=f"{target_delta/latest_price*100:.2f}%",
                        help="Teknik analize göre hesaplanan, 14 günlük ortalama volatilite (ATR) kullanılarak oluşturulmuş kısa vadeli fiyat hedefidir. AL/NÖTR için ATR*2, SAT için ATR*1.5 kullanılır."
                    )
                with m_col4:
                    st.metric(label="Teknik Sinyal", value=analysis_signal)
                
                st.markdown("---")
                
                # Grafik ve Analiz Detayları
                st.subheader("Teknik Analiz ve Fiyat Grafiği")
                g_col1, g_col2 = st.columns([2, 3])
                
                with g_col1:
                    st.markdown("##### Analiz Dökümü")
                    st.info(analysis_text)
                    
                    st.markdown("##### Destek & Direnç")
                    st.markdown(f"**Direnç 1 (R1 - 90 Gün Zirve):** `${resistance_1:.2f}`")
                    st.markdown(f"**Destek 1 (S1 - 90 Gün Dip):** `${support_1:.2f}`")

                    st.markdown("##### Şirket Profili")
                    st.write(info.get('longBusinessSummary', 'Profil bilgisi bulunamadı.'))
                    
                with g_col2:
                    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                    open=df['open'],
                                    high=df['high'],
                                    low=df['low'],
                                    close=df['close'])])

                    # Destek ve Direnç çizgileri
                    fig.add_hline(y=resistance_1, line_dash="dash", line_color="#ef4444", annotation_text="Direnç 1 (R1)", annotation_position="bottom right")
                    fig.add_hline(y=support_1, line_dash="dash", line_color="#22c55e", annotation_text="Destek 1 (S1)", annotation_position="bottom right")

                    fig.update_layout(
                        title=f'{ticker_input} Fiyat Grafiği',
                        yaxis_title='Fiyat ($)',
                        xaxis_rangeslider_visible=False,
                        template='plotly_dark',
                        plot_bgcolor='#101010',
                        paper_bgcolor='#101010',
                        font=dict(family="Inter, sans-serif", color="#FAFAFA")
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("---")
                
                # Akıllı Opsiyon Önerisi
                st.subheader("💡 Akıllı Opsiyon Önerisi")
                with st.spinner("En uygun opsiyon kontratı aranıyor..."):
                    best_option = get_smart_option(ticker_input, latest_price)
                
                if best_option is not None:
                    o_col1, o_col2, o_col3, o_col4 = st.columns(4)
                    exp_date = datetime.fromtimestamp(best_option['expiration']).strftime('%d %B %Y')
                    
                    o_col1.metric("Vade Tarihi", exp_date)
                    o_col2.metric("Kullanım Fiyatı (Strike)", f"${best_option['strike']:.2f}")
                    o_col3.metric("Kontrat Primi (Maliyet)", f"${best_option['ask']:.2f}")
                    o_col4.metric("Açık Pozisyon", f"{best_option['openInterest']:.0f}")

                    st.info(f"Bu Alım (Call) opsiyonu; 30-45 gün arası vadesi, yüksek likiditesi, dar alım-satım makası ve hisse fiyatına oranla makul maliyeti nedeniyle seçilmiştir. Bu bir yatırım tavsiyesi değildir.")
                else:
                    st.warning("Bu hisse için belirtilen kriterlere (30-45 gün vade, yeterli likidite, düşük maliyet) uygun bir opsiyon kontratı bulunamadı.")
