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
except Exception:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_next_refresh():
    """다음 새로고침 시각까지 남은 초 계산"""
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
# 🎨 MODERN DARK UI DESIGN - Naver Stock Style + Hip & Modern
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    /* 🌙 Dark Mode Colors */
    --bg-primary: #0a0e27;
    --bg-secondary: #111534;
    --bg-tertiary: #1a1f42;
    --surface: rgba(255, 255, 255, 0.04);
    --surface-hover: rgba(255, 255, 255, 0.08);
    --border: rgba(255, 255, 255, 0.1);
    --border-strong: rgba(255, 255, 255, 0.2);
    
    --text-primary: #ffffff;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    
    /* 💫 Neon Accents */
    --neon-blue: #60a5fa;
    --neon-cyan: #22d3ee;
    --neon-green: #34d399;
    --neon-red: #f87171;
    --neon-purple: #a78bfa;
    --neon-amber: #fbbf24;
    --neon-pink: #f472b6;
    
    /* 🎨 Gradients */
    --gradient-main: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-blue: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
    --gradient-green: linear-gradient(135deg, #34d399 0%, #10b981 100%);
    --gradient-red: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    --gradient-purple: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
    
    /* ✨ Shadows & Glows */
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.5);
    --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.6);
    --shadow-lg: 0 8px 40px rgba(0, 0, 0, 0.7);
    --glow-blue: 0 0 30px rgba(96, 165, 250, 0.4);
    --glow-green: 0 0 30px rgba(52, 211, 153, 0.4);
    --glow-red: 0 0 30px rgba(248, 113, 113, 0.4);
}

/* ══════════════════════════════════════════ */
/* 🌐 GLOBAL STYLES */
/* ══════════════════════════════════════════ */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    padding: 2.5rem 3rem 3rem 3rem !important;
    max-width: 1600px !important;
}

/* ══════════════════════════════════════════ */
/* 📋 HEADER - Ultra Modern */
/* ══════════════════════════════════════════ */
.page-header {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 0.8rem;
    padding: 2rem 2.5rem;
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: var(--shadow-md), var(--glow-blue);
}

.page-header-icon {
    width: 60px;
    height: 60px;
    background: var(--gradient-main);
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    box-shadow: var(--shadow-lg);
    animation: float 4s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(2deg); }
}

.page-title {
    font-size: 2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #ffffff 0%, var(--neon-cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    text-shadow: 0 0 40px rgba(34, 211, 238, 0.3);
}

.page-desc {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-bottom: 2rem;
    line-height: 1.8;
}

/* ══════════════════════════════════════════ */
/* 🎴 CARDS - Glassmorphism */
/* ══════════════════════════════════════════ */
.card {
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-md);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
    background: var(--surface-hover);
    border-color: var(--border-strong);
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}

.card-title {
    font-size: 0.8rem;
    font-weight: 800;
    color: var(--neon-cyan);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

.card-title .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 2s infinite;
    box-shadow: 0 0 15px currentColor;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.3); }
}

/* ══════════════════════════════════════════ */
/* 📊 KPI CARDS - Neon Glow */
/* ══════════════════════════════════════════ */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.kpi {
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.8rem 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-md);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.kpi::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 5px;
    border-radius: 22px 0 0 22px;
}

.kpi::after {
    content: '';
    position: absolute;
    top: -100%;
    right: -100%;
    width: 300%;
    height: 300%;
    opacity: 0;
    transition: opacity 0.4s;
}

.kpi:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-strong);
}

.kpi:hover::after {
    opacity: 0.05;
}

.kpi.blue::before { background: var(--gradient-blue); }
.kpi.blue::after { background: radial-gradient(circle, var(--neon-blue) 0%, transparent 70%); }
.kpi.blue:hover { box-shadow: var(--shadow-lg), var(--glow-blue); }

