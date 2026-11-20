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
    "ESRS.CA": "حدايد عز",
    "EFIH.CA": "إي فاينانس للاستثمارات المالية",
    "EKHO.CA": "القابضة المصرية الكويتية (دولار)",
    "EKHOA.CA": "القابضة المصرية الكويتية (جنيه)",
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
    "VALU.CA": "فاليو للتمويل الاستهلاكي",
    "ACTF.CA": "أكت فاينانشال للاستشارات",
    "OFH.CA": "أوراسكوم المالية القابضة",
    "OIH.CA": "أوراسكوم للاستثمار القابضة"
}
TRADES_FILE = "trades_log.csv"

def get_first_row(df_obj):
    return next(df_obj.iterrows())

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
        source_used = "TradingView (15m)"
        
        if tv_client is not None:
            try:
                tv_interval = Interval.in_15_minute if timeframe_choice == "15m" else Interval.in_daily
                df_tv = tv_client.get_hist(symbol=tv_sym, exchange="EGX", interval=tv_interval, n_bars=120)
                df_tv_d = tv_client.get_hist(symbol=tv_sym, exchange="EGX", interval=Interval.in_daily, n_bars=10)
                
                if df_tv is not None and len(df_tv) >= 15 and df_tv_d is not None and len(df_tv_d) >= 2:
                    df_tv.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
                    df_tv_d.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True)
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

    with ThreadPoolExecutor(max_workers=10) as executor:
        for ticker, data in executor.map(fetch_single, tickers_dict.items()):
            if data is not None:
                results[ticker] = data
                
    return results, fetch_time
st.sidebar.title("⚡ EGX Analyzer Pro")

if st.sidebar.button("🔄 تحديث الأسعار الآن (Refresh)", use_container_width=True, type="primary"):
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
        
        prev_day = df_day.iloc[-2]
        curr_bar = df_intra.iloc[-1]
        last_bar_time = df_intra.index[-1].strftime("%Y-%m-%d %H:%M")
        
        pivots = calculate_pivots(prev_day['High'], prev_day['Low'], prev_day['Close'], pivot_method)
        last_close = round(float(curr_bar['Close']), 2)
        bar_high = round(float(curr_bar['High']), 2)
        bar_low = round(float(curr_bar['Low']), 2)
        change_pct = round(((last_close - float(prev_day['Close'])) / float(prev_day['Close'])) * 100, 2)
        dist_to_r1 = round(((pivots["R1"] - last_close) / last_close) * 100, 2)
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
            "أعلى الشمعة": bar_high,
            "أقل الشمعة": bar_low,
            "التغير %": change_pct,
            "الاتجاه": status,
            "حجم التداول": vol_status,
            "نسبة السيولة": vol_ratio,
            "RSI": rsi_val,
            "الإشارة الفنية": smart_signal,
            "S3": pivots["S3"], "S2": pivots["S2"], "S1": pivots["S1"],
            "Pivot": pivots["P"],
            "R1": pivots["R1"], "R2": pivots["R2"], "R3": pivots["R3"],
            "المسافة لـ R1 %": dist_to_r1,
            "توقيت الشمعة": last_bar_time,
            "ticker_full": ticker
        })

df_summary = pd.DataFrame(summary_list)

if df_summary.empty:
    st.error("تعذر تحميل البيانات. تأكد من الاتصال بالإنترنت والمحاولة مرة أخرى.")
    st.stop()

default_index = 0
if custom_ticker:
    clean_custom = custom_ticker.replace(".CA", "")
    if clean_custom in df_summary["الرمز"].values:
        default_index = df_summary["الرمز"].tolist().index(clean_custom)

name_map = dict(zip(df_summary["الرمز"], df_summary["اسم الشركة"]))

selected_short = st.sidebar.selectbox(
    f"📈 اختر السهم ({len(df_summary)} سهم متاح):",
    options=df_summary["الرمز"].tolist(),
    index=default_index,
    format_func=lambda x: f"{x} - {name_map.get(x, '')}"
)

st.title("📊 منصة التحليل الفني للبورصة المصرية | EGX Analyzer Pro")

latest_bar_dt = get_first_row(df_summary)["توقيت الشمعة"]
st.markdown(f"""
<div class="timestamp-bar">
    📡 <strong>المصدر:</strong> {active_source} &nbsp;|&nbsp; 🕒 <strong>آخر سحب:</strong> <span dir="ltr">{last_update_time}</span> &nbsp;|&nbsp; 🕯️ <strong>آخر شمعة:</strong> <span dir="ltr">{latest_bar_dt}</span> &nbsp;|&nbsp; 📊 <strong>الأسهم:</strong> {len(df_summary)}
</div>
""", unsafe_allow_html=True)

hot_stocks = df_summary[(df_summary["نسبة السيولة"] >= 1.5) & (df_summary["الاتجاه"] == "صاعد 🟢")]
if not hot_stocks.empty:
    hot_list = " ، ".join(hot_stocks["الرمز"].head(8).tolist())
    st.info(f"🔥 **رادار السيولة اللحظي (15m):** أسهم صاعدة تشهد تدفق سيولة أعلى من 1.5 ضعف المتوسط: **{hot_list}**")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 الشارت والمستويات", 
    "📋 رادار السوق (Pivot & Volume)", 
    "🧮 إضافة صفقة جديدة", 
    "📑 تقرير سجل الصفقات"
])

with tab1:
    row = get_first_row(df_summary[df_summary["الرمز"] == selected_short])
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
    c3.metric("المقاومة R1", f"{row['R1']}", f"+{row['المسافة لـ R1 %']}%")
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

    st.plotly_chart(fig, use_container_width=True)
