import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega
from py_vollib.black_scholes import black_scholes as bs

# --- Streamlit Sayfa Yapılandırması ---
st.set_page_config(
    page_title="Hisse Senedi Analiz Aracı",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Stil Tanımlamaları ---
st.markdown("""
<style>
    .stMetric {
        border-radius: 10px;
        padding: 15px;
        background-color: #262730;
        border: 1px solid #262730;
    }
    .stMetric .st-ae {
        font-size: 1.1em;
        font-weight: bold;
        color: #fafafa;
    }
    .stMetric .st-af {
        font-size: 1.5em;
        font-weight: bold;
    }
    /* Risk seviyeleri için renkler */
    .risk-low { color: #28a745; }
    .risk-medium { color: #ffc107; }
    .risk-high { color: #dc3545; }
</style>
""", unsafe_allow_html=True)


# --- ÖNBELLEKLEME FONKSİYONLARI ---
@st.cache_data(ttl=300) # 5 dakika önbellekle
def get_stock_data(ticker):
    """Belirtilen hisse için geçmiş verileri çeker."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y") # Son 1 yıllık veri
        if hist.empty:
            return None
        return hist
    except Exception as e:
        st.error(f"Veri çekilirken bir hata oluştu: {e}")
        return None

@st.cache_data(ttl=300)
def get_stock_info(ticker):
    """Hisse senedi hakkında genel bilgileri çeker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        calendar = stock.calendar
        return info, calendar
    except Exception:
        return None, None

@st.cache_data(ttl=300)
def get_option_chain(ticker):
    """Hisse senedi için opsiyon zincirini çeker."""
    try:
        stock = yf.Ticker(ticker)
        exp_dates = stock.options
        if not exp_dates:
            return None, None, None
        
        # En yakın ve en az 30 gün sonrası vade tarihini bul
        today = datetime.now().date()
        valid_dates = [d for d in exp_dates if (datetime.strptime(d, '%Y-%m-%d').date() - today).days >= 30]
        if not valid_dates:
             # Eğer 30 gün sonrası yoksa en yakın vadeyi al
            exp_date = exp_dates[0]
        else:
            exp_date = valid_dates[0]

        options = stock.option_chain(exp_date)
        return options.calls, options.puts, exp_date
    except Exception:
        return None, None, None

@st.cache_data(ttl=3600) # 1 saat önbellekle
def get_risk_free_rate():
    """Risksiz faiz oranını (ABD 10 Yıllık Hazine) çeker."""
    try:
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="5d")
        if not hist.empty:
            return hist['Close'].iloc[-1] / 100
    except Exception:
        pass
    return 0.04 # Fallback değeri

# --- ANALİZ FONKSİYONLARI ---
def add_technical_indicators(df):
    """DataFrame'e teknik göstergeleri ekler."""
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

def find_support_resistance(df):
    """Daha gelişmiş pivot noktalarına dayalı destek ve direnç seviyelerini bulur."""
    support_levels = []
    resistance_levels = []
    
    recent_df = df.tail(180) # Son 6 ay
    
    if len(recent_df) < 11:
        return None, None

    for i in range(5, len(recent_df) - 5):
        if recent_df['Low'][i] <= min(recent_df['Low'][i-5:i+6]):
            support_levels.append(recent_df['Low'][i])
        if recent_df['High'][i] >= max(recent_df['High'][i-5:i+6]):
            resistance_levels.append(recent_df['High'][i])
            
    current_price = recent_df['Close'].iloc[-1]
    
    valid_supports = list(set([s for s in support_levels if s < current_price]))
    valid_resistances = list(set([r for r in resistance_levels if r > current_price]))
    
    closest_support = None
    closest_resistance = None

    if valid_supports:
        closest_support = max(valid_supports)
    else:
        low_of_period = recent_df['Low'].min()
        if low_of_period < current_price:
            closest_support = low_of_period

    if valid_resistances:
        closest_resistance = min(valid_resistances)
    else:
        high_of_period = recent_df['High'].max()
        if high_of_period > current_price:
            closest_resistance = high_of_period
        
    return closest_support, closest_resistance