.kpi.red::before { background: var(--gradient-red); }
.kpi.red::after { background: radial-gradient(circle, var(--neon-red) 0%, transparent 70%); }
.kpi.red:hover { box-shadow: var(--shadow-lg), var(--glow-red); }

.kpi.green::before { background: var(--gradient-green); }
.kpi.green::after { background: radial-gradient(circle, var(--neon-green) 0%, transparent 70%); }
.kpi.green:hover { box-shadow: var(--shadow-lg), var(--glow-green); }

.kpi.purple::before { background: var(--gradient-purple); }
.kpi.purple::after { background: radial-gradient(circle, var(--neon-purple) 0%, transparent 70%); }

.kpi-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 0.7rem;
}

.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.2;
    text-shadow: 0 2px 10px rgba(255, 255, 255, 0.15);
}

.kpi-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    margin-top: 0.5rem;
}

.kpi-delta.up {
    color: var(--neon-green);
    text-shadow: 0 0 15px rgba(52, 211, 153, 0.4);
}

.kpi-delta.down {
    color: var(--neon-red);
    text-shadow: 0 0 15px rgba(248, 113, 113, 0.4);
}

/* ══════════════════════════════════════════ */
/* 📢 REPORT BOX - Premium Gradient */
/* ══════════════════════════════════════════ */
.report-box {
    background: linear-gradient(135deg, rgba(96, 165, 250, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 24px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-md), 0 0 50px rgba(96, 165, 250, 0.15);
}

.report-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 1.2rem;
}

.report-badge {
    background: var(--gradient-blue);
    color: white;
    font-size: 0.7rem;
    font-weight: 900;
    padding: 6px 16px;
    border-radius: 24px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    box-shadow: 0 4px 15px rgba(96, 165, 250, 0.4);
}

.report-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
}

.report-title {
    font-size: 1.3rem;
    font-weight: 900;
    color: var(--text-primary);
    margin-bottom: 1rem;
    line-height: 1.5;
}

.report-body {
    font-size: 0.95rem;
    color: var(--text-secondary);
    line-height: 2;
}

.report-body strong {
    color: var(--text-primary);
    font-weight: 800;
}

.report-body .hl {
    background: rgba(96, 165, 250, 0.2);
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 800;
    color: var(--neon-cyan);
}

.report-divider {
    border: none;
    border-top: 1px dashed var(--border-strong);
    margin: 1.5rem 0;
}

.report-signal {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 18px;
    border-radius: 14px;
    font-size: 0.85rem;
    font-weight: 900;
    margin-top: 1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.signal-bullish {
    background: rgba(52, 211, 153, 0.2);
    color: var(--neon-green);
    border: 1px solid rgba(52, 211, 153, 0.4);
    box-shadow: 0 0 20px rgba(52, 211, 153, 0.3);
}

.signal-neutral {
    background: rgba(251, 191, 36, 0.2);
    color: var(--neon-amber);
    border: 1px solid rgba(251, 191, 36, 0.4);
}

.signal-bearish {
    background: rgba(248, 113, 113, 0.2);
    color: var(--neon-red);
    border: 1px solid rgba(248, 113, 113, 0.4);
    box-shadow: 0 0 20px rgba(248, 113, 113, 0.3);
}

/* ══════════════════════════════════════════ */
/* 🔄 REFRESH BAR - Animated */
/* ══════════════════════════════════════════ */
.refresh-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 10px 24px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.refresh-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--neon-green);
    animation: pulse-glow 2s infinite;
    box-shadow: 0 0 15px var(--neon-green);
}

@keyframes pulse-glow {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 15px var(--neon-green); }
    50% { opacity: 0.5; transform: scale(1.4); box-shadow: 0 0 25px var(--neon-green); }
}

