import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os

try:
    from tvDatafeed import TvDatafeed, Interval
    TV_AVAILABLE = True
except ImportError:
    TV_AVAILABLE = False

st.set_page_config(
    page_title="EGX Analyzer Pro | منصة تحليل البورصة المصرية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://googleapis.com');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans Arabic', sans-serif !important;
    }
    .stApp {
        direction: rtl;
        text-align: right;
    }
    section[data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(148, 163, 184, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.25);
        padding: 12px 14px;
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] div {
        font-size: 19px !important;
        direction: ltr;
        text-align: right;
    }
    div[data-testid="stMetricDelta"] div {
        direction: ltr;
    }
    .timestamp-bar {
        background-color: rgba(2, 132, 199, 0.1);
        border: 1px solid rgba(2, 132, 199, 0.35);
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 14px;
        margin-bottom: 12px;
        display: inline-block;
    }
    .info-card-sidebar {
        background-color: rgba(59, 130, 246, 0.1);
        border-right: 4px solid #3b82f6;
        padding: 10px 12px;
        border-radius: 6px;
        font-size: 12.5px;
        line-height: 1.6;
        margin-top: 8px;
        margin-bottom: 12px;
    }
    .t0-rules-box {
        background-color: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-right: 5px solid #10b981;
        padding: 14px 18px;
        border-radius: 8px;
        font-size: 13.5px;
        line-height: 1.8;
        margin-top: 15px;
    }
    .trend-bull {
        background-color: rgba(22, 163, 74, 0.12);
        border: 1px solid #16a34a;
        border-right: 6px solid #16a34a;
        color: #15803d;
        padding: 12px 18px;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 14px;
    }
    .trend-bear {
        background-color: rgba(220, 38, 38, 0.12);
        border: 1px solid #dc2626;
        border-right: 6px solid #dc2626;
        color: #b91c1c;
        padding: 12px 18px;
        border-radius: 8px;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 14px;
    }
    .disclaimer-box {
        background-color: rgba(100, 116, 139, 0.1);
        border: 1px solid rgba(100, 116, 139, 0.3);
        border-radius: 8px;
        padding: 14px 18px;
        margin-top: 30px;
        font-size: 13px;
        line-height: 1.7;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)
EGX_STOCKS = {
    "COMI.CA": "البنك التجاري الدولي (CIB)",
    "TMGH.CA": "مجموعة طلعت مصطفى القابضة",
    "SWDY.CA": "السويدي إليكتريك",
    "HRHO.CA": "مجموعة إي إف جي القابضة",
    "FWRY.CA": "فوري لتكنولوجيا البنوك",
    "EAST.CA": "الشرقية للدخان",
    "MFPC.CA": "مصر لإنتاج الأسمدة (موبكو)",
    "ABUK.CA": "أبو قير للأسمدة",
    "ETEL.CA": "المصرية للاتصالات",
    "ORAS.CA": "أوراسكوم كونستراكشون",
    "HELI.CA": "مصر الجديدة للإسكان والتعمير",
    "PHDC.CA": "بالم هيلز للتعمير",
    "EFIH.CA": "إي فاينانس للاستثمارات المالية",
    "AMOC.CA": "الإسكندرية للزيوت المعدنية (أموك)",
    "SKPC.CA": "سيدي كرير للبتروكيماويات",
    "ISPH.CA": "ابن سينا فارما",
    "CLHO.CA": "مستشفى كليوباترا",
    "JUFO.CA": "جهينة للصناعات الغذائية",
    "EFID.CA": "إيديتا للصناعات الغذائية",
    "ORWE.CA": "النساجون الشرقيون",
    "GBCO.CA": "جي بي كورب (غبور)",
    "ADIB.CA": "مصرف أبوظبي الإسلامي",
    "CIEB.CA": "بنك كريدي أجريكول مصر",
    "FAIT.CA": "بنك فيصل الإسلامي (جنيه)",
    "HDBK.CA": "بنك التعمير والإسكان",
    "EXPA.CA": "البنك المصري لتنمية الصادرات",
    "CIRA.CA": "القاهرة للاستثمار والتنمية العقارية",
    "MASR.CA": "مدينة مصر للإسكان والتعمير",
    "EMFD.CA": "إعمار مصر للتنمية",
    "OCDI.CA": "السادس من أكتوبر (سوديك)",
    "ORHD.CA": "أوراسكوم للتنمية مصر",
    "BTFH.CA": "بلتون القابضة",
    "CCAP.CA": "القلعة للاستشارات المالية",
    "ASCM.CA": "أسيك للتعدين (أسكوم)",
    "EGAL.CA": "مصر للألومنيوم",
    "ALCN.CA": "الإسكندرية لتداول الحاويات",
    "CSAG.CA": "القناة للتوكيلات الملاحية",
    "MPRC.CA": "المصرية لمدينة الإنتاج الإعلامي",
    "RMDA.CA": "العاشر من رمضان (راميدا)",
    "MCQE.CA": "مصر للأسمنت - قنا",
    "ARCC.CA": "الأسمنت العربية",
    "SVCE.CA": "أسمنت جنوب الوادي",
    "POUL.CA": "القاهرة للدواجن",
    "ISMQ.CA": "الحديد والصلب للمناجم والمحاجر",
    "MPCO.CA": "المنصورة للدواجن",
    "AJWA.CA": "أجواء للصناعات الغذائية",
    "BINV.CA": "بي إنفستمنتس القابضة",
    "ATQA.CA": "عتاقة للصلب",
    "ZMID.CA": "زهراء المعادي للاستثمار",
    "ELSH.CA": "الشمس للإسكان والتعمير",
    "UNIT.CA": "المتحدة للإسكان والتعمير",
    "EHDR.CA": "المصريين للإسكان والتنمية",
    "ACAMD.CA": "العربية لإدارة وتطوير الأصول",
    "DSCW.CA": "دايس للملابس الجاهزة",
    "KABO.CA": "النصر للملابس والمنسوجات (كابو)",
    "SPIN.CA": "الإسكندرية للغزل والنسيج (سبينالكس)",
    "EGTS.CA": "المصرية للمنتجعات السياحية",
    "SDTI.CA": "شارم دريمز للاستثمار السياحي",
    "PHTV.CA": "بيراميزا للفنادق والقرى السياحية",
    "RACC.CA": "راية لخدمات مراكز الاتصالات",
    "RAYA.CA": "راية القابضة للاستثمارات المالية",
    "MTIE.CA": "إم إم جروب للصناعة والتجارة",
    "CNFN.CA": "كونتكت المالية القابضة",
    "OFH.CA": "أوراسكوم المالية القابضة",
    "OIH.CA": "أوراسكوم للاستثمار القابضة"
}
TRADES_FILE = "trades_log.csv"

