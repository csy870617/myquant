import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from zoneinfo import ZoneInfo
from sklearn.linear_model import LinearRegression

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 페이지 설정 및 로고
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="유동성 × 시장 분석기 Pro", 
    page_icon="icon.png",  
    layout="wide"
)

try:
    st.logo("icon.png")
except Exception:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 자동 새로고침 로직
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_next_refresh():
    """다음 새로고침 시각까지 남은 초 계산 (PST 09/18 + KST 09/18)"""
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
    local_next = next_t.astimezone(ZoneInfo("Asia/Seoul"))
    return local_next, secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()

st.markdown(
    f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 디자인 시스템 (Modern / Bento Grid Style)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg-color: #F3F4F6;
    --card-bg: #FFFFFF;
    --text-main: #111827;
    --text-sub: #6B7280;
    --accent-primary: #3B82F6;
    --accent-success: #10B981;
    --accent-danger: #EF4444;
    --border-color: rgba(229, 231, 235, 0.8);
    --shadow-soft: 0 10px 40px -10px rgba(0,0,0,0.05);
    --shadow-hover: 0 20px 40px -10px rgba(0,0,0,0.1);
    --radius-l: 24px;
    --radius-m: 16px;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', sans-serif;
    background-color: var(--bg-color) !important;
    color: var(--text-main);
}

[data-testid="stHeader"] { background: transparent !important; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 1400px;
}

/* ── Header ── */
.header-container {
    display: flex; flex-direction: column; align-items: flex-start;
    margin-bottom: 2rem;
}
.header-badge {
    background: linear-gradient(135deg, #2563EB, #4F46E5);
    color: white; padding: 6px 14px; border-radius: 100px;
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 0.8rem; box-shadow: 0 4px 12px rgba(37,99,235,0.3);
}
.header-title {
    font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em;
    background: linear-gradient(90deg, #1F2937, #4B5563);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.4rem;
}
.header-desc { font-size: 1rem; color: var(--text-sub); }

/* ── Bento Grid ── */
.bento-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;
}
.bento-card {
    background: var(--card-bg); border-radius: var(--radius-l); padding: 1.5rem;
    border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    display: flex; flex-direction: column; justify-content: space-between;
}
.bento-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }

.kpi-title { font-size: 0.8rem; font-weight: 600; color: var(--text-sub); text-transform: uppercase; margin-bottom: 8px; }
.kpi-metric { font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 700; color: var(--text-main); margin-bottom: 4px; }
.kpi-sub { font-size: 0.85rem; font-weight: 500; }
.trend-up { color: var(--accent-success); background: rgba(16,185,129,0.1); padding: 2px 8px; border-radius: 6px; }
.trend-down { color: var(--accent-danger); background: rgba(239,68,68,0.1); padding: 2px 8px; border-radius: 6px; }
.trend-neu { color: var(--text-sub); background: rgba(107,114,128,0.1); padding: 2px 8px; border-radius: 6px; }

