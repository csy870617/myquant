import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="MyQuant: Liquidity Insight", 
    page_icon="icon.png", 
    layout="wide"
)

# 상단 로고 (파일 있으면 적용)
try:
    st.logo("icon.png")
except Exception:
    pass 

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 자동 새로고침 로직
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
    return next_t.astimezone(ZoneInfo("Asia/Seoul")), secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()
st.markdown(f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. CSS (마이퀀트 스타일 적용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-main: #1e293b;
    --text-sub: #64748b;
    --accent-blue: #2563eb;
    --up-color: #10b981;    /* 상승/매수: 에메랄드 그린 */
    --down-color: #ef4444;  /* 하락/매도: 레드 */
    --neutral-color: #f59e0b; /* 중립: 앰버 */
    --border-color: #e2e8f0;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', sans-serif;
    background-color: var(--bg-color) !important;
    color: var(--text-main);
}
[data-testid="stHeader"] { background: transparent !important; }

.block-container { 
    max-width: 1280px; 
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
}

/* ── 헤더 ── */
.mq-header { 
    display: flex; align-items: center; justify-content: space-between; 
    margin-bottom: 1.5rem; border-bottom: 2px solid var(--border-color);
    padding-bottom: 1rem;
}
.mq-title { 
    font-size: 1.8rem; font-weight: 800; letter-spacing: -0.5px; 
    background: linear-gradient(135deg, #1e3a8a, #3b82f6); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
}
.mq-subtitle { font-size: 0.95rem; color: var(--text-sub); font-weight: 500; margin-top: 2px; }

/* ── 퀀트 리포트 카드 (핵심 UI) ── */
.quant-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    margin-bottom: 24px;
}

/* 시그널 헤더 */
.signal-header { 
    display: flex; align-items: center; justify-content: space-between; 
    margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px dashed var(--border-color); 
}
.signal-badge { 
    padding: 8px 16px; border-radius: 99px; font-size: 1rem; font-weight: 800; 
    text-transform: uppercase; letter-spacing: 0.5px; color: white; display: inline-block;
}
.bg-buy { background: var(--up-color); box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25); }
.bg-sell { background: var(--down-color); box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25); }
.bg-neutral { background: var(--neutral-color); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25); }

.score-box { text-align: right; }
.score-val { font-size: 2.2rem; font-weight: 900; line-height: 1; letter-spacing: -1px; }
.score-label { font-size: 0.7rem; color: var(--text-sub); font-weight: 700; text-transform: uppercase; margin-top: 4px; }

