import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime
from newsapi import NewsApiClient
from textblob import TextBlob
import time # Bekleme fonksiyonu için eklendi

# --- UYGULAMA AYARLARI ---
st.set_page_config(layout="wide", page_title="AI Hisse Strateji Motoru")

# NewsAPI Anahtarı
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

# YENİ - HIZ LİMİTİNE KARŞI KORUMALI VERİ ÇEKME FONKSİYONU
def get_ticker_with_retry(ticker_symbol, retries=3, delay=60):
    """Hız limitine takılma durumunda bekleyip yeniden deneyen Ticker nesnesi döndürür."""
    for i in range(retries):
        try:
            return yf.Ticker(ticker_symbol)
        except yf.YFRateLimitError:
            st.warning(f"Yahoo Finance hız limitine takıldık. {delay} saniye bekleniyor... ({i+1}/{retries})")
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
    except Exception:
        return pd.DataFrame()

def analyze_for_ai_screener(data):
    # ... (Bu fonksiyonda değişiklik yok)
    pass

def recommend_option(options_df):
    # ... (Bu fonksiyonda değişiklik yok)
    pass

def get_detailed_analysis(data):
    # ... (Bu fonksiyonda değişiklik yok)
    pass

@st.cache_data(ttl=1800)
def get_market_health():
    # ... (Bu fonksiyonda değişiklik yok)
    pass

def analyze_portfolio_position(position, market_health_status):
    # ... (Bu fonksiyonda değişiklik yok)
    pass

@st.cache_data(ttl=3600)
def get_news_for_stock(ticker):
    # ... (Bu fonksiyonda değişiklik yok)
    pass

# --- ANA ARAYÜZ ---
st.title('🤖 AI Hisse Senedi Strateji Motoru')
# ... (Yasal uyarı vb. aynı)

full_stock_list = load_all_tradable_stocks()
if full_stock_list is None:
    st.error("Hisse senedi listesi yüklenemedi.")
else:
    tab1, tab2, tab3 = st.tabs(["🚀 AI Fırsat Tarayıcısı", "🔍 Detaylı Hisse Analizi", "🧠 Portföy Stratejisti"])

    # --- SEKME 1: AI FIRSAT TARAYICISI (GÜNCELLENDİ) ---
    with tab1:
        st.header("Yüksek Potansiyelli Hisse ve Opsiyon Fırsatlarını Keşfedin")
        
        scan_for_options = st.checkbox("Opsiyon Fırsatlarını da Tara (Tarama Süresini Ciddi Şekilde Uzatır)", value=False)
        
        st.warning(
            "**LÜTFEN DİKKAT:** 'Tüm Piyasayı Tara' işlemi, binlerce hisseyi analiz eder. "
            "Sadece hisse taraması **5-15 dakika**, opsiyonlarla birlikte tarama **20-60+ dakika** sürebilir.", 
            icon="⏳"
        )
        
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
                                    opportunity['option_strike'] = recommended_call['strike']
                                    opportunity['option_price'] = recommended_call['lastPrice']
                                    opportunity['option_expiry'] = exp_date
                            except Exception:
                                pass # Opsiyon hatasını atla
                    
                    opportunities.append(opportunity)
                
                progress_text = f"Analiz Ediliyor: {ticker} ({i+1}/{total_tickers}) - Fırsatlar: {len(opportunities)}"
                progress_bar.progress((i + 1) / total_tickers, text=progress_text)
            
            progress_bar.empty()
            # ... (Sonuç gösterme kısmı aynı)

    # --- SEKME 2: DETAYLI HİSSE ANALİZİ (GÜNCELLENDİ) ---
    with tab2:
        st.header("İstediğiniz Hisseyi Derinlemesine İnceleyin")
        selected_display_name = st.selectbox('...', full_stock_list['display_name'], index=None, placeholder="...", key="single_stock_selector")
        
        if selected_display_name:
            selected_ticker = selected_display_name.split(' - ')[0]
            ticker_obj = get_ticker_with_retry(selected_ticker) # Korumalı fonksiyonu kullan
            
            if ticker_obj is None:
                st.error(f"{selected_ticker} için veri çekilemedi. Lütfen daha sonra tekrar deneyin.")
            else:
                data = get_stock_data(selected_ticker)
                # ... (Geri kalan tüm analiz kodları burada. Bu kısımda büyük bir değişiklik yok, sadece ticker_obj'nin korumalı fonksiyondan geldiğinden emin oluyoruz.)
                # ... (Kodun kısalığı için önceki versiyondan kopyalanabilir)

    # --- SEKME 3: PORTFÖY STRATEJİSTİ (GÜNCELLENDİ) ---
    with tab3:
        st.header("Kişisel Portföyünüz İçin AI Destekli Stratejiler")
        # ... (Bu sekmedeki yf.Ticker çağrıları da get_ticker_with_retry ile değiştirilmeli)
        # ... (Kodun kısalığı için önceki versiyondan kopyalanabilir)