def calculate_greeks(df, stock_price, risk_free_rate, exp_date_str, option_type='c'):
    """Opsiyonlar için Yunan harflerini Black-Scholes modeli ile hesaplar."""
    if df is None or df.empty:
        return df

    today = datetime.now().date()
    exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d').date()
    time_to_expiry = (exp_date - today).days / 365.0

    if time_to_expiry <= 0: return df # Vadesi geçmişse hesaplama yapma

    required_cols = ['strike', 'impliedVolatility']
    if not all(col in df.columns for col in required_cols):
        return df

    df['delta'] = df.apply(lambda row: delta(option_type, stock_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    df['gamma'] = df.apply(lambda row: gamma(option_type, stock_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    df['theta'] = df.apply(lambda row: theta(option_type, stock_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    df['vega'] = df.apply(lambda row: vega(option_type, stock_price, row['strike'], time_to_expiry, risk_free_rate, row['impliedVolatility']), axis=1)
    
    return df

def analyze_buying_opportunity(df, info):
    """Kullanıcının belirttiği kriterlere göre alım fırsatını analiz eder."""
    signals = []
    score = 0
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    # 1. RSI
    if last_row['RSI'] > 30 and prev_row['RSI'] <= 30:
        signals.append("✅ RSI aşırı satım bölgesinden yukarı döndü.")
        score += 2
    elif last_row['RSI'] < 30:
        signals.append("⚠️ RSI aşırı satım bölgesinde, dönüş bekleniyor.")
        score += 1
    else:
        signals.append("➖ RSI nötr veya aşırı alım bölgesinde.")

    # 2. Golden Cross (MA20 vs MA50)
    if last_row['MA20'] > last_row['MA50'] and prev_row['MA20'] <= prev_row['MA50']:
        signals.append("✅ Golden Cross sinyali oluştu (MA20, MA50'yi yukarı kesti).")
        score += 2
    elif last_row['MA20'] > last_row['MA50']:
        signals.append("➖ Kısa vadeli ortalama, uzun vadelinin üzerinde (Pozitif).")
        score += 1
    else:
        signals.append("➖ Death Cross aktif (MA20, MA50'nin altında).")

    # 3. Hacim Artışı
    if last_row['Volume'] > df['Volume'].rolling(window=20).mean().iloc[-1] and last_row['Close'] > prev_row['Close']:
        signals.append("✅ Yükseliş, ortalamanın üzerinde bir hacimle destekleniyor.")
        score += 1
    else:
        signals.append("➖ Hacim, yükselişi belirgin şekilde desteklemiyor.")

    # 4. F/K Oranı
    pe_ratio = info.get('trailingPE')
    if pe_ratio and pe_ratio < 20:
        signals.append(f"✅ F/K oranı ({pe_ratio:.2f}) makul seviyede, hisse ucuz olabilir.")
        score += 1
    elif pe_ratio:
        signals.append(f"⚠️ F/K oranı ({pe_ratio:.2f}) yüksek, beklentiler fiyatlanmış olabilir.")
    else:
         signals.append("➖ F/K oranı verisi bulunamadı.")

    # 5. Borçluluk
    d_to_e = info.get('debtToEquity')
    if d_to_e is not None and d_to_e < 100: # %100'den az ise iyi kabul edelim
        signals.append(f"✅ Borç/Özkaynak oranı ({d_to_e:.2f}) sağlıklı seviyede.")
        score += 1
    elif d_to_e is not None:
        signals.append(f"⚠️ Borç/Özkaynak oranı ({d_to_e:.2f}) yüksek, risk unsuru olabilir.")
    else:
        signals.append("➖ Borçluluk verisi bulunamadı.")
    
    # Sonuç
    if score >= 5:
        return ("Güçlü Alım Fırsatı", "success", signals)
    elif score >= 3:
        return ("Potansiyel Alım Fırsatı", "success", signals)
    else:
        return ("Alım İçin Henüz Erken", "warning", signals)

def analyze_option_suitability(df_hist, df_options, info, risk_free_rate, exp_date_str, option_type='call'):
    """Call veya Put opsiyonu alımına uygunluğu analiz eder."""
    signals = []
    suggestion = "Spesifik kontrat önerisi yapılamıyor."
    
    if df_options is None or df_options.empty:
        return "Opsiyon verisi bulunamadı.", signals, suggestion, None

    last_row = df_hist.iloc[-1]
    current_price = last_row['Close']

    # Yunan harflerini hesapla
    df_options = calculate_greeks(df_options, current_price, risk_free_rate, exp_date_str, 'c' if option_type == 'call' else 'p')

    # Genel Trend ve Momentum Analizi
    is_bullish = last_row['MA20'] > last_row['MA50'] and last_row['RSI'] > 50 and last_row['MACD'] > last_row['Signal_Line']
    is_bearish = last_row['MA20'] < last_row['MA50'] and last_row['RSI'] < 50 and last_row['MACD'] < last_row['Signal_Line']

    if option_type == 'call':
        if is_bullish:
            signals.append("✅ Hisse, kısa ve orta vadeli yükseliş trendinde.")
        else:
            signals.append("❌ Hisse, Call alımı için uygun bir yükseliş trendinde değil.")
    else: # Put
        if is_bearish:
            signals.append("✅ Hisse, kısa ve orta vadeli düşüş trendinde.")
        else:
            signals.append("❌ Hisse, Put alımı için uygun bir düşüş trendinde değil.")
    
    # Opsiyon Zinciri Analizi
    df_options['liquidity_score'] = df_options['openInterest'].fillna(0) + df_options['volume'].fillna(0)
    if df_options['liquidity_score'].sum() > 1000:
        signals.append("✅ Opsiyon zincirinde yeterli likidite mevcut.")
    else:
        signals.append("⚠️ Opsiyon zincirinde likidite düşük, alım/satım zor olabilir.")

    # Sonuç ve Kontrat Önerisi
    analysis_result = "N/A"
    
    # Fiyata en yakın (At-the-Money) kontratları bul
    if option_type == 'call':
        atm_options = df_options[df_options['strike'] >= current_price].sort_values(by='strike').head(5)
    else: # Put
        atm_options = df_options[df_options['strike'] <= current_price].sort_values(by='strike', ascending=False).head(5)

    if not atm_options.empty:
        # En likit olanı seç
        best_option = atm_options.sort_values(by='liquidity_score', ascending=False).iloc[0]
        
        strike = best_option['strike']
        last_price = best_option['lastPrice']
        oi = best_option['openInterest']

        if option_type == 'call' and is_bullish:
            analysis_result = f"Yükseliş beklentisiyle **Call Opsiyonu** düşünülebilir."
            suggestion = f"**Öneri:** Vadesi **{exp_date_str}** olan, **${strike:.2f} kullanım fiyatlı** Call kontratı incelenebilir. (Son Fiyat: ${last_price:.2f}, Açık Pozisyon: {oi:.0f})"
        elif option_type == 'put' and is_bearish:
            analysis_result = f"Düşüş beklentisiyle **Put Opsiyonu** düşünülebilir."
            suggestion = f"**Öneri:** Vadesi **{exp_date_str}** olan, **${strike:.2f} kullanım fiyatlı** Put kontratı incelenebilir. (Son Fiyat: ${last_price:.2f}, Açık Pozisyon: {oi:.0f})"
        else:
            analysis_result = f"Mevcut trend, **{option_type.capitalize()} Opsiyonu** alımını desteklemiyor."
            suggestion = "Bu yönde bir işlem için daha uygun koşullar beklenmeli."

    # Gösterilecek sütunları seç
    display_cols = ['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility', 'delta', 'gamma', 'theta', 'vega']
    existing_cols = [col for col in display_cols if col in df_options.columns]
    
    return analysis_result, signals, suggestion, df_options[existing_cols]


# --- ANA UYGULAMA ARAYÜZÜ ---
st.title("📈 Profesyonel Hisse Senedi Analiz Aracı")
st.sidebar.header("Hisse Senedi Seçimi")
ticker_input = st.sidebar.text_input("NASDAQ Hisse Senedi Sembolünü Girin (örn: AAPL, NVDA, TSLA)", "NVDA").upper()

if ticker_input:
    # Verileri Çek
    hist_data = get_stock_data(ticker_input)
    
    if hist_data is None:
        st.error("Hisse senedi sembolünü kontrol edin veya daha sonra tekrar deneyin.")
    else:
        info, calendar = get_stock_info(ticker_input)
        calls_df, puts_df, exp_date = get_option_chain(ticker_input)
        risk_free_rate = get_risk_free_rate()
        
        # Analizleri Yap
        hist_data = add_technical_indicators(hist_data)
        support, resistance = find_support_resistance(hist_data)
        buy_analysis = analyze_buying_opportunity(hist_data, info)
        
        # --- SONUÇLARI GÖSTER ---
        st.header(f"{info.get('longName', ticker_input)} ({ticker_input}) Analizi")
        
        # Genel Bakış ve Ticaret Planı
        col_main, col_plan = st.columns([2, 1.5])

        with col_main:
            col_price, col_market, col_risk = st.columns(3)
            current_price = info.get('currentPrice', hist_data['Close'].iloc[-1])
            prev_close = info.get('previousClose', hist_data['Close'].iloc[-2])
            price_change = current_price - prev_close
            percent_change = (price_change / prev_close) * 100
            col_price.metric("Güncel Fiyat", f"${current_price:.2f}", f"{price_change:+.2f} ({percent_change:+.2f}%)")

            market_cap = info.get('marketCap', 0)
            col_market.metric("Piyasa Değeri", f"${market_cap / 1_000_000_000:.2f} Milyar")

            beta = info.get('beta')
            risk_level = "Orta"
            risk_color = "risk-medium"
            if beta:
                if beta < 1.0:
                    risk_level = "Düşük"
                    risk_color = "risk-low"
                elif beta > 1.5:
                    risk_level = "Yüksek"
                    risk_color = "risk-high"
            col_risk.markdown(f"**Risk Seviyesi**<br><span class='{risk_color}' style='font-size: 1.5em; font-weight:bold;'>{risk_level}</span>", unsafe_allow_html=True)

        with col_plan:
            st.markdown("**Ticaret Planı Önerisi**")
            entry = f"${current_price:.2f}"
            stop = f"${support:.2f}" if support else "N/A"
            target = f"${resistance:.2f}" if resistance else "N/A"
            
            rr_ratio = "N/A"
            if support and resistance and (current_price - support) > 0:
                potential_gain = resistance - current_price
                potential_loss = current_price - support
                ratio = potential_gain / potential_loss
                rr_ratio = f"{ratio:.2f} : 1"

            st.markdown(f"""
            - **Giriş:** <span style='color: white;'>{entry}</span>
            - **Zarar Durdur (Stop):** <span style='color: #dc3545;'>{stop}</span>
            - **Kâr Al (Hedef):** <span style='color: #28a745;'>{target}</span>
            - **Kazanç/Risk Oranı:** <span style='color: white;'>{rr_ratio}</span>
            """, unsafe_allow_html=True)
        
        st.subheader("Genel Alım Fırsatı Değerlendirmesi", divider='rainbow')
        st.markdown(f"**Sonuç:** <span style='color:{'#28a745' if buy_analysis[1]=='success' else '#ffc107'}; font-size: 1.2em;'>{buy_analysis[0]}</span>", unsafe_allow_html=True)
        with st.expander("Detaylı Sinyalleri Gör"):
            for signal in buy_analysis[2]:
                st.markdown(f"- {signal}")

        st.markdown("---")

        # Detaylı Analiz Sekmeleri
        tab1, tab2, tab3 = st.tabs(["📊 Teknik Analiz", "🏢 Temel Analiz", "⛓️ Opsiyon Analizi"])
        
        with tab1:
            st.subheader("Fiyat Grafiği ve Teknik Göstergeler")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            # Ana Fiyat Grafiği
            fig.add_trace(go.Candlestick(x=hist_data.index,
                                         open=hist_data['Open'], high=hist_data['High'],
                                         low=hist_data['Low'], close=hist_data['Close'], name='Fiyat'), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA20'], mode='lines', name='MA20', line=dict(color='yellow', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['MA50'], mode='lines', name='MA50', line=dict(color='orange', width=1)), row=1, col=1)
            
            # Destek ve Direnç Çizgileri
            if support:
                fig.add_hline(y=support, line_dash="dash", line_color="green", annotation_text=f"Destek ${support:.2f}", row=1, col=1)
            if resistance:
                fig.add_hline(y=resistance, line_dash="dash", line_color="red", annotation_text=f"Direnç ${resistance:.2f}", row=1, col=1)
            
            # RSI Grafiği
            fig.add_trace(go.Scatter(x=hist_data.index, y=hist_data['RSI'], mode='lines', name='RSI'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig.update_layout(
                title=f'{ticker_input} Fiyat Grafiği',
                xaxis_rangeslider_visible=False,
                height=600,
                template='plotly_dark'
            )
            fig.update_yaxes(title_text="Fiyat ($)", row=1, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Şirket Bilgileri ve Temel Veriler")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Sektör:** {info.get('sector', 'N/A')}")
                st.markdown(f"**Endüstri:** {info.get('industry', 'N/A')}")
                st.markdown(f"**Ülke:** {info.get('country', 'N/A')}")
                st.markdown(f"**Website:** {info.get('website', 'N/A')}")
                st.markdown("**İş Tanımı:**")
                st.info(info.get('longBusinessSummary', 'N/A'))
            
            with col2:
                st.markdown("**Finansal Metrikler:**")
                pe = info.get('trailingPE')
                st.write(f"**Fiyat/Kazanç (F/K):** {pe:.2f}" if pe else "N/A")
                pb = info.get('priceToBook')
                st.write(f"**Piyasa Değeri/Defter Değeri (PD/DD):** {pb:.2f}" if pb else "N/A")
                ps = info.get('priceToSalesTrailing12Months')
                st.write(f"**Fiyat/Satışlar:** {ps:.2f}" if ps else "N/A")
                
                low = info.get('fiftyTwoWeekLow')
                high = info.get('fiftyTwoWeekHigh')
                st.write(f"**52 Haftalık Aralık:** ${low:.2f} - ${high:.2f}" if low and high else "N/A")
                d_to_e = info.get('debtToEquity')
                st.write(f"**Borç/Özkaynak:** {d_to_e/100:.2f}" if d_to_e else "N/A")

                st.subheader("Yaklaşan Etkinlikler")
                earnings_date_found = False
                if calendar is not None:
                    if isinstance(calendar, dict):
                        if 'Earnings Date' in calendar and calendar['Earnings Date']:
                            earnings_date = calendar['Earnings Date'][0]
                            st.write(f"**Bilanço Açıklama Tarihi:** {earnings_date.strftime('%Y-%m-%d')}")
                            earnings_date_found = True
                    elif isinstance(calendar, pd.DataFrame):
                        if 'Earnings Date' in calendar.columns and not calendar['Earnings Date'].dropna().empty:
                            earnings_date = calendar['Earnings Date'].dropna().iloc[0]
                            st.write(f"**Bilanço Açıklama Tarihi:** {earnings_date.strftime('%Y-%m-%d')}")
                            earnings_date_found = True
                
                if not earnings_date_found:
                    st.write("Yakın zamanda bir etkinlik bulunmuyor.")
                    
        with tab3:
            st.subheader("Opsiyon Zinciri Analizi")
            
            if exp_date:
                st.info(f"Analiz, **{exp_date}** vadeli opsiyonlar için yapılmıştır.")
                
                # Call Opsiyon Analizi
                st.markdown("#### Yükseliş Beklentisi (Call Opsiyonu)")
                call_analysis, call_signals, call_suggestion, call_df_display = analyze_option_suitability(hist_data, calls_df, info, risk_free_rate, exp_date, 'call')
                st.markdown(f"**Durum:** {call_analysis}")
                for signal in call_signals:
                    st.markdown(f"- {signal}")
                st.success(call_suggestion)
                
                st.markdown("---")

                # Put Opsiyon Analizi
                st.markdown("#### Düşüş Beklentisi (Put Opsiyonu)")
                put_analysis, put_signals, put_suggestion, put_df_display = analyze_option_suitability(hist_data, puts_df, info, risk_free_rate, exp_date, 'put')
                st.markdown(f"**Durum:** {put_analysis}")
                for signal in put_signals:
                    st.markdown(f"- {signal}")
                st.warning(put_suggestion)
                
                st.markdown("---")
                
                # Opsiyon Zinciri DataFrame'leri
                with st.expander("Detaylı Opsiyon Zincirini Görüntüle"):
                    col_call, col_put = st.columns(2)
                    with col_call:
                        st.markdown("##### Call Opsiyonları")
                        st.dataframe(call_df_display.style.format(precision=2))
                    with col_put:
                        st.markdown("##### Put Opsiyonları")
                        st.dataframe(put_df_display.style.format(precision=2))
            else:
                st.warning("Bu hisse senedi için opsiyon verisi bulunamadı.")
else:
    st.info("Lütfen analiz etmek için soldaki menüden bir hisse senedi sembolü girin.")