/* 팩터 그리드 */
.factor-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.factor-item { 
    background: #f8fafc; padding: 16px; border-radius: 12px; border: 1px solid #f1f5f9; 
    transition: transform 0.2s;
}
.factor-item:hover { transform: translateY(-2px); border-color: #cbd5e1; }
.factor-name { font-size: 0.75rem; color: var(--text-sub); font-weight: 700; text-transform: uppercase; margin-bottom: 6px; }
.factor-val { font-size: 1.25rem; font-weight: 800; color: var(--text-main); font-family: 'IBM Plex Mono', monospace; }
.factor-sub { font-size: 0.75rem; margin-top: 4px; font-weight: 500; }

/* 코멘터리 박스 */
.commentary-box { 
    background: #fdfbf7; border-left: 4px solid var(--accent-blue); 
    padding: 18px; border-radius: 0 8px 8px 0; 
    font-size: 0.95rem; line-height: 1.7; color: #334155; 
}
.commentary-box strong { color: #1e293b; font-weight: 700; background: rgba(37, 99, 235, 0.1); padding: 0 4px; border-radius: 4px; }

/* 유틸리티 */
.text-up { color: var(--up-color); }
.text-down { color: var(--down-color); }
.text-neu { color: var(--neutral-color); }

/* 기타 */
div[data-testid="stMetric"] { display: none; }
.stSelectbox label { font-size: 0.85rem; font-weight: 600; color: var(--text-sub); }
.app-footer { text-align:center; color:var(--text-muted); font-size:0.75rem; margin-top:2rem; padding:1rem; border-top:1px solid var(--border); }
.modebar { opacity: 0.5 !important; }

@media (max-width: 768px) {
    .factor-grid { grid-template-columns: repeat(2, 1fr); }
    .mq-title { font-size: 1.4rem; }
    .score-val { font-size: 1.8rem; }
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 데이터 & 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    ("2022-10-13", "CPI 피크아웃", "인플레 둔화 확인", "📊", "up"),
    ("2023-01-19", "강세장 전환", "S&P500 골든크로스", "🐂", "up"),
    ("2024-09-18", "연준 빅컷", "금리인하 사이클 개시", "✂️", "up"),
    ("2024-11-05", "트럼프 2기 당선", "규제 완화 기대", "🗳️", "up"),
    ("2025-01-27", "DeepSeek 쇼크", "AI 수익성 우려", "🤖", "down"),
    ("2025-12-11", "RMP 국채매입", "유동성 재공급", "💰", "up"),
]

COUNTRY_CONFIG = {
    "🇺🇸 미국": {
        "indices": {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI"},
        "default_idx": 1,
        "fred_liq": "BOGMBASE", "fred_rate": "DFEDTARU", "rate_label": "Fed 금리",
        "liq_divisor": 1000, "liq_unit": "$B", "liq_prefix": "$",
        "events": MARKET_PIVOTS
    },
    "🇰🇷 대한민국": {
        "indices": {"KOSPI": "^KS11", "KOSDAQ": "^KQ11"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE", "fred_rate": "IRSTCI01KRM156N", "rate_label": "Call 금리",
        "liq_divisor": 1000, "liq_unit": "$B", "liq_prefix": "$",
        "events": MARKET_PIVOTS
    },
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 데이터 로드 (보조지표 추가)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker, fred_liq, fred_rate, liq_divisor):
    try:
        end_dt = datetime.now()
        fetch_start = end_dt - timedelta(days=365 * 5) # 5년치

        # 1. FRED 데이터
        fred_df = web.DataReader([fred_liq, fred_rate], "fred", fetch_start, end_dt).ffill()
        fred_df.columns = ["Liquidity", "Rate"]
        
        # 유동성 단위 보정
        if liq_divisor == 1 and fred_df["Liquidity"].iloc[-1] > 100000:
             fred_df["Liquidity"] = fred_df["Liquidity"] / 1000
        else:
             fred_df["Liquidity"] = fred_df["Liquidity"] / liq_divisor
        
        # 2. 주가 데이터
        import yfinance as yf
        yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
        
        if isinstance(yf_data.columns, pd.MultiIndex):
            idx_close = yf_data['Close'][[ticker]].rename(columns={ticker: 'SP500'})
            ohlc = yf_data.xs(ticker, level=1, axis=1)[['Open','High','Low','Close','Volume']]
            ohlc.columns = ['Open','High','Low','Close','Volume']
        else:
            idx_close = yf_data[['Close']].rename(columns={'Close': 'SP500'})
            ohlc = yf_data[['Open','High','Low','Close','Volume']]

        # 3. 데이터 통합
        df = pd.concat([fred_df, idx_close], axis=1).ffill().dropna()

        # 4. 퀀트 지표 계산 (RSI, MA, Z-Score, MDD)
        # 이동평균
        df["MA20"] = df["SP500"].rolling(20).mean()
        df["MA60"] = df["SP500"].rolling(60).mean()
        
        # RSI (14일)
        delta = df["SP500"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
        
        # 유동성 Z-Score (1년)
        df["Liq_Mean"] = df["Liquidity"].rolling(252).mean()
        df["Liq_Std"] = df["Liquidity"].rolling(252).std()
        df["Liq_Z"] = (df["Liquidity"] - df["Liq_Mean"]) / df["Liq_Std"]
        
        # MDD (1년)
        roll_max = df["SP500"].rolling(252, min_periods=1).max()
        df["MDD"] = (df["SP500"] / roll_max) - 1

        return df, ohlc
        
    except Exception as e:
        st.error(f"데이터 로드 실패: {str(e)}")
        return None, None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 메인 UI 구성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# [헤더]
now_str = datetime.now().strftime("%Y.%m.%d %H:%M")
st.markdown(f"""
<div class="mq-header">
    <div>
        <div class="mq-title">MYQUANT INSIGHT</div>
        <div class="mq-subtitle">AI & Liquidity Market Intelligence System</div>
    </div>
    <div style="text-align:right; font-size:0.8rem; color:#94a3b8; font-family:'IBM Plex Mono';">
        Updated: {now_str}<br>Algo v2.5
    </div>
</div>
""", unsafe_allow_html=True)

# [컨트롤]
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    country = st.selectbox("Market Region", list(COUNTRY_CONFIG.keys()))
with c2:
    idx_name = st.selectbox("Index", list(COUNTRY_CONFIG[country]["indices"].keys()))

CC = COUNTRY_CONFIG[country]
idx_ticker = CC["indices"][idx_name]

# 데이터 로딩
with st.spinner("퀀트 엔진 분석 중..."):
    df, ohlc = load_data(idx_ticker, CC["fred_liq"], CC["fred_rate"], CC["liq_divisor"])

if df is None: st.stop()

# 최신 데이터
last = df.iloc[-1]
prev_m = df.iloc[-22] if len(df) > 22 else df.iloc[0]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 스코어링 엔진 (Scoring Engine)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def calculate_quant_score(row, prev_row_m):
    score = 0
    # 1. 유동성 (30점)
    if row["Liquidity"] > prev_row_m["Liquidity"]: score += 15
    if row["Liq_Z"] > 0: score += 5
    if row["Liq_Z"] > 1.5: score += 10
    
    # 2. 추세 (30점)
    if row["SP500"] > row["MA60"]: score += 15
    if row["MA20"] > row["MA60"]: score += 15
    
    # 3. 모멘텀 (20점)
    if 40 <= row["RSI"] <= 70: score += 20
    elif row["RSI"] < 30: score += 10 # 과매도 반등 기대
    elif row["RSI"] > 75: score -= 5  # 과매수 경고
    
    # 4. 금리 (20점)
    rate_delta = row["Rate"] - prev_row_m["Rate"]
    if rate_delta < 0: score += 20
    elif rate_delta == 0: score += 10
    
    return min(max(score, 0), 100)

total_score = calculate_quant_score(last, prev_m)

# 시그널 결정
if total_score >= 80:
    sig_txt, badge_cls, sig_desc, score_col = "STRONG BUY", "bg-buy", "강력 매수: 유동성/추세 완벽", "#10b981"
elif total_score >= 60:
    sig_txt, badge_cls, sig_desc, score_col = "BUY", "bg-buy", "매수 우위: 긍정적 시장 환경", "#10b981"
elif total_score >= 40:
    sig_txt, badge_cls, sig_desc, score_col = "NEUTRAL", "bg-neutral", "중립: 방향성 탐색 구간", "#f59e0b"
elif total_score >= 20:
    sig_txt, badge_cls, sig_desc, score_col = "CAUTION", "bg-neutral", "주의: 하락 압력 존재", "#f59e0b"
else:
    sig_txt, badge_cls, sig_desc, score_col = "SELL / HEDGE", "bg-sell", "매도/관망: 리스크 관리 필수", "#ef4444"

# 자동 코멘트
liq_chg = (last['Liquidity'] - prev_m['Liquidity']) / prev_m['Liquidity'] * 100
commentary = f"""
현재 <strong>{idx_name}</strong> 시장의 퀀트 종합 점수는 <strong>{total_score}점</strong>으로 <strong>'{sig_txt}'</strong> 단계입니다.<br>
핵심 동력인 <strong>글로벌 유동성은 전월 대비 {liq_chg:+.2f}% {'확대' if liq_chg>0 else '축소'}</strong> 국면에 있으며, 유동성 강도(Z-Score)는 <strong>{last['Liq_Z']:.2f}</strong>입니다.
기술적으로는 <strong>{'상승' if last['SP500'] > last['MA60'] else '하락'} 추세</strong>(MA60 기준)를 보이며, RSI는 <strong>{last['RSI']:.1f}</strong>입니다.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 리포트 카드 렌더링
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div class="quant-card">
    <div class="signal-header">
        <div>
            <span class="signal-badge {badge_cls}">{sig_txt}</span>
            <span style="margin-left:12px; font-weight:600; color:#64748b; font-size:0.95rem;">{sig_desc}</span>
        </div>
        <div class="score-box">
            <div class="score-val" style="color:{score_col}">{total_score}</div>
            <div class="score-label">Quant Score</div>
        </div>
    </div>
    
    <div class="factor-grid">
        <div class="factor-item">
            <div class="factor-name">💧 Liquidity Flow</div>
            <div class="factor-val">{CC['liq_prefix']}{last['Liquidity']:,.0f}{CC['liq_unit']}</div>
            <div class="factor-sub { 'text-up' if liq_chg > 0 else 'text-down' }">MoM {liq_chg:+.2f}%</div>
        </div>
        <div class="factor-item">
            <div class="factor-name">📉 RSI (14)</div>
            <div class="factor-val">{last['RSI']:.1f}</div>
            <div class="factor-sub { 'text-down' if last['RSI'] > 70 else 'text-up' if last['RSI'] < 30 else 'text-neu' }">
                {'Overbought' if last['RSI'] > 70 else 'Oversold' if last['RSI'] < 30 else 'Neutral'}
            </div>
        </div>
        <div class="factor-item">
            <div class="factor-name">🏛 Rate ({CC['rate_label']})</div>
            <div class="factor-val">{last['Rate']:.2f}%</div>
            <div class="factor-sub text-neu">Spread {last['Rate'] - prev_m['Rate']:+.2f}bp</div>
        </div>
        <div class="factor-item">
            <div class="factor-name">⚠️ Risk (MDD)</div>
            <div class="factor-val" style="color:#ef4444">{last['MDD']*100:.2f}%</div>
            <div class="factor-sub">From 52w High</div>
        </div>
    </div>

    <div class="commentary-box">{commentary}</div>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 차트 섹션 (Tab 구조)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tab1, tab2 = st.tabs(["📈 Technical Analysis", "💧 Macro Correlation"])

with tab1:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    
    # 캔들 & 이평선
    fig.add_trace(go.Candlestick(x=ohlc.index, open=ohlc['Open'], high=ohlc['High'], low=ohlc['Low'], close=ohlc['Close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#f59e0b', width=1), name='MA20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='#3b82f6', width=1.5), name='MA60'), row=1, col=1)
    
    # 이벤트 마커
    for d, t, _, e, dir in CC["events"]:
        dt = pd.to_datetime(d)
        if dt >= df.index[0] and dt <= df.index[-1]:
            c = "#10b981" if dir == "up" else "#ef4444"
            fig.add_vline(x=dt, line_dash="dot", line_color="rgba(100,100,100,0.3)", row=1, col=1)
            fig.add_annotation(x=dt, y=1.02, yref="paper", text=e, showarrow=False, font=dict(size=14), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#8b5cf6', width=1.5), name='RSI'), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
    
    fig.update_layout(height=600, margin=dict(t=10, b=10, l=10, r=10), showlegend=False, xaxis_rangeslider_visible=False)
    fig.update_xaxes(showgrid=True, gridcolor='#f1f5f9')
    fig.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig_liq = go.Figure()
    # 정규화 함수
    def norm(s): return (s - s.min()) / (s.max() - s.min()) * 100
    
    fig_liq.add_trace(go.Scatter(x=df.index, y=norm(df['Liquidity']), name='Liquidity', fill='tozeroy', line=dict(color='#3b82f6', width=2)))
    fig_liq.add_trace(go.Scatter(x=df.index, y=norm(df['SP500']), name='Price', line=dict(color='#1e293b', width=2)))
    
    fig_liq.update_layout(title="Liquidity vs Price (Normalized)", height=500, margin=dict(t=30, b=10, l=10, r=10), hovermode="x unified")
    st.plotly_chart(fig_liq, use_container_width=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(f"""
<div class="app-footer">
    Data Sources: {CC["data_src"]} • Powered by MyQuant Engine<br>
    본 리포트는 투자 조언이 아니며, 모든 투자의 책임은 사용자에게 있습니다.
</div>
""", unsafe_allow_html=True)