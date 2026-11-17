import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
import os

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
    cairo_tz = pytz.timezone("Africa/Cairo")
    now_str = datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M")
    new_row = pd.DataFrame([{
        "تاريخ الإضافة": now_str,
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

@st.cache_data(ttl=180)
def fetch_all_stocks_parallel(tickers_dict):
    results = {}
    cairo_tz = pytz.timezone("Africa/Cairo")
    fetch_time = datetime.now(cairo_tz).strftime("%Y-%m-%d | %I:%M:%S %p")
    tickers_list = list(tickers_dict.keys())
    
    try:
        raw_daily = yf.download(
            tickers=tickers_list,
            period="4mo",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False
        )
    except Exception:
        return results, fetch_time

    raw_intra = pd.DataFrame()
    try:
        raw_intra = yf.download(
            tickers=tickers_list,
            period="2d",
            interval="15m",
            group_by="ticker",
            threads=True,
            progress=False
        )
    except Exception:
        pass

    for ticker, name in tickers_dict.items():
        try:
            if isinstance(raw_daily.columns, pd.MultiIndex):
                if ticker not in raw_daily.columns.get_level_values(0):
                    continue
                df_daily = raw_daily[ticker].dropna(subset=["Close"]).copy()
            else:
                df_daily = raw_daily.dropna(subset=["Close"]).copy()

            if len(df_daily) < 15:
                continue

            df_daily.index = pd.to_datetime(df_daily.index).tz_localize(None)
            last_daily_date = df_daily.index[-1].date()

            if not raw_intra.empty:
                df_intra = pd.DataFrame()
                if isinstance(raw_intra.columns, pd.MultiIndex):
                    if ticker in raw_intra.columns.get_level_values(0):
                        df_intra = raw_intra[ticker].dropna(subset=["Close"]).copy()
                else:
                    df_intra = raw_intra.dropna(subset=["Close"]).copy()

                if not df_intra.empty:
                    df_intra.index = pd.to_datetime(df_intra.index).tz_localize(None)
                    latest_intra_date = df_intra.index[-1].date()
                    if latest_intra_date >= last_daily_date:
                        today_bars = df_intra[df_intra.index.date == latest_intra_date]
                        if not today_bars.empty:
                            live_open = float(next(iter(today_bars["Open"])))
                            live_high = float(today_bars["High"].max())
                            live_low = float(today_bars["Low"].min())
                            live_close = float(today_bars["Close"].iloc[-1])
                            live_vol = float(today_bars["Volume"].sum())

                            new_ts = pd.Timestamp(latest_intra_date)
                            if latest_intra_date == last_daily_date:
                                df_daily.loc[df_daily.index[-1], ["Open", "High", "Low", "Close", "Volume"]] = [
                                    live_open, live_high, live_low, live_close, live_vol
                                ]
                            else:
                                new_candle = pd.DataFrame({
                                    "Open": [live_open],
                                    "High": [live_high],
                                    "Low": [live_low],
                                    "Close": [live_close],
                                    "Volume": [live_vol]
                                }, index=[new_ts])
                                df_daily = pd.concat([df_daily, new_candle])

            df_daily['RSI'] = calculate_rsi(df_daily['Close'], 14)
            df_daily['EMA20'] = df_daily['Close'].ewm(span=20, adjust=False).mean()
            df_daily['Vol_Avg10'] = df_daily['Volume'].rolling(window=10).mean()
            results[ticker] = (name, df_daily)
        except Exception:
            continue

    return results, fetch_time
st.sidebar.title("⚡ EGX Analyzer Pro")

if st.sidebar.button("🔄 تحديث الأسعار اللحظية الآن (Refresh)", use_container_width=True, type="primary"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")

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

with st.spinner("جاري سحب البيانات اللحظية واليومية للبورصة المصرية..."):
    raw_market_data, last_update_time = fetch_all_stocks_parallel(active_stocks)

summary_list = []
hist_dict = {}

for ticker, (name, df) in raw_market_data.items():
    if len(df) >= 2:
        hist_dict[ticker] = df
        prev = df.iloc[-2]
        curr = df.iloc[-1]
        last_session_date = df.index[-1].strftime("%Y-%m-%d")
        
        pivots = calculate_pivots(prev['High'], prev['Low'], prev['Close'], pivot_method)
        last_close = round(curr['Close'], 2)
        session_high = round(curr['High'], 2)
        session_low = round(curr['Low'], 2)
        change_pct = round(((last_close - prev['Close']) / prev['Close']) * 100, 2)
        dist_to_r1 = round(((pivots["R1"] - last_close) / last_close) * 100, 2)
        rsi_val = round(curr['RSI'], 1) if pd.notna(curr['RSI']) else 50.0
        
        vol_curr = float(curr['Volume'])
        vol_avg = float(curr['Vol_Avg10']) if pd.notna(curr['Vol_Avg10']) and curr['Vol_Avg10'] > 0 else vol_curr
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
            "السعر": last_close,
            "أعلى الجلسة": session_high,
            "أقل الجلسة": session_low,
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
            "تاريخ الجلسة": last_session_date,
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

latest_market_date = df_summary["تاريخ الجلسة"].max()
st.markdown(f"""
<div class="timestamp-bar">
    🕒 <strong>آخر تحديث (توقيت القاهرة):</strong> <span dir="ltr">{last_update_time}</span> &nbsp;|&nbsp; 📅 <strong>أحدث جلسة معروضة:</strong> <span dir="ltr">{latest_market_date}</span> &nbsp;|&nbsp; 📊 <strong>الأسهم المحللة:</strong> {len(df_summary)} سهم
</div>
""", unsafe_allow_html=True)

hot_stocks = df_summary[(df_summary["نسبة السيولة"] >= 1.5) & (df_summary["الاتجاه"] == "صاعد 🟢")]
if not hot_stocks.empty:
    hot_list = " ، ".join(hot_stocks["الرمز"].head(8).tolist())
    st.info(f"🔥 **رادار السيولة المرتفعة:** أسهم صاعدة تشهد تدفق سيولة أعلى من 1.5 ضعف المتوسط: **{hot_list}**")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 الشارت والمستويات", 
    "📋 رادار السوق (Pivot & Volume)", 
    "🧮 إضافة صفقة جديدة", 
    "📑 تقرير سجل الصفقات"
])

with tab1:
    row = get_first_row(df_summary[df_summary["الرمز"] == selected_short])
    df_chart = hist_dict[row["ticker_full"]]
    
    st.subheader(f"📌 {row['اسم الشركة']} ({selected_short}) — جلسة {row['تاريخ الجلسة']}")
    
    if row["السعر"] > row["Pivot"]:
        st.markdown(f"""
        <div class="trend-bull">
            📈 اتجاه السهم: <strong>صاعد (إيجابي)</strong> — السعر ({row['السعر']}) أعلى نقطة الارتكاز ({row['Pivot']}) &nbsp;|&nbsp; 📊 الفوليوم: <strong>{row['حجم التداول']}</strong> &nbsp;|&nbsp; ⚡ RSI: <strong>{row['RSI']}</strong> &nbsp;|&nbsp; 💡 {row['الإشارة الفنية']}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="trend-bear">
            📉 اتجاه السهم: <strong>هابط (سلبي)</strong> — السعر ({row['السعر']}) أدنى نقطة الارتكاز ({row['Pivot']}) &nbsp;|&nbsp; 📊 الفوليوم: <strong>{row['حجم التداول']}</strong> &nbsp;|&nbsp; ⚡ RSI: <strong>{row['RSI']}</strong> &nbsp;|&nbsp; 💡 {row['الإشارة الفنية']}
        </div>
        """, unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("السعر الحالي / الإغلاق", f"{row['السعر']} EGP", f"{row['التغير %']}%")
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
    fig.update_yaxes(title_text="السعر (EGP)", row=1, col=1)
    fig.update_yaxes(title_text="الحجم", row=2, col=1)
    fig.update_yaxes(dict(title_text="RSI (14)", range=list((0, 100))), row=3, col=1)

    st.plotly_chart(fig, use_container_width=True)
with tab2:
    st.subheader(f"📋 رادار البورصة المصرية الشامل ({pivot_method} Pivots)")
    
    col_f1, col_f2 = st.columns(2)
    filter_opt = col_f1.radio("تصفية حسب الاتجاه:", ["الكل", "صاعد 🟢", "هابط 🔴"], horizontal=True)
    vol_filter = col_f2.radio("تصفية حسب حجم التداول (Volume):", ["جميع الأحجام", "سيولة مرتفعة 🔥 / عالية 📈", "سيولة قليلة 📉"], horizontal=True)
    
    table_df = df_summary.drop(columns=["ticker_full", "أعلى الجلسة", "أقل الجلسة", "نسبة السيولة"])
    if filter_opt != "الكل":
        table_df = table_df[table_df["الاتجاه"] == filter_opt]
    if vol_filter == "سيولة مرتفعة 🔥 / عالية 📈":
        table_df = table_df[table_df["حجم التداول"].str.contains("مرتفع|عالي")]
    elif vol_filter == "سيولة قليلة 📉":
        table_df = table_df[table_df["حجم التداول"].str.contains("قليل")]

    def style_table(val):
        if isinstance(val, str):
            if "صاعد" in val or "مرتفع" in val or "اختراق" in val: return "color: #16a34a; font-weight: bold;"
            if "هابط" in val or "سلبي" in val: return "color: #dc2626; font-weight: bold;"
            if "عالي" in val or "تشبع بيعي" in val: return "color: #2563eb; font-weight: bold;"
        return ""

    st.dataframe(
        table_df.style
        .map(style_table)
        .background_gradient(subset=["S1", "S2", "S3"], cmap="Greens", low=0.25, high=0.55)
        .background_gradient(subset=["R1", "R2", "R3"], cmap="Reds", low=0.25, high=0.55)
        .format(precision=2),
        use_container_width=True,
        hide_index=True
    )

with tab3:
    st.subheader(f"🧮 تسجيل صفقة جديدة ومتابعتها لسهم {selected_short}")
    row = get_first_row(df_summary[df_summary["الرمز"] == selected_short])
    
    col_in1, col_in2, col_in3 = st.columns(3)
    entry_price = col_in1.number_input("سعر الشراء (EGP):", value=float(row["السعر"]), step=0.05)
    stop_loss = col_in2.number_input("سعر وقف الخسارة (مقترح S1):", value=float(row["S1"]), step=0.05)
    target_price = col_in3.number_input("سعر الهدف (مقترح R1):", value=float(row["R1"]), step=0.05)

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
        if st.button("💾 حفظ الصفقة في التقرير لمتابعتها مع التحديثات", type="primary", use_container_width=True):
            save_trade(selected_short, row["اسم الشركة"], entry_price, stop_loss, target_price)
            cairo_tz = pytz.timezone("Africa/Cairo")
            st.success(f"تم حفظ صفقة **{selected_short}** بتوقيت ({datetime.now(cairo_tz).strftime('%Y-%m-%d %H:%M')})! انتقل إلى تبويب **(📑 تقرير سجل الصفقات)** للمتابعة.")
    else:
        st.warning("تأكد من أن سعر الهدف أعلى من سعر الشراء، وسعر وقف الخسارة أقل من سعر الشراء.")

with tab4:
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
            entry_date_only = entry_dt.date()
            
            entry = float(t_row["سعر الشراء"])
            sl = float(t_row["وقف الخسارة"])
            target = float(t_row["الهدف"])
            
            status_label = "مفتوحة (جارية) ⏳"
            curr_p = entry

            if full_sym in hist_dict:
                stock_df = hist_dict[full_sym].copy()
                stock_df.index = stock_df.index.tz_localize(None)
                curr_p = round(float(stock_df.iloc[-1]["Close"]), 2)
                
                future_sessions = stock_df[stock_df.index.date > entry_date_only]
                
                if not future_sessions.empty:
                    for _, s_row in future_sessions.iterrows():
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
            use_container_width=True,
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
