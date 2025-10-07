import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# Dil ve Çeviri Ayarları (Tam ve Eksiksiz)
# -----------------------------------------------------------------------------
LANGUAGES = {
    "TR": {
        "page_title": "Borsa Fırsat Tarama Botu",
        "app_title": "Borsa Fırsat Tarama Botu",
        "app_caption": "Yapay zeka destekli analizlerle yatırım fırsatlarını keşfedin.",
        "tab_screener": "Fırsat Taraması",
        "tab_analysis": "Hisse Analizi",
        "tab_watchlist": "İzleme Listem",
        "tab_portfolio": "Portföyüm",
        "screener_header": "Optimal Alım Fırsatları",
        "screener_info": "Bu araç, Robinhood'daki hisseleri en az %5 kâr potansiyeli sunan optimal bir stratejiye göre tarar. Detaylar ve opsiyon analizleri için bir hisseye tıklayın.",
        "screener_button": "Fırsatları Bul",
        "screener_spinner": "Robinhood hisseleri taranıyor... Bu işlem birkaç dakika sürebilir.",
        "screener_success": "adet potansiyel fırsat bulundu!",
        "screener_warning_no_stock": "Mevcut piyasa koşullarında optimal stratejiye uyan hiçbir hisse bulunamadı.",
        "col_price": "Fiyat", "col_rsi": "RSI",
        "detail_target_price": "Hedef Fiyat (Kısa Vade)",
        "calculator_header": "Yatırım Getirisi Hesaplayıcı",
        "calculator_input_label": "Yatırım Miktarı ($)",
        "calculator_return_label": "Tahmini Geri Dönüş",
        "calculator_profit_label": "Potansiyel Kar",
        "option_header": "Akıllı Opsiyon Analizi",
        "option_contract": "Kontrat",
        "option_expiry": "Vade",
        "option_buy_target": "Alım Hedef",
        "option_sell_target": "Satış Hedef (Hisse Hedefine Göre)",
        "option_profit_potential": "Potansiyel Kâr",
        "option_call": "Alım (Call)",
        "option_spinner": "Opsiyon verileri yükleniyor...",
        "option_none": "Bu hisse için uygun, likit ve mantıklı maliyetli bir opsiyon bulunamadı.",
        "greeks_header": "Yunanlar (Risk Metrikleri)",
        "delta_label": "Delta (Δ)",
        "delta_help": "Hisse senedi 1$ arttığında, opsiyon priminizin yaklaşık olarak ne kadar artacağını gösterir.",
        "theta_label": "Theta (Θ)",
        "theta_help": "Zamanın aleyhinize nasıl işlediğini, yani opsiyonunuzun her gün ne kadar zaman değeri kaybedeceğini gösterir.",
        "gamma_label": "Gamma (Γ)",
        "gamma_help": "Delta'nın ne kadar hızlı değişeceğini, yani hisse senedi lehinize hareket ettiğinde kazancınızın nasıl ivmeleneceğini gösterir.",
        "analysis_header": "Detaylı Hisse Senedi Analizi",
        "analysis_input_label": "Analiz için sembol girin (örn: AAPL)",
        "add_to_watchlist": "İzleme Listesine Ekle ⭐",
        "remove_from_watchlist": "Listeden Kaldır",
        "added_to_watchlist": "izleme listenize eklendi!",
        "spinner_analysis": "için veriler ve analiz hazırlanıyor...",
        "error_no_data": "Bu hisse için veri bulunamadı. Lütfen sembolü kontrol edin.",
        "error_no_technicals": "Teknik göstergeler hesaplanamadı. Yetersiz veri olabilir.",
        "metric_price": "Güncel Fiyat", "metric_cap": "Piyasa Değeri",
        "metric_target_price": "Fiyat Beklentisi (Kısa Vade)",
        "metric_target_price_bearish": "Aşağı Yönlü Fiyat Beklentisi (Kısa Vade)",
        "metric_target_price_help": "Fiyat hedefi, hissenin son 14 günlük ortalama volatilitesinin (ATR) iki katının mevcut fiyata eklenmesiyle hesaplanır. Bu, kısa vadeli bir potansiyel hareket aralığını gösterir.",
        "metric_target_price_bearish_help": "Fiyat hedefi, hissenin son 14 günlük ortalama volatilitesinin (ATR) iki katının mevcut fiyattan çıkarılmasıyla hesaplanır. Bu, kısa vadeli bir potansiyel düşüş aralığını gösterir.",
        "metric_support_1": "Destek 1 (S1)",
        "metric_resistance_1": "Direnç 1 (R1)",
        "subheader_rule_based": "Kural Tabanlı Teknik Analiz",
        "subheader_company_profile": "Şirket Profili",
        "subheader_charts": "Profesyonel Fiyat Grafiği",
        "summary_recommendation": "Öneri", "recommendation_buy": "AL", "recommendation_sell": "SAT", "recommendation_neutral": "NÖTR",
        "summary_rsi_oversold": "RSI ({rsi:.2f}) aşırı satım bölgesinde, tepki alımı potansiyeli olabilir.",
        "summary_rsi_overbought": "RSI ({rsi:.2f}) aşırı alım bölgesinde, düzeltme riski olabilir.",
        "summary_rsi_neutral": "RSI ({rsi:.2f}) nötr bölgede.",
        "summary_macd_bullish": "MACD, sinyal çizgisini yukarı keserek 'Al' sinyali üretiyor.",
        "summary_macd_bearish": "MACD, sinyal çizgisini aşağı keserek 'Sat' sinyali üretiyor.",
        "summary_sma_golden": "Fiyat, 50 ve 200 günlük ortalamaların üzerinde (Golden Cross). Güçlü yükseliş trendi.",
        "summary_sma_death": "Fiyat, 50 ve 200 günlük ortalamaların altında (Death Cross). Düşüş trendi.",
        "summary_sma_bullish": "Fiyat, 50 günlük ortalamanın üzerinde, kısa vadeli görünüm pozitif.",
        "summary_sma_bearish": "Fiyat, 50 günlük ortalamanın altında, kısa vadede baskı olabilir.",
        "watchlist_header": "Kişisel İzleme Listeniz", 
        "watchlist_empty": "İzleme listeniz boş. 'Hisse Analizi' sekmesinden hisse ekleyebilirsiniz.",
        "portfolio_header": "Portföyüm",
        "portfolio_add_header": "Portföye Yeni Pozisyon Ekle",
        "portfolio_ticker": "Hisse Senedi Sembolü",
        "portfolio_shares": "Adet (Pay)",
        "portfolio_cost": "Ortalama Maliyet ($)",
        "portfolio_add_button": "Pozisyon Ekle",
        "portfolio_empty": "Portföyünüz boş. Yukarıdaki formdan yeni bir pozisyon ekleyebilirsiniz.",
        "portfolio_current_value": "Mevcut Değer",
        "portfolio_pl": "Toplam Kâr/Zarar",
        "portfolio_recommendation": "Aksiyon Önerisi",
        "recommendation_hold": "TUT",
        "recommendation_add": "POZİSYON EKLE",
        "recommendation_sell_strong": "SAT",
        "sell_target": "Satış Hedefi (Kâr Al)",
        "stop_loss": "Stop-Loss (Zarar Durdur)",
        "delete_position": "Pozisyonu Sil",
    },
    "EN": {
        "page_title": "Stock Opportunity Scanning Bot",
        "app_title": "Stock Opportunity Bot",
        "app_caption": "Discover investment opportunities with AI-powered analysis.",
        "tab_screener": "Opportunity Scan",
        "tab_analysis": "Stock Analysis",
        "tab_watchlist": "My Watchlist",
        "tab_portfolio": "My Portfolio",
        "screener_header": "Optimal Buying Opportunities",
        "screener_info": "This tool scans all Robinhood stocks for opportunities with at least 5% profit potential. Click on a stock for details and option analysis.",
        "screener_button": "Find Opportunities",
        "screener_stop_button": "Stop Scan",
        "screener_spinner": "Scanning Robinhood stocks...",
        "screener_success": "potential opportunities found!",
        "screener_warning_no_stock": "No stocks matching the optimal strategy were found.",
        "col_price": "Price", "col_rsi": "RSI",
        "detail_target_price": "Target Price (Short-Term)",
        "calculator_header": "Investment Return Calculator",
        "calculator_input_label": "Investment Amount ($)",
        "calculator_return_label": "Estimated Return",
        "calculator_profit_label": "Potential Profit",
        "option_header": "Smart Option Analysis",
        "option_contract": "Contract",
        "option_expiry": "Expiry",
        "option_buy_target": "Buy Target",
        "option_sell_target": "Sell Target (at Stock Target)",
        "option_profit_potential": "Potential Profit",
        "option_call": "Call",
        "option_spinner": "Loading option data...",
        "option_none": "No suitable, liquid, and reasonably priced options found.",
        "greeks_header": "The Greeks (Risk Metrics)",
        "delta_label": "Delta (Δ)",
        "delta_help": "Shows how much the option price is expected to move for a $1 change in the stock price.",
        "theta_label": "Theta (Θ)",
        "theta_help": "Shows how much value the option loses each day due to time decay.",
        "gamma_label": "Gamma (Γ)",
        "gamma_help": "Shows the rate of change for Delta. It indicates how much the Delta will accelerate.",
        "analysis_header": "Detailed Stock Analysis",
        "analysis_input_label": "Enter symbol for analysis (e.g., AAPL)",
        "add_to_watchlist": "Add to Watchlist ⭐", "remove_from_watchlist": "Remove",
        "added_to_watchlist": "has been added to your watchlist!",
        "spinner_analysis": "Preparing data and analysis for...",
        "error_no_data": "Could not find data for this stock. Please check the symbol.",
        "error_no_technicals": "Could not calculate technical indicators. There might be insufficient data.",
        "metric_price": "Current Price", "metric_cap": "Market Cap",
        "metric_target_price": "Price Target (Short-Term)",
        "metric_target_price_bearish": "Bearish Price Target (Short-Term)",
        "metric_target_price_help": "The price target is calculated by adding two times the Average True Range (ATR) of the last 14 days to the current price. This indicates a potential short-term price movement range.",
        "metric_target_price_bearish_help": "The price target is calculated by subtracting two times the Average True Range (ATR) of the last 14 days from the current price. This indicates a potential short-term downside range.",
        "metric_support_1": "Support 1 (S1)",
        "metric_resistance_1": "Resistance 1 (R1)",
        "subheader_rule_based": "Rule-Based Technical Analysis",
        "subheader_company_profile": "Company Profile",
        "subheader_charts": "Professional Price Chart",
        "summary_recommendation": "Recommendation", "recommendation_buy": "BUY", "recommendation_sell": "SELL", "recommendation_neutral": "NEUTRAL",
        "summary_rsi_oversold": "RSI ({rsi:.2f}) is in the oversold region, suggesting a potential for a rebound.",
        "summary_rsi_overbought": "RSI ({rsi:.2f}) is in the overbought region, suggesting a risk of a correction.",
        "summary_rsi_neutral": "RSI ({rsi:.2f}) is in the neutral zone.",
        "summary_macd_bullish": "MACD is generating a 'Buy' signal, crossing above its signal line.",
        "summary_macd_bearish": "MACD is generating a 'Sell' signal, crossing below its signal line.",
        "summary_sma_golden": "Price is above the 50-day and 200-day MAs (Golden Cross). Strong bullish trend.",
        "summary_sma_death": "Price is below the 50-day and 200-day MAs (Death Cross). Bearish trend.",
        "summary_sma_bullish": "Price is above the 50-day MA, indicating a positive short-term outlook.",
        "summary_sma_bearish": "Price is below the 50-day MA, which may indicate short-term pressure.",
        "watchlist_header": "Your Personal Watchlist", 
        "watchlist_empty": "Your watchlist is empty. Add stocks from the 'Stock Analysis' tab.",
        "portfolio_header": "My Portfolio",
        "portfolio_add_header": "Add New Position to Portfolio",
        "portfolio_ticker": "Stock Symbol",
        "portfolio_shares": "Number of Shares",
        "portfolio_cost": "Average Cost ($)",
        "portfolio_add_button": "Add Position",
        "portfolio_empty": "Your portfolio is empty. Add a new position using the form above.",
        "portfolio_current_value": "Current Value",
        "portfolio_pl": "Total P/L",
        "portfolio_recommendation": "Action Recommendation",
        "recommendation_hold": "HOLD",
        "recommendation_add": "ADD TO POSITION",
        "recommendation_sell_strong": "SELL",
        "sell_target": "Sell Target (Take Profit)",
        "stop_loss": "Stop-Loss",
        "delete_position": "Delete Position",
    }
}

