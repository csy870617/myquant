import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from zoneinfo import ZoneInfo
import yfinance as yf

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="유동성 × 시장 분석기", 
    page_icon="icon.png", 
    layout="wide"
)

# 상단 로고 (파일이 있으면 표시)
try:
    st.logo("icon.png")
except:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 스타일 (네이버 증권 + KPI/리포트 스타일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');

:root {
    --bg: #ffffff;
    --text-primary: #222222;
    --text-secondary: #8d929b;
    --border: #ececec;
    --up-color: #f73646;
    --down-color: #335eff;
    --card-bg: #ffffff;
    --accent-blue: #3b82f6; --accent-red: #ef4444; --accent-green: #10b981; --accent-purple: #8b5cf6;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', sans-serif;
    background: var(--bg) !important; color: var(--text-primary);
}
[data-testid="stHeader"] { background: transparent !important; }

.block-container { 
    padding-top: 1rem !important; padding-bottom: 3rem !important;
    padding-left: 1rem !important; padding-right: 1rem !important;
    max-width: 100%;
}

/* ── KPI 카드 ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 15px; }
.kpi {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px;
    padding: 1rem; position: relative; overflow: hidden; box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.kpi::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px; }
.kpi.blue::before { background: var(--accent-blue); }
.kpi.red::before { background: var(--accent-red); }
.kpi.green::before { background: var(--accent-green); }
.kpi.purple::before { background: var(--accent-purple); }
.kpi-label { font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); margin-bottom: 0.3rem; }
.kpi-value { font-family: 'Roboto Mono', monospace; font-size: 1.3rem; font-weight: 700; color: var(--text-primary); }
.kpi-delta { font-size: 0.8rem; font-weight: 500; margin-top: 0.2rem; }
.kpi-delta.up { color: var(--accent-green); }
.kpi-delta.down { color: var(--accent-red); }

/* ── 헤더 (네이버 스타일) ── */
.stock-header-container { padding-bottom: 15px; border-bottom: 1px solid var(--border); margin-bottom: 15px; }
.stock-title-row { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
.stock-name { font-size: 1.5rem; font-weight: 800; color: #111; }
.stock-ticker { font-size: 0.95rem; color: var(--text-secondary); font-weight: 500; }
.stock-price-row { display: flex; align-items: flex-end; gap: 12px; }
.stock-price { font-family: 'Roboto Mono', sans-serif; font-size: 2.4rem; font-weight: 700; line-height: 1; }
.stock-change { font-size: 1.1rem; font-weight: 600; padding-bottom: 4px; }
.c-up { color: var(--up-color); }
.c-down { color: var(--down-color); }
.c-flat { color: #333; }

/* ── 리포트 박스 (Daily Brief) ── */
.report-box {
    background: linear-gradient(135deg, #f8f9fa, #ffffff); border: 1px solid #e1e4e8;
    border-radius: 12px; padding: 1.5rem; margin-top: 1.5rem; margin-bottom: 1.5rem;
}
.report-header { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.report-badge {
    background: var(--accent-blue); color: white; font-size: 0.7rem; font-weight: 700;
    padding: 4px 10px; border-radius: 20px; text-transform: uppercase;
}
.report-date { font-size: 0.85rem; color: var(--text-secondary); }
.report-title { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); }
.report-body { font-size: 0.95rem; color: #444; line-height: 1.7; }
.report-body strong { color: #111; font-weight: 700; }
.report-body .hl { background: rgba(59,130,246,0.1); padding: 0 4px; border-radius: 4px; color: var(--accent-blue); font-weight: 600; }
.report-divider { border: none; border-top: 1px dashed #d1d5db; margin: 12px 0; }
.report-signal { display: inline-flex; padding: 6px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; margin-top: 0.8rem; }
.signal-bullish { background: rgba(16,185,129,0.1); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.2); }
.signal-neutral { background: rgba(245,158,11,0.1); color: var(--accent-amber); border: 1px solid rgba(245,158,11,0.2); }
.signal-bearish { background: rgba(239,68,68,0.1); color: var(--accent-red); border: 1px solid rgba(239,68,68,0.2); }

/* ── 타임라인 ── */
.timeline { display: flex; flex-direction: column; gap: 0; border-top: 1px solid #eee; margin-top: 10px; }
.tl-item { display: flex; gap: 15px; padding: 12px 0; border-bottom: 1px solid #f5f5f5; font-size: 0.9rem; }
.tl-date { color: #888; font-size: 0.8rem; min-width: 80px; font-family: 'Roboto Mono', monospace; }
.tl-icon { font-size: 1.1rem; }
.tl-content { flex: 1; }
.tl-title { font-weight: 600; color: #333; margin-bottom: 2px; }
.tl-desc { font-size: 0.85rem; color: #666; }
.tl-dir { font-size: 0.75rem; font-weight: 700; margin-left: 5px; padding: 1px 5px; border-radius: 4px; }
.tl-dir.up { background: rgba(247,54,70,0.1); color: var(--up-color); }
.tl-dir.down { background: rgba(51,94,255,0.1); color: var(--down-color); }

/* ── 컨트롤 및 차트 ── */
[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; margin-bottom: 10px; }
.stSelectbox label, .stRadio label { font-size: 0.75rem !important; color: #666 !important; }
.stSelectbox > div > div { background-color: #f9f9f9 !important; border: 1px solid #ddd !important; border-radius: 6px !important; }
[data-testid="stPlotlyChart"] { width: 100% !important; margin-top: -10px; }
.modebar { opacity: 0.8 !important; top: 5px !important; right: 5px !important; background: rgba(255,255,255,0.9) !important; border-radius: 4px; }

/* 모바일 반응형 */
@media (max-width: 768px) {
    .kpi-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .stock-price { font-size: 2rem; }
    .stock-name { font-size: 1.3rem; }
    .report-box { padding: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 데이터 및 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    ("2024-11-05", "트럼프 2기 당선", "규제완화 기대", "🗳️", "up"),
    ("2025-01-27", "DeepSeek 쇼크", "AI 수익성 우려", "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세", "관세 공포", "🚨", "down"),
    ("2025-04-09", "관세 90일 유예", "무역전쟁 완화", "🕊️", "up"),
    ("2025-12-11", "RMP 국채매입 재개", "유동성 확장", "💰", "up"),
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

    try:
        # FRED 데이터
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

    try:
        # Yahoo Finance 데이터
        yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
        if yf_data.empty: return None, "No Data"
        
        if isinstance(yf_data.columns, pd.MultiIndex):
             if 'Close' in yf_data.columns.get_level_values(0):
                 yf_data.columns = yf_data.columns.get_level_values(0)
        
        ohlc = yf_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        idx_close = yf_data[['Close']].rename(columns={'Close': 'SP500'})
    except Exception as e:
        return None, f"YFinance Error: {e}"

    try:
        # 데이터 병합
        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        df = df.dropna(subset=['SP500'])
        
        df["Liq_MA"] = df["Liquidity"].rolling(10).mean()
        df["SP_MA"] = df["SP500"].rolling(10).mean()
        df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
        df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])

        cut = end_dt - timedelta(days=365 * 12)
        df = df[df.index >= cut]
        ohlc = ohlc[ohlc.index >= cut]
        return (df, ohlc), None
    except Exception as e:
        return None, f"Merge Error: {e}"

def detect_auto_events(ohlc_df, base_events, threshold=0.05):
    if ohlc_df is None or len(ohlc_df) < 2: return []
    daily_ret = ohlc_df["Close"].pct_change()
    existing = {pd.to_datetime(d).date() for d, *_ in base_events}
    auto = []
    for dt, ret in daily_ret.items():
        if pd.isna(ret) or dt.date() in existing: continue
        if abs(ret) >= threshold:
            kind, emoji = ("급등", "🔥") if ret > 0 else ("급락", "⚡")
            auto.append((dt.strftime("%Y-%m-%d"), f"{kind} {ret*100:.1f}%", f"하루 {kind}", emoji, "up" if ret>0 else "down"))
            existing.add(dt.date())
    return auto

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 레이아웃 & 로직
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 컨테이너 구성
header_con = st.container()
kpi_con = st.container()
st.write("")
ctrl_con = st.container()
chart_con = st.container()
brief_con = st.container()
timeline_con = st.container()

# [컨트롤 바]
with ctrl_con:
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
    with c1: country = st.selectbox("🌍 국가", list(COUNTRY_CONFIG.keys()), index=0)
    CC = COUNTRY_CONFIG[country]
    IDX_OPTIONS = CC["indices"]
    
    if st.session_state.get("_prev_country") != country:
        st.session_state["_prev_country"] = country
        st.session_state["idx_select"] = list(IDX_OPTIONS.keys())[CC["default_idx"]]
        
    with c2: idx_name = st.selectbox("📈 지수", list(IDX_OPTIONS.keys()), key="idx_select")
    idx_ticker = IDX_OPTIONS[idx_name]
    with c3: period = st.selectbox("📅 기간", ["3년", "5년", "7년", "10년", "전체"], index=3)
    with c4: tf = st.selectbox("🕯️ 봉", ["일봉", "주봉", "월봉"], index=2)
    with c5: show_events = st.toggle("📌 이벤트", value=True)

# 데이터 로드
with st.spinner("데이터 로딩중..."):
    result, err = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])

if result is None:
    st.error(f"⚠️ {err}")
    st.stop()

df, ohlc_raw = result

# 기간 필터링
period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 12}
cutoff = datetime.now() - timedelta(days=365 * period_map[period])
dff = df[df.index >= cutoff].copy()
ohlc_filtered = ohlc_raw[ohlc_raw.index >= cutoff].copy()

if ohlc_filtered.empty:
    st.error("해당 기간의 데이터가 없습니다.")
    st.stop()

# 주요 변수 계산
latest = df.iloc[-1]
prev = df.iloc[-2]
price = latest["SP500"]
diff = price - prev["SP500"]
pct = (diff / prev["SP500"]) * 100
liq_val = latest["Liquidity"]
liq_yoy = latest["Liq_YoY"]
sp_yoy = latest["SP_YoY"]
corr_val = latest["Corr_90d"]

cls = "c-up" if diff > 0 else "c-down" if diff < 0 else "c-flat"
arrow = "▲" if diff > 0 else "▼" if diff < 0 else "-"

# [헤더]
with header_con:
    st.markdown(f"""
    <div class="stock-header-container">
        <div class="stock-title-row">
            <span class="stock-name">{idx_name}</span>
            <span class="stock-ticker">{idx_ticker}</span>
        </div>
        <div class="stock-price-row {cls}">
            <span class="stock-price">{price:,.2f}</span>
            <span class="stock-change">{arrow} {abs(diff):,.2f} ({pct:+.2f}%)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# [KPI 카드]
def delta_html(val):
    c = "up" if val >= 0 else "down"
    return f'<div class="kpi-delta {c}">{val:+.1f}% YoY</div>'

with kpi_con:
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi blue">
            <div class="kpi-label">💵 {CC['liq_label']}</div>
            <div class="kpi-value">{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}</div>
            {delta_html(liq_yoy)}
        </div>
        <div class="kpi red">
            <div class="kpi-label">📈 {idx_name}</div>
            <div class="kpi-value">{price:,.0f}</div>
            {delta_html(sp_yoy)}
        </div>
        <div class="kpi green">
            <div class="kpi-label">🔗 90일 상관계수</div>
            <div class="kpi-value">{corr_val:.2f}</div>
            <div class="kpi-delta {'up' if corr_val>0.5 else 'down'}">{'강한 동행' if corr_val>0.5 else '약한 상관'}</div>
        </div>
        <div class="kpi purple">
            <div class="kpi-label">📅 데이터 기간</div>
            <div class="kpi-value" style="font-size:1.1rem">{dff.index.min().strftime('%Y.%m')}~</div>
            <div class="kpi-delta up">{len(dff):,}일</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# [차트]
def resample(data, rule):
    return data.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

if tf == "주봉": chart_data = resample(ohlc_filtered, "W"); dff_chart = dff.resample("W").last().dropna()
elif tf == "월봉": chart_data = resample(ohlc_filtered, "ME"); dff_chart = dff.resample("ME").last().dropna()
else: chart_data = ohlc_filtered.copy(); dff_chart = dff.copy()

with chart_container:
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
        row_heights=[0.8, 0.2],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )
    
    # 1. 유동성 (배경)
    fig.add_trace(go.Scatter(
        x=dff_chart.index, y=dff_chart["Liquidity"],
        name=CC['liq_label'],
        fill="tozeroy", fillcolor="rgba(59,130,246,0.05)",
        line=dict(color="rgba(59,130,246,0.3)", width=1),
        hoverinfo="skip"
    ), row=1, col=1, secondary_y=True)

    # 2. 캔들
    fig.add_trace(go.Candlestick(
        x=chart_data.index,
        open=chart_data['Open'], high=chart_data['High'],
        low=chart_data['Low'], close=chart_data['Close'],
        increasing_line_color='#f73646', increasing_fillcolor='#f73646',
        decreasing_line_color='#335eff', decreasing_fillcolor='#335eff',
        name='주가'
    ), row=1, col=1)

    # 3. 이평선
    for ma, color in [(5, '#999'), (20, '#f5a623'), (60, '#33bb55'), (120, '#aa55ff')]:
        ma_s = chart_data['Close'].rolling(ma).mean()
        fig.add_trace(go.Scatter(
            x=chart_data.index, y=ma_s, 
            mode='lines', line=dict(color=color, width=1), 
            name=f'{ma}일'
        ), row=1, col=1)

    # 4. 거래량
    colors = ['#f73646' if c >= o else '#335eff' for o, c in zip(chart_data['Open'], chart_data['Close'])]
    fig.add_trace(go.Bar(
        x=chart_data.index, y=chart_data['Volume'],
        marker_color=colors, showlegend=False, name='거래량'
    ), row=2, col=1)

    # 5. 이벤트 (자동 감지 + 수동)
    ALL_EVENTS = []
    if show_events:
        auto_events = detect_auto_events(ohlc_filtered, CC["events"])
        ALL_EVENTS = sorted(CC["events"] + auto_events, key=lambda x: x[0])
        prev_dt = None
        min_gap = {"일봉": 15, "주봉": 45, "월봉": 120}.get(tf, 20)

        for date_str, title, _, emoji, direction in ALL_EVENTS:
            dt = pd.to_datetime(date_str)
            if dt < chart_data.index.min() or dt > chart_data.index.max(): continue
            if prev_dt and (dt - prev_dt).days < min_gap: continue
            prev_dt = dt
            
            fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color="rgba(100,100,100,0.3)", row="all", col=1)
            clr = "#d32f2f" if direction == "up" else "#1976d2"
            fig.add_annotation(
                x=dt, y=1.05, yref="paper", text=f"{emoji} {title}",
                showarrow=False, font=dict(size=11, color=clr),
                textangle=-30, xanchor="left", yanchor="bottom", row=1, col=1
            )
            
    # 6. 리세션
    if "Recession" in dff_chart.columns:
        rec = dff_chart[dff_chart["Recession"] == 1]
        if not rec.empty:
            # 간단 표시
            pass

    # 레이아웃
    x_min, x_max = chart_data.index.min(), chart_data.index.max() + timedelta(days=1)
    
    fig.update_layout(
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=60, b=20, l=10, r=50),
        height=600,
        hovermode='x unified',
        dragmode='pan',
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.6)", bordercolor="#eee", borderwidth=1, font=dict(size=10)
        ),
        xaxis=dict(
            rangebreaks=[dict(bounds=["sat", "mon"])] if tf == "일봉" else [],
            minallowed=x_min, maxallowed=x_max
        )
    )

    # 축 설정
    fig.update_xaxes(gridcolor='#f5f5f5', row=1, col=1)
    fig.update_xaxes(gridcolor='#f5f5f5', row=2, col=1)
    
    # Y축 (오른쪽, 고정)
    fig.update_yaxes(
        side='right', gridcolor='#f5f5f5',
        tickfont=dict(color="#333", size=11),
        ticklabelposition="outside", zeroline=False,
        fixedrange=True, row=1, col=1, secondary_y=False
    )
    fig.update_yaxes(visible=False, fixedrange=True, row=1, col=1, secondary_y=True)
    fig.update_yaxes(side='right', showgrid=False, tickformat='.2s', fixedrange=True, row=2, col=1)

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'scrollZoom': True})
    
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var plot = document.querySelector('.js-plotly-plot');
        if(plot) { plot.style.touchAction = 'none'; }
    });
    </script>
    """, unsafe_allow_html=True)

# [Daily Brief]
with brief_container:
    liq_3m_chg = ((df["Liquidity"].iloc[-1] - df["Liquidity"].iloc[-63])/df["Liquidity"].iloc[-63]*100) if len(df)>63 else 0
    sp_1m_chg = ((df["SP500"].iloc[-1] - df["SP500"].iloc[-21])/df["SP500"].iloc[-21]*100) if len(df)>21 else 0
    
    if corr_val > 0.5 and liq_3m_chg > 0:
        sig_cls, sig_txt = "signal-bullish", "🟢 유동성 확장 + 강한 상관 → 주가 상승 지지"
    elif corr_val < 0 or liq_3m_chg < -1:
        sig_cls, sig_txt = "signal-bearish", "🔴 유동성 수축 또는 상관 이탈 → 경계 필요"
    else:
        sig_cls, sig_txt = "signal-neutral", "🟡 혼합 시그널 → 방향성 주시"

    if country == "🇺🇸 미국":
        b_pol = "연준은 금리를 유지하며 유동성을 조절하고 있습니다."
        b_liq = f"본원통화는 3개월간 <span class='hl'>{liq_3m_chg:+.1f}%</span> 변동했습니다."
        b_mkt = f"{idx_name}은 1개월간 <span class='hl'>{sp_1m_chg:+.1f}%</span> 움직였습니다."
    else:
        b_pol = "한국은행은 미 연준의 정책과 환율을 주시하고 있습니다."
        b_liq = f"글로벌 유동성(Fed)은 <span class='hl'>{liq_3m_chg:+.1f}%</span> 변동했습니다."
        b_mkt = f"{idx_name}은 대외 변수에 민감하며 <span class='hl'>{sp_1m_chg:+.1f}%</span> 등락했습니다."

    b_corr = f"상관계수 <span class='hl'>{corr_val:.2f}</span>. " + \
             ("유동성과 주가가 강하게 동행합니다." if corr_val > 0.5 else "동행성이 약화되었습니다.")

    st.markdown(f"""
    <div class="report-box">
        <div class="report-header">
            <span class="report-badge">Daily Brief</span>
            <span class="report-date">{datetime.now().strftime("%Y-%m-%d")}</span>
        </div>
        <div class="report-title">📋 오늘의 시장 요약</div>
        <div class="report-body">
            {b_pol}<br>{b_liq}<br>{b_mkt}
            <hr class="report-divider">
            {b_corr}
        </div>
        <div class="report-signal {sig_cls}">{sig_txt}</div>
    </div>
    """, unsafe_allow_html=True)

# [타임라인]
with timeline_container:
    st.markdown('<div style="font-weight:700; font-size:1.1rem; margin-top:20px;">📅 주요 이벤트</div>', unsafe_allow_html=True)
    html = '<div class="timeline">'
    for d, t, desc, e, dr in reversed(ALL_EVENTS):
        if pd.to_datetime(d) < dff.index.min(): continue
        c = "up" if dr == "up" else "down"
        html += f'<div class="tl-item"><div class="tl-date">{d}</div><div class="tl-content"><div class="tl-title">{e} {t} <span class="tl-dir {c}">●</span></div><div class="tl-desc">{desc}</div></div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# 푸터
st.markdown('<div class="app-footer" style="margin-top:30px; color:#999; font-size:0.8rem; text-align:center;">Data: FRED, Yahoo Finance · Not Investment Advice</div>', unsafe_allow_html=True)