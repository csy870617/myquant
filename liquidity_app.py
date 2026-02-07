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
# 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="유동성 × 시장 분석기", 
    page_icon="icon.png", 
    layout="wide"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 스타일 (네이버 증권 스타일)
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

/* 헤더 */
.stock-header-container { padding-bottom: 15px; border-bottom: 1px solid var(--border); margin-bottom: 15px; }
.stock-title-row { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
.stock-name { font-size: 1.5rem; font-weight: 800; color: #111; }
.stock-ticker { font-size: 0.95rem; color: var(--text-secondary); }
.stock-price-row { display: flex; align-items: flex-end; gap: 12px; }
.stock-price { font-family: 'Roboto Mono', sans-serif; font-size: 2.4rem; font-weight: 700; line-height: 1; }
.stock-change { font-size: 1.1rem; font-weight: 600; padding-bottom: 4px; }
.c-up { color: var(--up-color); }
.c-down { color: var(--down-color); }
.c-flat { color: #333; }

/* KPI 바 */
.summary-bar { display: flex; gap: 15px; overflow-x: auto; padding-bottom: 5px; margin-bottom: 10px; font-size: 0.85rem; }
.summary-item { white-space: nowrap; display: flex; align-items: center; gap: 5px; background: #f8f9fa; padding: 6px 12px; border-radius: 18px; border: 1px solid #eee; }
.summary-label { color: #888; font-weight: 500; }
.summary-value { font-weight: 700; color: #333; }

/* 차트 */
[data-testid="stPlotlyChart"] { width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    ("2024-11-05", "트럼프 2기 당선", "규제완화 기대", "🗳️", "up"),
    ("2025-01-27", "DeepSeek 쇼크", "AI 수익성 우려", "🤖", "down"),
    # ... (기존 이벤트 유지)
]

COUNTRY_CONFIG = {
    "🇺🇸 미국": {
        "indices": {"NASDAQ": "^IXIC", "S&P 500": "^GSPC"},
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
    fetch_start = end_dt - timedelta(days=365 * 12) # 넉넉하게

    # 1. FRED (유동성)
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
    except Exception:
        # FRED 실패 시 빈 데이터프레임 생성 (차트는 그려지도록)
        fred_df = pd.DataFrame(columns=["Liquidity", "Recession"])

    # 2. Yahoo Finance (주가) - 핵심 수정 부분
    try:
        yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
        
        if yf_data.empty:
            return None, "주가 데이터를 가져올 수 없습니다."

        # MultiIndex 컬럼 평탄화 (yfinance 버전 호환성)
        if isinstance(yf_data.columns, pd.MultiIndex):
            # level 0가 속성(Close 등), level 1이 Ticker인 경우
            if 'Close' in yf_data.columns.get_level_values(0):
                 yf_data.columns = yf_data.columns.get_level_values(0)
        
        # 필요한 컬럼만 선택
        ohlc = yf_data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        # 결측치 제거
        ohlc = ohlc.dropna()
        
        # SP500 컬럼 생성 (분석용)
        idx_close = ohlc[['Close']].rename(columns={'Close': 'SP500'})

    except Exception as e:
        return None, f"주가 데이터 오류: {str(e)}"

    # 3. 데이터 병합
    try:
        # 인덱스 통일 (날짜형)
        fred_df.index = pd.to_datetime(fred_df.index)
        idx_close.index = pd.to_datetime(idx_close.index)
        
        # 병합
        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        df = df.dropna(subset=['SP500']) # 주가 없는 날은 제외

        # 파생변수
        df["Liq_MA"] = df["Liquidity"].rolling(10).mean()
        df["SP_MA"] = df["SP500"].rolling(10).mean()
        df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
        df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])
        
        return (df, ohlc), None

    except Exception as e:
        return None, f"데이터 병합 오류: {str(e)}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 로직
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1, 1])
with ctrl1:
    country = st.selectbox("🌍 국가", list(COUNTRY_CONFIG.keys()), index=0)
CC = COUNTRY_CONFIG[country]
IDX_OPTIONS = CC["indices"]

if st.session_state.get("_prev_country") != country:
    st.session_state["_prev_country"] = country
    st.session_state["idx_select"] = list(IDX_OPTIONS.keys())[0]

with ctrl2:
    idx_name = st.selectbox("📈 지수", list(IDX_OPTIONS.keys()), key="idx_select")
    idx_ticker = IDX_OPTIONS[idx_name]
with ctrl3:
    period = st.selectbox("📅 기간", ["1년", "3년", "5년", "10년", "전체"], index=1)
with ctrl4:
    tf = st.selectbox("🕯️ 봉", ["일봉", "주봉", "월봉"], index=2)
with ctrl5:
    show_events = st.toggle("📌 이벤트", value=True)

# 데이터 로드
with st.spinner("차트 구성중..."):
    result, err = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])

if result is None:
    st.error(f"⚠️ {err}")
    st.stop()

df, ohlc_raw = result

# 기간 필터링
period_days = {"1년": 365, "3년": 365*3, "5년": 365*5, "10년": 365*10, "전체": 365*30}
start_date = datetime.now() - timedelta(days=period_days.get(period, 365*3))

df = df[df.index >= start_date]
ohlc_raw = ohlc_raw[ohlc_raw.index >= start_date]

if df.empty or ohlc_raw.empty:
    st.error("해당 기간의 데이터가 없습니다.")
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헤더 정보
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
latest = df.iloc[-1]
prev = df.iloc[-2]
price = latest["SP500"]
diff = price - prev["SP500"]
pct = (diff / prev["SP500"]) * 100
cls = "c-up" if diff > 0 else "c-down" if diff < 0 else "c-flat"
arrow = "▲" if diff > 0 else "▼" if diff < 0 else "-"

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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 차트 그리기
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 리샘플링
def resample(data, rule):
    return data.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

if tf == "주봉": chart_data = resample(ohlc_raw, "W")
elif tf == "월봉": chart_data = resample(ohlc_raw, "ME")
else: chart_data = ohlc_raw

# 차트 생성
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
    row_heights=[0.8, 0.2],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# 1. 캔들
fig.add_trace(go.Candlestick(
    x=chart_data.index,
    open=chart_data['Open'], high=chart_data['High'],
    low=chart_data['Low'], close=chart_data['Close'],
    increasing_line_color='#f73646', increasing_fillcolor='#f73646',
    decreasing_line_color='#335eff', decreasing_fillcolor='#335eff',
    name='주가'
), row=1, col=1)

# 2. 이평선
for ma, color in [(5, '#999'), (20, '#f5a623'), (60, '#33bb55'), (120, '#aa55ff')]:
    ma_series = chart_data['Close'].rolling(ma).mean()
    fig.add_trace(go.Scatter(
        x=chart_data.index, y=ma_series, 
        mode='lines', line=dict(color=color, width=1), 
        name=f'{ma}일'
    ), row=1, col=1)

# 3. 거래량
colors = ['#f73646' if c >= o else '#335eff' for o, c in zip(chart_data['Open'], chart_data['Close'])]
fig.add_trace(go.Bar(
    x=chart_data.index, y=chart_data['Volume'],
    marker_color=colors, showlegend=False, name='거래량'
), row=2, col=1)

# 4. 유동성 (보조축)
if not df['Liquidity'].dropna().empty:
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Liquidity'],
        name=CC['liq_label'],
        line=dict(color='rgba(59,130,246,0.5)', width=1.5, dash='dot'),
        fill='tozeroy', fillcolor='rgba(59,130,246,0.05)'
    ), row=1, col=1, secondary_y=True)