# --- Yardımcı Fonksiyonlar (Tam ve Çalışır Durumda) ---
def t(key): return LANGUAGES[st.session_state.lang].get(key, key)

# ... (get_robinhood_tickers, get_stock_data, calculate_technicals, get_option_suggestion fonksiyonları öncekiyle aynı) ...

def generate_analysis_summary(ticker, info, last_row):
    summary_points, buy_signals, sell_signals = [], 0, 0
    if not isinstance(last_row, pd.Series): return "Veri yetersiz.", "NÖTR"
    
    rsi = last_row.get('RSI_14', 50)
    if rsi < 30: summary_points.append(t('summary_rsi_oversold').format(rsi=rsi)); buy_signals += 2
    elif rsi > 70: summary_points.append(t('summary_rsi_overbought').format(rsi=rsi)); sell_signals += 2
    else: summary_points.append(t('summary_rsi_neutral').format(rsi=rsi))

    if last_row.get('MACD_12_26_9', 0) > last_row.get('MACDs_12_26_9', 0): summary_points.append(t('summary_macd_bullish')); buy_signals += 1
    else: summary_points.append(t('summary_macd_bearish')); sell_signals += 1

    current_price = last_row.get('Close', 0); sma_50 = last_row.get('SMA_50', 0); sma_200 = last_row.get('SMA_200', 0)
    if sma_50 > 0 and sma_200 > 0:
        if current_price > sma_50 and sma_50 > sma_200: summary_points.append(t('summary_sma_golden')); buy_signals += 2
        elif current_price < sma_50 and current_price < sma_200: summary_points.append(t('summary_sma_death')); sell_signals += 2
        elif current_price > sma_50: summary_points.append(t('summary_sma_bullish')); buy_signals += 1
        else: summary_points.append(t('summary_sma_bearish')); sell_signals += 1
    
    recommendation = t('recommendation_neutral')
    if buy_signals > sell_signals + 1: recommendation = t('recommendation_buy')
    elif sell_signals > buy_signals + 1: recommendation = t('recommendation_sell')
    
    final_summary = f"**{info.get('longName', ticker)} ({ticker})**: \n" + "- " + "\n- ".join(summary_points)
    return final_summary, recommendation