/* ══════════════════════════════════════════ */
/* ⏱️ TIMELINE - Sleek & Modern */
/* ══════════════════════════════════════════ */
.timeline {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.tl-item {
    display: flex;
    align-items: flex-start;
    gap: 18px;
    padding: 1.2rem 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.9rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tl-item:hover {
    background: var(--surface);
    margin: 0 -1.5rem;
    padding: 1.2rem 1.5rem;
    border-radius: 16px;
}

.tl-item:last-child {
    border-bottom: none;
}

.tl-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    min-width: 100px;
    flex-shrink: 0;
    padding-top: 3px;
}

.tl-icon {
    font-size: 1.2rem;
    flex-shrink: 0;
}

.tl-content {
    flex: 1;
    min-width: 0;
}

.tl-title {
    font-weight: 800;
    color: var(--text-primary);
}

.tl-desc {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-top: 4px;
    line-height: 1.7;
}

.tl-dir {
    font-size: 0.75rem;
    font-weight: 900;
    padding: 5px 14px;
    border-radius: 10px;
    flex-shrink: 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.tl-dir.up {
    background: rgba(52, 211, 153, 0.2);
    color: var(--neon-green);
    border: 1px solid rgba(52, 211, 153, 0.4);
}

.tl-dir.down {
    background: rgba(248, 113, 113, 0.2);
    color: var(--neon-red);
    border: 1px solid rgba(248, 113, 113, 0.4);
}

/* ══════════════════════════════════════════ */
/* 📖 GUIDE BOX */
/* ══════════════════════════════════════════ */
.guide-box {
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.4rem 1.8rem;
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 2;
    margin-top: 1rem;
}

.guide-box strong {
    color: var(--text-primary);
    font-weight: 800;
}

/* ══════════════════════════════════════════ */
/* 🎬 FOOTER */
/* ══════════════════════════════════════════ */
.app-footer {
    margin-top: 3rem;
    padding: 1.5rem 0;
    text-align: center;
    font-size: 0.8rem;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
}

/* ══════════════════════════════════════════ */
/* 🎛️ CONTROLS & COMMON ELEMENTS */
/* ══════════════════════════════════════════ */
div[data-testid="stMetric"] {
    display: none;
}

footer {
    display: none !important;
}

.stSelectbox label,
.stMultiSelect label,
.stSlider label,
.stRadio label {
    color: var(--text-secondary) !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
}

.stSelectbox {
    margin-bottom: -0.3rem !important;
}

/* Custom Select Styling */
div[data-baseweb="select"] {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    border-radius: 14px !important;
    transition: all 0.3s !important;
}

div[data-baseweb="select"]:hover {
    border-color: var(--border-strong) !important;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.3) !important;
}

/* Toolbar */
.toolbar {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

/* ══════════════════════════════════════════ */
/* 📱 RESPONSIVE */
/* ══════════════════════════════════════════ */
@media (max-width: 768px) {
    .block-container {
        padding: 1.5rem 1.5rem 2rem 1.5rem !important;
    }
    
    .kpi-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
    
    .page-header {
        padding: 1.5rem;
    }
    
    .card {
        padding: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📌 설정 및 상수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 지수 설정 (유동성 소스별 설정)
INDEX_CONFIG = {
    "나스닥 (WALCL)": {
        "idx_ticker": "^IXIC", "idx_name": "나스닥종합지수",
        "liq_ticker": "WALCL", "liq_label": "연준 총자산", "liq_unit": "$", "liq_suffix": "B", "data_src": "FRED · Yahoo Finance"
    },
    "S&P 500 (WALCL)": {
        "idx_ticker": "^GSPC", "idx_name": "S&P 500",
        "liq_ticker": "WALCL", "liq_label": "연준 총자산", "liq_unit": "$", "liq_suffix": "B", "data_src": "FRED · Yahoo Finance"
    },
    "나스닥 (M2SL)": {
        "idx_ticker": "^IXIC", "idx_name": "나스닥종합지수",
        "liq_ticker": "M2SL", "liq_label": "통화량 M2", "liq_unit": "$", "liq_suffix": "B", "data_src": "FRED · Yahoo Finance"
    },
    "S&P 500 (M2SL)": {
        "idx_ticker": "^GSPC", "idx_name": "S&P 500",
        "liq_ticker": "M2SL", "liq_label": "통화량 M2", "liq_unit": "$", "liq_suffix": "B", "data_src": "FRED · Yahoo Finance"
    },
}

# 차트 컬러 (네이버 증권 스타일 + 다크 모드)
C = {
    "bg": "#0a0e27",          # 배경
    "grid": "#1e293b",        # 그리드
    "text": "#cbd5e1",        # 텍스트
    "candle_up": "#22c55e",   # 상승 캔들 (밝은 초록)
    "candle_down": "#ef4444", # 하락 캔들 (빨강)
    "ma20": "#fbbf24",        # MA20 (골드)
    "ma60": "#60a5fa",        # MA60 (블루)
    "ma120": "#a78bfa",       # MA120 (퍼플)
    "volume": "#475569",      # 거래량
    "liquidity": "#3b82f6",   # 유동성
    "recession": "#1e293b",   # 리세션
    "event": "#94a3b8",       # 이벤트
}

# 플롯리 기본 레이아웃 (네이버 스타일)
BASE_LAYOUT = dict(
    paper_bgcolor=C["bg"],
    plot_bgcolor=C["bg"],
    font=dict(family="JetBrains Mono, Inter, sans-serif", size=11, color=C["text"]),
    margin=dict(l=10, r=10, t=40, b=10),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="rgba(26, 31, 66, 0.95)",
        font_size=12,
        font_family="JetBrains Mono, monospace",
        bordercolor="rgba(96, 165, 250, 0.5)"
    ),
)

def ax(extra=None):
    """축 기본 스타일 (네이버 스타일)"""
    base = dict(
        showgrid=True,
        gridcolor=C["grid"],
        gridwidth=0.5,
        zeroline=False,
        showline=True,
        linecolor=C["grid"],
        linewidth=1,
        mirror=False,
        tickfont=dict(color=C["text"], size=10, family="JetBrains Mono, monospace"),
    )
    if extra:
        base.update(extra)
    return base

# 리세션 음영 함수
def add_recession(fig, df, is_subplot=False):
    """미국 경기침체 기간 음영 표시"""
    RECESSIONS = [
        ("2001-03-01", "2001-11-30"),
        ("2007-12-01", "2009-06-30"),
        ("2020-02-01", "2020-04-30"),
    ]
    for start, end in RECESSIONS:
        s_dt, e_dt = pd.to_datetime(start), pd.to_datetime(end)
        if s_dt > df.index.max() or e_dt < df.index.min():
            continue
        fig.add_vrect(
            x0=s_dt, x1=e_dt,
            fillcolor=C["recession"], opacity=0.15,
            layer="below", line_width=0,
            row="all" if is_subplot else None, col=1 if is_subplot else None
        )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 데이터 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(ttl=3600)
def load_data(idx_ticker, liq_ticker):
    """지수 + 유동성 데이터 로드"""
    start_date = "2000-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # 지수 데이터
    try:
        import yfinance as yf
        idx_data = yf.download(idx_ticker, start=start_date, end=end_date, progress=False)
        idx_data.index = pd.to_datetime(idx_data.index)
    except Exception as e:
        st.error(f"지수 데이터 로드 실패: {e}")
        return None
    
    # 유동성 데이터 (FRED)
    try:
        liq_data = web.DataReader(liq_ticker, "fred", start_date, end_date)
        liq_data.index = pd.to_datetime(liq_data.index)
        liq_data.columns = ["Liquidity"]
    except Exception as e:
        st.error(f"유동성 데이터 로드 실패: {e}")
        return None
    
    # 병합
    df = idx_data[["Open", "High", "Low", "Close", "Volume"]].copy()
    df = df.merge(liq_data, left_index=True, right_index=True, how="left")
    df["Liquidity"] = df["Liquidity"].fillna(method="ffill")
    
    # 이동평균
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["MA120"] = df["Close"].rolling(120).mean()
    df["Liq_MA"] = df["Liquidity"].rolling(20).mean()
    
    return df.dropna()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎯 주요 이벤트 타임라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ALL_EVENTS = [
    ("2001-09-11", "9·11 테러", "미국 본토 대규모 테러 공격", "💥", "down"),
    ("2003-03-20", "이라크 전쟁", "미국의 이라크 침공 개시", "⚔️", "down"),
    ("2008-09-15", "리먼 브러더스 파산", "글로벌 금융위기 촉발", "💥", "down"),
    ("2008-11-25", "QE1 시작", "연준 양적완화 1차 시작 ($6,000억)", "💵", "up"),
    ("2010-11-03", "QE2 시작", "연준 양적완화 2차 시작 ($6,000억)", "💵", "up"),
    ("2012-09-13", "QE3 시작", "연준 양적완화 3차 시작 (무제한)", "💵", "up"),
    ("2013-12-18", "테이퍼링", "양적완화 축소 시작", "📉", "down"),
    ("2015-12-16", "첫 금리인상", "제로금리 종료 (0.25%p ↑)", "📈", "down"),
    ("2020-03-03", "코로나 긴급인하", "금리 1.00%p 인하 (1.00~1.25%)", "🦠", "down"),
    ("2020-03-15", "제로금리 복귀", "금리 1.00%p 추가인하 (0~0.25%)", "🦠", "down"),
    ("2020-03-23", "무제한 QE", "자산매입 무제한 선언", "💵", "up"),
    ("2021-11-03", "테이퍼링 재개", "월 $150억 자산매입 축소", "📉", "down"),
    ("2022-03-16", "긴축 사이클", "금리 0.25%p 인상 (0.25~0.50%)", "📈", "down"),
    ("2022-06-01", "QT 시작", "양적긴축(보유자산 축소) 시작", "📉", "down"),
    ("2023-03-10", "SVB 파산", "실리콘밸리은행 파산", "🏦", "down"),
    ("2023-07-26", "금리인상 중단", "5.25~5.50% 동결", "⏸️", "up"),
    ("2024-09-18", "금리인하 사이클", "금리 0.50%p 인하 (4.75~5.00%)", "📉", "up"),
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 UI 레이아웃
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 헤더
st.markdown(
    """
    <div class="page-header">
        <div class="page-header-icon">📈</div>
        <div>
            <div class="page-title">유동성 × 시장 분석기</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-desc">금융시장 유동성과 주요 지수의 상관관계를 실시간으로 분석하는 프로페셔널 대시보드</div>',
    unsafe_allow_html=True
)

# 새로고침 바
st.markdown(
    f"""
    <div class="refresh-bar">
        <div class="refresh-dot"></div>
        <span>다음 자동 갱신</span>
        <strong>{NEXT_REFRESH_TIME.strftime('%m/%d %H:%M KST')}</strong>
    </div>
    """,
    unsafe_allow_html=True
)

# 컨트롤 패널
st.markdown('<div class="toolbar">', unsafe_allow_html=True)
cols = st.columns([2, 2, 1, 1])
with cols[0]:
    selected_config = st.selectbox(
        "지수 × 유동성 조합",
        list(INDEX_CONFIG.keys()),
        index=0,
        label_visibility="collapsed"
    )
with cols[1]:
    tf = st.selectbox(
        "캔들 주기",
        ["일봉", "주봉", "월봉"],
        index=0,
        label_visibility="collapsed"
    )
with cols[2]:
    period = st.selectbox(
        "기간",
        ["1년", "3년", "5년", "10년", "전체"],
        index=4,
        label_visibility="collapsed"
    )
with cols[3]:
    show_events = st.checkbox("이벤트 표시", value=True)
st.markdown('</div>', unsafe_allow_html=True)

# 선택된 설정
CC = INDEX_CONFIG[selected_config]

# 데이터 로드
df = load_data(CC["idx_ticker"], CC["liq_ticker"])
if df is None or len(df) == 0:
    st.error("⚠️ 데이터를 불러올 수 없습니다.")
    st.stop()

# 기간 필터링
period_map = {"1년": 252, "3년": 252*3, "5년": 252*5, "10년": 252*10, "전체": len(df)}
dff = df.iloc[-period_map[period]:]

# 리샘플링 (주봉/월봉)
if tf == "주봉":
    ohlc_chart = dff.resample("W-FRI").agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last",
        "Volume": "sum", "MA20": "last", "MA60": "last", "MA120": "last"
    }).dropna()
elif tf == "월봉":
    ohlc_chart = dff.resample("M").agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last",
        "Volume": "sum", "MA20": "last", "MA60": "last", "MA120": "last"
    }).dropna()
else:
    ohlc_chart = dff.copy()

idx_name = CC["idx_name"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 KPI 카드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
latest = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else latest

price_chg = (latest["Close"] - prev["Close"]) / prev["Close"] * 100
liq_chg = (latest["Liquidity"] - prev["Liquidity"]) / prev["Liquidity"] * 100

kpi_html = f"""
<div class="kpi-grid">
    <div class="kpi blue">
        <div class="kpi-label">{idx_name}</div>
        <div class="kpi-value">{latest["Close"]:,.0f}</div>
        <div class="kpi-delta {'up' if price_chg >= 0 else 'down'}">
            {'▲' if price_chg >= 0 else '▼'} {abs(price_chg):.2f}%
        </div>
    </div>
    <div class="kpi {'green' if liq_chg >= 0 else 'red'}">
        <div class="kpi-label">{CC['liq_label']}</div>
        <div class="kpi-value">{CC['liq_unit']}{latest["Liquidity"]:,.0f}{CC['liq_suffix']}</div>
        <div class="kpi-delta {'up' if liq_chg >= 0 else 'down'}">
            {'▲' if liq_chg >= 0 else '▼'} {abs(liq_chg):.2f}%
        </div>
    </div>
    <div class="kpi purple">
        <div class="kpi-label">거래량 (24H)</div>
        <div class="kpi-value">{latest["Volume"]/1e6:.0f}M</div>
        <div class="kpi-delta up">—</div>
    </div>
    <div class="kpi blue">
        <div class="kpi-label">MA20</div>
        <div class="kpi-value">{latest["MA20"]:,.0f}</div>
        <div class="kpi-delta {'up' if latest["Close"] > latest["MA20"] else 'down'}">
            {'위' if latest["Close"] > latest["MA20"] else '아래'}
        </div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📈 메인 차트 (네이버 스타일 캔들스틱 + 유동성)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f'<div class="card"><div class="card-title">'
    f'<span class="dot" style="background:{C["candle_up"]}"></span> '
    f'{idx_name} 차트 + {CC["liq_label"]} ({tf})</div></div>',
    unsafe_allow_html=True
)

# 거래량 색상
vol_colors = [C["candle_up"] if ohlc_chart.iloc[i]["Close"] >= ohlc_chart.iloc[i]["Open"] 
              else C["candle_down"] for i in range(len(ohlc_chart))]

# 차트 생성
fig_candle = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.75, 0.25],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# 🌊 유동성 영역 (배경)
liq_series = dff["Liq_MA"].dropna()
liq_hover_fmt = f"%{{y:,.0f}}{CC['liq_suffix']}<extra>{CC['liq_label']}</extra>"
fig_candle.add_trace(
    go.Scatter(
        x=liq_series.index,
        y=liq_series,
        name=f"{CC['liq_label']} ({CC['liq_unit']})",
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.1)",
        line=dict(color="rgba(96, 165, 250, 0.5)", width=2),
        hovertemplate=liq_hover_fmt
    ),
    row=1, col=1, secondary_y=True
)

# 🕯️ 캔들스틱 (네이버 스타일)
fig_candle.add_trace(
    go.Candlestick(
        x=ohlc_chart.index,
        open=ohlc_chart["Open"],
        high=ohlc_chart["High"],
        low=ohlc_chart["Low"],
        close=ohlc_chart["Close"],
        increasing_line_color=C["candle_up"],
        increasing_fillcolor=C["candle_up"],
        decreasing_line_color=C["candle_down"],
        decreasing_fillcolor=C["candle_down"],
        name=idx_name,
        whiskerwidth=0.3,
        increasing_line_width=1,
        decreasing_line_width=1,
    ),
    row=1, col=1
)

# 📏 이동평균선
ma_colors = {"MA20": C["ma20"], "MA60": C["ma60"], "MA120": C["ma120"]}
for ma_name, ma_color in ma_colors.items():
    s = ohlc_chart[ma_name].dropna()
    if len(s) > 0:
        fig_candle.add_trace(
            go.Scatter(
                x=s.index,
                y=s,
                name=ma_name,
                line=dict(color=ma_color, width=1.5),
                hovertemplate="%{y:,.0f}<extra>" + ma_name + "</extra>"
            ),
            row=1, col=1
        )

# 📊 거래량
fig_candle.add_trace(
    go.Bar(
        x=ohlc_chart.index,
        y=ohlc_chart["Volume"],
        name="거래량",
        marker_color=vol_colors,
        opacity=0.6,
        showlegend=False,
        hovertemplate="%{y:,.0f}<extra>Volume</extra>"
    ),
    row=2, col=1
)

# 🎯 이벤트 표시
if show_events:
    gap_map = {"일봉": 14, "주봉": 45, "월봉": 120}
    min_gap = gap_map.get(tf, 30)
    prev_dt = None
    for date_str, title, _, emoji, direction in ALL_EVENTS:
        dt = pd.to_datetime(date_str)
        if dt < ohlc_chart.index.min() or dt > ohlc_chart.index.max():
            continue
        if prev_dt and (dt - prev_dt).days < min_gap:
            continue
        prev_dt = dt
        
        fig_candle.add_vline(
            x=dt,
            line_width=1,
            line_dash="dot",
            line_color=C["event"],
            row="all",
            col=1
        )
        
        clr = C["candle_up"] if direction == "up" else C["candle_down"]
        fig_candle.add_annotation(
            x=dt,
            y=1.04,
            yref="paper",
            text=f"{emoji} {title}",
            showarrow=False,
            font=dict(size=10, color=clr),
            textangle=-35,
            xanchor="left"
        )

# 🌑 리세션 음영
add_recession(fig_candle, dff, True)

# 레이아웃 설정 (네이버 스타일)
liq_min_val = liq_series.min()
liq_max_val = liq_series.max()
liq_y_min = liq_min_val * 0.85
liq_y_max = liq_y_min + (liq_max_val - liq_y_min) / 0.6

fig_candle.update_layout(
    **BASE_LAYOUT,
    height=750,
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.98,
        xanchor="left",
        x=0.01,
        font=dict(size=11, family="JetBrains Mono, monospace"),
        bgcolor="rgba(26, 31, 66, 0.8)",
        bordercolor="rgba(96, 165, 250, 0.3)",
        borderwidth=1
    ),
    xaxis_rangeslider_visible=False,
)

# 축 설정
fig_candle.update_xaxes(ax(), row=1, col=1)
fig_candle.update_xaxes(ax(), row=2, col=1)
fig_candle.update_yaxes(
    ax(dict(title=None, ticklabelposition="outside", automargin=True)),
    row=1, col=1, secondary_y=False
)
fig_candle.update_yaxes(
    ax(dict(
        title=None,
        title_font=dict(color=C["liquidity"]),
        tickfont=dict(color=C["liquidity"], size=10),
        showgrid=False,
        range=[liq_y_min, liq_y_max],
        ticklabelposition="outside",
        automargin=True
    )),
    row=1, col=1, secondary_y=True
)
fig_candle.update_yaxes(
    ax(dict(title=None, tickformat=".2s", fixedrange=True, ticklabelposition="outside", automargin=True)),
    row=2, col=1
)

# 차트 표시
st.plotly_chart(
    fig_candle,
    use_container_width=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True,
        "modeBarButtonsToRemove": [
            "select2d", "lasso2d", "autoScale2d",
            "hoverClosestCartesian", "hoverCompareCartesian",
            "toggleSpikelines",
        ],
        "displaylogo": False,
        "responsive": True
    }
)