def get_row_at(df_obj, pos=0):
    target = df_obj.tail(abs(pos)) if pos < 0 else df_obj.iloc[pos:pos+1]
    _, row_data = next(target.iterrows())
    return row_data

def get_first_item(seq, fallback=None):
    return next(iter(seq), fallback)

def load_trades():
    if os.path.exists(TRADES_FILE):
        return pd.read_csv(TRADES_FILE)
    return pd.DataFrame(columns=["تاريخ الإضافة", "الرمز", "اسم الشركة", "سعر الشراء", "وقف الخسارة", "الهدف"])

def save_trade(ticker, name, entry, sl, target):
    df_t = load_trades()
    new_row = pd.DataFrame([{
        "تاريخ الإضافة": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "الرمز": ticker,
        "اسم الشركة": name,
        "سعر الشراء": round(entry, 2),
        "وقف الخسارة": round(sl, 2),
        "الهدف": round(target, 2)
    }])
    df_t = pd.concat([df_t, new_row], ignore_index=True)
    df_t.to_csv(TRADES_FILE, index=False, encoding="utf-8-sig")

def calculate_pivots(high, low, close, method="Classic"):
    p = (high + low + close) / 3
    rng = high - low
    if method == "Fibonacci":
        r1 = p + (0.382 * rng)
        r2 = p + (0.618 * rng)
        r3 = p + (1.000 * rng)
        s1 = p - (0.382 * rng)
        s2 = p - (0.618 * rng)
        s3 = p - (1.000 * rng)
    else:
        r1 = (2 * p) - low
        r2 = p + rng
        r3 = high + 2 * (p - low)
        s1 = (2 * p) - high
        s2 = p - rng
        s3 = low - 2 * (high - p)
        
    return {
        "P": round(p, 2),
        "R1": round(r1, 2), "R2": round(r2, 2), "R3": round(r3, 2),
        "S1": round(s1, 2), "S2": round(s2, 2), "S3": round(s3, 2)
    }

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=900)
def fetch_all_stocks_parallel(tickers_dict, timeframe_choice="15m"):
    results = {}
    fetch_time = datetime.now().strftime("%Y-%m-%d | %I:%M:%S %p")
    tv_client = TvDatafeed() if TV_AVAILABLE else None
    
    def fetch_single(item):
        ticker, name = item
        tv_sym = ticker.replace(".CA", "")
        df_intraday = None
        df_daily = None
        source_used = "TradingView (15m)" if timeframe_choice == "15m" else "TradingView (Daily)"
        
        if tv_client is not None:
            try:
                tv_interval = Interval.in_15_minute if timeframe_choice == "15m" else Interval.in_daily
                df_tv = tv_client.get_hist(symbol=tv_sym, exchange="EGX", interval=tv_interval, n_bars=120)
                df_tv_d = tv_client.get_hist(symbol=tv_sym, exchange="EGX", interval=Interval.in_daily, n_bars=10)
                
                if df_tv is not None and len(df_tv) >= 15 and df_tv_d is not None and len(df_tv_d) >= 2:
                    df_tv = df_tv.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
                    df_tv_d = df_tv_d.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
                    df_intraday = df_tv
                    df_daily = df_tv_d
            except Exception:
                pass

        if df_intraday is None or df_daily is None:
            try:
                source_used = "Yahoo Finance"
                stock = yf.Ticker(ticker)
                df_d = stock.history(period="2mo")
                if timeframe_choice == "15m":
                    df_i = stock.history(period="10d", interval="15m")
                    if len(df_i) >= 15 and len(df_d) >= 2:
                        df_intraday = df_i
                        df_daily = df_d
                else:
                    if len(df_d) >= 15:
                        df_intraday = df_d
                        df_daily = df_d
            except Exception:
                pass

        if df_intraday is not None and df_daily is not None and len(df_intraday) >= 15 and len(df_daily) >= 2:
            df_intraday['RSI'] = calculate_rsi(df_intraday['Close'], 14)
            df_intraday['EMA20'] = df_intraday['Close'].ewm(span=20, adjust=False).mean()
            df_intraday['Vol_Avg10'] = df_intraday['Volume'].rolling(window=10).mean()
            return ticker, (name, df_intraday, df_daily, source_used)
            
        return ticker, None

    with ThreadPoolExecutor(max_workers=2) as executor:
        for ticker, data in executor.map(fetch_single, tickers_dict.items()):
            if data is not None:
                results[ticker] = data
                
    return results, fetch_time
