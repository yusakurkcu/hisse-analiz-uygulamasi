import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

# -----------------------------------------------------------------------------
# Sayfa Yapılandırması
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NASDAQ Hisse Senedi Analiz Aracı",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# Veri Çekme ve Önbellekleme Fonksiyonları
# -----------------------------------------------------------------------------

# Veri çekme işlemlerini hızlandırmak için önbelleğe alma (caching) kullanılır.
@st.cache_data(ttl=300) # 5 dakika boyunca önbellekte tut
def get_stock_data(ticker, period="1y"):
    """Belirtilen hisse senedi için geçmiş verileri çeker."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    if hist.empty:
        return None
    return hist

@st.cache_data(ttl=3600) # 1 saat boyunca önbellekte tut
def get_stock_info(ticker):
    """Hisse senedi hakkında genel bilgileri ve takvimi çeker."""
    stock = yf.Ticker(ticker)
    return stock.info, stock.calendar

@st.cache_data(ttl=86400) # Günde bir kez çek
def get_risk_free_rate():
    """Risksiz faiz oranını (ABD 10 Yıllık Hazine Tahvili) çeker."""
    try:
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="5d")
        # Son kapanış değerini alıp 100'e bölerek ondalık formata çevir
        return hist['Close'].iloc[-1] / 100
    except:
        # Hata olursa varsayılan bir değer döndür
        return 0.04 

@st.cache_data(ttl=300) # 5 dakika boyunca önbellekte tut
def get_option_chain(ticker):
    """Hisse senedinin opsiyon zincirini çeker."""
    stock = yf.Ticker(ticker)
    try:
        exp_dates = stock.options
        if not exp_dates:
            return None, None, None
        
        # Analiz için en az 25 gün sonrası ilk vadeyi seç
        valid_dates = [d for d in exp_dates if (datetime.strptime(d, '%Y-%m-%d') - datetime.now()).days > 25]
        if not valid_dates:
            return None, None, None
            
        options = stock.option_chain(valid_dates[0])
        # Serileştirilebilir DataFrame'leri ve tarihi döndür
        return options.calls, options.puts, valid_dates[0]
    except Exception:
        return None, None, None

# -----------------------------------------------------------------------------
# Analiz Fonksiyonları
# -----------------------------------------------------------------------------

def calculate_technical_indicators(df):
    """Teknik göstergeleri hesaplar: MA, RSI, MACD."""
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # RSI Hesaplaması
    delta_rsi = df['Close'].diff()
    gain = (delta_rsi.where(delta_rsi > 0, 0)).rolling(window=14).mean()
    loss = (-delta_rsi.where(delta_rsi < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD Hesaplaması
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def find_support_resistance(df):
    """Basit pivot noktalarına dayalı destek ve direnç seviyelerini bulur."""
    support_levels = []
    resistance_levels = []
    
    # Son 6 aydaki veriyi kullan
    recent_df = df.tail(180)
    
    for i in range(5, len(recent_df) - 5):
        # Destek (Yerel Minimum)
        if recent_df['Low'][i] < min(recent_df['Low'][i-5:i+6]):
            support_levels.append(recent_df['Low'][i])
        # Direnç (Yerel Maksimum)
        if recent_df['High'][i] > max(recent_df['High'][i-5:i+6]):
            resistance_levels.append(recent_df['High'][i])
            
    # Son fiyata en yakın 2 seviyeyi al
    current_price = recent_df['Close'].iloc[-1]
    
    closest_support = min([s for s in support_levels if s < current_price], key=lambda x: abs(x-current_price)) if any(s < current_price for s in support_levels) else None
    closest_resistance = min([r for r in resistance_levels if r > current_price], key=lambda x: abs(x-current_price)) if any(r > current_price for r in resistance_levels) else None
    
    return closest_support, closest_resistance


def analyze_buying_opportunity(df, info):
    """Kullanıcının belirttiği kriterlere göre alım fırsatını analiz eder."""
    signals = []
    score = 0
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    # 1. Teknik Analiz Sinyalleri
    if last_row['RSI'] < 35 and last_row['RSI'] > prev_row['RSI']:
        signals.append("✅ RSI aşırı satım bölgesinden (<30) yukarı dönüyor.")
        score += 2
    elif last_row['RSI'] < 50:
        signals.append("⚠️ RSI 50'nin altında, zayıf momentum.")
    else:
        signals.append("👍 RSI 50'nin üzerinde, pozitif momentum.")
        score += 1
        
    if last_row['MA20'] > last_row['MA50'] and prev_row['MA20'] < prev_row['MA50']:
        signals.append("✅ Golden Cross (20 Günlük > 50 Günlük) sinyali oluştu.")
        score += 2
    elif last_row['MA20'] > last_row['MA50']:
        signals.append("👍 Kısa vadeli ortalama (20) uzun vadelinin (50) üzerinde.")
        score += 1
        
    if last_row['Volume'] > df['Volume'].rolling(window=20).mean().iloc[-1] * 1.5:
        signals.append("✅ Son işlem gününde hacim ortalamanın üzerinde, ilgi artıyor.")
        score += 1
        
    # 2. Temel Analiz Sinyalleri
    pe_ratio = info.get('trailingPE')
    if pe_ratio is not None:
        if pe_ratio < 20:
            signals.append(f"👍 F/K Oranı ({pe_ratio:.2f}) makul seviyede.")
            score += 1
        elif pe_ratio < 40:
            signals.append(f"⚠️ F/K Oranı ({pe_ratio:.2f}) sektör ortalamalarına göre değerlendirilmeli.")
        else:
            signals.append(f"❌ F/K Oranı ({pe_ratio:.2f}) yüksek, primli olabilir.")
            score -= 1
        
    debt_to_equity = info.get('debtToEquity')
    if debt_to_equity is not None:
        if debt_to_equity < 50: # % olarak
            signals.append(f"👍 Düşük borçluluk oranı (Borç/Özkaynak: {debt_to_equity/100:.2%}).")
            score += 1
        elif debt_to_equity > 150:
            signals.append(f"❌ Yüksek borçluluk oranı (Borç/Özkaynak: {debt_to_equity/100:.2%}).")
            score -=1

    # Sonuç
    if score >= 5:
        result = ("GÜÇLÜ ALIM FIRSATI", "success")
    elif score >= 3:
        result = ("ALIM FIRSATI OLABİLİR", "success")
    elif score >= 1:
        result = ("NÖTR / İZLEMEDE", "info")
    else:
        result = ("RİSKLİ / UZAK DUR", "warning")
        
    return result, signals


def calculate_greeks_for_chain(df, current_price, exp_date, risk_free_rate):
    """Opsiyon zinciri için Yunan harflerini hesaplar."""
    if df is None or df.empty:
        return df

    # Vadeye kalan süreyi yıl cinsinden hesapla
    time_to_expiry = (datetime.strptime(exp_date, '%Y-%m-%d') - datetime.now()).days / 365.25
    if time_to_expiry <= 0: time_to_expiry = 0.0001 # Sıfır veya negatif olmasını engelle

    # Yunan harflerini hesapla
    df['delta'] = df.apply(lambda row: delta('c', current_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    df['gamma'] = df.apply(lambda row: gamma('c', current_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    df['theta'] = df.apply(lambda row: theta('c', current_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    df['vega'] = df.apply(lambda row: vega('c', current_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    
    return df


def analyze_option_suitability(df, calls_df, info, risk_free_rate, exp_date):
    """Call opsiyonu alımına uygunluğu analiz eder."""
    if calls_df is None or calls_df.empty:
        return ("Opsiyon verisi bulunamadı.", "warning"), [], "", None
        
    signals = []
    score = 0
    last_row = df.iloc[-1]
    current_price = last_row['Close']

    # --- Yunan Harflerini Hesapla ---
    try:
        calls_df = calculate_greeks_for_chain(calls_df, current_price, exp_date, risk_free_rate)
    except Exception as e:
        st.warning(f"Yunan harfleri hesaplanırken bir sorun oluştu: {e}")

    # 1. Trend ve Momentum
    if last_row['MA20'] > last_row['MA50']:
        signals.append("✅ Yükseliş Trendi (20MA > 50MA).")
        score += 2
    else:
        signals.append("❌ Düşüş Trendi (20MA < 50MA), Call için uygun değil.")
        return ("Call Alımı İçin Riskli", "error"), signals, "", None

    if last_row['RSI'] > 55:
        signals.append(f"✅ Güçlü Momentum (RSI: {last_row['RSI']:.2f}).")
        score += 1
    else:
        signals.append(f"⚠️ Zayıf Momentum (RSI: {last_row['RSI']:.2f}).")
    
    if last_row['MACD'] > last_row['Signal_Line']:
        signals.append("✅ MACD pozitif sinyal veriyor.")
        score += 1
        
    # 2. Opsiyon Zinciri Analizi
    calls = calls_df
    
    # Fiyata en yakın (At-the-money) kontratları bul
    atm_calls = calls.iloc[(calls['strike'] - current_price).abs().argsort()[:5]]
    
    avg_oi = atm_calls['openInterest'].mean()
    avg_volume = atm_calls['volume'].mean()
    
    if avg_oi > 100 and avg_volume > 50:
        signals.append(f"✅ Opsiyonlar likit (Ort. Açık Pozisyon: {avg_oi:.0f}, Ort. Hacim: {avg_volume:.0f}).")
        score += 1
    else:
        signals.append("❌ Opsiyonlar yeterince likit değil, spreadler geniş olabilir.")
        score -= 2
        
    avg_iv = atm_calls['impliedVolatility'].mean()
    if avg_iv < 0.6: # %60
        signals.append(f"👍 Implied Volatility (IV) makul seviyede ({avg_iv:.2%}), primler şişkin değil.")
        score += 1
    else:
        signals.append(f"⚠️ IV yüksek ({avg_iv:.2%}), primler pahalı olabilir.")

    # Sonuç
    if score >= 5:
        result = ("CALL OPSİYONU İÇİN UYGUN", "success")
    elif score >= 3:
        result = ("Call Opsiyonu Değerlendirilebilir", "info")
    else:
        result = ("Call Alımı İçin Riskli", "warning")
        
    # Uygun kontrat önerisi
    suggestion = ""
    if result[1] in ["success", "info"] and 'delta' in calls.columns:
        # Delta'sı 0.5 - 0.75 arasına en yakın ve en likit olanı seç
        suitable_contracts = calls[(calls['delta'] >= 0.5) & (calls['delta'] <= 0.75)].sort_values(by='openInterest', ascending=False)
        if not suitable_contracts.empty:
            best_contract = suitable_contracts.iloc[0]
            suggestion = (f"**Öneri:** {best_contract['strike']}$ kullanım fiyatlı (Strike) kontrat değerlendirilebilir. "
                          f"(Delta: {best_contract['delta']:.2f}, IV: {best_contract['impliedVolatility']:.2%})")
        else:
             suggestion = "**Bilgi:** İstenen Delta (0.5-0.75) aralığında likit bir kontrat bulunamadı."
            
    # Hata vermemesi için gösterilecek kolonları mevcut olanlar arasından seç
    display_cols = ['strike', 'lastPrice', 'delta', 'gamma', 'theta', 'vega', 'impliedVolatility', 'volume', 'openInterest']
    existing_cols_in_atm = [col for col in display_cols if col in atm_calls.columns]
    
    return result, signals, suggestion, atm_calls[existing_cols_in_atm] if not atm_calls.empty else None


# -----------------------------------------------------------------------------
# Grafik Çizim Fonksiyonu
# -----------------------------------------------------------------------------

def plot_stock_chart(df, ticker, support, resistance):
    """Paylaşılan hisse senedi için bir grafik oluşturur."""
    fig = go.Figure()

    # Fiyat Mumu Grafiği
    fig.add_trace(go.Candlestick(x=df.index,
                               open=df['Open'],
                               high=df['High'],
                               low=df['Low'],
                               close=df['Close'],
                               name='Fiyat'))

    # Hareketli Ortalamalar
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', name='20 Günlük MA', line=dict(color='blue', width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='50 Günlük MA', line=dict(color='orange', width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], mode='lines', name='200 Günlük MA', line=dict(color='red', width=2)))

    # Destek ve Direnç Seviyeleri
    if support:
        fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text=f"Destek: {support:.2f}", annotation_position="bottom right")
    if resistance:
        fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text=f"Direnç: {resistance:.2f}", annotation_position="top right")

    fig.update_layout(
        title=f'{ticker} Fiyat Grafiği ve Teknik Göstergeler',
        yaxis_title='Fiyat (USD)',
        xaxis_title='Tarih',
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500
    )
    return fig

# -----------------------------------------------------------------------------
# Streamlit Arayüzü
# -----------------------------------------------------------------------------

st.title("📈 NASDAQ Hisse Senedi Analiz Aracı")
st.markdown("""
Bu araç, NASDAQ'da işlem gören hisse senetleri için teknik, temel ve opsiyon analizleri sunar. 
Hisse senedi sembolünü girin (örn: `AAPL`, `TSLA`, `NVDA`) ve 'Analiz Et' butonuna tıklayın.
""")
st.info("**Not:** Bu uygulama bir yatırım tavsiyesi değildir. Yalnızca eğitim ve bilgilendirme amaçlıdır. Finansal kararlarınızı vermeden önce profesyonel bir danışmana başvurun.", icon="ℹ️")


col1, col2 = st.columns([1, 4])
with col1:
    ticker_input = st.text_input("Hisse Senedi Sembolü:", "NVDA").upper()
with col2:
    st.write("") # Boşluk için
    st.write("")
    analyze_button = st.button("Analiz Et", type="primary", use_container_width=True)


if analyze_button:
    if not ticker_input:
        st.warning("Lütfen bir hisse senedi sembolü girin.")
    else:
        with st.spinner(f"{ticker_input} verileri çekiliyor ve analiz ediliyor... Lütfen bekleyin."):
            try:
                hist_data = get_stock_data(ticker_input)
                
                if hist_data is None or hist_data.empty:
                    st.error(f"'{ticker_input}' için veri bulunamadı. Lütfen sembolü kontrol edin.")
                else:
                    info, calendar = get_stock_info(ticker_input)
                    calls_df, puts_df, exp_date = get_option_chain(ticker_input)
                    risk_free_rate = get_risk_free_rate()
                    
                    # Analizler
                    hist_data = calculate_technical_indicators(hist_data)
                    support, resistance = find_support_resistance(hist_data)
                    
                    buy_analysis, buy_signals = analyze_buying_opportunity(hist_data, info)
                    option_analysis, option_signals, option_suggestion, option_df = analyze_option_suitability(hist_data, calls_df, info, risk_free_rate, exp_date)

                    # --- SONUÇLARI GÖSTER ---
                    st.header(f"{info.get('longName', ticker_input)} ({ticker_input}) Analizi")
                    
                    # Genel Bakış
                    price_info, summary, analysis_col = st.columns([1,1,2])
                    
                    with price_info:
                        current_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
                        prev_close = info.get('previousClose', hist_data['Close'].iloc[-2])
                        price_change = current_price - prev_close
                        percent_change = (price_change / prev_close) * 100
                        st.metric("Güncel Fiyat", f"${current_price:.2f}", f"{price_change:+.2f} ({percent_change:+.2f}%)")

                    with summary:
                        market_cap = info.get('marketCap', 0)
                        st.metric("Piyasa Değeri", f"${market_cap / 1_000_000_000:.2f} Milyar")

                    with analysis_col:
                        st.subheader("Genel Alım Fırsatı Değerlendirmesi")
                        st.markdown(f"**Sonuç:** <span style='color:{'green' if buy_analysis[1]=='success' else 'orange'}; font-size: 1.2em;'>{buy_analysis[0]}</span>", unsafe_allow_html=True)

                    st.markdown("---")

                    # Detaylı Analiz Sekmeleri
                    tab1, tab2, tab3 = st.tabs(["📊 Teknik Analiz", "🏢 Temel Analiz", "⛓️ Opsiyon Analizi"])

                    with tab1:
                        st.plotly_chart(plot_stock_chart(hist_data, ticker_input, support, resistance), use_container_width=True)
                        st.subheader("Teknik Sinyaller")
                        for signal in buy_signals:
                            if "✅" in signal or "👍" in signal:
                                st.markdown(f"<p style='color:green;'>{signal}</p>", unsafe_allow_html=True)
                            elif "⚠️" in signal:
                                st.markdown(f"<p style='color:orange;'>{signal}</p>", unsafe_allow_html=True)
                            else:
                                st.write(signal)

                    with tab2:
                        st.subheader("Şirket Profili ve Temel Veriler")
                        col_prof1, col_prof2 = st.columns(2)
                        with col_prof1:
                            st.write(f"**Sektör:** {info.get('sector', 'N/A')}")
                            st.write(f"**Endüstri:** {info.get('industry', 'N/A')}")
                            pe = info.get('trailingPE')
                            st.write(f"**F/K Oranı:** {pe:.2f}" if pe else "N/A")
                            div_yield = info.get('dividendYield')
                            st.write(f"**Temettü Verimi:** {div_yield * 100:.2f}%" if div_yield else "N/A")
                        with col_prof2:
                            beta = info.get('beta')
                            st.write(f"**Beta:** {beta:.2f}" if beta else "N/A")
                            low = info.get('fiftyTwoWeekLow')
                            high = info.get('fiftyTwoWeekHigh')
                            st.write(f"**52 Haftalık Aralık:** ${low:.2f} - ${high:.2f}" if low and high else "N/A")
                            d_to_e = info.get('debtToEquity')
                            st.write(f"**Borç/Özkaynak:** {d_to_e:.2f}" if d_to_e else "N/A")

                        st.subheader("Yaklaşan Etkinlikler")
                        if calendar is not None and 'Earnings Date' in calendar and not calendar['Earnings Date'].empty:
                             st.write(f"**Bilanço Açıklama Tarihi:** {calendar['Earnings Date'][0].strftime('%Y-%m-%d')}")
                        else:
                            st.write("Yakın zamanda bir etkinlik bulunmuyor.")
                            
                    with tab3:
                        st.subheader("Call Opsiyonu Alım Uygunluğu")
                        st.markdown(f"**Sonuç:** <span style='color:{'green' if option_analysis[1]=='success' else 'orange'}; font-size: 1.2em;'>{option_analysis[0]}</span>", unsafe_allow_html=True)
                        if exp_date:
                            st.write(f"_(Vade Tarihi: {exp_date} için analiz edilmiştir.)_")
                        
                        st.subheader("Opsiyon Sinyalleri")
                        for signal in option_signals:
                             if "✅" in signal or "👍" in signal:
                                st.markdown(f"<p style='color:green;'>{signal}</p>", unsafe_allow_html=True)
                             else:
                                st.markdown(f"<p style='color:orange;'>{signal}</p>", unsafe_allow_html=True)

                        if option_suggestion:
                            st.success(option_suggestion)
                        
                        if option_df is not None:
                            st.subheader("Fiyata Yakın Call Opsiyonları (Hesaplanan Yunan Harfleriyle)")
                            st.dataframe(option_df.set_index('strike').style.format({
                                'lastPrice': '{:.2f}',
                                'delta': '{:.3f}',
                                'gamma': '{:.3f}',
                                'theta': '{:.3f}',
                                'vega': '{:.3f}',
                                'impliedVolatility': '{:.2%}',
                            }))


            except Exception as e:
                st.error(f"Bir hata oluştu: {e}. Lütfen hisse senedi sembolünü kontrol edin veya daha sonra tekrar deneyin.")