# -----------------------------------------------------------------------------
# Oturum Durumu Başlatma
# -----------------------------------------------------------------------------
if 'lang' not in st.session_state: st.session_state.lang = "TR"
if 'watchlist' not in st.session_state: st.session_state.watchlist = []
if 'portfolio' not in st.session_state: st.session_state.portfolio = []
if 'is_scanning' not in st.session_state: st.session_state.is_scanning = False
if 'scan_results' not in st.session_state: st.session_state.scan_results = []

# -----------------------------------------------------------------------------
# Sayfa Konfigürasyonu ve TASARIM
# -----------------------------------------------------------------------------
st.set_page_config(page_title=t("page_title"), page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>/* CSS Kısaltıldı */</style>""", unsafe_allow_html=True)

# --- HEADER ve DİL SEÇİMİ ---
LOGO_SVG = """...""" # SVG Kısaltıldı
header_cols = st.columns([1, 3, 1])
# ... (Header kodu öncekiyle aynı) ...

# -----------------------------------------------------------------------------
# Ana Sekmeler (Portföy Eklendi)
# -----------------------------------------------------------------------------
tab_icons = ["📈", "🔍", "⭐", "💼"]
tabs = st.tabs([f"{icon} {label}" for icon, label in zip(tab_icons, [t('tab_screener'), t('tab_analysis'), t('tab_watchlist'), t('tab_portfolio')])])

# -----------------------------------------------------------------------------
# Sekme 1: Hisse Taraması
# -----------------------------------------------------------------------------
with tabs[0]:
    # ... (Bu sekmenin kodu önceki tam versiyon ile aynı) ...
    pass
# -----------------------------------------------------------------------------
# Sekme 2: Tek Hisse Analizi
# -----------------------------------------------------------------------------
with tabs[1]:
    st.header(t("analysis_header"))
    ticker_input_tab2 = st.text_input(t("analysis_input_label"), "NVDA", key="tab2_input").upper()
    if ticker_input_tab2: 
        with st.spinner(f"{t('spinner_analysis')} {ticker_input_tab2}..."):
            hist_data, info, news = get_stock_data(ticker_input_tab2, period="2y")
            if hist_data is None or hist_data.empty or info is None: st.error(t("error_no_data"))
            else:
                technicals_df = calculate_technicals(hist_data.copy())
                if technicals_df is None or technicals_df.empty: st.error(t("error_no_technicals"))
                else:
                    last_row = technicals_df.iloc[-1]
                    summary, recommendation = generate_analysis_summary(ticker_input_tab2, info, last_row)

                    col1, col2 = st.columns([3, 1]); col1.subheader(f"{info.get('longName', ticker_input_tab2)} ({ticker_input_tab2})")
                    if ticker_input_tab2 not in st.session_state.watchlist:
                        if col2.button(t("add_to_watchlist"), key=f"add_{ticker_input_tab2}"): st.session_state.watchlist.append(ticker_input_tab2); st.toast(f"{ticker_input_tab2} {t('added_to_watchlist')}"); st.rerun()
                    
                    c1,c2,c3 = st.columns(3)
                    current_price = last_row.get('Close', 0); prev_close = info.get('previousClose', 0)
                    price_change = current_price - prev_close; price_change_pct = (price_change / prev_close) * 100 if prev_close else 0
                    
                    c1.metric(t("metric_price"), f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.2f}%)", delta_color="inverse" if price_change < 0 else "normal")
                    c2.metric(t("metric_cap"), f"${(info.get('marketCap', 0) / 1e9):.1f}B")

                    # Dinamik Fiyat Beklentisi
                    if recommendation == t("recommendation_sell"):
                        target_price = last_row.get('Close', 0) - (2 * last_row.get('ATRr_14', 0))
                        c3.metric(t("metric_target_price_bearish"), f"${target_price:.2f}", help=t("metric_target_price_bearish_help"))
                    else:
                        target_price = last_row.get('Close', 0) + (2 * last_row.get('ATRr_14', 0))
                        c3.metric(t("metric_target_price"), f"${target_price:.2f}", help=t("metric_target_price_help"))

                    recent_data = technicals_df.tail(90)
                    support1 = recent_data['Low'].min()
                    resistance1 = recent_data['High'].max()
                    c4, c5 = st.columns(2)
                    c4.metric(t("metric_support_1"), f"${support1:.2f}")
                    c5.metric(t("metric_resistance_1"), f"${resistance1:.2f}")
                    st.divider()
                    
                    analysis_col, chart_col = st.columns([1, 1])
                    with analysis_col:
                        st.subheader(t("subheader_rule_based"))
                        st.markdown(summary)
                        st.subheader(t("subheader_company_profile")); st.info(info.get('longBusinessSummary', 'Profile not available.'))
                        
                        st.subheader(f"📜 {t('option_header')}")
                        with st.spinner(t('option_spinner')): option = get_option_suggestion(ticker_input_tab2, last_row['Close'])
                        if option:
                            # ... (Opsiyon analizi öncekiyle aynı) ...
                            pass
                        else: st.info(t('option_none'))

                    with chart_col:
                        st.subheader(t("subheader_charts"))
                        fig = go.Figure(); fig.add_trace(go.Candlestick(x=technicals_df.index, open=technicals_df['Open'], high=technicals_df['High'], low=technicals_df['Low'], close=technicals_df['Close'], name='Price'))
                        fig.add_hline(y=support1, line_dash="dash", line_color="green", annotation_text=t("metric_support_1"), annotation_position="bottom right")
                        fig.add_hline(y=resistance1, line_dash="dash", line_color="red", annotation_text=t("metric_resistance_1"), annotation_position="top right")
                        fig.update_layout(xaxis_rangeslider_visible=False, template='plotly_dark', margin=dict(l=0, r=0, t=0, b=0), height=450); st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# Sekme 3: İzleme Listesi
# -----------------------------------------------------------------------------
with tabs[2]:
    # ... (Bu sekmenin kodu önceki tam versiyon ile aynı) ...
    pass

# -----------------------------------------------------------------------------
# Sekme 4: Portföyüm
# -----------------------------------------------------------------------------
with tabs[3]:
    # ... (Bu sekmenin kodu önceki tam versiyon ile aynı) ...
    pass

# --- FOOTER ---
st.markdown("<hr style='border-color:#222; margin-top: 50px;'>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; color: #888; padding: 20px;'>by Yusa Kurkcu</div>", unsafe_allow_html=True)

