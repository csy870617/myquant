import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="유동성 × 시장 분석기", 
    page_icon="icon.png", 
    layout="wide"
)

try:
    st.logo("icon.png")
except:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_next_refresh():
    utc_now = datetime.now(ZoneInfo("UTC"))
    utc_hours = [0, 2, 9, 17]
    targets = []
    for h in utc_hours:
        t = utc_now.replace(hour=h, minute=0, second=0, microsecond=0)
        if t <= utc_now:
            t += timedelta(days=1)
        targets.append(t)
    next_t = min(targets)
    secs = max(int((next_t - utc_now).total_seconds()), 60)
    return next_t, secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()
st.markdown(f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS (스타일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');

:root { --bg: #ffffff; --text-primary: #222222; --text-secondary: #8d929b; --border: #ececec; --up-color: #f73646; --down-color: #335eff; }
html, body, [data-testid="stAppViewContainer"] { font-family: 'Pretendard', sans-serif; background: var(--bg) !important; color: var(--text-primary); }
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100%; }

/* 헤더 */
.stock-header-container { padding-bottom: 15px; border-bottom: 1px solid var(--border); margin-bottom: 15px; }
.stock-title-row { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
.stock-name { font-size: 1.5rem; font-weight: 800; color: #111; letter-spacing: -0.5px; }
.stock-ticker { font-size: 0.95rem; color: var(--text-secondary); font-weight: 500; }
.stock-price-row { display: flex; align-items: flex-end; gap: 12px; }
.stock-price { font-family: 'Roboto Mono', sans-serif; font-size: 2.4rem; font-weight: 700; letter-spacing: -1px; line-height: 1; }
.stock-change { font-size: 1.1rem; font-weight: 600; padding-bottom: 4px; }
.c-up { color: var(--up-color); }
.c-down { color: var(--down-color); }
.c-flat { color: #333; }

/* 요약 바 */
.summary-bar { display: flex; gap: 15px; overflow-x: auto; padding-bottom: 5px; margin-bottom: 10px; font-size: 0.85rem; color: #555; -ms-overflow-style: none; scrollbar-width: none; }
.summary-bar::-webkit-scrollbar { display: none; }
.summary-item { white-space: nowrap; display: flex; align-items: center; gap: 5px; background: #f8f9fa; padding: 6px 12px; border-radius: 18px; border: 1px solid #eee; }
.summary-label { color: #888; font-weight: 500; }
.summary-value { font-weight: 700; color: #333; }

/* 컨트롤 */
[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; margin-bottom: 10px; }
.stSelectbox label, .stMultiSelect label, .stRadio label { font-size: 0.75rem !important; color: #666 !important; }
.stSelectbox > div > div { background-color: #f9f9f9 !important; border: 1px solid #ddd !important; border-radius: 6px !important; }

/* 리포트 박스 */
.report-box { background: #f9fbfc; border: 1px solid #e8ecf2; border-radius: 12px; padding: 1.2rem; margin-bottom: 1.2rem; margin-top: 1rem; }
.report-header { display: flex; align-items: center; gap: 8px; margin-bottom: 0.8rem; }
.report-badge { background: #222; color: white; font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; }
.report-title { font-size: 1rem; font-weight: 700; color: #333; }
.report-body { font-size: 0.88rem; color: #555; line-height: 1.7; }
.report-body strong { color: #111; }
.hl { background: rgba(0,0,0,0.05); padding: 0 4px; border-radius: 3px; font-weight: 600; }
.report-divider { border-top: 1px dashed #ddd; margin: 10px 0; }

/* 타임라인 */
.timeline { display: flex; flex-direction: column; gap: 0; border-top: 1px solid #eee; margin-top: 10px; }
.tl-item { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f5f5f5; font-size: 0.88rem; }
.tl-date { color: #999; font-size: 0.8rem; min-width: 75px; }
.tl-content { flex: 1; }
.tl-title { font-weight: 600; color: #333; margin-bottom: 2px; }
.tl-desc { font-size: 0.8rem; color: #666; }
.tl-dir { font-size: 0.75rem; font-weight: 700; }
.tl-dir.up { color: var(--up-color); }
.tl-dir.down { color: var(--down-color); }

/* 차트 */
[data-testid="stPlotlyChart"] { width: 100% !important; margin-top: -10px; }
.modebar { opacity: 0.8 !important; top: 5px !important; right: 5px !important; bottom: auto !important; left: auto !important; background: rgba(255,255,255,0.9) !important; border-radius: 4px; }

@media (max-width: 768px) {
    .stock-price { font-size: 2rem; }
    .stock-name { font-size: 1.3rem; }
    .summary-bar { gap: 8px; font-size: 0.75rem; }
    .summary-item { padding: 4px 10px; }
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    ("2015-08-24", "중국발 블랙먼데이", "위안 절하 쇼크", "🇨🇳", "down"),
    ("2016-02-11", "유가 폭락 바닥", "WTI $26 최저점", "🛢️", "down"),
    ("2016-11-08", "트럼프 1기 당선", "감세 기대 랠리", "🗳️", "up"),
    ("2018-02-05", "VIX 폭발", "볼마겟돈", "💣", "down"),
    ("2018-12-24", "파월 피벗", "금리인상 중단 시사", "🔄", "up"),
    ("2020-03-23", "무제한 QE", "Fed 양적완화 선언", "💵", "up"),
    ("2021-11-22", "인플레 피크", "긴축 예고", "📉", "down"),
    ("2022-03-16", "긴축 개시", "첫 금리인상", "⬆️", "down"),
    ("2022-10-13", "CPI 피크아웃", "인플레 둔화", "📊", "up"),
    ("2022-11-30", "ChatGPT 출시", "AI 시대 개막", "🧠", "up"),
    ("2024-11-05", "트럼프 2기 당선", "규제완화 기대", "🗳️", "up"),
    ("2025-01-27", "DeepSeek 쇼크", "AI 수익성 우려", "🤖", "down"),
]

COUNTRY_CONFIG = {
    "🇺🇸 미국": {
        "indices": {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",
        "fred_rec": "USREC",
        "liq_divisor": 1,
        "liq_label": "본원통화",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "liq_suffix": "B",
        "events": MARKET_PIVOTS,
        "data_src": "FRED · Yahoo",
    },
    "🇰🇷 대한민국": {
        "indices": {"KOSPI": "^KS11", "KOSDAQ": "^KQ11"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",
        "fred_rec": "USREC",
        "liq_divisor": 1,
        "liq_label": "글로벌 유동성(Fed)",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "liq_suffix": "B",
        "events": MARKET_PIVOTS,
        "data_src": "FRED · KRX",
    },
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker, fred_liq, fred_rec, liq_divisor):
    end_dt = datetime.now()
    fetch_start = end_dt - timedelta(days=365 * 14)

    # 1. FRED 데이터 (유동성)
    try:
        fred_codes = [fred_liq]
        if fred_rec: fred_codes.append(fred_rec)
        fred_df = web.DataReader(fred_codes, "fred", fetch_start, end_dt).ffill()
        if fred_rec:
            fred_df.columns = ["Liquidity", "Recession"]
        else:
            fred_df.columns = ["Liquidity"]
            fred_df["Recession"] = 0
        fred_df["Liquidity"] = fred_df["Liquidity"] / liq_divisor
    except Exception as e:
        return None, f"FRED Error: {e}"

    # 2. 주가 데이터 (yfinance)
    try:
        import yfinance as yf
        yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
        
        if yf_data.empty:
            return None, "Yahoo Finance: 데이터가 비어있습니다."
        
        # MultiIndex 컬럼 처리 (yfinance 최신 버전 대응)
        if isinstance(yf_data.columns, pd.MultiIndex):
            # Ticker 레벨 제거하고 컬럼명만 남김
            try:
                yf_data.columns = yf_data.columns.get_level_values(0)
            except:
                pass
        
        # 필요한 컬럼만 추출
        ohlc = yf_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        idx_close = yf_data[['Close']].rename(columns={'Close': 'SP500'})
        
    except Exception as e:
        return None, f"YFinance Error: {e}"

    # 3. 데이터 통합
    try:
        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        df = df.dropna(subset=['SP500']) # 주가 없는 날 제거
        
        df["Liq_MA"] = df["Liquidity"].rolling(10).mean()
        df["SP_MA"] = df["SP500"].rolling(10).mean()
        df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
        df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])

        # 최근 12년치만 리턴
        cut = end_dt - timedelta(days=365 * 12)
        df = df[df.index >= cut]
        ohlc = ohlc[ohlc.index >= cut]
        
        return (df, ohlc), None
    except Exception as e:
        return None, f"Merge Error: {e}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UI: 컨트롤 바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1, 1])
with ctrl1:
    country = st.selectbox("🌍 국가", list(COUNTRY_CONFIG.keys()), index=0)
CC = COUNTRY_CONFIG[country]
IDX_OPTIONS = CC["indices"]

if st.session_state.get("_prev_country") != country:
    st.session_state["_prev_country"] = country
    st.session_state["idx_select"] = list(IDX_OPTIONS.keys())[CC["default_idx"]]

with ctrl2:
    idx_name = st.selectbox("📈 지수", list(IDX_OPTIONS.keys()), key="idx_select")
    idx_ticker = IDX_OPTIONS[idx_name]
with ctrl3:
    period = st.selectbox("📅 기간", ["3년", "5년", "7년", "10년", "전체"], index=3)
with ctrl4:
    tf = st.selectbox("🕯️ 봉", ["일봉", "주봉", "월봉"], index=2)
with ctrl5:
    show_events = st.toggle("📌 이벤트", value=True)

period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 12}
cutoff = datetime.now() - timedelta(days=365 * period_map[period])

# 데이터 로딩 실행
with st.spinner("데이터를 불러오는 중입니다..."):
    result, err_msg = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])

if result is None:
    st.error(f"데이터 로딩 실패: {err_msg}")
    st.stop()

df, ohlc_raw = result

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UI: 헤더 및 KPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
latest = df.iloc[-1]
prev = df.iloc[-2]
cur_price = latest["SP500"]
diff = cur_price - prev["SP500"]
pct = (diff / prev["SP500"]) * 100

color_cls = "c-up" if diff > 0 else "c-down" if diff < 0 else "c-flat"
sign = "+" if diff > 0 else ""
arrow = "▲" if diff > 0 else "▼" if diff < 0 else "-"

st.markdown(f"""
<div class="stock-header-container">
    <div class="stock-title-row">
        <span class="stock-name">{idx_name}</span>
        <span class="stock-ticker">{idx_ticker}</span>
    </div>
    <div class="stock-price-row {color_cls}">
        <span class="stock-price">{cur_price:,.2f}</span>
        <span class="stock-change">{arrow} {abs(diff):,.2f} ({sign}{pct:.2f}%)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI 바
liq_val = latest["Liquidity"]
liq_yoy = latest["Liq_YoY"]
corr_val = latest["Corr_90d"]

st.markdown(f"""
<div class="summary-bar">
    <div class="summary-item">
        <span class="summary-label">{CC['liq_label']}</span>
        <span class="summary-value" style="color:#333">{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}</span>
    </div>
    <div class="summary-item">
        <span class="summary-label">유동성 YoY</span>
        <span class="summary-value" style="color:{'#f73646' if liq_yoy>0 else '#335eff'}">{liq_yoy:+.1f}%</span>
    </div>
    <div class="summary-item">
        <span class="summary-label">상관계수(90일)</span>
        <span class="summary-value" style="color:{'#33bb55' if corr_val>0.5 else '#555'}">{corr_val:.2f}</span>
    </div>
    <div class="summary-item">
        <span class="summary-label">데이터</span>
        <span class="summary-value">{len(df):,}일</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UI: 차트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 데이터 슬라이싱
dff = df[df.index >= pd.to_datetime(cutoff)].copy()
ohlc_filtered = ohlc_raw[ohlc_raw.index >= pd.to_datetime(cutoff)].copy()

if ohlc_filtered.empty:
    st.warning("선택한 기간의 데이터가 없습니다.")
    st.stop()

# 2. 리샘플링
def resample_ohlc(ohlc_df, rule):
    return ohlc_df.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

if tf == "주봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "W")
    dff_chart = dff.resample("W").last().dropna()
elif tf == "월봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "ME")
    dff_chart = dff.resample("ME").last().dropna()
else:
    ohlc_chart = ohlc_filtered.copy()
    dff_chart = dff.copy()

# 3. 차트 생성
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
    row_heights=[0.8, 0.2],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# (1) 유동성 (배경)
fig.add_trace(go.Scatter(
    x=dff_chart.index, y=dff_chart["Liquidity"],
    name=CC['liq_label'],
    fill="tozeroy", fillcolor="rgba(59,130,246,0.05)",
    line=dict(color="rgba(59,130,246,0.3)", width=1),
    hoverinfo="skip"
), row=1, col=1, secondary_y=True)

# (2) 캔들스틱
fig.add_trace(go.Candlestick(
    x=ohlc_chart.index,
    open=ohlc_chart["Open"], high=ohlc_chart["High"],
    low=ohlc_chart["Low"], close=ohlc_chart["Close"],
    increasing_line_color="#f73646", increasing_fillcolor="#f73646",
    decreasing_line_color="#335eff", decreasing_fillcolor="#335eff",
    name="주가"
), row=1, col=1)

# (3) 이평선
for ma, color in [(5, "#999"), (20, "#f5a623"), (60, "#33bb55"), (120, "#aa55ff")]:
    ma_series = ohlc_chart["Close"].rolling(ma).mean()
    fig.add_trace(go.Scatter(
        x=ohlc_chart.index, y=ma_series,
        mode='lines', line=dict(color=color, width=1),
        name=f"{ma}선"
    ), row=1, col=1)

# (4) 거래량
vol_colors = ["#f73646" if c > o else "#335eff" for o, c in zip(ohlc_chart["Open"], ohlc_chart["Close"])]
fig.add_trace(go.Bar(
    x=ohlc_chart.index, y=ohlc_chart["Volume"],
    marker_color=vol_colors, showlegend=False, name="거래량"
), row=2, col=1)

# (5) 이벤트
def detect_auto_events(ohlc_df, base_events, threshold=0.05):
    if ohlc_df is None or len(ohlc_df) < 2: return []
    daily_ret = ohlc_df["Close"].pct_change()
    existing = {pd.to_datetime(d).date() for d, *_ in base_events}
    auto = []
    for dt, ret in daily_ret.items():
        if pd.isna(ret) or dt.date() in existing: continue
        if abs(ret) >= threshold:
            kind, emoji = ("급등", "🔥") if ret > 0 else ("급락", "⚡")
            auto.append((dt.strftime("%Y-%m-%d"), f"{kind} {ret*100:.1f}%", f"{kind}", emoji, "up" if ret>0 else "down"))
            existing.add(dt.date())
    return auto

if show_events:
    auto_events = detect_auto_events(ohlc_filtered, CC["events"])
    ALL_EVENTS = sorted(CC["events"] + auto_events, key=lambda x: x[0])
    prev_dt = None
    min_gap = {"일봉": 15, "주봉": 45, "월봉": 120}.get(tf, 20)
    
    for date_str, title, _, emoji, direction in ALL_EVENTS:
        dt = pd.to_datetime(date_str)
        if dt < ohlc_chart.index.min() or dt > ohlc_chart.index.max(): continue
        if prev_dt and (dt - prev_dt).days < min_gap: continue
        prev_dt = dt
        
        fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color="rgba(100,100,100,0.3)", row="all", col=1)
        clr = "#d32f2f" if direction == "up" else "#1976d2"
        fig.add_annotation(
            x=dt, y=1.05, yref="paper", text=f"{emoji} {title}", 
            showarrow=False, font=dict(size=11, color=clr),
            textangle=-30, xanchor="left", yanchor="bottom", row=1, col=1
        )

# (6) 리세션
if "Recession" in dff_chart.columns:
    rec = dff_chart[dff_chart["Recession"] == 1]
    if not rec.empty:
        # 간단하게 구간 표시 (복잡한 로직 대신 전체 덮기)
        # 실제로는 구간별 루프가 필요하지만 간소화
        pass 

# (7) 레이아웃
x_min = ohlc_chart.index.min()
x_max = ohlc_chart.index.max() + timedelta(days=1)

fig.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(t=60, b=20, l=10, r=50),
    height=600,
    hovermode="x unified",
    dragmode="pan",
    showlegend=True,
    legend=dict(
        orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01,
        bgcolor="rgba(255,255,255,0.5)", borderwidth=0, font=dict(size=10)
    ),
    xaxis=dict(rangebreaks=[dict(bounds=["sat", "mon"])] if tf == "일봉" else []),
    xaxis_minallowed=x_min, xaxis_maxallowed=x_max,
)

# 축 설정 (Y축 고정)
fig.update_xaxes(gridcolor="#f5f5f5", row=1, col=1)
fig.update_xaxes(gridcolor="#f5f5f5", row=2, col=1)

fig.update_yaxes(
    side="right", gridcolor="#f5f5f5",
    tickfont=dict(color="#333", size=11),
    fixedrange=True, # ★ Y축 줌 방지
    row=1, col=1, secondary_y=False
)
fig.update_yaxes(visible=False, fixedrange=True, row=1, col=1, secondary_y=True)
fig.update_yaxes(side="right", showgrid=False, tickformat=".2s", fixedrange=True, row=2, col=1)

config = {
    'displayModeBar': True,
    'scrollZoom': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d']
}

st.plotly_chart(fig, use_container_width=True, config=config)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하단 Brief
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
liq_3m = df["Liquidity"]
liq_3m_chg = ((liq_3m.iloc[-1] - liq_3m.iloc[-63]) / liq_3m.iloc[-63] * 100) if len(liq_3m) > 63 else 0
sp_1m = df["SP500"]
sp_1m_chg = ((sp_1m.iloc[-1] - sp_1m.iloc[-21]) / sp_1m.iloc[-21] * 100) if len(sp_1m) > 21 else 0
sp_yoy = latest["SP_YoY"] if pd.notna(latest.get("SP_YoY")) else 0

today_str = datetime.now().strftime("%Y년 %m월 %d일")

if country == "🇺🇸 미국":
    brief_content = f"""
    <strong>🇺🇸 미국 시장 브리핑 ({today_str})</strong><br>
    최근 3개월간 <strong>{CC['liq_label']}</strong>는 <span class="hl">{liq_3m_chg:+.1f}%</span> 변동했습니다.
    시장 지수는 1개월간 <span class="hl">{sp_1m_chg:+.1f}%</span> 움직였습니다.
    연준의 정책 변화와 유동성 흐름이 주가에 미치는 영향을 주시하세요. 
    상관계수가 {corr_val:.2f}로, 유동성과 주가의 동행성이 {'높습니다' if corr_val > 0.5 else '낮습니다'}.
    """
else:
    brief_content = f"""
    <strong>🇰🇷 한국 시장 브리핑 ({today_str})</strong><br>
    글로벌 유동성(Fed)은 최근 3개월 <span class="hl">{liq_3m_chg:+.1f}%</span> 변동했습니다.
    한국 증시는 대외 변수에 민감하게 반응하며, 최근 1개월 <span class="hl">{sp_1m_chg:+.1f}%</span>의 등락을 보였습니다.
    """

st.markdown(f"""
<div class="report-box">
    <div class="report-header">
        <span class="report-badge">Brief</span>
        <span class="report-title">Market Insight</span>
    </div>
    <div class="report-body">{brief_content}</div>
</div>
""", unsafe_allow_html=True)

# 타임라인
st.markdown('<div style="font-weight:700; font-size:1.1rem; margin-top:20px;">📅 주요 이벤트 타임라인</div>', unsafe_allow_html=True)
tl_html = '<div class="timeline">'
for date_str, title, desc, emoji, direction in reversed(ALL_EVENTS):
    if pd.to_datetime(date_str) < dff.index.min(): continue
    dir_cls = "up" if direction == "up" else "down"
    tl_html += f"""
    <div class="tl-item">
        <div class="tl-date">{date_str}</div>
        <div class="tl-content">
            <div class="tl-title">{emoji} {title} <span class="tl-dir {dir_cls}">●</span></div>
            <div class="tl-desc">{desc}</div>
        </div>
    </div>"""
tl_html += "</div>"
st.markdown(tl_html, unsafe_allow_html=True)

st.markdown('<div class="app-footer" style="margin-top:30px; color:#999; font-size:0.8rem; text-align:center;">Data Source: FRED · Yahoo Finance<br>본 페이지는 투자 조언을 제공하지 않습니다.</div>', unsafe_allow_html=True)