st.sidebar.title("⚡ EGX Analyzer Pro")

if st.sidebar.button("🔄 تحديث الأسعار الآن (Refresh)", width="stretch", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

timeframe_opt = st.sidebar.radio(
    "⏱️ الإطار الزمني للبيانات (Timeframe):",
    ["15m", "Daily"],
    format_func=lambda x: "لحظي كل 15 دقيقة (TradingView 15m)" if x == "15m" else "يومي (Daily)"
)

pivot_method = st.sidebar.selectbox(
    "📐 معادلة الحساب (Pivot Formula):",
    ["Classic", "Fibonacci"]
)

if pivot_method == "Classic":
    st.sidebar.markdown("""
    <div class="info-card-sidebar">
        <strong>📘 المعادلة الكلاسيكية (Classic):</strong><br>
        الأكثر استخداماً في المضاربة اليومية بالبورصة المصرية؛ تعتمد على مضاعفة الفارق بين نقطة الارتكاز وأعلى/أدنى سعر لتحديد مستويات اختراق واضحة وسريعة.
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div class="info-card-sidebar">
        <strong>📙 معادلة فيبوناتشي (Fibonacci):</strong><br>
        تعتمد على النسب الذهبية (<strong>38.2%</strong>، <strong>61.8%</strong>، <strong>100%</strong>) من مدى حركة السعر؛ تعطي مستويات ارتداد أكثر دقة وهدوءاً في الأسهم ذات التذبذب العالي.
    </div>
    """, unsafe_allow_html=True)

custom_ticker = st.sidebar.text_input(
    "🔍 بحث سريع عن أي سهم إضافي:",
    placeholder="اكتب رمز السهم واضغط Enter..."
).strip().upper()

active_stocks = EGX_STOCKS.copy()
if custom_ticker:
    formatted_ticker = custom_ticker if custom_ticker.endswith(".CA") else f"{custom_ticker}.CA"
    if formatted_ticker not in active_stocks:
        active_stocks[formatted_ticker] = f"سهم مخصص ({custom_ticker.replace('.CA', '')})"

saved_trades_df = load_trades()
for t_code in saved_trades_df["الرمز"].unique():
    full_t = f"{t_code}.CA" if not str(t_code).endswith(".CA") else str(t_code)
    if full_t not in active_stocks:
        active_stocks[full_t] = f"سهم مسجل ({t_code})"

with st.spinner("جاري سحب البيانات المحدثة كل 15 دقيقة من TradingView..."):
    raw_market_data, last_update_time = fetch_all_stocks_parallel(active_stocks, timeframe_opt)

summary_list = []
hist_dict = {}
active_source = "TradingView (15m)"

for ticker, (name, df_intra, df_day, src_used) in raw_market_data.items():
    if len(df_intra) >= 2 and len(df_day) >= 2:
        active_source = src_used
        hist_dict[ticker] = df_intra
        
        prev_day = get_row_at(df_day, -2)
        curr_bar = get_row_at(df_intra, -1)
        last_bar_time = df_intra.tail(1).index.strftime("%Y-%m-%d %H:%M").tolist().pop()
        
        pivots = calculate_pivots(prev_day['High'], prev_day['Low'], prev_day['Close'], pivot_method)
        last_close = round(float(curr_bar['Close']), 2)
        change_pct = round(((last_close - float(prev_day['Close'])) / float(prev_day['Close'])) * 100, 2)
        dist_to_r1 = round(((pivots["R1"] - last_close) / last_close) * 100, 2)
        dist_from_pivot = round(((last_close - pivots["P"]) / pivots["P"]) * 100, 2)
        rsi_val = round(float(curr_bar['RSI']), 1) if pd.notna(curr_bar['RSI']) else 50.0
        
        vol_curr = float(curr_bar['Volume'])
        vol_avg = float(curr_bar['Vol_Avg10']) if pd.notna(curr_bar['Vol_Avg10']) and curr_bar['Vol_Avg10'] > 0 else vol_curr
        vol_ratio = round(vol_curr / vol_avg, 2) if vol_avg > 0 else 1.0
        
        if vol_ratio >= 1.5:
            vol_status = f"مرتفع جداً 🔥 ({vol_ratio}x)"
        elif vol_ratio >= 1.1:
            vol_status = f"عالي 📈 ({vol_ratio}x)"
        elif vol_ratio >= 0.7:
            vol_status = f"متوسط ➖ ({vol_ratio}x)"
        else:
            vol_status = f"قليل 📉 ({vol_ratio}x)"
            
        status = "صاعد 🟢" if last_close > pivots["P"] else "هابط 🔴"
        
        if last_close > pivots["P"] and vol_ratio >= 1.3:
            smart_signal = "اختراق بسيولة عالية 🚀"
        elif rsi_val <= 32:
            smart_signal = "تشبع بيعي (ارتداد) 💎"
        elif rsi_val >= 72:
            smart_signal = "تشبع شرائي (حذر) ⚠️"
        elif last_close > pivots["P"]:
            smart_signal = "إيجابي أعلى الارتكاز ✅"
        else:
            smart_signal = "سلبي أدنى الارتكاز 🔻"

        summary_list.append({
            "الرمز": ticker.replace(".CA", ""),
            "اسم الشركة": name,
            "آخر سعر": last_close,
            "التغير %": change_pct,
            "الاتجاه": status,
            "حجم التداول": vol_status,
            "RSI": rsi_val,
            "الإشارة الفنية": smart_signal,
            "الهدف R1 %": dist_to_r1,
            "S3": pivots["S3"], "S2": pivots["S2"], "S1": pivots["S1"],
            "Pivot": pivots["P"],
            "R1": pivots["R1"], "R2": pivots["R2"], "R3": pivots["R3"],
            "نسبة السيولة": vol_ratio,
            "البعد عن الارتكاز %": dist_from_pivot,
            "توقيت الشمعة": last_bar_time,
            "ticker_full": ticker
        })

df_summary = pd.DataFrame(summary_list)

if df_summary.empty:
    st.error("تعذر تحميل البيانات. تأكد من الاتصال بالإنترنت والمحاولة مرة أخرى.")
    st.stop()

symbols_list = df_summary["الرمز"].tolist()
first_symbol = get_first_item(symbols_list)

if "active_symbol" not in st.session_state:
    st.session_state["active_symbol"] = first_symbol

if custom_ticker:
    clean_custom = custom_ticker.replace(".CA", "")
    if clean_custom in symbols_list and st.session_state.get("last_custom") != clean_custom:
        st.session_state["active_symbol"] = clean_custom
        st.session_state["last_custom"] = clean_custom

if st.session_state["active_symbol"] not in symbols_list:
    st.session_state["active_symbol"] = first_symbol

name_map = dict(zip(df_summary["الرمز"], df_summary["اسم الشركة"]))

sidebar_choice = st.sidebar.selectbox(
    f"📈 اختر السهم ({len(df_summary)} سهم متاح):",
    options=symbols_list,
    index=symbols_list.index(st.session_state["active_symbol"]),
    format_func=lambda x: f"{x} - {name_map.get(x, '')}"
)

if sidebar_choice != st.session_state["active_symbol"]:
    st.session_state["active_symbol"] = sidebar_choice
    st.rerun()

selected_short = st.session_state["active_symbol"]
st.title("📊 منصة التحليل الفني للبورصة المصرية | EGX Analyzer Pro")

latest_bar_dt = get_row_at(df_summary, 0)["توقيت الشمعة"]
st.markdown(f"""
<div class="timestamp-bar">
    📡 <strong>المصدر:</strong> {active_source} &nbsp;|&nbsp; 🕒 <strong>آخر سحب:</strong> <span dir="ltr">{last_update_time}</span> &nbsp;|&nbsp; 🕯️ <strong>آخر شمعة:</strong> <span dir="ltr">{latest_bar_dt}</span> &nbsp;|&nbsp; 📊 <strong>السهم المحدد:</strong> {selected_short}
</div>
""", unsafe_allow_html=True)

hot_stocks = df_summary[(df_summary["نسبة السيولة"] >= 1.5) & (df_summary["الاتجاه"] == "صاعد 🟢")]
if not hot_stocks.empty:
    hot_list = " ، ".join(hot_stocks["الرمز"].head(8).tolist())
    st.info(f"🔥 **رادار السيولة اللحظي (15m):** أسهم صاعدة تشهد تدفق سيولة أعلى من 1.5 ضعف المتوسط: **{hot_list}**")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 الشارت والمستويات", 
    "⚡ رادار صفقات T+0 السريعة",
    "📋 رادار السوق (Pivot & Volume)", 
    "🧮 إضافة صفقة جديدة", 
    "📑 تقرير سجل الصفقات"
])