/* ── Report Container ── */
.report-container {
    background: #FFFFFF; border-radius: var(--radius-l); border: 1px solid var(--border-color);
    padding: 2rem; margin-bottom: 24px; box-shadow: var(--shadow-soft);
}
.report-top { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px dashed var(--border-color); padding-bottom: 1.2rem; margin-bottom: 1.2rem; }
.signal-badge { padding: 6px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; }
.sig-bull { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.sig-bear { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.sig-neu  { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }

/* ── Timeline ── */
.timeline-track { position: relative; padding-left: 24px; margin-top: 1rem; }
.timeline-track::before { content: ''; position: absolute; left: 6px; top: 0; bottom: 0; width: 2px; background: #E5E7EB; border-radius: 2px; }
.tl-card { position: relative; background: #fff; margin-bottom: 16px; padding: 16px; border-radius: var(--radius-m); border: 1px solid var(--border-color); }
.tl-dot { position: absolute; left: -23px; top: 20px; width: 10px; height: 10px; background: #fff; border: 2px solid var(--accent-primary); border-radius: 50%; z-index: 2; }
.tl-date { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-sub); margin-bottom: 4px; }
.tl-tag { font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 100px; text-transform: uppercase; float: right; }
.tag-up { background: #ECFDF5; color: #059669; }
.tag-down { background: #FEF2F2; color: #DC2626; }

/* ── Control & Chart ── */
div[data-testid="stHorizontalBlock"] { background: white; padding: 12px; border-radius: 16px; border: 1px solid var(--border-color); box-shadow: var(--shadow-soft); align-items: center; }
.chart-wrapper { background: white; border-radius: var(--radius-l); border: 1px solid var(--border-color); padding: 16px; box-shadow: var(--shadow-soft); }
.status-pill { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #E5E7EB; padding: 6px 16px; border-radius: 100px; font-size: 0.75rem; color: var(--text-sub); font-weight: 500; box-shadow: 0 2px 5px rgba(0,0,0,0.03); margin-bottom: 1.5rem; }
.status-dot { width: 8px; height: 8px; background: #10B981; border-radius: 50%; animation: pulse 2s infinite; }

@media (max-width: 768px) {
    .bento-grid { grid-template-columns: repeat(2, 1fr); }
    .header-title { font-size: 1.6rem; }
}
@media (max-width: 480px) {
    .bento-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 데이터 & 이벤트 로드 (Net Liquidity 적용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    ("2024-02-22", "NVIDIA 실적 서프라이즈", "AI 매출 폭증 → 시총 $2T 돌파, AI 랠리 가속", "🚀", "up"),
    ("2024-08-05", "엔 캐리트레이드 청산", "일본 금리인상 → 글로벌 디레버리징, VIX 65", "🇯🇵", "down"),
    ("2024-09-18", "연준 빅컷 (50bp)", "금리인하 사이클 개시, 소형주 급등", "✂️", "up"),
    ("2024-11-05", "트럼프 2기 당선", "감세·규제완화 기대 → 지수 역대 신고가", "🗳️", "up"),
    ("2025-01-27", "DeepSeek AI 쇼크", "중국 저비용 AI 모델 → 반도체주 폭락", "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세", "전방위 관세 발표 → 이틀간 -10%, VIX 60", "🚨", "down"),
    ("2025-04-09", "관세 90일 유예", "트럼프 관세 일시중단 → 역대급 반등 +9.5%", "🕊️", "up"),
    ("2025-12-11", "RMP 국채매입 재개", "준비금 관리 매입 개시 → 유동성 확장 전환", "💰", "up"),
]

MARKET_PIVOTS_KR = [
    ("2024-01-02", "밸류업 프로그램 발표", "PBR 1배 미만 기업 개선 요구 → 저PBR주 급등", "📋", "up"),
    ("2024-08-05", "엔 캐리트레이드 청산", "글로벌 디레버리징 → KOSPI -8.8% 블랙먼데이", "🇯🇵", "down"),
    ("2024-12-03", "윤석열 비상계엄 선포", "정치 위기 → KOSPI 급락, 원화 1,440원 돌파", "🚨", "down"),
    ("2025-01-27", "DeepSeek AI 쇼크", "중국 AI 충격 → 삼성전자·SK하이닉스 급락", "🤖", "down"),
    ("2025-06-03", "한은 기준금리 2.50% 인하", "경기 부양 위해 추가 인하 → 유동성 확대", "✂️", "up"),
]

COUNTRY_CONFIG = {
    "🇺🇸 미국": {
        "indices": {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI"},
        "default_idx": 1,
        "liq_source": "NET_LIQUIDITY", # Net Liquidity 모드
        "liq_label": "Net Liquidity",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "events": MARKET_PIVOTS,
        "data_src": "FRED (WALCL, WTREGEN, RRP) · Yahoo Finance",
    },
    "🇰🇷 대한민국": {
        "indices": {"KOSPI": "^KS11", "KOSDAQ": "^KQ11"},
        "default_idx": 0,
        "liq_source": "NET_LIQUIDITY", # 한국도 글로벌 유동성(Fed) 영향 받음
        "liq_label": "Fed Net Liquidity",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "events": MARKET_PIVOTS_KR,
        "data_src": "FRED (Global Liquidity) · Yahoo Finance (KRX)",
    },
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker, country_code):
    try:
        end_dt = datetime.now()
        fetch_start = end_dt - timedelta(days=365 * 10)

        # [A] FRED 데이터 (Net Liquidity Components)
        # WALCL: Fed Total Assets
        # WTREGEN: Treasury General Account (TGA)
        # RRPONTSYD: Reverse Repo (RRP)
        try:
            fred_codes = ["WALCL", "WTREGEN", "RRPONTSYD", "USREC"]
            fred_df = web.DataReader(fred_codes, "fred", fetch_start, end_dt).ffill()
            fred_df.columns = ["Assets", "TGA", "RRP", "Recession"]
            
            # Net Liquidity = Assets - TGA - RRP
            # FRED 데이터 단위는 모두 Millions of USD
            fred_df["Net_Liquidity"] = fred_df["Assets"] - fred_df["TGA"] - fred_df["RRP"]
            
            # Billions 단위로 변환
            fred_df["Liquidity"] = fred_df["Net_Liquidity"] / 1000 
            
        except Exception as e:
            st.error(f"FRED 데이터 로드 실패: {e}")
            return None, None

        # [B] 주가 지수 데이터
        try:
            import yfinance as yf
            yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
            if yf_data.empty: return None, None
            
            if isinstance(yf_data.columns, pd.MultiIndex):
                idx_close = yf_data['Close'][[ticker]].rename(columns={ticker: 'SP500'})
                ohlc = yf_data[[('Open',ticker),('High',ticker),('Low',ticker),('Close',ticker),('Volume',ticker)]].copy()
                ohlc.columns = ['Open','High','Low','Close','Volume']
            else:
                idx_close = yf_data[['Close']].rename(columns={'Close': 'SP500'})
                ohlc = yf_data[['Open','High','Low','Close','Volume']].copy()
        except Exception as e:
            st.error(f"지수 데이터 로드 실패: {e}")
            return None, None

        # [C] 데이터 통합
        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        df = df.dropna(subset=["SP500", "Liquidity"])

        if 'SP500' in df.columns:
            df["Liq_MA"] = df["Liquidity"].rolling(20).mean() # 20일 이동평균 (한달 추세)
            df["SP_MA"] = df["SP500"].rolling(20).mean()
            df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
            df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        else:
            return None, None

        # 상관계수 (90일 Rolling)
        df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])
        
        # [D] Fair Value Model (Linear Regression on last 1 year)
        # 최근 1년 데이터로 회귀분석하여 '적정 주가' 추정
        reg_window = 252
        if len(df) > reg_window:
            recent_df = df.iloc[-reg_window:]
            X = recent_df["Liquidity"].values.reshape(-1, 1)
            y = recent_df["SP500"].values
            model = LinearRegression()
            model.fit(X, y)
            df["Fair_Value"] = model.predict(df["Liquidity"].values.reshape(-1, 1))
            df["Valuation_Gap"] = (df["SP500"] - df["Fair_Value"]) / df["Fair_Value"] * 100
            
            # R-Squared (결정계수)
            df["R_Squared"] = model.score(X, y)
        else:
            df["Fair_Value"] = np.nan
            df["Valuation_Gap"] = 0
            df["R_Squared"] = 0

        return df, ohlc
    except Exception as e:
        st.error(f"시스템 오류: {str(e)}")
        return None, None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 차트 헬퍼
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C = {
    "liq": "#3B82F6", "liq_fill": "rgba(59,130,246,0.1)",
    "sp": "#1F2937", "sp_fill": "rgba(0,0,0,0)",
    "corr_pos": "#10B981", "corr_neg": "#EF4444",
    "grid": "rgba(0,0,0,0.06)", "bg": "rgba(0,0,0,0)", "paper": "rgba(0,0,0,0)",
    "event": "rgba(0,0,0,0.15)", "rec": "rgba(239,68,68,0.05)",
}
BASE_LAYOUT = dict(
    plot_bgcolor=C["bg"], paper_bgcolor=C["paper"],
    font=dict(family="Pretendard, sans-serif", color="#4B5563", size=12),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", bordercolor="#E5E7EB", font=dict(color="#111827", size=12, family="Pretendard")),
    margin=dict(t=50, b=30, l=10, r=10), dragmode="pan",
)

def add_events_to_fig(fig, dff, events, has_rows=False, min_gap_days=30):
    prev_dt = None
    for date_str, title, _, emoji, direction in events:
        dt = pd.to_datetime(date_str)
        if dt < dff.index.min() or dt > dff.index.max(): continue
        if prev_dt and (dt - prev_dt).days < min_gap_days: continue
        prev_dt = dt
        kw = dict(row="all", col=1) if has_rows else {}
        fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color=C["event"], **kw)
        clr = "#10B981" if direction == "up" else "#EF4444"
        fig.add_annotation(x=dt, y=1.02, yref="paper", text=f"{emoji}",
            showarrow=False, font=dict(size=14), xanchor="center")

def add_recession(fig, dff, has_rows=False):
    if "Recession" not in dff.columns: return
    rec_idx = dff[dff["Recession"] == 1].index
    if rec_idx.empty: return
    groups, start = [], rec_idx[0]
    for i in range(1, len(rec_idx)):
        if (rec_idx[i] - rec_idx[i - 1]).days > 5:
            groups.append((start, rec_idx[i - 1])); start = rec_idx[i]
    groups.append((start, rec_idx[-1]))
    for s, e in groups:
        kw = dict(row="all", col=1) if has_rows else {}
        fig.add_vrect(x0=s, x1=e, fillcolor=C["rec"], layer="below", line_width=0, **kw)

def ax(extra=None):
    d = dict(gridcolor=C["grid"], linecolor="#E5E7EB", tickfont=dict(size=11, color="#6B7280"), showgrid=True, zeroline=False, gridwidth=1)
    if extra: d.update(extra)
    return d

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 헤더 및 상태바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div class="header-container">
    <div class="header-badge">QUANT / MACRO INTELLIGENCE PRO</div>
    <div class="header-title">LIQUIDITY & MARKET</div>
    <div class="header-desc">
        <strong>Fed Net Liquidity(순유동성)</strong> 모델을 기반으로 시장을 분석합니다.<br>
        유동성 사이클과 적정 주가(Fair Value) 괴리율을 실시간으로 추적하세요.
    </div>
</div>
""", unsafe_allow_html=True)

now_str = datetime.now().strftime("%Y.%m.%d %H:%M")
next_str = NEXT_REFRESH_TIME.strftime("%m/%d %H:%M")
st.markdown(
    f'<div class="status-pill">'
    f'<span class="status-dot"></span>'
    f'LIVE DATA · 갱신 {now_str}'
    f'</div>',
    unsafe_allow_html=True,
)

kpi_container = st.container()
brief_container = st.container()
st.write("")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 컨트롤 바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1, 0.5])
with ctrl1:
    country = st.selectbox("국가 선택", list(COUNTRY_CONFIG.keys()), index=0)
CC = COUNTRY_CONFIG[country]
IDX_OPTIONS = CC["indices"]

if st.session_state.get("_prev_country") != country:
    st.session_state["_prev_country"] = country
    st.session_state["idx_select"] = list(IDX_OPTIONS.keys())[CC["default_idx"]]

with ctrl2:
    idx_name = st.selectbox("지수 선택", list(IDX_OPTIONS.keys()), key="idx_select")
    idx_ticker = IDX_OPTIONS[idx_name]
with ctrl3:
    period = st.selectbox("분석 기간", ["3년", "5년", "7년", "10년", "전체"], index=1)
with ctrl4:
    tf = st.selectbox("캔들 주기", ["일봉", "주봉", "월봉"], index=1)
with ctrl5:
    st.write("") 
    st.write("")
    show_events = st.toggle("이벤트", value=True)

period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 12}
period_years = period_map[period]
cutoff = datetime.now() - timedelta(days=365 * period_years)

with st.spinner("Fed 데이터 및 시장 데이터를 분석 중..."):
    df, ohlc_raw = load_data(idx_ticker, country)

if df is None or df.empty:
    st.error("데이터 로드 실패. 잠시 후 다시 시도해주세요.")
    st.stop()

# Auto Events
def detect_auto_events(ohlc_df, base_events, threshold=0.05):
    if ohlc_df is None or ohlc_df.empty or len(ohlc_df) < 2: return []
    daily_ret = ohlc_df["Close"].pct_change()
    existing_dates = {pd.to_datetime(d).date() for d, *_ in base_events}
    auto = []
    for dt_idx, ret in daily_ret.items():
        if pd.isna(ret) or dt_idx.date() in existing_dates: continue
        if abs(ret) < threshold: continue
        pct = ret * 100
        if ret > 0: auto.append((dt_idx.strftime("%Y-%m-%d"), f"급등 {pct:+.1f}%", f"변동폭 확대", "🔥", "up"))
        else: auto.append((dt_idx.strftime("%Y-%m-%d"), f"급락 {pct:+.1f}%", f"변동폭 확대", "⚡", "down"))
        existing_dates.add(dt_idx.date())
    return auto

BASE_EVENTS = CC["events"]
AUTO_EVENTS = detect_auto_events(ohlc_raw, BASE_EVENTS)
ALL_EVENTS = sorted(BASE_EVENTS + AUTO_EVENTS, key=lambda x: x[0])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. KPI (Bento Style)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with kpi_container:
    latest = df.iloc[-1]
    prev_week = df.iloc[-5] if len(df) > 5 else latest
    
    liq_val = latest["Liquidity"]
    liq_chg_w = (latest["Liquidity"] - prev_week["Liquidity"]) / prev_week["Liquidity"] * 100
    
    sp_val = latest["SP500"]
    sp_chg_w = (latest["SP500"] - prev_week["SP500"]) / prev_week["SP500"] * 100
    
    corr_val = latest["Corr_90d"]
    r_squared = latest["R_Squared"]
    val_gap = latest["Valuation_Gap"]

    def trend_badge(val, neutral_range=0.5):
        if val > neutral_range:
            return f'<span class="trend-up">▲ {val:+.1f}%</span>'
        elif val < -neutral_range:
            return f'<span class="trend-down">▼ {val:+.1f}%</span>'
        else:
            return f'<span class="trend-neu">- {val:+.1f}%</span>'

    liq_display = f"{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}"
    
    # Valuation Badge
    if val_gap > 5: val_badge = '<span class="trend-down">Overvalued (고평가)</span>'
    elif val_gap < -5: val_badge = '<span class="trend-up">Undervalued (저평가)</span>'
    else: val_badge = '<span class="trend-neu">Fair Value (적정)</span>'

    st.markdown(f"""
    <div class="bento-grid">
        <div class="bento-card">
            <div>
                <div class="kpi-title">💧 {CC['liq_label']} (순유동성)</div>
                <div class="kpi-metric">{liq_display}</div>
            </div>
            <div class="kpi-sub">{trend_badge(liq_chg_w)} <span style="color:#9CA3AF; font-size:0.75rem;">vs 1W</span></div>
        </div>
        <div class="bento-card">
            <div>
                <div class="kpi-title">📈 {idx_name}</div>
                <div class="kpi-metric">{sp_val:,.0f}</div>
            </div>
            <div class="kpi-sub">{trend_badge(sp_chg_w)} <span style="color:#9CA3AF; font-size:0.75rem;">vs 1W</span></div>
        </div>
        <div class="bento-card">
            <div>
                <div class="kpi-title">⚖️ Fair Value 괴리율</div>
                <div class="kpi-metric" style="color:{'#EF4444' if val_gap>5 else '#10B981' if val_gap<-5 else '#111827'}">{val_gap:+.1f}%</div>
            </div>
            <div class="kpi-sub">{val_badge}</div>
        </div>
        <div class="bento-card">
            <div>
                <div class="kpi-title">📊 R-Squared (설명력)</div>
                <div class="kpi-metric">{r_squared:.2f}</div>
            </div>
            <div class="kpi-sub"><span style="color:#6B7280; font-size:0.8rem;">유동성의 주가 설명력 (최근 1년)</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. AI Strategy Report (Enhanced Logic)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with brief_container:
    # ── [A] 데이터 분석 (Concrete Data Analysis) ──
    # 1. 유동성 구성요소 변화 분석 (Why is liquidity changing?)
    # 최근 2주간 변화량 계산
    delta_days = 10
    if len(df) > delta_days:
        past = df.iloc[-delta_days]
        
        # Assets change
        assets_chg = (latest["Assets"] - past["Assets"])
        assets_desc = "증가" if assets_chg > 0 else "감소"
        
        # TGA change (TGA 증가는 유동성 감소 요인)
        tga_chg = (latest["TGA"] - past["TGA"])
        tga_impact = "부정적" if tga_chg > 0 else "긍정적"
        
        # RRP change (RRP 증가는 유동성 감소 요인)
        rrp_chg = (latest["RRP"] - past["RRP"])
        rrp_impact = "부정적" if rrp_chg > 0 else "긍정적"
        
        liq_driver_text = []
        if abs(assets_chg) > 10000: # 의미있는 변화가 있을 때만 언급
            liq_driver_text.append(f"연준 자산이 {assets_desc}하며 유동성에 영향을 주었습니다.")
        if tga_chg > 20000:
            liq_driver_text.append(f"재무부 계좌(TGA) 잔고가 증가하여 시중 유동성을 흡수했습니다(Liquidity Drain).")
        elif tga_chg < -20000:
            liq_driver_text.append(f"재무부 계좌(TGA) 자금 집행으로 유동성이 공급되었습니다.")
        if rrp_chg > 20000:
            liq_driver_text.append(f"역레포(RRP) 잔고 증가로 자금이 연준으로 흡수되었습니다.")
        elif rrp_chg < -20000:
            liq_driver_text.append(f"역레포(RRP) 자금이 시장으로 방출되어 유동성을 지지했습니다.")
            
        liq_comment = " ".join(liq_driver_text) if liq_driver_text else "특이한 유동성 구성 요소의 급격한 변화는 관찰되지 않았습니다."
    else:
        liq_comment = "데이터 분석을 위한 충분한 기간이 확보되지 않았습니다."

    # 2. 시장 국면 진단 (Regime Detection)
    liq_trend_slope = (latest["Liq_MA"] - df.iloc[-20]["Liq_MA"]) if len(df) > 20 else 0
    sp_trend_slope = (latest["SP_MA"] - df.iloc[-20]["SP_MA"]) if len(df) > 20 else 0

    if liq_trend_slope > 0 and sp_trend_slope > 0:
        regime = "Liquidity Supported Rally (유동성 장세)"
        regime_desc = "유동성 증가가 주가 상승을 뒷받침하는 건강한 상승장입니다."
        badge_cls = "sig-bull"
    elif liq_trend_slope < 0 and sp_trend_slope < 0:
        regime = "Liquidity Driven Correction (유동성 위축)"
        regime_desc = "유동성 감소가 주가 하락 압력으로 작용하고 있습니다. 보수적 접근이 필요합니다."
        badge_cls = "sig-bear"
    elif liq_trend_slope < 0 and sp_trend_slope > 0:
        regime = "Divergence: Liquidity Drag (괴리 발생)"
        regime_desc = "유동성은 감소하는데 주가는 상승 중입니다. 펀더멘털 개선이 없다면 조정 위험이 높습니다."
        badge_cls = "sig-neu"
    elif liq_trend_slope > 0 and sp_trend_slope < 0:
        regime = "Divergence: Liquidity Support (저가 매수 기회)"
        regime_desc = "주가는 하락 중이나 유동성은 증가하고 있습니다. 하방 경직성이 확보될 가능성이 높습니다."
        badge_cls = "sig-bull"
    else:
        regime = "Neutral / Sideways (방향성 탐색)"
        regime_desc = "뚜렷한 추세가 관찰되지 않는 구간입니다."
        badge_cls = "sig-neu"

    # ── [B] UI 렌더링 ──
    st.markdown(f"""
    <div class="report-container">
        <div class="report-top">
            <div style="display:flex; flex-direction:column; gap:4px;">
                <div style="font-size:0.8rem; font-weight:600; color:#9CA3AF;">AI STRATEGY REPORT</div>
                <div style="font-weight:800; font-size:1.4rem; color:#111827;">Market & Liquidity Analysis</div>
            </div>
            <div class="signal-badge {badge_cls}" style="font-size:1rem; padding:8px 16px;">{regime}</div>
        </div>
        
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px; margin-bottom:1.5rem;">
            <div style="background:#F9FAFB; padding:20px; border-radius:16px; border:1px solid #F3F4F6;">
                <div style="font-size:0.9rem; font-weight:700; color:#4B5563; margin-bottom:10px;">⚖️ Valuation Model</div>
                <div style="margin-bottom:12px;">
                    <span style="font-size:1.8rem; font-weight:800; color:#1F2937;">{val_gap:+.1f}%</span>
                    <span style="font-size:0.9rem; color:#6B7280; margin-left:8px;">Over/Under Valued</span>
                </div>
                <div style="font-size:0.85rem; color:#4B5563; line-height:1.6;">
                    현재 Net Liquidity 기준 적정 주가는 <strong>{latest['Fair_Value']:,.0f}</strong>입니다.<br>
                    실제 주가({latest['SP500']:,.0f})와의 괴리는 <strong>{abs(latest['SP500'] - latest['Fair_Value']):,.0f}pt</strong> 입니다.<br>
                    <div style="margin-top:8px; padding-top:8px; border-top:1px dashed #E5E7EB; font-size:0.8rem; color:#9CA3AF;">
                        *기반: 최근 1년 유동성-주가 회귀분석 (R²={r_squared:.2f})
                    </div>
                </div>
            </div>

            <div style="background:#F9FAFB; padding:20px; border-radius:16px; border:1px solid #F3F4F6;">
                <div style="font-size:0.9rem; font-weight:700; color:#4B5563; margin-bottom:10px;">🌊 Liquidity Drivers (Why?)</div>
                <div style="font-size:1.1rem; font-weight:700; color:#1F2937; margin-bottom:8px; line-height:1.4;">
                    {regime_desc}
                </div>
                <div style="font-size:0.85rem; color:#4B5563; line-height:1.6; background:#FFFFFF; padding:10px; border-radius:8px; border:1px solid #E5E7EB;">
                    <strong>🔍 상세 분석:</strong><br>
                    {liq_comment}
                </div>
            </div>
        </div>

        <div style="border-top:1px dashed #E5E7EB; padding-top:16px; font-size:0.9rem; color:#4B5563; line-height:1.6;">
            💡 <strong>Actionable Insight:</strong> 
            현재 시장은 <strong>{regime}</strong> 국면입니다. 
            {'적극적인 비중 확대' if 'Supported Rally' in regime or 'Liquidity Support' in regime else '리스크 관리 및 현금 비중 유지' if 'Correction' in regime or 'Liquidity Drag' in regime else '박스권 트레이딩'} 전략이 유효해 보입니다. 
            특히 <strong>{'TGA(재무부 계좌)' if abs(latest['TGA'] - prev_week['TGA']) > abs(latest['RRP'] - prev_week['RRP']) else 'RRP(역레포)'}</strong>의 변화가 유동성 흐름을 주도하고 있으니 지속적인 모니터링이 필요합니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. 차트 (Net Liquidity Visualization)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<div class="chart-wrapper">', unsafe_allow_html=True)

dff = df[df.index >= pd.to_datetime(cutoff)].copy()
ohlc_filtered = ohlc_raw[ohlc_raw.index >= pd.to_datetime(cutoff)].copy()

def resample_ohlc(ohlc_df, rule):
    return ohlc_df.resample(rule).agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()

if tf == "주봉": ohlc_chart = resample_ohlc(ohlc_filtered, "W")
elif tf == "월봉": ohlc_chart = resample_ohlc(ohlc_filtered, "ME")
else: ohlc_chart = ohlc_filtered.copy()

for ma_len in [20, 60, 120]:
    ohlc_chart[f"MA{ma_len}"] = ohlc_chart["Close"].rolling(ma_len).mean()

vol_colors = ["#EF4444" if c < o else "#10B981" for o, c in zip(ohlc_chart["Open"], ohlc_chart["Close"])]

fig_candle = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
    row_heights=[0.75, 0.25],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

# Net Liquidity (우측 Y축, 배경 영역)
liq_series = dff["Liq_MA"].dropna()
fig_candle.add_trace(go.Scatter(
    x=liq_series.index, y=liq_series, name=f"{CC['liq_label']}",
    fill="tozeroy", fillcolor=C["liq_fill"],
    line=dict(color=C["liq"], width=2),
    hovertemplate=f"%{{y:,.0f}}{CC['liq_suffix']}<extra>{CC['liq_label']}</extra>"
), row=1, col=1, secondary_y=True)

# 캔들스틱
fig_candle.add_trace(go.Candlestick(
    x=ohlc_chart.index,
    open=ohlc_chart["Open"], high=ohlc_chart["High"],
    low=ohlc_chart["Low"], close=ohlc_chart["Close"],
    increasing_line_color="#10B981", increasing_fillcolor="#10B981",
    decreasing_line_color="#EF4444", decreasing_fillcolor="#EF4444",
    name=idx_name, whiskerwidth=0.4,
), row=1, col=1)

# MA
ma_colors = {"MA20": "#F59E0B", "MA60": "#8B5CF6", "MA120": "#6B7280"}
for ma_name, ma_color in ma_colors.items():
    s = ohlc_chart[ma_name].dropna()
    if len(s) > 0:
        fig_candle.add_trace(go.Scatter(
            x=s.index, y=s, name=ma_name,
            line=dict(color=ma_color, width=1.5),
            hovertemplate="%{y:,.0f}<extra>" + ma_name + "</extra>"
        ), row=1, col=1)

# 거래량
fig_candle.add_trace(go.Bar(
    x=ohlc_chart.index, y=ohlc_chart["Volume"], name="Volume",
    marker_color=vol_colors, opacity=0.4, showlegend=False,
    hovertemplate="%{y:,.0f}<extra>Volume</extra>"
), row=2, col=1)

# 이벤트
if show_events:
    gap_map = {"일봉": 14, "주봉": 45, "월봉": 120}
    min_gap = gap_map.get(tf, 30)
    prev_dt = None
    for date_str, title, _, emoji, direction in ALL_EVENTS:
        dt = pd.to_datetime(date_str)
        if dt < ohlc_chart.index.min() or dt > ohlc_chart.index.max(): continue
        if prev_dt and (dt - prev_dt).days < min_gap: continue
        prev_dt = dt
        fig_candle.add_vline(x=dt, line_width=1, line_dash="solid", line_color="rgba(0,0,0,0.1)", row="all", col=1)

add_recession(fig_candle, dff, True)

# Y축 스케일링 (Net Liquidity 최적화)
liq_min_val = liq_series.min()
liq_max_val = liq_series.max()
liq_y_min = liq_min_val * 0.95
liq_y_max = liq_y_min + (liq_max_val - liq_y_min) / 0.7

fig_candle.update_layout(
    **BASE_LAYOUT, height=700, showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
    xaxis_rangeslider_visible=False,
)
fig_candle.update_xaxes(ax(), row=1, col=1)
fig_candle.update_xaxes(ax(), row=2, col=1)
fig_candle.update_yaxes(ax(dict(ticklabelposition="outside", automargin=True)), row=1, col=1, secondary_y=False)
fig_candle.update_yaxes(ax(dict(
    showgrid=False, range=[liq_y_min, liq_y_max], 
    ticklabelposition="inside", tickfont=dict(color=C["liq"]), automargin=True
)), row=1, col=1, secondary_y=True)
fig_candle.update_yaxes(ax(dict(tickformat=".2s", fixedrange=True)), row=2, col=1)

st.plotly_chart(fig_candle, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. Timeline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.write("")
st.markdown(f"""
<div style="margin-bottom:1rem; font-weight:700; font-size:1.2rem;">
    📅 Major Events Timeline <span style="font-weight:400; font-size:0.9rem; color:#6B7280; margin-left:8px;">({len([x for x in ALL_EVENTS if pd.to_datetime(x[0])>=dff.index.min()])} events in view)</span>
</div>
<div class="timeline-track">
""", unsafe_allow_html=True)

for date_str, title, desc, emoji, direction in reversed(ALL_EVENTS):
    dt = pd.to_datetime(date_str)
    if dt < dff.index.min(): continue
    tag_cls = "tag-up" if direction == "up" else "tag-down"
    
    st.markdown(f"""
    <div class="tl-card">
        <div class="tl-dot"></div>
        <div class="tl-tag {tag_cls}">{emoji} {direction.upper()}</div>
        <div class="tl-date">{date_str}</div>
        <div style="font-weight:700; margin-bottom:4px; font-size:0.95rem;">{title}</div>
        <div style="font-size:0.85rem; color:#6B7280;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. Footer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div style="text-align:center; margin-top:3rem; padding:2rem; border-top:1px solid #E5E7EB; color:#9CA3AF; font-size:0.8rem;">
    <strong>Data Source:</strong> FRED (WALCL, WTREGEN, RRPONTSYD) · Yahoo Finance<br>
    This dashboard provides a 'Net Liquidity' model based on Fed balance sheet mechanics. Not investment advice.
</div>
""", unsafe_allow_html=True)