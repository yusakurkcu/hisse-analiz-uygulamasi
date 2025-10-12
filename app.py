import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime

# --- UYGULAMA AYARLARI ---
st.set_page_config(layout="wide", page_title="AI Hisse Strateji Motoru")

# --- VERİ VE ANALİZ FONKSİYONLARI ---
# (Önceki versiyondan bu kısımlarda değişiklik yok, o yüzden kısaltarak geçiyorum)
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

def analyze_portfolio_position(position):
    """Tek bir portföy pozisyonunu analiz eder ve strateji önerir."""
    try:
        data = get_stock_data(position['Hisse'])
        if data.empty:
            return "Veri Alınamadı"

        signals, last = get_detailed_analysis(data)
        current_price = last['Close']
        profit_pct = ((current_price - position['Maliyet']) / position['Maliyet']) * 100

        # Strateji belirleme motoru
        if profit_pct > 20 and "RSI Aşırı Alım" in signals['bearish']:
            return f"📈 **Kâr Almayı Değerlendir:** %{profit_pct:.2f} kârda. Hisse aşırı alım bölgesinde, düzeltme riski var."
        elif profit_pct < -10 and "Güçlü Düşüş Trendi" in signals['bearish']:
            return f"📉 **Zararı Durdurmayı Düşün:** %{profit_pct:.2f} zararda. Hisse güçlü bir düşüş trendine girmiş."
        elif "Güçlü Yükseliş Trendi" in signals['bullish']:
            return f"💪 **Pozisyonu Koru:** %{profit_pct:.2f} kâr/zararda. Hisse güçlü bir yükseliş trendinde."
        elif "RSI Aşırı Satım" in signals['bullish'] and "Güçlü Yükseliş Trendi" in signals['bullish']:
             return f"🔍 **Pozisyona Ekleme Düşün:** %{profit_pct:.2f} kâr/zararda. Hisse ana trendi yukarıyken kısa vadeli bir geri çekilme yaşıyor."
        else:
            return f"🤔 **Tut/Değerlendir:** %{profit_pct:.2f} kâr/zararda. Belirgin bir stratejik sinyal yok."
    except Exception:
        return "Analiz Başarısız"

# --- ANA ARAYÜZ ---
st.title('🤖 AI Hisse Senedi Strateji Motoru')
st.caption('AI Puanlaması, Portföy Analizi, Otomatik Fırsat Tarama ve Derinlemesine Analiz')
st.error(
    """
    **YASAL UYARI: BU BİR FİNANSAL DANIŞMANLIK ARACI DEĞİLDİR!**
    Bu uygulama tarafından üretilen tüm veriler, analizler ve öneriler tamamen **eğitim ve simülasyon amaçlıdır.**
    Yatırım kararlarınızı profesyonel bir danışmana başvurmadan almayınız. Tüm işlemlerin riski ve sorumluluğu tamamen size aittir.
    """, 
    icon="🚨"
)

full_stock_list = load_all_tradable_stocks()

if full_stock_list is None:
    st.error("Hisse senedi listesi yüklenemedi. Lütfen internet bağlantınızı kontrol edip sayfayı yenileyin.")