# 모바일 핀치 줌
st.markdown("""
<script>
document.querySelectorAll('.js-plotly-plot').forEach(function(plot) {
    plot.style.touchAction = 'none';
    plot.addEventListener('touchstart', function(e) {}, {passive: false});
});
</script>
""", unsafe_allow_html=True)

# 최근 캔들 요약
if len(ohlc_chart) >= 2:
    last = ohlc_chart.iloc[-1]
    prev = ohlc_chart.iloc[-2]
    chg = (last["Close"] - prev["Close"]) / prev["Close"] * 100
    chg_arrow = "▲" if chg >= 0 else "▼"
    chg_color = "neon-green" if chg >= 0 else "neon-red"
    
    st.markdown(
        f'<div class="guide-box">'
        f'🕯️ <strong>최근 {tf}:</strong> '
        f'시 <strong>{last["Open"]:,.0f}</strong> · '
        f'고 <strong>{last["High"]:,.0f}</strong> · '
        f'저 <strong>{last["Low"]:,.0f}</strong> · '
        f'종 <strong>{last["Close"]:,.0f}</strong> '
        f'<span style="color:var(--{chg_color})">{chg_arrow} {abs(chg):.2f}%</span>'
        f'<br>'
        f'이평선: <span style="color:{C["ma20"]}">●</span> MA20 · '
        f'<span style="color:{C["ma60"]}">●</span> MA60 · '
        f'<span style="color:{C["ma120"]}">●</span> MA120 · '
        f'<span style="color:rgba(96,165,250,0.7)">파란 영역</span> = {CC["liq_label"]}'
        f'</div>',
        unsafe_allow_html=True
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📜 이벤트 타임라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
event_count = sum(1 for d,_,_,_,_ in ALL_EVENTS if pd.to_datetime(d) >= dff.index.min())
st.markdown(
    f"""<div class="card">
        <div class="card-title">
            <span class="dot" style="background:{C['liquidity']}"></span>
            주요 매크로 이벤트 타임라인 ({event_count} 이벤트)
        </div>
    """,
    unsafe_allow_html=True
)

tl_html = '<div class="timeline">'
for date_str, title, desc, emoji, direction in reversed(ALL_EVENTS):
    dt = pd.to_datetime(date_str)
    if dt < dff.index.min():
        continue
    dir_cls = "up" if direction == "up" else "down"
    dir_label = "상승" if direction == "up" else "하락"
    tl_html += f"""
    <div class="tl-item">
        <div class="tl-date">{date_str}</div>
        <div class="tl-icon">{emoji}</div>
        <div class="tl-content">
            <div class="tl-title">{title}</div>
            <div class="tl-desc">{desc}</div>
        </div>
        <div class="tl-dir {dir_cls}">{dir_label}</div>
    </div>"""
tl_html += "</div>"
st.markdown(tl_html + "</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔚 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f'<div class="app-footer">'
    f'📊 데이터: {CC["data_src"]} · 업데이트: {df.index.max().strftime("%Y-%m-%d")}'
    f'<br>🔄 자동 갱신 4회/일 (PST·KST 09/18시) · 본 페이지는 투자 조언이 아닙니다'
    f'</div>',
    unsafe_allow_html=True
)