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
    page_icon="📈", 
    layout="wide"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 스타일 (네이버 증권 모바일/웹 스타일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');

:root {
    --bg-color: #ffffff;
    --text-main: #222222;
    --text-sub: #6e7582;
    --border-color: #e0e0e0;
    --up-color: #f73646;   /* 상승 빨강 */
    --down-color: #335eff; /* 하락 파랑 */
    --accent-color: #3b82f6;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', sans-serif;
    background-color: var(--bg-color);
    color: var(--text-main);
}

/* 컨테이너 여백 최적화 */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 5rem !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
    max-width: 100%;
}

/* 헤더 스타일 */
.stock-header {
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 12px;
    margin-bottom: 15px;
}
.header-top { display: flex; align-items: baseline; gap: 8px; }
.stock-name { font-size: 1.6rem; font-weight: 800; color: #111; }
.stock-code { font-size: 0.9rem; color: #888; font-weight: 500; }
.price-row { display: flex; align-items: flex-end; gap: 10px; margin-top: 2px; }
.current-price { 
    font-family: 'Roboto Mono', monospace; 
    font-size: 2.2rem; font-weight: 700; letter-spacing: -1px; line-height: 1; 
}
.price-change { font-size: 1.1rem; font-weight: 600; padding-bottom: 4px; }
.up { color: var(--up-color); }
.down { color: var(--down-color); }
.flat { color: #333; }

/* KPI 요약 바 */
.kpi-bar {
    display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 5px;
    -ms-overflow-style: none; scrollbar-width: none;
}
.kpi-bar::-webkit-scrollbar { display: none; }
.kpi-item {
    background: #f8f9fa; padding: 8px 14px; border-radius: 8px; 
    display: flex; flex-direction: column; min-width: 100px;
    border: 1px solid #eee;
}
.kpi-title { font-size: 0.75rem; color: #666; margin-bottom: 2px; }
.kpi-val { font-size: 1rem; font-weight: 700; color: #222; font-family: 'Roboto Mono'; }
.kpi-sub { font-size: 0.75rem; font-weight: 500; }

/* 컨트롤 바 */
div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
.stSelectbox > div > div { background: #f9f9f9; border: 1px solid #ddd; border-radius: 6px; }

/* 리포트 박스 */
.report-card {
    background: #fcfcfd; border: 1px solid #e1e4e8; border-radius: 12px;
    padding: 1.2rem; margin-top: 20px;
}
.report-title { font-size: 1rem; font-weight: 800; margin-bottom: 10px; display: flex; align-items: center; gap: 6px; }
.report-text { font-size: 0.9rem; color: #444; line-height: 1.6; }
.highlight { background: rgba(59,130,246,0.08); color: var(--accent-color); padding: 0 4px; border-radius: 4px; font-weight: 700; }

/* 차트 툴바 커스텀 */
.modebar {
    opacity: 0.9 !important;
    top: 0px !important; right: 0px !important;
    background: rgba(255,255,255,0.8) !important;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 데이터 로딩 및 처리 (안정성 강화)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=3600)
def load_market_data(ticker, fred_code, liq_div):
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=365 * 15)  # 15년치 데이터

    # (1) 유동성 데이터 (FRED)
    try:
        fred_df = web.DataReader(fred_code, "fred", start_dt, end_dt)
        fred_df.columns = ["Liquidity"]
        fred_df["Liquidity"] = fred_df["Liquidity"] / liq_div
    except Exception:
        # 실패 시 빈 데이터프레임 생성 (차트는 그려지도록)
        fred_df = pd.DataFrame(columns=["Liquidity"])

    # (2) 주가 데이터 (Yahoo Finance)
    try:
        yf_df = yf.download(ticker, start=start_dt, end=end_dt, progress=False)
        
        # MultiIndex 컬럼 처리 (핵심)
        if isinstance(yf_df.columns, pd.MultiIndex):
            try:
                # Ticker 레벨 제거하고 속성(Open, Close 등)만 남김
                yf_df.columns = yf_df.columns.get_level_values(0)
            except:
                pass
        
        # 필수 컬럼 확인 및 복사
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in yf_df.columns for col in required_cols):
             return None, None, "주가 데이터 형식이 올바르지 않습니다."
             
        ohlc = yf_df[required_cols].copy()
        # 결측치 제거
        ohlc.dropna(inplace=True)
        
    except Exception as e:
        return None, None, f"주가 데이터 로딩 실패: {str(e)}"

    # (3) 데이터 병합
    try:
        # 인덱스 시간대 제거 (tz-naive) 후 병합
        fred_df.index = fred_df.index.tz_localize(None)
        ohlc.index = ohlc.index.tz_localize(None)
        
        merged = pd.concat([fred_df, ohlc['Close'].rename('Price')], axis=1).ffill()
        merged = merged.dropna(subset=['Price'])
        
        # 파생 변수 계산
        merged["Liq_MA"] = merged["Liquidity"].rolling(20).mean()
        merged["Price_MA5"] = merged["Price"].rolling(5).mean()
        merged["Price_MA20"] = merged["Price"].rolling(20).mean()
        merged["Price_MA60"] = merged["Price"].rolling(60).mean()
        merged["Price_MA120"] = merged["Price"].rolling(120).mean()
        
        # YoY 및 상관계수
        merged["Liq_YoY"] = merged["Liquidity"].pct_change(252) * 100
        merged["Price_YoY"] = merged["Price"].pct_change(252) * 100
        merged["Corr"] = merged["Liquidity"].rolling(60).corr(merged["Price"])

        return ohlc, merged, None

    except Exception as e:
        return None, None, f"데이터 처리 중 오류: {str(e)}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 설정 및 데이터 준비
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_EVENTS = [
    ("2024-11-05", "트럼프 당선", "🗳️", "up"),
    ("2025-01-27", "DeepSeek 쇼크", "🤖", "down"),
    ("2025-04-09", "관세 유예", "🕊️", "up"),
    ("2025-12-11", "RMP 재개", "💰", "up"),
    ("2026-02-05", "유동성 확장", "📈", "up"),
]

CONFIG = {
    "🇺🇸 미국": {"idx": {"S&P 500": "^GSPC", "나스닥": "^IXIC"}, "liq": "BOGMBASE", "div": 1, "label": "본원통화"},
    "🇰🇷 대한민국": {"idx": {"코스피": "^KS11", "코스닥": "^KQ11"}, "liq": "BOGMBASE", "div": 1, "label": "글로벌 유동성"},
}

# 컨트롤 바
c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 1])
with c1: country = st.selectbox("국가", list(CONFIG.keys()))
CC = CONFIG[country]

# 국가 변경 시 지수 초기화
if st.session_state.get("prev_country") != country:
    st.session_state["prev_country"] = country
    st.session_state["idx_idx"] = 0

with c2: 
    idx_name = st.selectbox("지수", list(CC["idx"].keys()), index=st.session_state.get("idx_idx", 0))
    idx_ticker = CC["idx"][idx_name]

with c3: period = st.selectbox("기간", ["1년", "3년", "5년", "10년", "전체"], index=1)
with c4: tf = st.selectbox("봉", ["일봉", "주봉", "월봉"], index=0)
with c5: show_evt = st.toggle("이벤트", True)

# 데이터 로드 실행
with st.spinner(f"{idx_name} 데이터 분석 중..."):
    ohlc_data, metrics_data, error = load_market_data(idx_ticker, CC["liq"], CC["div"])

if error:
    st.error(error)
    st.stop()

# 기간 필터링
p_days = {"1년": 365, "3년": 1095, "5년": 1825, "10년": 3650, "전체": 10000}
start_date = datetime.now() - timedelta(days=p_days[period])
ohlc_view = ohlc_data[ohlc_data.index >= start_date]
metrics_view = metrics_data[metrics_data.index >= start_date]

# 리샘플링 (주봉/월봉 선택 시)
if tf == "주봉":
    ohlc_view = ohlc_view.resample("W").agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
elif tf == "월봉":
    ohlc_view = ohlc_view.resample("ME").agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. UI 렌더링: 헤더 & KPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
last_row = metrics_data.iloc[-1]
prev_row = metrics_data.iloc[-2]
price = last_row["Price"]
diff = price - prev_row["Price"]
pct = (diff / prev_row["Price"]) * 100
cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
arrow = "▲" if diff > 0 else "▼" if diff < 0 else ""

st.markdown(f"""
<div class="stock-header">
    <div class="header-top">
        <span class="stock-name">{idx_name}</span>
        <span class="stock-code">{idx_ticker}</span>
    </div>
    <div class="price-row">
        <span class="current-price {cls}">{price:,.2f}</span>
        <span class="price-change {cls}">{arrow} {abs(diff):,.2f} ({pct:+.2f}%)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI 바
st.markdown(f"""
<div class="kpi-bar">
    <div class="kpi-item">
        <span class="kpi-title">{CC['label']}</span>
        <span class="kpi-val">{last_row['Liquidity']:,.0f}B</span>
    </div>
    <div class="kpi-item">
        <span class="kpi-title">유동성(YoY)</span>
        <span class="kpi-val {cls}">{last_row['Liq_YoY']:+.1f}%</span>
    </div>
    <div class="kpi-item">
        <span class="kpi-title">주가(YoY)</span>
        <span class="kpi-val {cls}">{last_row['Price_YoY']:+.1f}%</span>
    </div>
    <div class="kpi-item">
        <span class="kpi-title">상관계수(60일)</span>
        <span class="kpi-val" style="color:{'#f73646' if last_row['Corr']>0.5 else '#333'}">{last_row['Corr']:.2f}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 차트 그리기 (네이버 스타일)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
fig = make_subplots(
    rows=2, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.02, 
    row_heights=[0.75, 0.25],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# [1] 유동성 (배경 영역)
if not metrics_view["Liquidity"].dropna().empty:
    fig.add_trace(go.Scatter(
        x=metrics_view.index, y=metrics_view["Liquidity"],
        name=CC["label"],
        fill="tozeroy", fillcolor="rgba(59,130,246,0.05)",
        line=dict(color="rgba(59,130,246,0.4)", width=1.5),
        hoverinfo="skip"
    ), row=1, col=1, secondary_y=True)

# [2] 캔들스틱
fig.add_trace(go.Candlestick(
    x=ohlc_view.index,
    open=ohlc_view['Open'], high=ohlc_view['High'],
    low=ohlc_view['Low'], close=ohlc_view['Close'],
    increasing_line_color='#f73646', increasing_fillcolor='#f73646',
    decreasing_line_color='#335eff', decreasing_fillcolor='#335eff',
    name='주가'
), row=1, col=1)

# [3] 이동평균선
for ma, color in [(5, '#999'), (20, '#f5a623'), (60, '#33bb55'), (120, '#aa55ff')]:
    # 일봉 기준 MA 계산 (ohlc_view 기준)
    ma_series = ohlc_view['Close'].rolling(ma).mean()
    fig.add_trace(go.Scatter(
        x=ohlc_view.index, y=ma_series,
        mode='lines', line=dict(color=color, width=1),
        name=f'{ma}일'
    ), row=1, col=1)

# [4] 거래량
colors = ['#f73646' if c >= o else '#335eff' for o, c in zip(ohlc_view['Open'], ohlc_view['Close'])]
fig.add_trace(go.Bar(
    x=ohlc_view.index, y=ohlc_view['Volume'],
    marker_color=colors, name='거래량', showlegend=False
), row=2, col=1)

# [5] 이벤트 마커
if show_evt:
    for d, t, emo, dr in MARKET_EVENTS:
        dt = pd.to_datetime(d)
        if dt >= ohlc_view.index.min() and dt <= ohlc_view.index.max():
            fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color="#888", row=1, col=1)
            # 텍스트
            fig.add_annotation(
                x=dt, y=1.02, yref="paper",
                text=f"{emo} {t}",
                showarrow=False,
                font=dict(size=11, color="#f73646" if dr=="up" else "#335eff"),
                textangle=-30,
                xanchor="left", yanchor="bottom",
                row=1, col=1
            )

# [레이아웃 설정]
x_min = ohlc_view.index.min()
x_max = ohlc_view.index.max() + timedelta(days=1)

fig.update_layout(
    plot_bgcolor='white', paper_bgcolor='white',
    margin=dict(t=50, b=20, l=10, r=50), # 우측 여백 확보 (Y축)
    height=600,
    hovermode='x unified',
    dragmode='pan',
    showlegend=True,
    legend=dict(
        orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01,
        bgcolor="rgba(255,255,255,0.7)", borderwidth=0
    ),
    xaxis=dict(
        type='date',
        rangebreaks=[dict(bounds=["sat", "mon"])] if tf == "일봉" else [], # 주말 제거
        minallowed=x_min, maxallowed=x_max
    )
)

# 축 스타일
fig.update_xaxes(gridcolor='#f5f5f5', row=1, col=1)
fig.update_xaxes(gridcolor='#f5f5f5', row=2, col=1)

# Y축: 오른쪽 배치
fig.update_yaxes(
    side='right', gridcolor='#f5f5f5',
    tickfont=dict(color="#333", size=11),
    ticklabelposition="outside",
    fixedrange=True, # Y축 줌 방지
    row=1, col=1, secondary_y=False
)
fig.update_yaxes(visible=False, fixedrange=True, row=1, col=1, secondary_y=True) # 유동성 축 숨김
fig.update_yaxes(side='right', showgrid=False, tickformat='.2s', fixedrange=True, row=2, col=1)

# 차트 렌더링
st.plotly_chart(fig, use_container_width=True, config={
    'displayModeBar': True,
    'scrollZoom': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d']
})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 하단 Daily Brief & 타임라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div class="report-card">
    <div class="report-title">📢 Daily Market Brief</div>
    <div class="report-text">
        <strong>{country} 시장 분석 ({datetime.now().strftime('%Y.%m.%d')})</strong><br>
        현재 <strong>{CC['label']}</strong> 지표는 전년 대비 <span class="highlight">{last_row['Liq_YoY']:+.1f}%</span> 변동을 보이고 있습니다.<br>
        {idx_name} 지수는 <span class="highlight">{last_row['Price_YoY']:+.1f}%</span>의 연간 변동률을 기록 중이며, 
        유동성과의 상관계수는 <strong>{last_row['Corr']:.2f}</strong>로 
        {'매우 밀접하게' if last_row['Corr']>0.7 else '다소 약하게' if last_row['Corr']>0.3 else '반대로'} 움직이고 있습니다.<br><br>
        최근 시장은 중앙은행의 정책 변화와 거시경제 지표에 민감하게 반응하고 있으니, 
        주요 이벤트 구간에서의 변동성에 유의하시기 바랍니다.
    </div>
</div>
""", unsafe_allow_html=True)

# 간단 타임라인
st.markdown("##### 🗓️ 주요 매크로 이벤트")
for d, t, emo, dr in reversed(MARKET_EVENTS):
    if pd.to_datetime(d) < ohlc_view.index.min(): continue
    color = "#f73646" if dr == "up" else "#335eff"
    st.markdown(
        f"<div style='padding:8px 0; border-bottom:1px solid #eee; font-size:0.9rem;'>"
        f"<span style='color:#888; font-family:monospace; margin-right:10px;'>{d}</span>"
        f"{emo} <strong>{t}</strong>"
        f"<span style='float:right; font-weight:bold; color:{color};'>{dr.upper()}</span>"
        f"</div>", 
        unsafe_allow_html=True
    )

# 푸터
st.markdown("<br><div style='text-align:center; color:#999; font-size:0.8rem;'>Data: FRED, Yahoo Finance / Dev: Streamlit</div>", unsafe_allow_html=True)