# 5. 이벤트
if show_events:
    for date_str, title, _, emoji, direction in CC["events"]:
        dt = pd.to_datetime(date_str)
        if dt >= chart_data.index.min() and dt <= chart_data.index.max():
            fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color="#ccc")
            fig.add_annotation(
                x=dt, y=1.02, yref="paper", text=f"{emoji} {title}",
                showarrow=False, font=dict(size=11, color="#555"), textangle=-30
            )

# 6. 리세션
if "Recession" in df.columns:
    rec_dates = df[df["Recession"] == 1].index
    # 간단하게 구현: 리세션 기간이 있으면 표시
    # (복잡한 로직 생략하고 데이터 있으면 전체적으로 표시되지 않게 주의)
    pass 

# 레이아웃 설정
fig.update_layout(
    plot_bgcolor='white', paper_bgcolor='white',
    margin=dict(t=40, b=20, l=10, r=50),
    height=600,
    hovermode='x unified',
    dragmode='pan',
    showlegend=True,
    legend=dict(orientation="h", y=1, x=0, bgcolor='rgba(255,255,255,0.5)'),
    xaxis_rangeslider_visible=False
)

# 축 설정 (네이버 스타일: Y축 오른쪽)
fig.update_xaxes(gridcolor='#f0f0f0', showgrid=True, row=1, col=1)
fig.update_xaxes(gridcolor='#f0f0f0', showgrid=True, row=2, col=1)

# 일봉일 때만 휴장일 제거
if tf == "일봉":
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

# Y축 설정
fig.update_yaxes(side='right', gridcolor='#f0f0f0', showgrid=True, row=1, col=1, secondary_y=False)
fig.update_yaxes(visible=False, row=1, col=1, secondary_y=True) # 유동성 축 숨김
fig.update_yaxes(side='right', showgrid=False, tickformat='.2s', row=2, col=1)

# Y축 고정 (줌/팬 방지)
fig.update_yaxes(fixedrange=True)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하단 Brief
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")

liq_3m_chg = df["Liq_YoY"].iloc[-1] if not df.empty else 0
sp_1m_chg = df["SP500"].pct_change(20).iloc[-1] * 100 if not df.empty else 0
sp_yoy = df["SP_YoY"].iloc[-1] if not df.empty else 0

st.markdown(f"""
<div class="report-box">
    <div class="report-header">
        <span class="report-badge">Daily Brief</span>
        <span class="report-date">{datetime.now().strftime("%Y-%m-%d")}</span>
    </div>
    <div class="report-body">
        <strong>{country} 시장 요약</strong><br>
        • <strong>{CC['liq_label']}:</strong> 현재 수치는 전년 대비 <span class="hl">{liq_3m_chg:+.1f}%</span> 변동했습니다.<br>
        • <strong>주가 지수:</strong> {idx_name}은 최근 1개월간 <span class="hl">{sp_1m_chg:+.1f}%</span>, 
          전년 대비 <span class="hl">{sp_yoy:+.1f}%</span> 변동했습니다.<br>
        • <strong>상관관계:</strong> 최근 90일간 유동성과 주가의 상관계수는 
          <strong>{corr_val:.2f}</strong>로, 
          {'강한 동행' if corr_val > 0.5 else '약한 상관' if corr_val > 0 else '역상관'} 관계를 보입니다.
    </div>
</div>
""", unsafe_allow_html=True)

# 푸터
st.markdown('<div style="text-align:center; color:#999; font-size:0.8rem; margin-top:20px;">Data: FRED, Yahoo Finance</div>', unsafe_allow_html=True)