with tab1:
    row = get_row_at(df_summary[df_summary["الرمز"] == selected_short], 0)
    df_chart = hist_dict[row["ticker_full"]]
    
    st.subheader(f"📌 {row['اسم الشركة']} ({selected_short}) — فريم {timeframe_opt}")
    
    if row["آخر سعر"] > row["Pivot"]:
        st.markdown(f"""
        <div class="trend-bull">
            📈 اتجاه السهم: <strong>صاعد (إيجابي)</strong> — السعر ({row['آخر سعر']}) أعلى نقطة الارتكاز ({row['Pivot']}) &nbsp;|&nbsp; 📊 الفوليوم: <strong>{row['حجم التداول']}</strong> &nbsp;|&nbsp; ⚡ RSI: <strong>{row['RSI']}</strong> &nbsp;|&nbsp; 💡 {row['الإشارة الفنية']}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="trend-bear">
            📉 اتجاه السهم: <strong>هابط (سلبي)</strong> — السعر ({row['آخر سعر']}) أدنى نقطة الارتكاز ({row['Pivot']}) &nbsp;|&nbsp; 📊 الفوليوم: <strong>{row['حجم التداول']}</strong> &nbsp;|&nbsp; ⚡ RSI: <strong>{row['RSI']}</strong> &nbsp;|&nbsp; 💡 {row['الإشارة الفنية']}
        </div>
        """, unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("آخر سعر", f"{row['آخر سعر']} EGP", f"{row['التغير %']}%")
    c2.metric("نقطة الارتكاز (P)", f"{row['Pivot']}")
    c3.metric("المقاومة R1", f"{row['R1']}", f"{row['الهدف R1 %']}%")
    c4.metric("المقاومة R2", f"{row['R2']}")
    c5.metric("الدعم S1", f"{row['S1']}")
    c6.metric("حجم التداول", f"{row['نسبة السيولة']}x", "مقارنة بالمتوسط")

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, 
        vertical_spacing=0.04, row_heights=[0.60, 0.18, 0.22]
    )

    fig.add_trace(go.Candlestick(
        x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
        low=df_chart['Low'], close=df_chart['Close'], name="السعر",
        increasing_line_color='#16a34a', decreasing_line_color='#dc2626'
    ), row=1, col=1)

    if 'EMA20' in df_chart.columns:
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart['EMA20'], mode='lines',
            line=dict(color='#f59e0b', width=1.5), name="EMA 20"
        ), row=1, col=1)

    vol_colors = ['#16a34a' if c >= o else '#dc2626' for c, o in zip(df_chart['Close'], df_chart['Open'])]
    fig.add_trace(go.Bar(
        x=df_chart.index, y=df_chart['Volume'], marker_color=vol_colors, name="الحجم", opacity=0.85
    ), row=2, col=1)

    if 'RSI' in df_chart.columns:
        fig.add_trace(go.Scatter(
            x=df_chart.index, y=df_chart['RSI'], mode='lines',
            line=dict(color='#7c3aed', width=2), name="RSI (14)"
        ), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#dc2626", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#16a34a", line_width=1, row=3, col=1)

    levels = [
        ("R3", row["R3"], "#991b1b", "dot"),
        ("R2", row["R2"], "#dc2626", "dash"),
        ("R1", row["R1"], "#ef4444", "solid"),
        ("P", row["Pivot"], "#1d4ed8", "solid"),
        ("S1", row["S1"], "#16a34a", "solid"),
        ("S2", row["S2"], "#15803d", "dash"),
        ("S3", row["S3"], "#166534", "dot"),
    ]

    for lbl, val, clr, dsh in levels:
        fig.add_hline(
            y=val, line_dash=dsh, line_color=clr, line_width=1.8,
            annotation_text=f" {lbl}: {val} ",
            annotation_position="right",
            annotation_font=dict(color="#ffffff", size=10.5, family="IBM Plex Sans Arabic"),
            annotation_bgcolor=clr,
            row=1, col=1
        )

    fig.update_layout(
        font=dict(family="IBM Plex Sans Arabic, sans-serif", size=11),
        height=720,
        margin=dict(l=10, r=90, t=15, b=10),
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    fig.update_xaxes(type="category", nticks=12)
    fig.update_yaxes(title_text="السعر (EGP)", row=1, col=1)
    fig.update_yaxes(title_text="الحجم", row=2, col=1)
    fig.update_yaxes(dict(title_text="RSI (14)", range=list((0, 100))), row=3, col=1)

    st.plotly_chart(fig, width="stretch")
if "table_reset_id" not in st.session_state:
    st.session_state["table_reset_id"] = 0
if "last_clicked_table" not in st.session_state:
    st.session_state["last_clicked_table"] = ""

def render_interactive_table(df_to_show, table_key, styler_obj=None):
    target_obj = styler_obj if styler_obj is not None else df_to_show.style.format(precision=2)
    dynamic_key = f"{table_key}_{st.session_state['table_reset_id']}"
    
    event = st.dataframe(
        target_obj,
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=dynamic_key
    )
    try:
        selected_rows_list = list(event.selection.rows)
        if len(selected_rows_list) > 0:
            selected_row_idx = int(get_first_item(selected_rows_list, 0))
            clicked_ticker = str(get_row_at(df_to_show, selected_row_idx)["الرمز"])
            if clicked_ticker != st.session_state["active_symbol"]:
                st.session_state["active_symbol"] = clicked_ticker
                st.session_state["last_clicked_table"] = table_key
                st.session_state["table_reset_id"] += 1
                st.rerun()
    except Exception:
        pass

with tab2:
    st.subheader("⚡ رادار المضاربة اللحظية السريعة (T+0 Scalping Radar)")
    st.caption("💡 **تلميح:** اضغط على أي سهم في الجداول بالأسفل ليتم تحديده حصرياً في القائمة الجانبية وإلغاء أي تحديد سابق تلقائياً.")

    active_t0_row = get_row_at(df_summary[df_summary["الرمز"] == selected_short], 0)
    t0_entry = float(active_t0_row["آخر سعر"])
    t0_target = float(active_t0_row["R1"]) if t0_entry < float(active_t0_row["R1"]) else float(active_t0_row["R2"])
    if t0_target <= t0_entry:
        t0_target = round(t0_entry * 1.02, 2)
    t0_sl = float(active_t0_row["Pivot"]) if t0_entry > float(active_t0_row["Pivot"]) else float(active_t0_row["S1"])
    if t0_sl >= t0_entry:
        t0_sl = round(t0_entry * 0.985, 2)

    with st.container(border=True):
        st.markdown(f"**⚡ تنفيذ وحفظ صفقة T+0 سريعة للسهم المحدد: `{selected_short}` — {active_t0_row['اسم الشركة']}**")
        q1, q2, q3, q4 = st.columns([1.2, 1.2, 1.2, 1.4])
        q_entry = q1.number_input("سعر الدخول:", value=t0_entry, step=0.05, key=f"t0_e_{selected_short}")
        q_target = q2.number_input("الهدف اللحظي:", value=t0_target, step=0.05, key=f"t0_t_{selected_short}")
        q_sl = q3.number_input("وقف الخسارة:", value=t0_sl, step=0.05, key=f"t0_s_{selected_short}")
        q4.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if q4.button(f"💾 حفظ صفقة {selected_short} (T+0)", type="primary", width="stretch"):
            if q_target > q_entry and q_sl < q_entry:
                save_trade(selected_short, active_t0_row["اسم الشركة"], q_entry, q_sl, q_target)
                st.success(f"تم حفظ صفقة T+0 لسهم **{selected_short}** في تقرير سجل الصفقات بنجاح!")
            else:
                st.error("تأكد أن الهدف أعلى من الدخول والوقف أقل من الدخول.")

    st.markdown("---")

    st.markdown("### 1️⃣ أفضل الخيارات الفنية (T+0) — استراتيجية الاختراق والزخم (Breakout & Momentum)")
    t0_momentum_df = df_summary[
        (df_summary["الاتجاه"] == "صاعد 🟢") &
        (df_summary["نسبة السيولة"] >= 1.0) &
        (df_summary["RSI"] < 68)
    ].sort_values(by="نسبة السيولة", ascending=False).head(6)

    if t0_momentum_df.empty:
        st.info("لا توجد أسهم صاعدة بسيولة أعلى من المتوسط (1.0x) حالياً في هذه الجلسة.")
    else:
        mom_rows = []
        for _, m_row in t0_momentum_df.iterrows():
            target_lvl = m_row["R1"] if m_row["آخر سعر"] < m_row["R1"] else m_row["R2"]
            stop_lvl = m_row["Pivot"] if m_row["آخر سعر"] > m_row["Pivot"] else m_row["S1"]
            mom_rows.append({
                "الرمز": m_row["الرمز"],
                "اسم الشركة": m_row["اسم الشركة"],
                "آخر سعر": m_row["آخر سعر"],
                "حجم التداول": m_row["حجم التداول"],
                "RSI": m_row["RSI"],
                "الهدف اللحظي": target_lvl,
                "وقف الخسارة": stop_lvl,
                "التقييم الفني": "زخم صاعد بسيولة نشطة؛ مناسب للدخول السريع مع الالتزام بالوقف."
            })
        mom_df_clean = pd.DataFrame(mom_rows).reset_index(drop=True)
        render_interactive_table(mom_df_clean, "t0_mom_table")

    st.markdown("---")

    st.markdown("### 2️⃣ أفضل الخيارات الفنية (T+0) — استراتيجية الارتداد الآمن من الارتكاز (Pivot Bounce)")
    t0_bounce_df = df_summary[
        (df_summary["الاتجاه"] == "صاعد 🟢") &
        (df_summary["البعد عن الارتكاز %"] >= 0.0) &
        (df_summary["البعد عن الارتكاز %"] <= 2.2) &
        (df_summary["RSI"] >= 40) &
        (df_summary["RSI"] <= 62) &
        (df_summary["التغير %"] >= 0)
    ].sort_values(by="البعد عن الارتكاز %", ascending=True).head(6)

    if t0_bounce_df.empty:
        st.info("لا توجد أسهم قريبة من نقطة الارتكاز بشروط الأمان المثالية حالياً.")
    else:
        bounce_rows = []
        for _, b_row in t0_bounce_df.iterrows():
            target_b = b_row["R1"] if b_row["آخر سعر"] < b_row["R1"] else b_row["R2"]
            stop_b = b_row["S1"]
            bounce_rows.append({
                "الرمز": b_row["الرمز"],
                "اسم الشركة": b_row["اسم الشركة"],
                "آخر سعر": b_row["آخر سعر"],
                "نقطة الارتكاز": b_row["Pivot"],
                "البعد عن الارتكاز %": b_row["البعد عن الارتكاز %"],
                "RSI": b_row["RSI"],
                "الهدف (R1/R2)": target_b,
                "وقف الخسارة (S1)": stop_b,
                "التقييم الفني": f"مخاطرة منخفضة (أعلى الارتكاز بـ {b_row['البعد عن الارتكاز %']}%)؛ ارتداد متزن."
            })
        bounce_df_clean = pd.DataFrame(bounce_rows).reset_index(drop=True)
        render_interactive_table(bounce_df_clean, "t0_bounce_table")

    st.markdown("---")

    st.markdown("### 3️⃣ أسهم يُفضل تجنبها في الـ T+0 حالياً (رغم صعودها)")
    avoid_df = df_summary[
        (df_summary["الاتجاه"] == "صاعد 🟢") &
        ((df_summary["نسبة السيولة"] < 0.45) | (df_summary["RSI"] >= 68) | (df_summary["التغير %"] < 0))
    ].head(8)

    if not avoid_df.empty:
        avoid_rows = []
        for _, a_row in avoid_df.iterrows():
            reasons = []
            if a_row["نسبة السيولة"] < 0.45:
                reasons.append(f"سيولة ضعيفة جداً ({a_row['نسبة السيولة']}x) تصعّب الخروج السريع")
            if a_row["RSI"] >= 68:
                reasons.append(f"تشبع شرائي مرتفع (RSI = {a_row['RSI']})")
            if a_row["التغير %"] < 0:
                reasons.append(f"تغير لحظي سلبي ({a_row['التغير %']}%)")
            avoid_rows.append({
                "الرمز": a_row["الرمز"],
                "اسم الشركة": a_row["اسم الشركة"],
                "آخر سعر": a_row["آخر سعر"],
                "حجم التداول": a_row["حجم التداول"],
                "RSI": a_row["RSI"],
                "سبب التجنب في T+0": " + ".join(reasons)
            })
        avoid_df_clean = pd.DataFrame(avoid_rows).reset_index(drop=True)
        render_interactive_table(avoid_df_clean, "t0_avoid_table")

    st.markdown("""
    <div class="t0-rules-box">
        <strong>📌 الخلاصة وقواعد المضاربة اللحظية (T+0) على هذه الشاشة:</strong><br>
        1. <strong>قاعدة السيولة أولاً:</strong> في السوق المصري، السهم ذو الفوليوم الأقل من <code>0.7x</code> قد يرتفع بصفقات صغيرة لكنه يحبس المضارب عند البيع؛ امنح الأولوية دائماً للأسهم ذات السيولة الأعلى.<br>
        2. <strong>قاعدة القرب من الارتكاز:</strong> أفضل نقطة دخول في صفقات الارتداد هي عندما يكون السعر قريباً جداً من <code>Pivot</code> (فارق أقل من <code>1.5%</code>) ليكون وقف الخسارة قريباً ومحدداً.<br>
        3. <strong>قاعدة RSI المثالي:</strong> استهدف الأسهم التي يتراوح فيها <code>RSI</code> بين <strong>45 و 60</strong>، وتجنب الدخول الجديد عندما يتجاوز <strong>68</strong>.<br>
        4. <strong>الانضباط اللحظي:</strong> لا تحوّل صفقة <code>T+0</code> خاسرة إلى استثمار طويل الأجل؛ كسر مستوى الارتكاز أو الدعم المحدد هو إشارة خروج فورية.
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.subheader(f"📋 رادار البورصة المصرية الشامل ({pivot_method} Pivots — {timeframe_opt})")
    st.caption("💡 **تلميح:** اضغط على أي صف في الجدول بالأسفل ليتم اختيار السهم تلقائياً في القائمة الجانبية وإلغاء أي تحديد سابق.")
    
    col_f1, col_f2 = st.columns(2)
    filter_opt = col_f1.radio("تصفية حسب الاتجاه:", ["الكل", "صاعد 🟢", "هابط 🔴"], horizontal=True)
    vol_filter = col_f2.radio("تصفية حسب حجم التداول (Volume):", ["جميع الأحجام", "سيولة مرتفعة 🔥 / عالية 📈", "سيولة قليلة 📉"], horizontal=True)
    
    table_df = df_summary.drop(columns=["ticker_full", "توقيت الشمعة", "نسبة السيولة", "البعد عن الارتكاز %"]).reset_index(drop=True)
    if filter_opt != "الكل":
        table_df = table_df[table_df["الاتجاه"] == filter_opt].reset_index(drop=True)
    if vol_filter == "سيولة مرتفعة 🔥 / عالية 📈":
        table_df = table_df[table_df["حجم التداول"].str.contains("مرتفع|عالي")].reset_index(drop=True)
    elif vol_filter == "سيولة قليلة 📉":
        table_df = table_df[table_df["حجم التداول"].str.contains("قليل")].reset_index(drop=True)

    def style_table(val):
        if isinstance(val, str):
            if "صاعد" in val or "مرتفع" in val or "اختراق" in val: return "color: #16a34a; font-weight: bold;"
            if "هابط" in val or "سلبي" in val: return "color: #dc2626; font-weight: bold;"
            if "عالي" in val or "تشبع بيعي" in val: return "color: #2563eb; font-weight: bold;"
        return ""

    radar_styler = (
        table_df.style
        .map(style_table)
        .background_gradient(subset=["S1", "S2", "S3"], cmap="Greens", low=0.25, high=0.55)
        .background_gradient(subset=["R1", "R2", "R3"], cmap="Reds", low=0.25, high=0.55)
        .format(precision=2)
    )
    render_interactive_table(table_df, "radar_table_select", radar_styler)

with tab4:
    st.subheader(f"🧮 تسجيل صفقة جديدة ومتابعتها لسهم {selected_short}")
    row = get_row_at(df_summary[df_summary["الرمز"] == selected_short], 0)
    
    curr_price_val = float(row["آخر سعر"])
    
    valid_supports = [float(row["S1"]), float(row["S2"]), float(row["S3"])]
    below_supports = [s for s in valid_supports if s < curr_price_val]
    default_sl = float(get_first_item(below_supports, round(curr_price_val * 0.98, 2)))

    valid_resistances = [float(row["Pivot"]), float(row["R1"]), float(row["R2"]), float(row["R3"])]
    above_resistances = [r for r in valid_resistances if r > curr_price_val]
    default_target = float(get_first_item(above_resistances, round(curr_price_val * 1.03, 2)))
    
    col_in1, col_in2, col_in3 = st.columns(3)
    entry_price = col_in1.number_input("سعر الشراء (EGP):", value=curr_price_val, step=0.05, key=f"entry_{selected_short}")
    stop_loss = col_in2.number_input("وقف الخسارة (أقرب دعم فعلي):", value=default_sl, step=0.05, key=f"sl_{selected_short}")
    target_price = col_in3.number_input("سعر الهدف (أقرب مقاومة فعلية):", value=default_target, step=0.05, key=f"target_{selected_short}")

    risk = entry_price - stop_loss
    reward = target_price - entry_price

    st.markdown("---")
    if risk > 0 and reward > 0:
        rr_ratio = round(reward / risk, 2)
        risk_pct = round((risk / entry_price) * 100, 2)
        reward_pct = round((reward / entry_price) * 100, 2)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("نسبة المخاطرة (Risk)", f"-{risk_pct}%", f"-{round(risk, 2)} EGP", delta_color="inverse")
        m2.metric("العائد المتوقع (Reward)", f"+{reward_pct}%", f"+{round(reward, 2)} EGP")
        m3.metric("نسبة العائد للمخاطرة (R:R)", f"1 : {rr_ratio}", "ممتازة" if rr_ratio >= 2 else "متوسطة")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 حفظ الصفقة في التقرير لمتابعتها مع التحديثات", type="primary", width="stretch"):
            save_trade(selected_short, row["اسم الشركة"], entry_price, stop_loss, target_price)
            st.success(f"تم حفظ صفقة **{selected_short}** بتوقيت ({datetime.now().strftime('%Y-%m-%d %H:%M')})! انتقل إلى تبويب **(📑 تقرير سجل الصفقات)** للمتابعة.")
    else:
        st.warning("تأكد من أن سعر الهدف أعلى من سعر الشراء، وسعر وقف الخسارة أقل من سعر الشراء.")

with tab5:
    st.subheader("📑 التقرير الإحصائي الشامل للصفقات المسجلة")
    trades_df = load_trades()

    if trades_df.empty:
        st.info("لا توجد صفقات مسجلة حتى الآن. يمكنك تسجيل صفقاتك من تبويب **(🧮 إضافة صفقة جديدة)**.")
    else:
        evaluated_rows = []
        wins_count = 0
        losses_count = 0
        open_count = 0

        for _, t_row in trades_df.iterrows():
            sym = str(t_row["الرمز"])
            full_sym = f"{sym}.CA" if not sym.endswith(".CA") else sym
            entry_dt = pd.to_datetime(t_row["تاريخ الإضافة"])
            
            entry = float(t_row["سعر الشراء"])
            sl = float(t_row["وقف الخسارة"])
            target = float(t_row["الهدف"])
            
            status_label = "مفتوحة (جارية) ⏳"
            curr_p = entry

            if full_sym in hist_dict:
                stock_df = hist_dict[full_sym].copy()
                if stock_df.index.tz is not None:
                    stock_df.index = stock_df.index.tz_localize(None)
                curr_p = round(float(get_row_at(stock_df, -1)["Close"]), 2)
                
                future_bars = stock_df[stock_df.index > entry_dt]
                
                if not future_bars.empty:
                    for _, s_row in future_bars.iterrows():
                        if float(s_row["Low"]) <= sl:
                            status_label = "خاسرة (وقف خسارة) ❌"
                            break
                        elif float(s_row["High"]) >= target:
                            status_label = "ناجحة (تحقق الهدف) ✅"
                            break
                else:
                    if curr_p != entry:
                        if curr_p >= target:
                            status_label = "ناجحة (تحقق الهدف) ✅"
                        elif curr_p <= sl:
                            status_label = "خاسرة (وقف خسارة) ❌"

            if "ناجحة" in status_label:
                wins_count += 1
            elif "خاسرة" in status_label:
                losses_count += 1
            else:
                open_count += 1

            current_pnl_pct = round(((curr_p - entry) / entry) * 100, 2)

            evaluated_rows.append({
                "تاريخ ووقت الإضافة": t_row["تاريخ الإضافة"],
                "الرمز": sym,
                "اسم الشركة": t_row["اسم الشركة"],
                "سعر الشراء": entry,
                "وقف الخسارة": sl,
                "الهدف": target,
                "السعر الحالي": curr_p,
                "العائد الحالي %": current_pnl_pct,
                "حالة الصفقة": status_label
            })

        total_trades = len(evaluated_rows)
        closed_trades = wins_count + losses_count
        win_rate_total = round((wins_count / total_trades) * 100, 1) if total_trades > 0 else 0.0
        loss_rate_total = round((losses_count / total_trades) * 100, 1) if total_trades > 0 else 0.0
        win_rate_closed = round((wins_count / closed_trades) * 100, 1) if closed_trades > 0 else 0.0

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("إجمالي الصفقات", f"{total_trades}")
        k2.metric("صفقات ناجحة ✅", f"{wins_count}", f"{win_rate_total}% من الإجمالي")
        k3.metric("صفقات خاسرة ❌", f"{losses_count}", f"-{loss_rate_total}% من الإجمالي", delta_color="inverse")
        k4.metric("صفقات مفتوحة ⏳", f"{open_count}")
        k5.metric("نسبة النجاح (المغلقة)", f"{win_rate_closed}%")
        k6.metric("نسبة الخسارة (المغلقة)", f"{round(100 - win_rate_closed, 1) if closed_trades > 0 else 0.0}%")

        st.markdown("<br>", unsafe_allow_html=True)

        eval_df = pd.DataFrame(evaluated_rows)

        def style_trade_status(val):
            if isinstance(val, str):
                if "ناجحة" in val: return "color: #16a34a; font-weight: bold;"
                if "خاسرة" in val: return "color: #dc2626; font-weight: bold;"
                if "مفتوحة" in val: return "color: #d97706; font-weight: bold;"
            return ""

        st.dataframe(
            eval_df.style
            .map(style_trade_status, subset=["حالة الصفقة"])
            .format(precision=2),
            width="stretch",
            hide_index=True
        )

        col_btn1, col_btn2 = st.columns(2)
        csv_export = eval_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        col_btn1.download_button(
            label="📥 تحميل التقرير بصيغة Excel / CSV",
            data=csv_export,
            file_name=f"EGX_Trades_Report_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )
        if col_btn2.button("🗑️ مسح سجل الصفقات بالكامل"):
            if os.path.exists(TRADES_FILE):
                os.remove(TRADES_FILE)
            st.rerun()

st.markdown("""
<div class="disclaimer-box">
    ⚠️ <strong>إخلاء مسؤولية (Disclaimer):</strong><br>
    جميع البيانات والمستويات السعرية ومؤشرات التحليل الفني المعروضة في منصة <strong>EGX Analyzer Pro</strong> هي لأغراض تعليمية واسترشادية فقط، ولا تُعد بأي حال من الأحوال توصية مباشرة بالبيع أو الشراء. التداول في سوق الأوراق المالية ينطوي على مخاطر عالية، وقرارك الاستثماري هو مسؤوليتك الشخصية الكاملة.
</div>
""", unsafe_allow_html=True)
