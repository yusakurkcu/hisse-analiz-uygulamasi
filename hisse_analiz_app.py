import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import locale

# Türkçe tarih formatlaması için yerel ayarı ayarla
try:
    # 'tr_TR.UTF-8' çoğu Linux sisteminde çalışır
    locale.setlocale(locale.LC_TIME, 'tr_TR.UTF-8')
except locale.Error:
    try:
        # Windows için alternatif
        locale.setlocale(locale.LC_TIME, 'turkish')
    except locale.Error:
        # Ayarlanamazsa, sistem varsayılanını kullanır (genellikle İngilizce)
        pass

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
    """NASDAQ borsasında işlem gören hisselerin tam listesini çeker."""
    # Bu liste, NASDAQ tarafından sağlanan halka açık verilerden oluşturulmuştur.
    # Test hisseleri ve yfinance ile uyumsuz olabilecek semboller filtrelenmiştir.
    tickers = [
        'AACG', 'AACI', 'AACIU', 'AACIW', 'AADR', 'AAL', 'AALG', 'AAME', 'AAOI', 'AAON', 'AAPB', 'AAPD', 'AAPG', 'AAPL', 'AAPU',
        'AARD', 'AAUS', 'AAVM', 'AAXJ', 'ABAT', 'ABCL', 'ABCS', 'ABEO', 'ABI', 'ABIG', 'ABL', 'ABLV', 'ABLVW', 'ABNB', 'ABOS',
        'ABP', 'ABPWW', 'ABSI', 'ABTC', 'ABTS', 'ABUS', 'ABVC', 'ABVE', 'ABVEW', 'ABVX', 'ACAD', 'ACB', 'ACDC', 'ACET', 'ACFN',
        'ACGL', 'ACGLN', 'ACGLO', 'ACHC', 'ACHV', 'ACIC', 'ACIU', 'ACIW', 'ACLS', 'ACLX', 'ACMR', 'ACNB', 'ACNT', 'ACOG', 'ACON',
        'ACONW', 'ACRS', 'ACRV', 'ACT', 'ACTG', 'ACTU', 'ACWI', 'ACWX', 'ACXP', 'ADAG', 'ADAM', 'ADAP', 'ADBE', 'ADBG', 'ADEA',
        'ADGM', 'ADI', 'ADIL', 'ADMA', 'ADN', 'ADNWW', 'ADP', 'ADPT', 'ADSE', 'ADSEW', 'ADSK', 'ADTN', 'ADTX', 'ADUR', 'ADUS',
        'ADV', 'ADVB', 'ADVM', 'ADVWW', 'ADXN', 'AEBI', 'AEC', 'AEHL', 'AEHR', 'AEI', 'AEIS', 'AEMD', 'AENT', 'AENTW', 'AEP',
        'AERT', 'AERTW', 'AEVA', 'AEVAW', 'AEYE', 'AFBI', 'AFCG', 'AFJK', 'AFJKR', 'AFJKU', 'AFOS', 'AFRI', 'AFRIW', 'AFRM',
        'AFSC', 'AFYA', 'AGAE', 'AGEM', 'AGEN', 'AGGA', 'AGH', 'AGIO', 'AGIX', 'AGMH', 'AGMI', 'AGNC', 'AGNCL', 'AGNCM', 'AGNCN',
        'AGNCO', 'AGNCP', 'AGNCZ', 'AGNG', 'AGRI', 'AGRZ', 'AGYS', 'AGZD', 'AHCO', 'AHG', 'AIA', 'AIFD', 'AIFF', 'AIFU', 'AIHS',
        'AIIO', 'AIIOW', 'AIMD', 'AIMDW', 'AIOT', 'AIP', 'AIPI', 'AIPO', 'AIQ', 'AIRE', 'AIRG', 'AIRJ', 'AIRJW', 'AIRO', 'AIRR',
        'AIRS', 'AIRT', 'AIRTP', 'AISP', 'AISPW', 'AIXI', 'AKAM', 'AKAN', 'AKBA', 'AKRO', 'AKTX', 'ALAB', 'ALAR', 'ALBT', 'ALCO',
        'ALCY', 'ALCYU', 'ALCYW', 'ALDF', 'ALDFU', 'ALDFW', 'ALDX', 'ALEC', 'ALF', 'ALFUU', 'ALFUW', 'ALGM', 'ALGN', 'ALGS',
        'ALGT', 'ALHC', 'ALIL', 'ALKS', 'ALKT', 'ALLO', 'ALLR', 'ALLT', 'ALLW', 'ALM', 'ALMS', 'ALMU', 'ALNT', 'ALNY', 'ALOT',
        'ALRM', 'ALRS', 'ALT', 'ALTI', 'ALTO', 'ALTS', 'ALTY', 'ALVO', 'ALVOW', 'ALXO', 'ALZN', 'AMAL', 'AMAT', 'AMBA', 'AMBR',
        'AMCX', 'AMD', 'AMDD', 'AMDG', 'AMDL', 'AMDU', 'AMGN', 'AMID', 'AMIX', 'AMKR', 'AMLX', 'AMOD', 'AMODW', 'AMPG', 'AMPGW',
        'AMPH', 'AMPL', 'AMRK', 'AMRN', 'AMRX', 'AMSC', 'AMSF', 'AMST', 'AMTX', 'AMUU', 'AMWD', 'AMYY', 'AMZD', 'AMZN', 'AMZU',
        'AMZZ', 'ANAB', 'ANDE', 'ANEB', 'ANEL', 'ANGH', 'ANGHW', 'ANGI', 'ANGL', 'ANGO', 'ANIK', 'ANIP', 'ANIX', 'ANL', 'ANNA',
        'ANNAW', 'ANNX', 'ANPA', 'ANSC', 'ANSCU', 'ANSCW', 'ANTA', 'ANTX', 'ANY', 'AOHY', 'AOSL', 'AOTG', 'AOUT', 'APA', 'APACU',
        'APAD', 'APADR', 'APADU', 'APED', 'APEI', 'APGE', 'API', 'APLD', 'APLM', 'APLMW', 'APLS', 'APLT', 'APM', 'APOG', 'APP',
        'APPF', 'APPN', 'APPS', 'APPX', 'APRE', 'APVO', 'APWC', 'APYX', 'AQB', 'AQMS', 'AQST', 'AQWA', 'ARAI', 'ARAY', 'ARBB',
        'ARBE', 'ARBEW', 'ARBK', 'ARBKL', 'ARCB', 'ARCC', 'ARCT', 'ARDX', 'AREB', 'AREBW', 'AREC', 'ARGX', 'ARHS', 'ARKO',
        'ARKOW', 'ARKR', 'ARLP', 'ARM', 'ARMG', 'AROW', 'ARQ', 'ARQQ', 'ARQQW', 'ARQT', 'ARRY', 'ARTL', 'ARTNA', 'ARTV', 'ARTW',
        'ARVN', 'ARVR', 'ARWR', 'ASBP', 'ASBPW', 'ASET', 'ASLE', 'ASMB', 'ASMG', 'ASML', 'ASND', 'ASNS', 'ASO', 'ASPC', 'ASPCR',
        'ASPCU', 'ASPI', 'ASPS', 'ASPSW', 'ASPSZ', 'ASRT', 'ASRV', 'ASST', 'ASTC', 'ASTE', 'ASTH', 'ASTI', 'ASTL', 'ASTLW',
        'ASTS', 'ASUR', 'ASYS', 'ATAI', 'ATAT', 'ATEC', 'ATER', 'ATEX', 'ATGL', 'ATHA', 'ATHE', 'ATHR', 'ATII', 'ATIIU', 'ATIIW',
        'ATLC', 'ATLCL', 'ATLCP', 'ATLCZ', 'ATLN', 'ATLO', 'ATLX', 'ATMC', 'ATMCR', 'ATMCU', 'ATMCW', 'ATMV', 'ATMVR', 'ATMVU',
        'ATNI', 'ATOM', 'ATON', 'ATOS', 'ATPC', 'ATRA', 'ATRC', 'ATRO', 'ATXG', 'ATXS', 'ATYR', 'AUBN', 'AUDC', 'AUGO', 'AUID',
        'AUMI', 'AUPH', 'AUR', 'AURA', 'AUROW', 'AUTL', 'AUUD', 'AUUDW', 'AVAH', 'AVAV', 'AVBH', 'AVBP', 'AVDL', 'AVDX', 'AVGB',
        'AVGG', 'AVGO', 'AVGU', 'AVGX', 'AVIR', 'AVL', 'AVNW', 'AVO', 'AVPT', 'AVR', 'AVS', 'AVT', 'AVTX', 'AVUQ', 'AVXC', 'AVXL',
        'AWRE', 'AXGN', 'AXIN', 'AXINR', 'AXINU', 'AXON', 'AXSM', 'AXTI', 'AYTU', 'AZ', 'AZI', 'AZN', 'AZTA', 'AZYY', 'BABX',
        'BACC', 'BACCR', 'BACCU', 'BACQ', 'BACQR', 'BACQU', 'BAER', 'BAERW', 'BAFE', 'BAFN', 'BAIG', 'BAND', 'BANF', 'BANFP',
        'BANL', 'BANR', 'BANX', 'BAOS', 'BASG', 'BASV', 'BATRA', 'BATRK', 'BAYA', 'BAYAR', 'BAYAU', 'BBB', 'BBCP', 'BBGI', 'BBH',
        'BBIO', 'BBLG', 'BBLGW', 'BBNX', 'BBOT', 'BBSI', 'BCAB', 'BCAL', 'BCAR', 'BCARU', 'BCARW', 'BCAX', 'BCBP', 'BCDA', 'BCG',
        'BCGWW', 'BCIC', 'BCLO', 'BCML', 'BCPC', 'BCRX', 'BCTX', 'BCTXW', 'BCTXZ', 'BCYC', 'BDCIU', 'BDGS', 'BDMD', 'BDMDW',
        'BDRX', 'BDSX', 'BDTX', 'BDVL', 'BDYN', 'BEAG', 'BEAGR', 'BEAGU', 'BEAM', 'BEAT', 'BEATW', 'BEEM', 'BEEP', 'BEEX', 'BEEZ',
        'BELFA', 'BELFB', 'BELT', 'BENF', 'BENFW', 'BETR', 'BETRW', 'BFC', 'BFIN', 'BFRG', 'BFRGW', 'BFRI', 'BFRIW', 'BFST',
        'BGC', 'BGL', 'BGLC', 'BGLWW', 'BGM', 'BGMS', 'BGMSP', 'BGRN', 'BGRO', 'BHAT', 'BHF', 'BHFAL', 'BHFAM', 'BHFAN', 'BHFAO',
        'BHFAP', 'BHRB', 'BHST', 'BIAF', 'BIAFW', 'BIB', 'BIDU', 'BIIB', 'BILI', 'BINI', 'BIOA', 'BIOX', 'BIRD', 'BIS', 'BITF',
        'BITS', 'BIVI', 'BIVIW', 'BIYA', 'BJDX', 'BJK', 'BJRI', 'BKCH', 'BKHA', 'BKHAR', 'BKHAU', 'BKNG', 'BKR', 'BKYI', 'BL',
        'BLBD', 'BLBX', 'BLCN', 'BLCR', 'BLDP', 'BLFS', 'BLFY', 'BLIN', 'BLIV', 'BLKB', 'BLMN', 'BLMZ', 'BLNE', 'BLNK', 'BLRX',
        'BLTE', 'BLUW', 'BLUWU', 'BLUWW', 'BLZE', 'BLZRU', 'BMAX', 'BMBL', 'BMDL', 'BMEA', 'BMGL', 'BMHL', 'BMR', 'BMRA', 'BMRC',
        'BMRN', 'BNAI', 'BNAIW', 'BNBX', 'BNC', 'BNCWW', 'BND', 'BNDW', 'BNDX', 'BNGO', 'BNR', 'BNRG', 'BNTC', 'BNTX', 'BNZI',
        'BNZIW', 'BODI', 'BOED', 'BOEG', 'BOEU', 'BOF', 'BOKF', 'BOLD', 'BOLT', 'BON', 'BOOM', 'BOSC', 'BOTJ', 'BOTT', 'BOTZ',
        'BOWN', 'BOWNR', 'BOWNU', 'BOXL', 'BPOP', 'BPOPM', 'BPRN', 'BPYPM', 'BPYPN', 'BPYPO', 'BPYPP', 'BRAG', 'BRBI', 'BRCB',
        'BRFH', 'BRHY', 'BRID', 'BRKD', 'BRKR', 'BRKRP', 'BRKU', 'BRLS', 'BRLSW', 'BRLT', 'BRNS', 'BRNY', 'BRR', 'BRRR', 'BRRWU',
        'BRRWW', 'BRTR', 'BRTX', 'BRY', 'BRZE', 'BSAA', 'BSAAR', 'BSAAU', 'BSBK', 'BSCP', 'BSCQ', 'BSCR', 'BSCS', 'BSCT', 'BSCU',
        'BSCV', 'BSCW', 'BSCX', 'BSCY', 'BSCZ', 'BSET', 'BSJP', 'BSJQ', 'BSJR', 'BSJS', 'BSJT', 'BSJU', 'BSJV', 'BSJW', 'BSJX',
        'BSLK', 'BSLKW', 'BSMP', 'BSMQ', 'BSMR', 'BSMS', 'BSMT', 'BSMU', 'BSMV', 'BSMW', 'BSMY', 'BSMZ', 'BSRR', 'BSSX', 'BSVN',
        'BSVO', 'BSY', 'BTAI', 'BTBD', 'BTBDW', 'BTBT', 'BTCS', 'BTCT', 'BTDR', 'BTF', 'BTFX', 'BTGD', 'BTM', 'BTMD', 'BTMWW',
        'BTOC', 'BTOG', 'BTQ', 'BTSG', 'BTSGU', 'BTTC', 'BUFC', 'BUFI', 'BUFM', 'BUG', 'BULD', 'BULG', 'BULL', 'BULLW', 'BULX',
        'BUSE', 'BUSEP', 'BUUU', 'BVFL', 'BVS', 'BWAY', 'BWB', 'BWBBP', 'BWEN', 'BWFG', 'BWIN', 'BWMN', 'BYFC', 'BYND', 'BYRN',
        'BYSI', 'BZ', 'BZAI', 'BZAIW', 'BZFD', 'BZFDW', 'BZUN', 'CA', 'CAAS', 'CABA', 'CAC', 'CACC', 'CADL', 'CAEP', 'CAFG',
        'CAI', 'CAKE', 'CALC', 'CALI', 'CALM', 'CAMP', 'CAMT', 'CAN', 'CANC', 'CANQ', 'CAPN', 'CAPNR', 'CAPNU', 'CAPR', 'CAPS',
        'CAPT', 'CAPTW', 'CAR', 'CARE', 'CARG', 'CARL', 'CARM', 'CART', 'CARV', 'CARY', 'CARZ', 'CASH', 'CASI', 'CASS', 'CASY',
        'CATH', 'CATY', 'CBAT', 'CBFV', 'CBIO', 'CBK', 'CBLL', 'CBNK', 'CBRL', 'CBSH', 'CBUS', 'CCAP', 'CCB', 'CCBG', 'CCCC',
        'CCCS', 'CCCX', 'CCCXU', 'CCCXW', 'CCD', 'CCEC', 'CCEP', 'CCFE', 'CCG', 'CCGWW', 'CCHH', 'CCII', 'CCIIU', 'CCIIW', 'CCIX',
        'CCIXU', 'CCIXW', 'CCLD', 'CCLDO', 'CCNE', 'CCNEP', 'CCNR', 'CCOI', 'CCRN', 'CCSB', 'CCSI', 'CCSO', 'CCTG', 'CDC', 'CDIG',
        'CDIO', 'CDIOW', 'CDL', 'CDLX', 'CDNA', 'CDNS', 'CDRO', 'CDROW', 'CDT', 'CDTG', 'CDTTW', 'CDTX', 'CDW', 'CDXS', 'CDZI',
        'CDZIP', 'CECO', 'CEFA', 'CEG', 'CELC', 'CELH', 'CELU', 'CELUW', 'CELZ', 'CENN', 'CENT', 'CENTA', 'CENX', 'CEP', 'CEPF',
        'CEPI', 'CEPO', 'CEPT', 'CERO', 'CEROW', 'CERS', 'CERT', 'CETX', 'CETY', 'CEVA', 'CFA', 'CFBK', 'CFFI', 'CFFN', 'CFLT',
        'CFO', 'CFSB', 'CG', 'CGABL', 'CGBD', 'CGBDL', 'CGC', 'CGCT', 'CGCTU', 'CGCTW', 'CGEM', 'CGEN', 'CGNT', 'CGNX', 'CGO',
        'CGON', 'CGTL', 'CGTX', 'CHA', 'CHAC', 'CHACR', 'CHACU', 'CHAI', 'CHAR', 'CHARR', 'CHARU', 'CHCI', 'CHCO', 'CHDN',
        'CHECU', 'CHEF', 'CHEK', 'CHGX', 'CHI', 'CHKP', 'CHMG', 'CHNR', 'CHPG', 'CHPGR', 'CHPGU', 'CHPS', 'CHPX', 'CHR', 'CHRD',
        'CHRI', 'CHRS', 'CHRW', 'CHSCL', 'CHSCM', 'CHSCN', 'CHSCO', 'CHSCP', 'CHSN', 'CHTR', 'CHW', 'CHY', 'CHYM', 'CIBR',
        'CIFR', 'CIFRW', 'CIGI', 'CIGL', 'CIIT', 'CIL', 'CINF', 'CING', 'CINGW', 'CISO', 'CISS', 'CIVB', 'CJET', 'CJMB', 'CLAR',
        'CLBK', 'CLBT', 'CLDX', 'CLFD', 'CLGN', 'CLIK', 'CLIR', 'CLLS', 'CLMB', 'CLMT', 'CLNE', 'CLNN', 'CLNNW', 'CLOA', 'CLOD',
        'CLOU', 'CLOV', 'CLPS', 'CLPT', 'CLRB', 'CLRO', 'CLSD', 'CLSK', 'CLSKW', 'CLSM', 'CLST', 'CLWT', 'CLYM', 'CMBM', 'CMCO',
        'CMCSA', 'CMCT', 'CME', 'CMMB', 'CMND', 'CMPOW', 'CMPR', 'CMPS', 'CMPX', 'CMRC', 'CMTL', 'CNCK', 'CNCKW', 'CNDT', 'CNET',
        'CNEY', 'CNOB', 'CNOBP', 'CNQQ', 'CNSP', 'CNTA', 'CNTB', 'CNTX', 'CNTY', 'CNVS', 'CNXC', 'CNXN', 'COCH', 'COCHW', 'COCO',
        'COCP', 'CODA', 'CODX', 'COEP', 'COEPW', 'COFS', 'COGT', 'COHU', 'COIG', 'COIN', 'COKE', 'COLA', 'COLAR', 'COLAU',
        'COLB', 'COLL', 'COLM', 'COMM', 'COMT', 'CONI', 'CONL', 'COO', 'COOT', 'COOTW', 'COPJ', 'COPP', 'CORO', 'CORT', 'CORZ',
        'CORZW', 'CORZZ', 'COSM', 'COST', 'COTG', 'COWG', 'COWS', 'COYA', 'COYY', 'CPAG', 'CPB', 'CPBI', 'CPHC', 'CPHY', 'CPIX',
        'CPLS', 'CPOP', 'CPRT', 'CPRX', 'CPSH', 'CPSS', 'CPZ', 'CRAI', 'CRAQ', 'CRAQR', 'CRAQU', 'CRBP', 'CRBU', 'CRCG', 'CRCT',
        'CRDF', 'CRDL', 'CRDO', 'CRE', 'CREG', 'CRESW', 'CRESY', 'CREV', 'CREVW', 'CREX', 'CRGO', 'CRGOW', 'CRIS', 'CRMD', 'CRMG',
        'CRML', 'CRMLW', 'CRMT', 'CRNC', 'CRNT', 'CRNX', 'CRON', 'CROX', 'CRSP', 'CRSR', 'CRTO', 'CRUS', 'CRVL', 'CRVO', 'CRVS',
        'CRWD', 'CRWG', 'CRWL', 'CRWS', 'CRWV', 'CSAI', 'CSB', 'CSBR', 'CSCL', 'CSCO', 'CSCS', 'CSGP', 'CSGS', 'CSIQ', 'CSPI',
        'CSQ', 'CSTE', 'CSTL', 'CSWC', 'CSWCZ', 'CSX', 'CTAS', 'CTBI', 'CTEC', 'CTKB', 'CTLP', 'CTMX', 'CTNM', 'CTNT', 'CTOR',
        'CTRM', 'CTRN', 'CTSH', 'CTSO', 'CTW', 'CTXR', 'CUB', 'CUBWU', 'CUBWW', 'CUE', 'CUPR', 'CURI', 'CURIW', 'CURR', 'CURX',
        'CV', 'CVAC', 'CVBF', 'CVCO', 'CVGI', 'CVGW', 'CVKD', 'CVLT', 'CVNX', 'CVRX', 'CVV', 'CWBC', 'CWCO', 'CWD', 'CWST',
        'CXAI', 'CXAIW', 'CXDO', 'CXSE', 'CYBR', 'CYCN', 'CYCU', 'CYCUW', 'CYN', 'CYRX', 'CYTK', 'CZAR', 'CZFS', 'CZNC', 'CZR',
        'CZWI', 'DAAQ', 'DAAQU', 'DAAQW', 'DADS', 'DAIC', 'DAICW', 'DAIO', 'DAK', 'DAKT', 'DALI', 'DAPP', 'DARE', 'DASH', 'DAVE',
        'DAVEW', 'DAWN', 'DAX', 'DBGI', 'DBVT', 'DBX', 'DCBO', 'DCGO', 'DCOM', 'DCOMG', 'DCOMP', 'DCTH', 'DDI', 'DDIV', 'DDOG',
        'DECO', 'DEFT', 'DEMZ', 'DENN', 'DERM', 'DEVS', 'DFDV', 'DFGP', 'DFGX', 'DFLI', 'DFLIW', 'DFSC', 'DFSCW', 'DGCB', 'DGICA',
        'DGICB', 'DGII', 'DGLO', 'DGLY', 'DGNX', 'DGRE', 'DGRS', 'DGRW', 'DGXX', 'DH', 'DHAI', 'DHAIW', 'DHC', 'DHCNI', 'DHCNL',
        'DHIL', 'DIBS', 'DIME', 'DIOD', 'DIVD', 'DJCO', 'DJT', 'DJTWW', 'DKI', 'DKNG', 'DKNX', 'DLHC', 'DLLL', 'DLO', 'DLPN',
        'DLTH', 'DLTR', 'DLXY', 'DMAA', 'DMAAR', 'DMAAU', 'DMAC', 'DMAT', 'DMIIU', 'DMLP', 'DMRC', 'DMXF', 'DNLI', 'DNTH', 'DNUT',
        'DOCU', 'DOGZ', 'DOMH', 'DOMO', 'DOOO', 'DORM', 'DOX', 'DOYU', 'DPRO', 'DPZ', 'DRCT', 'DRDB', 'DRDBU', 'DRDBW', 'DRIO',
        'DRIV', 'DRMA', 'DRMAW', 'DRS', 'DRTS', 'DRTSW', 'DRUG', 'DRVN', 'DSGN', 'DSGR', 'DSGX', 'DSP', 'DSWL', 'DSY', 'DSYWW',
        'DTCK', 'DTCR', 'DTI', 'DTIL', 'DTSQ', 'DTSQR', 'DTSQU', 'DTSS', 'DTST', 'DTSTW', 'DUKH', 'DUKX', 'DUO', 'DUOL', 'DUOT',
        'DVAL', 'DVAX', 'DVIN', 'DVLT', 'DVLU', 'DVOL', 'DVQQ', 'DVRE', 'DVSP', 'DVUT', 'DVXB', 'DVXC', 'DVXE', 'DVXF', 'DVXK',
        'DVXP', 'DVXV', 'DVXY', 'DVY', 'DWAS', 'DWAW', 'DWSH', 'DWSN', 'DWTX', 'DWUS', 'DXCM', 'DXLG', 'DXPE', 'DXR', 'DXST',
        'DYAI', 'DYCQ', 'DYCQR', 'DYCQU', 'DYFI', 'DYN', 'DYNB', 'DYTA', 'EA', 'EASY', 'EBAY', 'EBC', 'EBI', 'EBIZ', 'EBMT',
        'EBON', 'ECBK', 'ECDA', 'ECDAW', 'ECOR', 'ECOW', 'ECPG', 'ECX', 'ECXWW', 'EDAP', 'EDBL', 'EDBLW', 'EDHL', 'EDIT', 'EDRY',
        'EDSA', 'EDTK', 'EDUC', 'EEFT', 'EEIQ', 'EEMA', 'EFAS', 'EFOI', 'EFRA', 'EFSC', 'EFSCP', 'EFSI', 'EFTY', 'EGAN', 'EGBN',
        'EGGQ', 'EGHA', 'EGHAR', 'EGHAU', 'EGHT', 'EH', 'EHGO', 'EHLD', 'EHLS', 'EHTH', 'EJH', 'EKG', 'EKSO', 'ELAB', 'ELBM',
        'ELDN', 'ELFY', 'ELIL', 'ELIS', 'ELOG', 'ELPW', 'ELSE', 'ELTK', 'ELTX', 'ELUT', 'ELVA', 'ELVN', 'ELVR', 'ELWS', 'EM',
        'EMB', 'EMBC', 'EMCB', 'EMEQ', 'EMIF', 'EMISU', 'EML', 'EMPD', 'EMPG', 'EMXC', 'EMXF', 'ENDW', 'ENGN', 'ENGNW', 'ENGS',
        'ENLT', 'ENLV', 'ENPH', 'ENSC', 'ENSG', 'ENTA', 'ENTG', 'ENTO', 'ENTX', 'ENVB', 'ENVX', 'ENZL', 'EOLS', 'EOSE', 'EOSEW',
        'EPIX', 'EPOW', 'EPRX', 'EPSM', 'EPSN', 'EPWK', 'EQ', 'EQIX', 'EQRR', 'ERAS', 'ERET', 'ERIC', 'ERIE', 'ERII', 'ERNA',
        'ERNZ', 'ESCA', 'ESEA', 'ESGD', 'ESGE', 'ESGL', 'ESGLW', 'ESGU', 'ESHA', 'ESHAR', 'ESLA', 'ESLAW', 'ESLT', 'ESMV', 'ESN',
        'ESOA', 'ESPO', 'ESPR', 'ESQ', 'ESTA', 'ETEC', 'ETHA', 'ETHI', 'ETHM', 'ETHMU', 'ETHMW', 'ETHZ', 'ETHZW', 'ETNB', 'ETON',
        'ETOR', 'ETRL', 'ETS', 'ETSY', 'EU', 'EUDA', 'EUDAW', 'EUFN', 'EURK', 'EURKR', 'EURKU', 'EVAX', 'EVCM', 'EVER', 'EVGN',
        'EVGO', 'EVGOW', 'EVLV', 'EVLVW', 'EVMT', 'EVO', 'EVOK', 'EVRG', 'EVSD', 'EVTV', 'EVYM', 'EWBC', 'EWCZ', 'EWJV', 'EWTX',
        'EWZS', 'EXAS', 'EXC', 'EXE', 'EXEL', 'EXFY', 'EXLS', 'EXOZ', 'EXPE', 'EXPI', 'EXPO', 'EXTR', 'EXUS', 'EYE', 'EYEG',
        'EYPT', 'EZGO', 'EZPW', 'FA', 'FAAR', 'FAB', 'FACT', 'FACTU', 'FACTW', 'FAD', 'FALN', 'FAMI', 'FANG', 'FARM', 'FAST',
        'FAT', 'FATBB', 'FATBP', 'FATE', 'FATN', 'FBGL', 'FBIO', 'FBIOP', 'FBIZ', 'FBL', 'FBLA', 'FBLG', 'FBNC', 'FBOT', 'FBRX',
        'FBYD', 'FBYDW', 'FCA', 'FCAL', 'FCAP', 'FCBC', 'FCCO', 'FCEF', 'FCEL', 'FCFS', 'FCHL', 'FCNCA', 'FCNCO', 'FCNCP',
        'FCTE', 'FCUV', 'FCVT', 'FDBC', 'FDCF', 'FDFF', 'FDIF', 'FDIG', 'FDIV', 'FDMT', 'FDNI', 'FDSB', 'FDT', 'FDTS', 'FDTX',
        'FDUS', 'FEAM', 'FEAT', 'FEBO', 'FEIM', 'FELE', 'FEM', 'FEMB', 'FEMS', 'FEMY', 'FENC', 'FEP', 'FEPI', 'FER', 'FERA',
        'FERAR', 'FERAU', 'FEUZ', 'FEX', 'FFAI', 'FFAIW', 'FFBC', 'FFIC', 'FFIN', 'FFIV', 'FFUT', 'FGBI', 'FGBIP', 'FGEN', 'FGI',
        'FGIWW', 'FGL', 'FGM', 'FGMC', 'FGMCR', 'FGMCU', 'FGNX', 'FGNXP', 'FGSI', 'FHB', 'FHTX', 'FIBK', 'FICS', 'FID', 'FIEE',
        'FIGR', 'FIGX', 'FIGXU', 'FIGXW', 'FINW', 'FINX', 'FIP', 'FISI', 'FITB', 'FITBI', 'FITBO', 'FITBP', 'FIVE', 'FIVN',
        'FIVY', 'FIXD', 'FIZZ', 'FJP', 'FKU', 'FKWL', 'FLD', 'FLDB', 'FLDDW', 'FLEX', 'FLGC', 'FLGT', 'FLL', 'FLN', 'FLNC',
        'FLNT', 'FLUX', 'FLWS', 'FLX', 'FLXS', 'FLY', 'FLYE', 'FLYW', 'FMAO', 'FMB', 'FMBH', 'FMED', 'FMET', 'FMFC', 'FMHI',
        'FMNB', 'FMST', 'FMSTW', 'FMTM', 'FMUB', 'FMUN', 'FNGR', 'FNK', 'FNKO', 'FNLC', 'FNWB', 'FNWD', 'FNX', 'FNY', 'FOFO',
        'FOLD', 'FONR', 'FORA', 'FORD', 'FORL', 'FORLU', 'FORLW', 'FORM', 'FORR', 'FORTY', 'FOSL', 'FOSLL', 'FOX', 'FOXA', 'FOXF',
        'FOXX', 'FOXXW', 'FPA', 'FPAY', 'FPXE', 'FPXI', 'FRAF', 'FRBA', 'FRD', 'FRDD', 'FRDU', 'FRGT', 'FRHC', 'FRME', 'FRMEP',
        'FRMI', 'FROG', 'FRPH', 'FRPT', 'FRSH', 'FRST', 'FRSX', 'FSBC', 'FSBW', 'FSCS', 'FSEA', 'FSFG', 'FSGS', 'FSHP', 'FSHPR',
        'FSHPU', 'FSLR', 'FSTR', 'FSUN', 'FSV', 'FSZ', 'FTA', 'FTAG', 'FTAI', 'FTAIM', 'FTAIN', 'FTC', 'FTCI', 'FTCS', 'FTDR',
        'FTDS', 'FTEK', 'FTEL', 'FTFT', 'FTGC', 'FTGS', 'FTHI', 'FTHM', 'FTLF', 'FTNT', 'FTQI', 'FTRE', 'FTRI', 'FTRK', 'FTSL',
        'FTSM', 'FTXG', 'FTXH', 'FTXL', 'FTXN', 'FTXO', 'FTXR', 'FUFU', 'FUFUW', 'FULC', 'FULT', 'FULTP', 'FUNC', 'FUND', 'FUSB',
        'FUTU', 'FV', 'FVC', 'FVCB', 'FVN', 'FVNNR', 'FVNNU', 'FWONA', 'FWONK', 'FWRD', 'FWRG', 'FXNC', 'FYBR', 'FYC', 'FYT',
        'FYX', 'GABC', 'GAIA', 'GAIN', 'GAINI', 'GAINL', 'GAINN', 'GAINZ', 'GALT', 'GAMB', 'GAME', 'GANX', 'GASS', 'GAUZ', 'GBDC',
        'GBFH', 'GBIO', 'GBUG', 'GCBC', 'GCL', 'GCLWW', 'GCMG', 'GCMGW', 'GCT', 'GCTK', 'GDC', 'GDEN', 'GDEV', 'GDEVW', 'GDFN',
        'GDHG', 'GDRX', 'GDS', 'GDTC', 'GDYN', 'GECC', 'GECCG', 'GECCH', 'GECCI', 'GECCO', 'GEG', 'GEGGL', 'GEHC', 'GELS', 'GEME',
        'GEMI', 'GEN', 'GENK', 'GENVR', 'GEOS', 'GERN', 'GEVO', 'GEW', 'GFAI', 'GFAIW', 'GFGF', 'GFLW', 'GFS', 'GGAL', 'GGLL',
        'GGLS', 'GGR', 'GGROW', 'GH', 'GHRS', 'GIBO', 'GIBOW', 'GIFI', 'GIFT', 'GIG', 'GIGGU', 'GIGGW', 'GIGM', 'GIII', 'GILD',
        'GILT', 'GIND', 'GINX', 'GIPR', 'GIPRW', 'GITS', 'GIWWU', 'GKAT', 'GLAD', 'GLADZ', 'GLBE', 'GLBS', 'GLBZ', 'GLCR', 'GLDD',
        'GLDI', 'GLDY', 'GLE', 'GLGG', 'GLIBA', 'GLIBK', 'GLMD', 'GLNG', 'GLOW', 'GLPG', 'GLPI', 'GLRE', 'GLSI', 'GLTO', 'GLUE',
        'GLXG', 'GLXY', 'GMAB', 'GMGI', 'GMHS', 'GMM', 'GNFT', 'GNLN', 'GNLX', 'GNMA', 'GNOM', 'GNPX', 'GNSS', 'GNTA', 'GNTX',
        'GO', 'GOCO', 'GOGO', 'GOOD', 'GOODN', 'GOODO', 'GOOG', 'GOOGL', 'GORV', 'GOSS', 'GOVI', 'GOVX', 'GP', 'GPAT', 'GPATU',
        'GPATW', 'GPCR', 'GPIQ', 'GPIX', 'GPRE', 'GPRF', 'GPRO', 'GPT', 'GQQQ', 'GRAB', 'GRABW', 'GRAL', 'GRAN', 'GRCE', 'GREE',
        'GREEL', 'GRFS', 'GRI', 'GRID', 'GRIN', 'GRNQ', 'GROW', 'GRPN', 'GRRR', 'GRRRW', 'GRVY', 'GRW', 'GRWG', 'GSAT', 'GSBC',
        'GSHD', 'GSHR', 'GSHRU', 'GSHRW', 'GSIB', 'GSIT', 'GSIW', 'GSM', 'GSRFU', 'GSRT', 'GSRTR', 'GSRTU', 'GSUN', 'GT', 'GTBP',
        'GTEC', 'GTEN', 'GTENU', 'GTENW', 'GTERA', 'GTERR', 'GTERU', 'GTERW', 'GTI', 'GTIM', 'GTLB', 'GTM', 'GTR', 'GTX', 'GURE',
        'GUTS', 'GV', 'GVH', 'GWAV', 'GWRS', 'GXAI', 'GXDW', 'GYRE', 'GYRO', 'HAFC', 'HAIN', 'HALO', 'HAO', 'HAS', 'HBAN',
        'HBANL', 'HBANM', 'HBANP', 'HBCP', 'HBDC', 'HBIO', 'HBNB', 'HBNC', 'HBT', 'HCAI', 'HCAT', 'HCHL', 'HCKT', 'HCM', 'HCMA',
        'HCMAU', 'HCMAW', 'HCOW', 'HCSG', 'HCTI', 'HCWB', 'HDL', 'HDSN', 'HEAL', 'HECO', 'HEJD', 'HELE', 'HEPS', 'HEQQ', 'HERD',
        'HERO', 'HERZ', 'HFBL', 'HFFG', 'HFSP', 'HFWA', 'HGBL', 'HHS', 'HIDE', 'HIFS', 'HIHO', 'HIMX', 'HIMY', 'HIMZ', 'HIND',
        'HISF', 'HIT', 'HITI', 'HIVE', 'HKIT', 'HKPD', 'HLAL', 'HLIT', 'HLMN', 'HLNE', 'HLP', 'HMR', 'HNDL', 'HNNA', 'HNNAZ',
        'HNRG', 'HNST', 'HNVR', 'HOFT', 'HOLO', 'HOLOW', 'HOLX', 'HON', 'HOND', 'HONDU', 'HONDW', 'HONE', 'HOOD', 'HOOG', 'HOOI',
        'HOOX', 'HOPE', 'HOTH', 'HOUR', 'HOVNP', 'HOVR', 'HOVRW', 'HOWL', 'HOYY', 'HPAI', 'HPAIW', 'HPK', 'HQGO', 'HQI', 'HQY',
        'HRMY', 'HROW', 'HROWL', 'HRTS', 'HRTX', 'HRZN', 'HSAI', 'HSCS', 'HSCSW', 'HSDT', 'HSIC', 'HSII', 'HSPO', 'HSPOR',
        'HSPOU', 'HSPOW', 'HSPT', 'HSPTR', 'HSPTU', 'HST', 'HSTM', 'HTBK', 'HTCO', 'HTCR', 'HTFL', 'HTHT', 'HTLD', 'HTLM', 'HTO',
        'HTOO', 'HTOOW', 'HTZ', 'HTZWW', 'HUBC', 'HUBCW', 'HUBCZ', 'HUBG', 'HUDI', 'HUHU', 'HUIZ', 'HUMA', 'HUMAW', 'HURA', 'HURC',
        'HURN', 'HUT', 'HVII', 'HVIIR', 'HVIIU', 'HVMC', 'HVMCU', 'HVMCW', 'HWAY', 'HWBK', 'HWC', 'HWCPZ', 'HWH', 'HWKN', 'HWSM',
        'HXHX', 'HYBI', 'HYDR', 'HYFM', 'HYFT', 'HYLS', 'HYMC', 'HYP', 'HYPD', 'HYPR', 'HYXF', 'HYZD', 'IAC', 'IART', 'IAS',
        'IBAC', 'IBACR', 'IBAT', 'IBB', 'IBBQ', 'IBCP', 'IBEX', 'IBG', 'IBGA', 'IBGB', 'IBGK', 'IBGL', 'IBIO', 'IBIT', 'IBKR',
        'IBOC', 'IBOT', 'IBRX', 'IBTF', 'IBTG', 'IBTH', 'IBTI', 'IBTJ', 'IBTK', 'IBTL', 'IBTM', 'IBTO', 'IBTP', 'IBTQ', 'ICCC',
        'ICCM', 'ICFI', 'ICG', 'ICHR', 'ICLN', 'ICLR', 'ICMB', 'ICON', 'ICOP', 'ICU', 'ICUCW', 'ICUI', 'IDAI', 'IDCC', 'IDEF',
        'IDN', 'IDXX', 'IDYA', 'IEF', 'IEI', 'IEP', 'IESC', 'IEUS', 'IFBD', 'IFGL', 'IFLO', 'IFRX', 'IFV', 'IGF', 'IGIB', 'IGIC',
        'IGOV', 'IGSB', 'IHRT', 'IHYF', 'III', 'IIIV', 'IINN', 'IINNW', 'IJT', 'IKT', 'ILAG', 'ILIT', 'ILLR', 'ILLRW', 'ILMN',
        'ILPT', 'IMA', 'IMAB', 'IMCC', 'IMCR', 'IMCV', 'IMDX', 'IMG', 'IMKTA', 'IMMP', 'IMMR', 'IMMX', 'IMNM', 'IMNN', 'IMOM',
        'IMOS', 'IMPP', 'IMPPP', 'IMRN', 'IMRX', 'IMTE', 'IMTX', 'IMUX', 'IMVT', 'IMXI', 'INAB', 'INAC', 'INACR', 'INACU',
        'INBK', 'INBKZ', 'INBS', 'INBX', 'INCR', 'INCY', 'INDB', 'INDH', 'INDI', 'INDP', 'INDV', 'INDY', 'INEO', 'INFR', 'INGN',
        'INHD', 'INKT', 'INLF', 'INM', 'INMB', 'INMD', 'INNV', 'INO', 'INOD', 'INRO', 'INSE', 'INSG', 'INSM', 'INTA', 'INTC',
        'INTG', 'INTJ', 'INTR', 'INTS', 'INTU', 'INTW', 'INTZ', 'INV', 'INVA', 'INVE', 'INVZ', 'INVZW', 'IOBT', 'IONL', 'IONR',
        'IONS', 'IONX', 'IONZ', 'IOSP', 'IOTR', 'IOVA', 'IPAR', 'IPCX', 'IPCXR', 'IPCXU', 'IPDN', 'IPGP', 'IPHA', 'IPKW', 'IPM',
        'IPOD', 'IPODU', 'IPODW', 'IPSC', 'IPST', 'IPW', 'IPWR', 'IPX', 'IQ', 'IQQQ', 'IQST', 'IRBT', 'IRD', 'IRDM', 'IREN',
        'IRIX', 'IRMD', 'IRON', 'IROQ', 'IRTC', 'IRWD', 'ISBA', 'ISHG', 'ISHP', 'ISPC', 'ISPO', 'ISPOW', 'ISPR', 'ISRG', 'ISRL',
        'ISRLU', 'ISRLW', 'ISSC', 'ISTB', 'ISTR', 'ISUL', 'ITIC', 'ITRI', 'ITRM', 'ITRN', 'IUS', 'IUSB', 'IUSG', 'IUSV', 'IVA',
        'IVAL', 'IVDA', 'IVDAW', 'IVF', 'IVP', 'IVVD', 'IXHL', 'IXUS', 'IZEA', 'IZM', 'JACK', 'JAGX', 'JAKK', 'JAMF', 'JANX',
        'JAPN', 'JAZZ', 'JBDI', 'JBHT', 'JBIO', 'JBLU', 'JBSS', 'JCAP', 'JCSE', 'JCTC', 'JD', 'JDOC', 'JDZG', 'JEM', 'JEPQ',
        'JFB', 'JFBR', 'JFBRW', 'JFIN', 'JFU', 'JG', 'JGLO', 'JHAI', 'JIVE', 'JJSF', 'JKHY', 'JL', 'JLHL', 'JMID', 'JMSB',
        'JOUT', 'JOYY', 'JPEF', 'JPX', 'JPY', 'JRSH', 'JRVR', 'JSM', 'JSMD', 'JSML', 'JSPR', 'JSPRW', 'JTAI', 'JTEK', 'JUNS',
        'JVA', 'JWEL', 'JXG', 'JYD', 'JYNT', 'JZ', 'JZXN', 'KALA', 'KALU', 'KALV', 'KARO', 'KAT', 'KAVL', 'KBAB', 'KBSX', 'KBWB',
        'KBWD', 'KBWP', 'KBWR', 'KBWY', 'KC', 'KCHV', 'KCHVR', 'KCHVU', 'KDK', 'KDKRW', 'KDP', 'KE', 'KEAT', 'KELYA', 'KELYB',
        'KEQU', 'KFFB', 'KFII', 'KFIIR', 'KFIIU', 'KG', 'KGEI', 'KHC', 'KIDS', 'KIDZ', 'KIDZW', 'KINS', 'KITT', 'KITTW', 'KLAC',
        'KLIC', 'KLRS', 'KLTO', 'KLTOW', 'KLTR', 'KLXE', 'KMB', 'KMDA', 'KMLI', 'KMRK', 'KMTS', 'KNDI', 'KNGZ', 'KNSA', 'KOD',
        'KOID', 'KOPN', 'KOSS', 'KOYN', 'KOYNU', 'KOYNW', 'KPDD', 'KPLT', 'KPLTW', 'KPRX', 'KPTI', 'KQQQ', 'KRKR', 'KRMA',
        'KRMD', 'KRNT', 'KRNY', 'KROP', 'KROS', 'KRRO', 'KRT', 'KRUS', 'KRYS', 'KSCP', 'KSPI', 'KTCC', 'KTOS', 'KTTA', 'KTTAW',
        'KURA', 'KVAC', 'KVACU', 'KVACW', 'KVHI', 'KWM', 'KWMWW', 'KXIN', 'KYIV', 'KYIVW', 'KYMR', 'KYTX', 'KZIA', 'KZR', 'LAB',
        'LAES', 'LAKE', 'LAMR', 'LAND', 'LANDM', 'LANDO', 'LANDP', 'LARK', 'LASE', 'LASR', 'LATAU', 'LAUR', 'LAWR', 'LAYS',
        'LAZR', 'LBGJ', 'LBRDA', 'LBRDK', 'LBRDP', 'LBRX', 'LBTYA', 'LBTYB', 'LBTYK', 'LCCC', 'LCCCR', 'LCCCU', 'LCDL', 'LCDS',
        'LCFY', 'LCFYW', 'LCID', 'LCNB', 'LCUT', 'LDEM', 'LDRX', 'LDSF', 'LDWY', 'LE', 'LECO', 'LEDS', 'LEE', 'LEGH', 'LEGN',
        'LEGR', 'LENZ', 'LESL', 'LEXI', 'LEXX', 'LEXXW', 'LFCR', 'LFMD', 'LFMDP', 'LFS', 'LFSC', 'LFST', 'LFUS', 'LFVN', 'LFWD',
        'LGCB', 'LGCF', 'LGCL', 'LGHL', 'LGIH', 'LGN', 'LGND', 'LGO', 'LGRO', 'LGVN', 'LHAI', 'LHSW', 'LI', 'LICN', 'LIDR',
        'LIDRW', 'LIEN', 'LIF', 'LILA', 'LILAK', 'LIMN', 'LIMNW', 'LIN', 'LINC', 'LIND', 'LINE', 'LINK', 'LIQT', 'LITE', 'LITM',
        'LITP', 'LITS', 'LIVE', 'LIVN', 'LIXT', 'LIXTW', 'LKFN', 'LKQ', 'LKSPU', 'LLYVA', 'LLYVK', 'LLYZ', 'LMAT', 'LMB', 'LMBS',
        'LMFA', 'LMNR', 'LMTL', 'LMTS', 'LNAI', 'LNKB', 'LNKS', 'LNSR', 'LNT', 'LNTH', 'LNW', 'LNZA', 'LNZAW', 'LOAN', 'LOBO',
        'LOCO', 'LOGI', 'LOGO', 'LOKV', 'LOKVU', 'LOKVW', 'LOOP', 'LOPE', 'LOT', 'LOTI', 'LOTWW', 'LOVE', 'LPAA', 'LPAAU',
        'LPAAW', 'LPBB', 'LPBBU', 'LPBBW', 'LPCN', 'LPLA', 'LPRO', 'LPSN', 'LPTH', 'LPTX', 'LQDA', 'LQDT', 'LRCX', 'LRE', 'LRGE',
        'LRHC', 'LRMR', 'LRND', 'LSAK', 'LSBK', 'LSCC', 'LSE', 'LSH', 'LSTA', 'LSTR', 'LTBR', 'LTRN', 'LTRX', 'LTRYW', 'LUCD',
        'LUCY', 'LUCYW', 'LULU', 'LUNG', 'LUNR', 'LVHD', 'LVLU', 'LVO', 'LVRO', 'LVROW', 'LVTX', 'LWAC', 'LWACU', 'LWACW',
        'LWAY', 'LWLG', 'LX', 'LXEH', 'LXEO', 'LXRX', 'LYEL', 'LYFT', 'LYRA', 'LYTS', 'LZ', 'LZMH', 'MAAS', 'MACI', 'MACIU',
        'MACIW', 'MAGH', 'MAMA', 'MAMK', 'MAMO', 'MANH', 'MAPS', 'MAPSW', 'MAR', 'MARA', 'MARPS', 'MASI', 'MASK', 'MASS', 'MAT',
        'MATH', 'MATW', 'MAXI', 'MAXN', 'MAYA', 'MAYAR', 'MAYAU', 'MAYS', 'MAZE', 'MB', 'MBAV', 'MBAVU', 'MBAVW', 'MBB', 'MBBC',
        'MBCN', 'MBIN', 'MBINL', 'MBINM', 'MBINN', 'MBIO', 'MBLY', 'MBNKO', 'MBOT', 'MBRX', 'MBS', 'MBUU', 'MBVIU', 'MBWM',
        'MBX', 'MCBS', 'MCDS', 'MCFT', 'MCGA', 'MCGAU', 'MCGAW', 'MCHB', 'MCHI', 'MCHP', 'MCHPP', 'MCHS', 'MCHX', 'MCRB', 'MCRI',
        'MCSE', 'MCTR', 'MCW', 'MDAI', 'MDAIW', 'MDB', 'MDBH', 'MDCX', 'MDCXW', 'MDGL', 'MDIA', 'MDIV', 'MDLZ', 'MDRR', 'MDWD',
        'MDXG', 'MDXH', 'MEDP', 'MEDX', 'MEGL', 'MELI', 'MEMS', 'MENS', 'MEOH', 'MERC', 'MESA', 'MESO', 'META', 'METC', 'METCB',
        'METCI', 'METCZ', 'METD', 'METL', 'METU', 'MFH', 'MFI', 'MFIC', 'MFICL', 'MFIN', 'MFLX', 'MGEE', 'MGIC', 'MGIH', 'MGN',
        'MGNI', 'MGNX', 'MGPI', 'MGRC', 'MGRT', 'MGRX', 'MGTX', 'MGX', 'MGYR', 'MHUA', 'MIDD', 'MIGI', 'MILN', 'MIMI', 'MIND',
        'MIRA', 'MIRM', 'MIST', 'MITK', 'MKAM', 'MKDW', 'MKDWW', 'MKLY', 'MKLYR', 'MKLYU', 'MKSI', 'MKTW', 'MKTX', 'MKZR',
        'MLAB', 'MLAC', 'MLACR', 'MLACU', 'MLCI', 'MLCO', 'MLEC', 'MLECW', 'MLGO', 'MLKN', 'MLTX', 'MLYS', 'MMLP', 'MMSI',
        'MMYT', 'MNDO', 'MNDR', 'MNDY', 'MNKD', 'MNMD', 'MNOV', 'MNPR', 'MNRO', 'MNSB', 'MNSBP', 'MNST', 'MNTK', 'MNTS', 'MNTSW',
        'MNY', 'MNYWW', 'MOB', 'MOBBW', 'MOBX', 'MOBXW', 'MODD', 'MODL', 'MOFG', 'MOGO', 'MOLN', 'MOMO', 'MOOD', 'MORN', 'MOVE',
        'MPAA', 'MPB', 'MPWR', 'MQ', 'MQQQ', 'MRAL', 'MRAM', 'MRBK', 'MRCC', 'MRCY', 'MREO', 'MRKR', 'MRM', 'MRNA', 'MRNO',
        'MRNOW', 'MRSN', 'MRTN', 'MRUS', 'MRVI', 'MRVL', 'MRX', 'MSAI', 'MSAIW', 'MSBI', 'MSBIP', 'MSDD', 'MSEX', 'MSFD', 'MSFL',
        'MSFT', 'MSFU', 'MSGM', 'MSGY', 'MSPR', 'MSPRW', 'MSPRZ', 'MSS', 'MST', 'MSTP', 'MSTR', 'MSTX', 'MSW', 'MTC', 'MTCH',
        'MTEK', 'MTEKW', 'MTEN', 'MTEX', 'MTLS', 'MTRX', 'MTSI', 'MTSR', 'MTVA', 'MTYY', 'MU', 'MUD', 'MULL', 'MULT', 'MURA',
        'MUU', 'MVBF', 'MVIS', 'MVLL', 'MVST', 'MVSTW', 'MWYN', 'MXCT', 'MXL', 'MYCF', 'MYCG', 'MYCH', 'MYCI', 'MYCJ', 'MYCK',
        'MYCL', 'MYCM', 'MYCN', 'MYCO', 'MYFW', 'MYGN', 'MYMF', 'MYMG', 'MYMH', 'MYMI', 'MYMJ', 'MYMK', 'MYNZ', 'MYPS', 'MYPSW',
        'MYRG', 'MYSE', 'MYSEW', 'MYSZ', 'MZTI', 'NA', 'NAAS', 'NAGE', 'NAII', 'NAKA', 'NAMI', 'NAMM', 'NAMMW', 'NAMS', 'NAMSW',
        'NAOV', 'NATH', 'NATO', 'NATR', 'NAUT', 'NAVI', 'NB', 'NBBK', 'NBIL', 'NBIS', 'NBIX', 'NBN', 'NBTB', 'NBTX', 'NCEW',
        'NCI', 'NCIQ', 'NCMI', 'NCNA', 'NCNO', 'NCPB', 'NCPL', 'NCPLW', 'NCRA', 'NCSM', 'NCT', 'NCTY', 'NDAA', 'NDAQ', 'NDLS',
        'NDRA', 'NDSN', 'NECB', 'NEGG', 'NEO', 'NEOG', 'NEON', 'NEOV', 'NEOVW', 'NEPH', 'NERV', 'NESR', 'NETD', 'NETDU', 'NETDW',
        'NEUP', 'NEWT', 'NEWTG', 'NEWTH', 'NEWTI', 'NEWTP', 'NEWTZ', 'NEWZ', 'NEXM', 'NEXN', 'NEXT', 'NFBK', 'NFE', 'NFLX',
        'NFTY', 'NFXL', 'NFXS', 'NGNE', 'NHIC', 'NHICU', 'NHICW', 'NHPAP', 'NHPBP', 'NHTC', 'NICE', 'NIKL', 'NIOBW', 'NIPG',
        'NISN', 'NITO', 'NIU', 'NIVF', 'NIVFW', 'NIXT', 'NIXX', 'NIXXW', 'NKSH', 'NKTR', 'NKTX', 'NLSP', 'NLSPW', 'NMFC', 'NMFCZ',
        'NMIH', 'NMP', 'NMPAR', 'NMPAU', 'NMRA', 'NMRK', 'NMTC', 'NN', 'NNAVW', 'NNBR', 'NNDM', 'NNE', 'NNNN', 'NNOX', 'NODK',
        'NOEM', 'NOEMR', 'NOEMU', 'NOEMW', 'NOTV', 'NOVT', 'NOWL', 'NPAC', 'NPACU', 'NPACW', 'NPCE', 'NPFI', 'NRC', 'NRDS',
        'NRES', 'NRIM', 'NRIX', 'NRSN', 'NRSNW', 'NRXP', 'NRXPW', 'NSCR', 'NSI', 'NSIT', 'NSPR', 'NSSC', 'NSTS', 'NSYS', 'NTAP',
        'NTCL', 'NTCT', 'NTES', 'NTGR', 'NTHI', 'NTIC', 'NTLA', 'NTNX', 'NTRA', 'NTRB', 'NTRBW', 'NTRP', 'NTRS', 'NTRSO', 'NTSK',
        'NTWK', 'NTWO', 'NTWOU', 'NTWOW', 'NUAI', 'NUAIW', 'NUKK', 'NUKKW', 'NUSB', 'NUTR', 'NUTX', 'NUVL', 'NUWE', 'NVA',
        'NVAWW', 'NVAX', 'NVCR', 'NVCT', 'NVD', 'NVDA', 'NVDD', 'NVDG', 'NVDL', 'NVDS', 'NVDU', 'NVEC', 'NVFY', 'NVMI', 'NVNI',
        'NVNIW', 'NVNO', 'NVTS', 'NVVE', 'NVVEW', 'NVX', 'NVYY', 'NWBI', 'NWE', 'NWFL', 'NWGL', 'NWL', 'NWPX', 'NWS', 'NWSA',
        'NWTG', 'NXGL', 'NXGLW', 'NXL', 'NXPI', 'NXPL', 'NXPLW', 'NXST', 'NXT', 'NXTC', 'NXTG', 'NXTT', 'NXXT', 'NYAX', 'NYXH',
        'NZAC', 'NZUS', 'OABI', 'OABIW', 'OACC', 'OACCU', 'OACCW', 'OAKU', 'OAKUR', 'OAKUU', 'OAKUW', 'OBA', 'OBAWU', 'OBAWW',
        'OBIL', 'OBIO', 'OBLG', 'OBT', 'OCC', 'OCCI', 'OCCIM', 'OCCIN', 'OCCIO', 'OCFC', 'OCG', 'OCGN', 'OCS', 'OCSAW', 'OCSL',
        'OCUL', 'ODD', 'ODDS', 'ODFL', 'ODP', 'ODVWZ', 'ODYS', 'OESX', 'OFAL', 'OFIX', 'OFLX', 'OFS', 'OFSSH', 'OFSSO', 'OGI',
        'OKLL', 'OKTA', 'OKUR', 'OKYO', 'OLB', 'OLED', 'OLLI', 'OLMA', 'OLPX', 'OM', 'OMAB', 'OMCC', 'OMCL', 'OMDA', 'OMER',
        'OMEX', 'OMH', 'OMSE', 'ON', 'ONB', 'ONBPO', 'ONBPP', 'ONC', 'ONCH', 'ONCHU', 'ONCHW', 'ONCO', 'ONCY', 'ONDS', 'ONEG',
        'ONEQ', 'ONEW', 'ONFO', 'ONFOW', 'ONMD', 'ONMDW', 'OOQB', 'OOSB', 'OOSL', 'OP', 'OPAL', 'OPBK', 'OPCH', 'OPEN', 'OPK',
        'OPPJ', 'OPRA', 'OPRT', 'OPRX', 'OPT', 'OPTX', 'OPTXW', 'OPTZ', 'OPXS', 'ORBS', 'ORCX', 'ORGN', 'ORGNW', 'ORGO', 'ORIC',
        'ORIQ', 'ORIQU', 'ORIQW', 'ORIS', 'ORKA', 'ORKT', 'ORLY', 'ORMP', 'ORR', 'ORRF', 'OS', 'OSBC', 'OSCX', 'OSIS', 'OSPN',
        'OSRH', 'OSRHW', 'OSS', 'OST', 'OSUR', 'OSW', 'OTEX', 'OTGAU', 'OTGL', 'OTLK', 'OTLY', 'OTTR', 'OUST', 'OUSTZ', 'OVBC',
        'OVID', 'OVLY', 'OXBR', 'OXBRW', 'OXLC', 'OXLCG', 'OXLCI', 'OXLCL', 'OXLCN', 'OXLCO', 'OXLCP', 'OXLCZ', 'OXSQ', 'OXSQG',
        'OXSQH', 'OYSE', 'OYSER', 'OYSEU', 'OZEM', 'OZK', 'OZKAP', 'PAA', 'PABD', 'PABU', 'PACB', 'PACH', 'PACHU', 'PACHW',
        'PAGP', 'PAHC', 'PAL', 'PALD', 'PALI', 'PALU', 'PAMT', 'PANG', 'PANL', 'PANW', 'PASG', 'PASW', 'PATK', 'PATN', 'PAVM',
        'PAVS', 'PAX', 'PAYO', 'PAYS', 'PAYX', 'PBBK', 'PBFS', 'PBHC', 'PBM', 'PBMWW', 'PBPB', 'PBQQ', 'PBYI', 'PC', 'PCAP',
        'PCAPU', 'PCAPW', 'PCAR', 'PCB', 'PCH', 'PCLA', 'PCMM', 'PCRX', 'PCSA', 'PCSC', 'PCT', 'PCTTU', 'PCTTW', 'PCTY', 'PCVX',
        'PCYO', 'PDBA', 'PDBC', 'PDD', 'PDDL', 'PDEX', 'PDFS', 'PDLB', 'PDP', 'PDSB', 'PDYN', 'PDYNW', 'PEBK', 'PEBO', 'PECO',
        'PEGA', 'PELI', 'PELIR', 'PELIU', 'PENG', 'PENN', 'PEP', 'PEPG', 'PEPS', 'PERI', 'PESI', 'PETS', 'PETZ', 'PEY', 'PEZ',
        'PFAI', 'PFBC', 'PFF', 'PFG', 'PFI', 'PFIS', 'PFM', 'PFSA', 'PFX', 'PFXNZ', 'PGAC', 'PGACR', 'PGACU', 'PGC', 'PGEN',
        'PGJ', 'PGNY', 'PGY', 'PGYWW', 'PHAR', 'PHAT', 'PHH', 'PHIO', 'PHLT', 'PHO', 'PHOE', 'PHUN', 'PHVS', 'PI', 'PID', 'PIE',
        'PIII', 'PIIIW', 'PINC', 'PIO', 'PIZ', 'PKBK', 'PKOH', 'PKW', 'PLAB', 'PLAY', 'PLBC', 'PLBL', 'PLBY', 'PLCE', 'PLMK',
        'PLMKU', 'PLMKW', 'PLMR', 'PLPC', 'PLRX', 'PLRZ', 'PLSE', 'PLT', 'PLTD', 'PLTG', 'PLTK', 'PLTR', 'PLTS', 'PLTU', 'PLTZ',
        'PLUG', 'PLUR', 'PLUS', 'PLUT', 'PLXS', 'PLYY', 'PMAX', 'PMBS', 'PMCB', 'PMEC', 'PMN', 'PMTR', 'PMTRU', 'PMTRW', 'PMTS',
        'PMVP', 'PN', 'PNBK', 'PNFP', 'PNFPP', 'PNQI', 'PNRG', 'PNTG', 'POAI', 'POCI', 'PODC', 'PODD', 'POET', 'POLA', 'POLE',
        'POLEU', 'POLEW', 'POM', 'PONY', 'POOL', 'POWI', 'POWL', 'POWW', 'POWWP', 'PPBT', 'PPC', 'PPCB', 'PPH', 'PPI', 'PPIH',
        'PPSI', 'PPTA', 'PQAP', 'PQJA', 'PQJL', 'PQOC', 'PRAA', 'PRAX', 'PRCH', 'PRCT', 'PRDO', 'PRE', 'PRENW', 'PRFX', 'PRFZ',
        'PRGS', 'PRHI', 'PRHIZ', 'PRLD', 'PRME', 'PRN', 'PROF', 'PROK', 'PROP', 'PROV', 'PRPH', 'PRPL', 'PRPO', 'PRQR', 'PRSO',
        'PRTA', 'PRTC', 'PRTH', 'PRTS', 'PRVA', 'PRZO', 'PSC', 'PSCC', 'PSCD', 'PSCE', 'PSCF', 'PSCH', 'PSCI', 'PSCM', 'PSCT',
        'PSCU', 'PSEC', 'PSET', 'PSHG', 'PSIG', 'PSIX', 'PSKY', 'PSL', 'PSMT', 'PSNL', 'PSNY', 'PSNYW', 'PSTR', 'PSTV', 'PSWD',
        'PT', 'PTC', 'PTCT', 'PTEN', 'PTF', 'PTGX', 'PTH', 'PTHL', 'PTIR', 'PTIX', 'PTIXW', 'PTLE', 'PTLO', 'PTNM', 'PTNQ',
        'PTON', 'PTRN', 'PUBM', 'PUI', 'PULM', 'PVBC', 'PVLA', 'PWM', 'PWP', 'PWRD', 'PXI', 'PXLW', 'PXS', 'PXSAW', 'PY', 'PYPD',
        'PYPG', 'PYPL', 'PYXS', 'PYZ', 'PZZA', 'QABA', 'QALT', 'QAT', 'QB', 'QBIG', 'QBTZ', 'QBUF', 'QCLN', 'QCLR', 'QCLS',
        'QCMD', 'QCML', 'QCMU', 'QCOM', 'QCRH', 'QDEL', 'QDTY', 'QETA', 'QETAR', 'QETAU', 'QFIN', 'QGRD', 'QH', 'QHDG', 'QIPT',
        'QLDY', 'QLGN', 'QLYS', 'QMCO', 'QMID', 'QMMM', 'QMOM', 'QNCX', 'QNRX', 'QNST', 'QNTM', 'QNXT', 'QOWZ', 'QPUX', 'QQA',
        'QQDN', 'QQEW', 'QQHG', 'QQJG', 'QQLV', 'QQMG', 'QQQ', 'QQQA', 'QQQE', 'QQQG', 'QQQH', 'QQQI', 'QQQJ', 'QQQM', 'QQQP',
        'QQQS', 'QQQT', 'QQQX', 'QQQY', 'QQUP', 'QQWZ', 'QQXL', 'QQXT', 'QRHC', 'QRMI', 'QRVO', 'QSEA', 'QSEAR', 'QSEAU', 'QSG',
        'QSI', 'QSIAW', 'QSIX', 'QSML', 'QTEC', 'QTOP', 'QTR', 'QTRX', 'QTTB', 'QTUM', 'QUBT', 'QUIK', 'QUMS', 'QUMSR', 'QUMSU',
        'QURE', 'QVAL', 'QVCGA', 'QVCGP', 'QXQ', 'QYLD', 'QYLG', 'RAA', 'RAAQ', 'RAAQU', 'RAAQW', 'RADX', 'RAIL', 'RAIN',
        'RAINW', 'RAND', 'RANG', 'RANGR', 'RANGU', 'RANI', 'RAPP', 'RAPT', 'RARE', 'RAUS', 'RAVE', 'RAY', 'RAYA', 'RBB', 'RBBN',
        'RBCAA', 'RBIL', 'RBKB', 'RBNE', 'RCAT', 'RCEL', 'RCGE', 'RCKT', 'RCKTW', 'RCKY', 'RCMT', 'RCON', 'RCT', 'RDAC', 'RDACR',
        'RDACU', 'RDAG', 'RDAGU', 'RDAGW', 'RDCM', 'RDGT', 'RDHL', 'RDI', 'RDIB', 'RDNT', 'RDNW', 'RDTL', 'RDTY', 'RDVT', 'RDVY',
        'RDWR', 'RDZN', 'RDZNW', 'REAI', 'REAL', 'REAX', 'REBN', 'RECT', 'REE', 'REFI', 'REFR', 'REG', 'REGCO', 'REGCP', 'REGN',
        'REIT', 'REKR', 'RELI', 'RELIW', 'RELL', 'RELY', 'REMG', 'RENT', 'REPL', 'RETO', 'REVB', 'REVBW', 'REYN', 'RFAI', 'RFAIR',
        'RFAIU', 'RFDI', 'RFEM', 'RFEU', 'RFIL', 'RGC', 'RGCO', 'RGEN', 'RGLD', 'RGLO', 'RGNX', 'RGP', 'RGS', 'RGTI', 'RGTIW',
        'RGTX', 'RGTZ', 'RIBB', 'RIBBR', 'RIBBU', 'RICK', 'RIFR', 'RIGL', 'RILY', 'RILYG', 'RILYK', 'RILYL', 'RILYN', 'RILYP',
        'RILYT', 'RILYZ', 'RIME', 'RING', 'RINT', 'RIOT', 'RITR', 'RIVN', 'RKDA', 'RKLB', 'RKLX', 'RLAY', 'RLMD', 'RLYB', 'RMBI',
        'RMBS', 'RMCF', 'RMCO', 'RMCOW', 'RMNI', 'RMR', 'RMSG', 'RMSGW', 'RMTI', 'RNA', 'RNAC', 'RNAZ', 'RNEM', 'RNGTU', 'RNIN',
        'RNRG', 'RNTX', 'RNW', 'RNWWW', 'RNXT', 'ROAD', 'ROBT', 'ROCK', 'ROE', 'ROIV', 'ROKU', 'ROMA', 'ROOT', 'ROP', 'ROST',
        'RPAY', 'RPD', 'RPID', 'RPRX', 'RPTX', 'RR', 'RRBI', 'RRGB', 'RRR', 'RSSS', 'RSVR', 'RSVRW', 'RTAC', 'RTACU', 'RTACW',
        'RTH', 'RTXG', 'RUBI', 'RUM', 'RUMBW', 'RUN', 'RUNN', 'RUSC', 'RUSHA', 'RUSHB', 'RVMD', 'RVMDW', 'RVNL', 'RVPH', 'RVPHW',
        'RVSB', 'RVSN', 'RVSNW', 'RVYL', 'RWAY', 'RWAYL', 'RWAYZ', 'RXRX', 'RXST', 'RXT', 'RYAAY', 'RYET', 'RYM', 'RYOJ', 'RYTM',
        'RZLT', 'RZLV', 'RZLVW', 'SABR', 'SABS', 'SABSW', 'SAFT', 'SAFX', 'SAGT', 'SAIA', 'SAIC', 'SAIH', 'SAIHW', 'SAIL',
        'SAMG', 'SANA', 'SANG', 'SANM', 'SARK', 'SATL', 'SATLW', 'SATS', 'SAVA', 'SBAC', 'SBC', 'SBCF', 'SBCWW', 'SBET', 'SBFG',
        'SBFM', 'SBFMW', 'SBGI', 'SBLK', 'SBLX', 'SBRA', 'SBUX', 'SCAG', 'SCAGW', 'SCDS', 'SCHL', 'SCKT', 'SCLX', 'SCLXW',
        'SCNI', 'SCNX', 'SCOR', 'SCSC', 'SCVL', 'SCWO', 'SCYX', 'SCZ', 'SDA', 'SDAWW', 'SDG', 'SDGR', 'SDHI', 'SDHIR', 'SDHIU',
        'SDM', 'SDOT', 'SDSI', 'SDST', 'SDSTW', 'SDTY', 'SDVY', 'SEAT', 'SEATW', 'SEDG', 'SEED', 'SEEM', 'SEER', 'SEGG', 'SEIC',
        'SEIE', 'SEIS', 'SELF', 'SELX', 'SENEA', 'SENEB', 'SEPN', 'SERA', 'SERV', 'SETM', 'SEVN', 'SEZL', 'SFBC', 'SFD', 'SFHG',
        'SFIX', 'SFLO', 'SFM', 'SFNC', 'SFST', 'SFWL', 'SGA', 'SGBX', 'SGC', 'SGD', 'SGHT', 'SGLY', 'SGML', 'SGMO', 'SGMT',
        'SGRP', 'SGRY', 'SHBI', 'SHC', 'SHEN', 'SHFS', 'SHFSW', 'SHIM', 'SHIP', 'SHLS', 'SHMD', 'SHMDW', 'SHOO', 'SHOP', 'SHOT',
        'SHOTW', 'SHPD', 'SHPH', 'SHPU', 'SHRY', 'SHV', 'SHY', 'SIBN', 'SIDU', 'SIEB', 'SIFY', 'SIGA', 'SIGI', 'SIGIP', 'SILC',
        'SILO', 'SIMA', 'SIMAU', 'SIMAW', 'SIMO', 'SINT', 'SION', 'SIRI', 'SITM', 'SIXG', 'SJ', 'SJCP', 'SJLD', 'SKBL', 'SKIN',
        'SKK', 'SKOR', 'SKRE', 'SKWD', 'SKYE', 'SKYQ', 'SKYT', 'SKYU', 'SKYW', 'SKYX', 'SKYY', 'SLAB', 'SLDB', 'SLDE', 'SLDP',
        'SLDPW', 'SLE', 'SLGL', 'SLM', 'SLMBP', 'SLMT', 'SLN', 'SLNG', 'SLNH', 'SLNHP', 'SLNO', 'SLP', 'SLQD', 'SLRC', 'SLRX',
        'SLS', 'SLSN', 'SLVO', 'SLVR', 'SLXN', 'SLXNW', 'SMBC', 'SMCC', 'SMCF', 'SMCI', 'SMCL', 'SMCO', 'SMCX', 'SMCZ', 'SMH',
        'SMHX', 'SMID', 'SMLR', 'SMMT', 'SMOM', 'SMPL', 'SMRI', 'SMSI', 'SMST', 'SMTC', 'SMTI', 'SMTK', 'SMX', 'SMXT', 'SMXWW',
        'SMYY', 'SNAL', 'SNBR', 'SNCR', 'SNCY', 'SND', 'SNDK', 'SNDL', 'SNDX', 'SNES', 'SNEX', 'SNFCA', 'SNGX', 'SNOA', 'SNPS',
        'SNSE', 'SNSR', 'SNT', 'SNTG', 'SNTI', 'SNWV', 'SNY', 'SNYR', 'SOBR', 'SOCA', 'SOCAU', 'SOCAW', 'SOCL', 'SOFI', 'SOFX',
        'SOGP', 'SOHO', 'SOHOB', 'SOHON', 'SOHOO', 'SOHU', 'SOLT', 'SOLZ', 'SOND', 'SONDW', 'SONM', 'SONN', 'SONO', 'SOPA',
        'SOPH', 'SORA', 'SOTK', 'SOUN', 'SOUNW', 'SOUX', 'SOWG', 'SOXQ', 'SOXX', 'SPAI', 'SPAM', 'SPAQ', 'SPBC', 'SPC', 'SPCB',
        'SPCT', 'SPCX', 'SPCY', 'SPEG', 'SPEGR', 'SPEGU', 'SPFI', 'SPHL', 'SPIT', 'SPKL', 'SPKLU', 'SPKLW', 'SPNS', 'SPOK',
        'SPPL', 'SPRB', 'SPRC', 'SPRO', 'SPRX', 'SPRY', 'SPSC', 'SPT', 'SPWH', 'SPWR', 'SPWRW', 'SPXD', 'SPYQ', 'SQFT', 'SQFTP',
        'SQFTW', 'SQLV', 'SQQQ', 'SRAD', 'SRBK', 'SRCE', 'SRDX', 'SRET', 'SRPT', 'SRRK', 'SRTA', 'SRTAW', 'SRTS', 'SRZN',
        'SRZNW', 'SSBI', 'SSEA', 'SSEAR', 'SSEAU', 'SSII', 'SSKN', 'SSM', 'SSNC', 'SSP', 'SSRM', 'SSSS', 'SSSSL', 'SSTI', 'SSYS',
        'STAA', 'STAI', 'STAK', 'STBA', 'STEC', 'STEP', 'STEX', 'STFS', 'STGW', 'STHO', 'STI', 'STIM', 'STKE', 'STKH', 'STKL',
        'STKS', 'STLD', 'STNC', 'STNE', 'STOK', 'STRA', 'STRC', 'STRD', 'STRF', 'STRK', 'STRL', 'STRO', 'STRR', 'STRRP', 'STRS',
        'STRT', 'STRZ', 'STSS', 'STSSW', 'STTK', 'STX', 'SUGP', 'SUIG', 'SUNE', 'SUNS', 'SUPN', 'SUPP', 'SUPX', 'SURG', 'SUSB',
        'SUSC', 'SUSL', 'SUUN', 'SVA', 'SVAC', 'SVACU', 'SVACW', 'SVC', 'SVCC', 'SVCCU', 'SVCCW', 'SVCO', 'SVII', 'SVIIR',
        'SVIIU', 'SVIIW', 'SVRA', 'SVRE', 'SVREW', 'SWAG', 'SWAGW', 'SWBI', 'SWIM', 'SWIN', 'SWKH', 'SWKHL', 'SWKS', 'SWP',
        'SWVL', 'SWVLW', 'SXTC', 'SXTP', 'SXTPW', 'SY', 'SYBT', 'SYBX', 'SYM', 'SYNA', 'SYPR', 'SYRE', 'SYZ', 'SZZL', 'SZZLR',
        'SZZLU', 'TACH', 'TACHU', 'TACHW', 'TACO', 'TACOU', 'TACOW', 'TACT', 'TAIT', 'TALK', 'TALKW', 'TANH', 'TAOP', 'TAOX',
        'TARA', 'TARK', 'TARS', 'TASK', 'TATT', 'TAVI', 'TAVIR', 'TAVIU', 'TAX', 'TAXE', 'TAXI', 'TAXS', 'TAXT', 'TAYD', 'TBBK',
        'TBCH', 'TBH', 'TBHC', 'TBIL', 'TBLA', 'TBLAW', 'TBLD', 'TBMC', 'TBMCR', 'TBPH', 'TBRG', 'TC', 'TCBI', 'TCBIO', 'TCBK',
        'TCBS', 'TCHI', 'TCMD', 'TCOM', 'TCPC', 'TCRT', 'TCRX', 'TCX', 'TDAC', 'TDACU', 'TDACW', 'TDI', 'TDIC', 'TDIV', 'TDSB',
        'TDSC', 'TDTH', 'TDUP', 'TEAD', 'TEAM', 'TECH', 'TECTP', 'TECX', 'TEKX', 'TEKY', 'TELA', 'TELO', 'TEM', 'TENB', 'TENX',
        'TER', 'TERN', 'TEXN', 'TFNS', 'TFSL', 'TGHL', 'TGL', 'TGTX', 'TH', 'THAR', 'THCH', 'THFF', 'THH', 'THMZ', 'THRM',
        'THRV', 'THRY', 'TIGO', 'TIGR', 'TIL', 'TILE', 'TIPT', 'TIRX', 'TITN', 'TIVC', 'TKLF', 'TKNO', 'TLF', 'TLIH', 'TLN',
        'TLNC', 'TLNCU', 'TLNCW', 'TLPH', 'TLRY', 'TLS', 'TLSA', 'TLSI', 'TLSIW', 'TLT', 'TLX', 'TMB', 'TMC', 'TMCI', 'TMCWW',
        'TMDX', 'TMED', 'TMET', 'TMUS', 'TMUSI', 'TMUSL', 'TMUSZ', 'TNDM', 'TNGX', 'TNMG', 'TNON', 'TNXP', 'TNYA', 'TOI',
        'TOIIW', 'TOMZ', 'TONX', 'TOP', 'TORO', 'TOUR', 'TOWN', 'TOYO', 'TPCS', 'TPG', 'TPGXL', 'TPLS', 'TPST', 'TQQQ', 'TQQY',
        'TRAW', 'TRBF', 'TRDA', 'TREE', 'TRI', 'TRIB', 'TRIL', 'TRIN', 'TRINI', 'TRINZ', 'TRIP', 'TRMB', 'TRMD', 'TRMK', 'TRML',
        'TRNR', 'TRNS', 'TRON', 'TROO', 'TROW', 'TRS', 'TRSG', 'TRST', 'TRUD', 'TRUE', 'TRUG', 'TRUP', 'TRUT', 'TRVG', 'TRVI',
        'TSAT', 'TSBK', 'TSCO', 'TSDD', 'TSEL', 'TSEM', 'TSHA', 'TSL', 'TSLA', 'TSLG', 'TSLL', 'TSLQ', 'TSLR', 'TSLS', 'TSMG',
        'TSMU', 'TSMX', 'TSMZ', 'TSPY', 'TSSI', 'TSYY', 'TTAN', 'TTD', 'TTEC', 'TTEK', 'TTEQ', 'TTGT', 'TTMI', 'TTRX', 'TTSH',
        'TTWO', 'TUG', 'TUGN', 'TUR', 'TURB', 'TURF', 'TUSK', 'TVA', 'TVACU', 'TVACW', 'TVAI', 'TVAIR', 'TVAIU', 'TVGN', 'TVGNW',
        'TVRD', 'TVTX', 'TW', 'TWFG', 'TWG', 'TWIN', 'TWNP', 'TWST', 'TXG', 'TXMD', 'TXN', 'TXRH', 'TXSS', 'TXUE', 'TXUG',
        'TYGO', 'TYRA', 'TZOO', 'TZUP', 'UAE', 'UAL', 'UBCP', 'UBFO', 'UBND', 'UBRL', 'UBSI', 'UBXG', 'UCAR', 'UCFI', 'UCFIW',
        'UCL', 'UCRD', 'UCTT', 'UCYB', 'UDMY', 'UEIC', 'UEVM', 'UFCS', 'UFG', 'UFIV', 'UFO', 'UFPI', 'UFPT', 'UG', 'UGRO', 'UHG',
        'UHGWW', 'UITB', 'UIVM', 'UK', 'UKOMW', 'ULBI', 'ULCC', 'ULH', 'ULTA', 'ULVM', 'ULY', 'UMBF', 'UMBFO', 'UMMA', 'UNB',
        'UNCY', 'UNHG', 'UNIT', 'UNIY', 'UNTY', 'UOKA', 'UONE', 'UONEK', 'UPB', 'UPBD', 'UPC', 'UPGR', 'UPLD', 'UPST', 'UPWK',
        'UPXI', 'URBN', 'URGN', 'URNJ', 'UROY', 'USAF', 'USAR', 'USARW', 'USAU', 'USCB', 'USCL', 'USDX', 'USEA', 'USEG', 'USFI',
        'USGO', 'USGOW', 'USIG', 'USIN', 'USIO', 'USLM', 'USMC', 'USOI', 'USOY', 'USRD', 'USSH', 'USTB', 'USVM', 'USVN', 'USXF',
        'UTEN', 'UTHR', 'UTHY', 'UTMD', 'UTRE', 'UTSI', 'UTWO', 'UTWY', 'UVSP', 'UXIN', 'UYLD', 'UYSC', 'UYSCR', 'UYSCU', 'VABK',
        'VACH', 'VACHU', 'VACHW', 'VALN', 'VALU', 'VANI', 'VBIL', 'VBIX', 'VBNK', 'VBTX', 'VC', 'VCEL', 'VCIC', 'VCICU', 'VCICW',
        'VCIG', 'VCIT', 'VCLT', 'VCRB', 'VCSH', 'VCTR', 'VCYT', 'VECO', 'VEEA', 'VEEAW', 'VEEE', 'VELO', 'VEON', 'VERA', 'VERI',
        'VERO', 'VERU', 'VERX', 'VFF', 'VFLO', 'VFS', 'VFSWW', 'VGAS', 'VGASW', 'VGIT', 'VGLT', 'VGSH', 'VGSR', 'VGUS', 'VHC',
        'VIASP', 'VIAV', 'VICR', 'VIGI', 'VINP', 'VIOT', 'VIR', 'VIRC', 'VITL', 'VIVK', 'VIVS', 'VIXI', 'VKTX', 'VLGEA', 'VLY',
        'VLYPN', 'VLYPO', 'VLYPP', 'VMAR', 'VMBS', 'VMD', 'VMEO', 'VNDA', 'VNET', 'VNME', 'VNMEU', 'VNMEW', 'VNOM', 'VNQI',
        'VOD', 'VOLT', 'VONE', 'VONG', 'VONV', 'VOR', 'VOTE', 'VOXR', 'VPLS', 'VRA', 'VRAR', 'VRAX', 'VRCA', 'VRDN', 'VREX',
        'VRIG', 'VRM', 'VRME', 'VRNS', 'VRNT', 'VRRM', 'VRSK', 'VRSN', 'VRTL', 'VRTX', 'VS', 'VSA', 'VSAT', 'VSDA', 'VSEC',
        'VSEE', 'VSEEW', 'VSME', 'VSMV', 'VSSYW', 'VSTA', 'VSTD', 'VSTL', 'VSTM', 'VTC', 'VTGN', 'VTHR', 'VTIP', 'VTRS', 'VTSI',
        'VTVT', 'VTWG', 'VTWO', 'VTWV', 'VTYX', 'VUZI', 'VVOS', 'VVPR', 'VWAV', 'VWAVW', 'VWOB', 'VXUS', 'VYGR', 'VYMI', 'VYNE',
        'WABC', 'WABF', 'WAFD', 'WAFDP', 'WAFU', 'WAI', 'WALD', 'WALDW', 'WASH', 'WATT', 'WAVE', 'WAY', 'WB', 'WBD', 'WBTN',
        'WBUY', 'WCBR', 'WCLD', 'WCT', 'WDAF', 'WDAY', 'WDC', 'WDFC', 'WDGF', 'WEEI', 'WEN', 'WENN', 'WENNU', 'WENNW', 'WERN',
        'WEST', 'WETH', 'WETO', 'WEYS', 'WFCF', 'WFF', 'WFRD', 'WGMI', 'WGRX', 'WGS', 'WGSWW', 'WHF', 'WHFCL', 'WHLR', 'WHLRD',
        'WHLRL', 'WHLRP', 'WHWK', 'WILC', 'WIMI', 'WINA', 'WING', 'WISE', 'WIX', 'WKEY', 'WKHS', 'WKSP', 'WLAC', 'WLACU', 'WLACW',
        'WLDN', 'WLDS', 'WLDSW', 'WLFC', 'WMG', 'WNEB', 'WNW', 'WOK', 'WOOD', 'WOOF', 'WORX', 'WPRT', 'WRAP', 'WRD', 'WRLD',
        'WRND', 'WSBC', 'WSBCO', 'WSBCP', 'WSBF', 'WSBK', 'WSC', 'WSFS', 'WSML', 'WTBA', 'WTBN', 'WTF', 'WTFC', 'WTFCN', 'WTG',
        'WTGUR', 'WTGUU', 'WTIP', 'WTMU', 'WTMY', 'WTO', 'WTW', 'WULF', 'WVE', 'WVVI', 'WVVIP', 'WW', 'WWD', 'WXM', 'WYFI',
        'WYHG', 'WYNN', 'XAIR', 'XAIX', 'XBIL', 'XBIO', 'XBIT', 'XBP', 'XBPEW', 'XBTY', 'XCH', 'XCNY', 'XCUR', 'XEL', 'XELB',
        'XELLL', 'XENE', 'XERS', 'XFIX', 'XFOR', 'XGN', 'XHG', 'XHLD', 'XLO', 'XMAG', 'XMTR', 'XNCR', 'XNET', 'XOMA', 'XOMAO',
        'XOMAP', 'XOMX', 'XOMZ', 'XOS', 'XOSWW', 'XOVR', 'XP', 'XPEL', 'XPON', 'XRAY', 'XRPI', 'XRPT', 'XRTX', 'XRX', 'XT',
        'XTIA', 'XTKG', 'XTLB', 'XWEL', 'XXII', 'XYZG', 'YAAS', 'YB', 'YDDL', 'YDES', 'YDESW', 'YDKG', 'YGMZ', 'YHC', 'YHGJ',
        'YHNA', 'YHNAR', 'YHNAU', 'YI', 'YIBO', 'YJ', 'YLDE', 'YMAT', 'YMT', 'YNOT', 'YOKE', 'YORW', 'YOUL', 'YQ', 'YQQQ',
        'YSPY', 'YSXT', 'YTRA', 'YXT', 'YYAI', 'YYGH', 'Z', 'ZAP', 'ZBAI', 'ZBAO', 'ZBIO', 'ZBRA', 'ZCMD', 'ZD', 'ZDAI', 'ZENA',
        'ZENV', 'ZEO', 'ZEOWW', 'ZEUS', 'ZG', 'ZGM', 'ZIMV', 'ZION', 'ZIONP', 'ZIPP', 'ZJK', 'ZJYL', 'ZKIN', 'ZLAB', 'ZM',
        'ZMUN', 'ZNB', 'ZNTL', 'ZOOZ', 'ZOOZW', 'ZS', 'ZSPC', 'ZTEK', 'ZTEN', 'ZTOP', 'ZTRE', 'ZTWO', 'ZUMZ', 'ZURA', 'ZVRA',
        'ZYBT', 'ZYME', 'ZYN', 'ZYXI'
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
        if not exp_dates:
            return None
        
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
            if calls.empty:
                continue
            
            # Hata Düzeltmesi: Vade tarihini manuel ekle ve sütun adlarını standartlaştır
            calls['expiration'] = date
            calls.columns = calls.columns.str.lower()

            if 'openinterest' not in calls.columns:
                continue
            
            # Filtreleme
            calls = calls[calls['openinterest'] > 50] # Likidite
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
        if all_options.empty:
            return None
        
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

            if info is None or 'shortName' not in info or df is None or df.empty:
                st.error(f"'{ticker_input}' için veri bulunamadı. Lütfen sembolü kontrol edin veya geçerli bir borsa sembolü girdiğinizden emin olun.")
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
                    
                    # Hata Düzeltmesi: Tarih formatı metin olarak geldiği için strptime kullanıldı ve sütun adları küçük harfe çevrildi.
                    exp_date = datetime.strptime(best_option['expiration'], '%Y-%m-%d').strftime('%d %B %Y')
                    
                    o_col1.metric("Vade Tarihi", exp_date)
                    o_col2.metric("Kullanım Fiyatı (Strike)", f"${best_option['strike']:.2f}")
                    o_col3.metric("Kontrat Primi (Maliyet)", f"${best_option['ask']:.2f}")
                    o_col4.metric("Açık Pozisyon", f"{best_option['openinterest']:.0f}")

                    st.info(f"Bu Alım (Call) opsiyonu; 30-45 gün arası vadesi, yüksek likiditesi, dar alım-satım makası ve hisse fiyatına oranla makul maliyeti nedeniyle seçilmiştir. Bu bir yatırım tavsiyesi değildir.")
                else:
                    st.warning("Bu hisse için belirtilen kriterlere (30-45 gün vade, yeterli likidite, düşük maliyet) uygun bir opsiyon kontratı bulunamadı.")