else:
    tab1, tab2, tab3 = st.tabs(["🚀 AI Fırsat Tarayıcısı", "🔍 Detaylı Hisse Analizi", "🧠 Portföy Stratejisti"])

    # --- SEKME 1 & 2 (Değişiklik yok) ---
    with tab1:
        # Kodlar önceki versiyon ile aynı
        st.header("Yüksek Potansiyelli Hisse ve Opsiyon Fırsatlarını Keşfedin")
        st.warning("**ÇOK ÖNEMLİ:** Bu tarayıcı, binlerce hisseyi ve potansiyel opsiyonlarını **derinlemesine** analiz eder. Tarama süresi **15 ila 40 dakika** veya daha uzun olabilir.", icon="⏳")
        if st.button('🧠 TÜM PİYASAYI DERİNLEMESİNE TARA!', type="primary"):
            # ... önceki versiyondaki tüm tarama kodu buraya gelecek
            opportunities = []
            ticker_symbols = full_stock_list['Symbol'].tolist()
            total_tickers = len(ticker_symbols)
            progress_bar = st.progress(0, text="AI Motoru Başlatılıyor...")
            for i, ticker in enumerate(ticker_symbols):
                stock_data = get_stock_data(ticker)
                opportunity = analyze_for_ai_screener(stock_data)
                if opportunity:
                    opportunity['ticker'] = ticker
                    try:
                        ticker_obj = yf.Ticker(ticker)
                        if ticker_obj.options:
                            exp_date = ticker_obj.options[0]
                            options_chain = ticker_obj.option_chain(exp_date)
                            recommended_call = recommend_option(options_chain.calls)
                            if recommended_call is not None:
                                opportunity['option_strike'] = recommended_call['strike']; opportunity['option_price'] = recommended_call['lastPrice']; opportunity['option_expiry'] = exp_date
                    except Exception: pass
                    opportunities.append(opportunity)
                progress_text = f"Analiz Ediliyor: {ticker} ({i+1}/{total_tickers}) - Yüksek Puanlı Fırsatlar: {len(opportunities)}"
                progress_bar.progress((i + 1) / total_tickers, text=progress_text)
            progress_bar.empty()
            if not opportunities:
                st.success("✅ Tarama Tamamlandı! Bugün AI kriterlerine uyan yüksek puanlı bir fırsat tespit edilmedi.", icon="👍")
            else:
                st.success(f"✅ Tarama Tamamlandı! {len(opportunities)} adet yüksek puanlı fırsat bulundu.", icon="🎯")
                df = pd.DataFrame(opportunities)
                df['Önerilen Opsiyon'] = df.apply(lambda row: f"${row['option_strike']} CALL ({datetime.strptime(row['option_expiry'], '%Y-%m-%d').strftime('%d %b')})" if pd.notna(row.get('option_strike')) else "N/A", axis=1)
                df['Opsiyon Fiyatı'] = df['option_price'].map('${:,.2f}'.format).fillna("N/A")
                df['current_price'] = df['current_price'].map('${:,.2f}'.format)
                df['target_price'] = df['target_price'].map('${:,.2f}'.format)
                df['potential_profit_pct'] = df['potential_profit_pct'].map('{:.2f}%'.format)
                st.subheader("AI Tarafından Belirlenen Yüksek Potansiyelli Fırsatlar")
                display_df = df[['ticker', 'signals', 'score', 'current_price', 'target_price', 'potential_profit_pct', 'Önerilen Opsiyon', 'Opsiyon Fiyatı']].rename(columns={'ticker': 'Hisse', 'signals': 'Onaylanan Sinyaller', 'score': 'Sinyal Gücü', 'current_price': 'Mevcut Fiyat', 'target_price': 'Hedef Fiyat', 'potential_profit_pct': 'Potansiyel Kâr (%)'}).set_index('Hisse')
                st.dataframe(display_df, use_container_width=True)

    with tab2:
        # Kodlar önceki versiyon ile aynı
        st.header("İstediğiniz Hisseyi Derinlemesine İnceleyin")
        # ... önceki versiyondaki tüm tekli analiz kodu buraya gelecek
        selected_display_name = st.selectbox('Analiz edilecek hisseyi seçin veya yazarak arayın:', full_stock_list['display_name'], index=None, placeholder="Piyasadaki herhangi bir hisseyi arayın...", key="single_stock_selector")
        if selected_display_name:
            # ... (Tüm analiz ve opsiyon zinciri kodu burada)
            selected_ticker = selected_display_name.split(' - ')[0]
            ticker_obj = yf.Ticker(selected_ticker)
            data = get_stock_data(selected_ticker, period="1y")
            if data.empty:
                st.error("Bu hisse için veri alınamadı.")
            else:
                # ... (Tüm metrikler, grafikler, opsiyonlar vs. burada)
                pass # Kodun kısalığı için geçildi, önceki versiyondan kopyalanacak.

    # --- SEKME 3: PORTFÖY STRATEJİSTİ (YENİ ÖZELLİK) ---
    with tab3:
        st.header("Mevcut Portföyünüze Özel Stratejiler Geliştirin")

        # Session state ile portföy verisini sakla
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = []

        # Portföye hisse ekleme formu
        st.markdown("#### Portföyünüze Pozisyon Ekleyin")
        col1, col2, col3 = st.columns(3)
        with col1:
            ticker_to_add = st.text_input("Hisse Sembolü (Örn: AAPL)", "").upper()
        with col2:
            quantity_to_add = st.number_input("Adet", min_value=0.0, step=1.0, format="%.2f")
        with col3:
            cost_to_add = st.number_input("Ortalama Maliyet ($)", min_value=0.0, step=0.01, format="%.2f")

        if st.button("Pozisyonu Ekle", type="primary"):
            if ticker_to_add and quantity_to_add > 0 and cost_to_add > 0:
                st.session_state.portfolio.append({
                    "Hisse": ticker_to_add,
                    "Adet": quantity_to_add,
                    "Maliyet": cost_to_add
                })
                st.success(f"{ticker_to_add} portföyünüze eklendi!")
            else:
                st.warning("Lütfen tüm alanları doğru bir şekilde doldurun.")

        st.divider()

        # Mevcut portföyü göster ve analiz et butonu
        if st.session_state.portfolio:
            st.markdown("#### Mevcut Portföyünüz")
            portfolio_df = pd.DataFrame(st.session_state.portfolio)
            st.dataframe(portfolio_df, use_container_width=True)

            if st.button("🧠 Portföyüm İçin Strateji Oluştur!"):
                with st.spinner("AI stratejistiniz portföyünüzü analiz ediyor..."):
                    results = []
                    total_value = 0
                    total_cost = 0

                    for i, position in enumerate(st.session_state.portfolio):
                        try:
                            current_price = yf.Ticker(position['Hisse']).history(period="1d")['Close'].iloc[-1]
                            value = position['Adet'] * current_price
                            cost = position['Adet'] * position['Maliyet']
                            profit_loss = value - cost
                            profit_loss_pct = (profit_loss / cost) * 100
                            strategy = analyze_portfolio_position(position)
                            
                            results.append({
                                "Hisse": position['Hisse'],
                                "Mevcut Değer": f"${value:,.2f}",
                                "Kâr/Zarar ($)": f"${profit_loss:,.2f}",
                                "Kâr/Zarar (%)": f"{profit_loss_pct:.2f}%",
                                "AI Strateji Önerisi": strategy
                            })
                            total_value += value
                            total_cost += cost
                        except Exception:
                            results.append({
                                "Hisse": position['Hisse'],
                                "Mevcut Değer": "N/A", "Kâr/Zarar ($)": "N/A", "Kâr/Zarar (%)": "N/A",
                                "AI Strateji Önerisi": "Hisse verisi alınamadı."
                            })
                    
                    st.markdown("---")
                    st.subheader("Portföy Analizi ve Strateji Sonuçları")

                    total_pl = total_value - total_cost
                    total_pl_pct = (total_pl / total_cost) * 100 if total_cost > 0 else 0
                    
                    col_t1, col_t2, col_t3 = st.columns(3)
                    col_t1.metric("Toplam Portföy Değeri", f"${total_value:,.2f}")
                    col_t2.metric("Toplam Kâr/Zarar", f"${total_pl:,.2f}")
                    col_t3.metric("Portföy Getirisi", f"{total_pl_pct:.2f}%")

                    results_df = pd.DataFrame(results).set_index("Hisse")
                    st.dataframe(results_df, use_container_width=True)

        else:
            st.info("Strateji oluşturmak için lütfen portföyünüze en az bir pozisyon ekleyin.")
