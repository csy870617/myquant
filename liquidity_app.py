import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import json
import threading
import urllib.request
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Keep-alive: 백그라운드 self-ping으로 슬립 방지
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_KEEP_ALIVE_INTERVAL = 300  # 5분마다 self-ping

def _keep_alive_ping():
    """백그라운드에서 주기적으로 앱 URL에 ping을 보내 슬립 방지"""
    import time
    while True:
        time.sleep(_KEEP_ALIVE_INTERVAL)
        try:
            urllib.request.urlopen("https://myquant.streamlit.app/", timeout=30)
        except Exception:
            pass

if "keep_alive_started" not in st.session_state:
    st.session_state.keep_alive_started = True
    t = threading.Thread(target=_keep_alive_ping, daemon=True)
    t.start()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 페이지 설정 (즐겨찾기 아이콘 적용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="유동성 × 시장 분석기", 
    page_icon="icon.png",  # ★ 수정: 즐겨찾기 아이콘 설정
    layout="wide"
)

# ★ 수정: 상단 로고 적용
try:
    st.logo("icon.png")
except Exception:
    pass  # 파일이 없거나 구버전 Streamlit일 경우 무시

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침 (5분 간격 실시간 업데이트)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFRESH_INTERVAL_SEC = 300  # 5분마다 자동 새로고침

def get_next_refresh():
    """다음 새로고침 시각 계산 (5분 간격)"""
    utc_now = datetime.now(ZoneInfo("UTC"))
    next_t = utc_now + timedelta(seconds=REFRESH_INTERVAL_SEC)
    local_next = next_t.astimezone(ZoneInfo("Asia/Seoul"))
    return local_next, REFRESH_INTERVAL_SEC

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()

st.markdown(
    f'<meta http-equiv="refresh" content="{REFRESH_INTERVAL_SEC}">'
    f'<meta name="description" content="중앙은행 유동성과 주가지수의 상관관계를 실시간으로 분석하는 대시보드입니다.">'
    f'<script>document.documentElement.setAttribute("lang", "ko");</script>'
    '<script>'
    '(function(){'
    '  function keepAlive(){'
    '    fetch(window.location.href,{method:"HEAD"}).catch(function(){});'
    '  }'
    '  setInterval(keepAlive, 120000);'  # 2분마다 fetch로 연결 유지
    '})();'
    '</script>',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS (툴바 위치 상단 이동 및 여백 조정)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --bg: #f8fafc; --card: #ffffff; --border: #e2e8f0;
    --text-primary: #1e293b; --text-secondary: #475569; --text-muted: #64748b;
    --accent-blue: #3b82f6; --accent-red: #ef4444; --accent-green: #10b981;
    --accent-purple: #8b5cf6; --accent-amber: #f59e0b;
}
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg) !important; color: var(--text-primary);
}
[data-testid="stHeader"] { background: transparent !important; }

/* ── 접근성: 스크린 리더 전용 텍스트 ── */
.sr-only {
    position: absolute; width: 1px; height: 1px;
    padding: 0; margin: -1px; overflow: hidden;
    clip: rect(0,0,0,0); white-space: nowrap; border: 0;
}

/* ── 접근성: 건너뛰기 내비게이션 ── */
.skip-link {
    position: absolute; top: -100%; left: 50%; transform: translateX(-50%);
    background: var(--accent-blue); color: #fff; padding: 12px 24px;
    border-radius: 0 0 8px 8px; font-size: 0.9rem; font-weight: 700;
    z-index: 9999; text-decoration: none; transition: top 0.2s;
}
.skip-link:focus { top: 0; outline: 3px solid var(--accent-amber); }

/* ── 접근성: 포커스 스타일 ── */
*:focus-visible {
    outline: 3px solid var(--accent-blue) !important;
    outline-offset: 2px !important;
}
a:focus-visible, button:focus-visible, [tabindex]:focus-visible {
    outline: 3px solid var(--accent-blue) !important;
    outline-offset: 2px !important;
    border-radius: 4px;
}

/* 기본 컨테이너 여백 */
.block-container { 
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1280px;
}

/* ── 페이지 헤더 ── */
.page-header { display: flex; align-items: center; gap: 14px; margin-bottom: 0.4rem; }
.page-header-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
    border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; flex-shrink: 0;
}
.page-title { font-size: 1.6rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.5px; }
.page-desc { font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.6; }

/* ── 카드 ── */
.card {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 1.25rem 1.4rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.card-title {
    font-size: 0.78rem; font-weight: 700; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.8rem;
    display: flex; align-items: center; gap: 6px;
}
.card-title .dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }

/* ── KPI ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.2rem; }
.kpi {
    background: var(--card); border: 1px solid var(--border); border-radius: 14px;
    padding: 1.1rem 1.3rem; position: relative; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.kpi::before { content:''; position:absolute; left:0; top:0; bottom:0; width:4px; border-radius: 14px 0 0 14px; }
.kpi.blue::before { background: var(--accent-blue); }
.kpi.red::before { background: var(--accent-red); }
.kpi.green::before { background: var(--accent-green); }
.kpi.purple::before { background: var(--accent-purple); }
.kpi-label { font-size: 0.72rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 0.35rem; }
.kpi-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.4rem; font-weight: 700; color: var(--text-primary); line-height: 1.2; }
.kpi-delta { font-family: 'IBM Plex Mono', monospace; font-size: 0.76rem; font-weight: 500; margin-top: 0.25rem; }
.kpi-delta.up { color: var(--accent-green); }
.kpi-delta.down { color: var(--accent-red); }

/* ── 리포트 박스 ── */
.report-box {
    background: linear-gradient(135deg, #eff6ff, #f0fdf4); border: 1px solid #bfdbfe;
    border-radius: 14px; padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
}
.report-header { display: flex; align-items: center; gap: 10px; margin-bottom: 0.8rem; }
.report-badge {
    background: var(--accent-blue); color: white; font-size: 0.68rem; font-weight: 700;
    padding: 3px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px;
}
.report-date { font-size: 0.78rem; color: var(--text-muted); font-weight: 500; }
.report-title { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); margin-bottom: 0.7rem; line-height: 1.4; }
.report-body { font-size: 0.88rem; color: var(--text-secondary); line-height: 1.8; }
.report-body strong { color: var(--text-primary); font-weight: 600; }
.report-body .hl { background: rgba(59,130,246,0.08); padding: 2px 6px; border-radius: 4px; font-weight: 600; color: var(--accent-blue); }
.report-divider { border: none; border-top: 1px dashed #cbd5e1; margin: 0.8rem 0; }
.report-signal { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 700; margin-top: 0.5rem; }
.signal-bullish { background: rgba(16,185,129,0.1); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.2); }
.signal-neutral { background: rgba(245,158,11,0.1); color: var(--accent-amber); border: 1px solid rgba(245,158,11,0.2); }
.signal-bearish { background: rgba(239,68,68,0.1); color: var(--accent-red); border: 1px solid rgba(239,68,68,0.2); }

/* ── 새로고침 바 ── */
.refresh-bar {
    display: flex; align-items: center; justify-content: center; gap: 8px;
    background: #f1f5f9; border: 1px solid var(--border); border-radius: 10px;
    padding: 6px 16px; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 1rem;
    flex-wrap: wrap;
}
.refresh-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent-green); animation: pulse 2s infinite; flex-shrink: 0; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── 타임라인 ── */
.timeline { display: flex; flex-direction: column; gap: 0; }
.tl-item { display: flex; align-items: flex-start; gap: 14px; padding: 0.65rem 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
.tl-item:last-child { border-bottom: none; }
.tl-date { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: var(--text-muted); min-width: 82px; flex-shrink: 0; padding-top: 1px; }
.tl-icon { font-size: 1.05rem; flex-shrink: 0; }
.tl-content { flex: 1; min-width: 0; }
.tl-title { font-weight: 600; color: var(--text-primary); }
.tl-desc { color: var(--text-secondary); font-size: 0.8rem; margin-top: 2px; word-break: keep-all; }
.tl-dir { font-size: 0.7rem; font-weight: 700; padding: 1px 7px; border-radius: 4px; flex-shrink: 0; }
.tl-dir.up { background: rgba(16,185,129,0.1); color: var(--accent-green); }
.tl-dir.down { background: rgba(239,68,68,0.1); color: var(--accent-red); }

/* ── 가이드 박스 ── */
.guide-box {
    background: #f8fafc; border: 1px solid var(--border); border-radius: 10px;
    padding: 0.9rem 1.2rem; font-size: 0.84rem; color: var(--text-secondary);
    line-height: 1.7; margin-top: 0.5rem;
}
.guide-box strong { color: var(--text-primary); }

/* ── 공통 ── */
div[data-testid="stMetric"] { display: none; }
footer { display: none !important; }
.stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label {
    color: var(--text-secondary)!important; font-weight:600!important; font-size:0.82rem!important;
}
/* 컨트롤 바 간격 최소화 */
[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
.stSelectbox { margin-bottom: -0.6rem !important; }
.stRadio { margin-bottom: -0.6rem !important; }
.app-footer { text-align:center; color:var(--text-muted); font-size:0.75rem; margin-top:2rem; padding:1rem; border-top:1px solid var(--border); }

/* ── Plotly 차트 ── */
.js-plotly-plot, .plotly, .js-plotly-plot .plotly,
[data-testid="stPlotlyChart"], [data-testid="stPlotlyChart"] > div,
.stPlotlyChart, .stPlotlyChart > div > div > div {
    touch-action: none !important;
    -webkit-touch-callout: none;
}
[data-testid="stPlotlyChart"] {
    width: 100% !important;
}

/* ★ 툴바(Modebar) 스타일: 우측 상단 고정, 항상 표시 */
.modebar { 
    opacity: 1 !important; /* 항상 표시 */
    top: 0px !important;   /* 차트 상단 */
    right: 0px !important; /* 차트 우측 */
    bottom: auto !important;
    left: auto !important;
    background: transparent !important; /* 배경 투명 */
}
.modebar-btn { font-size: 15px !important; }
.modebar-group { padding: 0 4px !important; background: rgba(255,255,255,0.8); border-radius: 4px; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   모바일 반응형 (≤768px)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
@media (max-width: 768px) {
    /* 레이아웃: 가독성 좋은 패딩 확보 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;  
        padding-right: 1rem !important; 
    }

    /* 헤더 축소 */
    .page-header { gap: 10px; margin-bottom: 0.2rem; }
    .page-header-icon { width: 36px; height: 36px; font-size: 1.1rem; border-radius: 10px; }
    .page-title { font-size: 1.2rem; }
    .page-desc { font-size: 0.8rem; margin-bottom: 0.8rem; line-height: 1.5; }

    /* 새로고침 바 */
    .refresh-bar { font-size: 0.68rem; padding: 5px 10px; gap: 4px; }

    /* 컨트롤 바: 비율 조정 대응 */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.3rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 0 0 48% !important; 
        min-width: 45% !important;
        max-width: 50% !important;
    }
    
    .stSelectbox { margin-bottom: -0.3rem !important; }
    .stRadio { margin-bottom: -0.3rem !important; }
    .stSelectbox > div > div { min-height: 34px !important; font-size: 0.82rem !important; }
    .stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label {
        font-size: 0.72rem !important;
    }
    
    /* KPI 2열 + 콤팩트 */
    .kpi-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 0.8rem; }
    .kpi { padding: 0.8rem 0.9rem; border-radius: 10px; }
    .kpi-label { font-size: 0.65rem; margin-bottom: 0.2rem; }
    .kpi-value { font-size: 1.1rem; }
    .kpi-delta { font-size: 0.68rem; }

    /* 리포트 박스 콤팩트 */
    .report-box { padding: 1rem 1rem; border-radius: 10px; margin-bottom: 0.8rem; }
    .report-title { font-size: 0.95rem; }
    .report-body { font-size: 0.82rem; line-height: 1.7; }
    .report-signal { font-size: 0.73rem; padding: 4px 10px; }

    /* 가이드 박스 */
    .guide-box { padding: 0.7rem 0.9rem; font-size: 0.76rem; line-height: 1.6; }

    /* 카드 콤팩트 */
    .card { padding: 1rem 1rem; border-radius: 10px; }
    .card-title { font-size: 0.72rem; margin-bottom: 0.6rem; }

    /* 타임라인 콤팩트 */
    .tl-item { gap: 8px; padding: 0.5rem 0; font-size: 0.78rem; }
    .tl-date { font-size: 0.67rem; min-width: 68px; }
    .tl-icon { font-size: 0.9rem; }
    .tl-title { font-size: 0.8rem; }
    .tl-desc { font-size: 0.72rem; }
    .tl-dir { font-size: 0.62rem; padding: 1px 5px; }

    /* 푸터 */
    .app-footer { font-size: 0.68rem; padding: 0.8rem 0.5rem; }

    /* Plotly 모드바 모바일: 상단 고정 */
    .modebar { opacity: 1 !important; top: 2px !important; right: 2px !important; bottom: auto !important; }
    .modebar-btn { font-size: 18px !important; padding: 6px !important; }
}

/* ━━ 초소형 화면 (≤480px) ━━ */
@media (max-width: 480px) {
    .block-container {
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
    }
    .page-header-icon { width: 32px; height: 32px; font-size: 1rem; }
    .page-title { font-size: 1.05rem; letter-spacing: -0.3px; }
    .page-desc { font-size: 0.78rem; margin-bottom: 0.6rem; }
    .kpi-value { font-size: 0.95rem; }
    .kpi-label { font-size: 0.7rem; letter-spacing: 0.3px; }
    .report-title { font-size: 0.88rem; }
    .report-body { font-size: 0.78rem; line-height: 1.6; }
    .tl-date { min-width: 60px; font-size: 0.7rem; }
    .tl-desc { font-size: 0.7rem; }
}

/* ── 접근성: 사용자 설정 존중 ── */
@media (prefers-reduced-motion: reduce) {
    .refresh-dot { animation: none; }
    * { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
}

/* ── 접근성: 고대비 모드 ── */
@media (forced-colors: active) {
    .kpi { border: 2px solid CanvasText; }
    .kpi::before { background: Highlight; }
    .report-box { border: 2px solid CanvasText; }
    .card { border: 2px solid CanvasText; }
    .tl-dir { border: 1px solid CanvasText; }
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 & 이벤트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    # 2000
    ("2000-03-10", "닷컴 버블 정점",          "나스닥 5,048 사상 최고 → 이후 -78% 대폭락",           "💻", "down"),
    ("2000-05-16", "Fed 긴축 마지막 인상",     "기준금리 6.5% → 경기 과열 억제, 기술주 본격 하락",      "⬆️", "down"),
    # 2001
    ("2001-01-03", "Fed 긴급 금리인하",        "6.5→6.0% 긴급 인하, 경기침체 대응 시작",              "✂️", "up"),
    ("2001-09-11", "9·11 테러",               "뉴욕 무역센터 공격 → 증시 4일 폐장, 재개 후 -12%",     "🏢", "down"),
    ("2001-11-26", "미국 경기침체 공식 선언",   "NBER 2001.3~11 침체 인정, 나스닥 -60% 수준",          "📉", "down"),
    # 2002
    ("2002-07-24", "엔론·월드컴 회계부정",      "기업 신뢰 붕괴 → S&P 776 저점, 5년래 최저",           "📋", "down"),
    ("2002-10-09", "닷컴 버블 바닥",           "S&P 776, 나스닥 1,114 → 이후 5년 상승장 시작",        "🔄", "up"),
    # 2003
    ("2003-03-20", "이라크 전쟁 개전",         "미국 침공 시작 → 불확실성 해소로 오히려 반등",          "⚔️", "up"),
    ("2003-06-25", "Fed 금리 1.0%",           "45년래 최저 금리 → 부동산 버블 씨앗",                 "💵", "up"),
    # 2004
    ("2004-06-30", "Fed 긴축 사이클 개시",     "1.0→1.25% 첫 인상 → 17회 연속 인상 시작",             "⬆️", "down"),
    # 2005
    ("2005-08-29", "허리케인 카트리나",        "뉴올리언스 초토화 → 유가 $70 돌파, 보험주 폭락",       "🌀", "down"),
    # 2006
    ("2006-06-29", "Fed 금리 5.25% 정점",     "긴축 사이클 종료 → 부동산 시장 냉각 시작",             "📌", "down"),
    # 2007
    ("2007-02-27", "상하이 폭락 (글로벌 전염)", "중국 증시 -9% → 글로벌 동반 급락, 서브프라임 전조",     "🇨🇳", "down"),
    ("2007-08-09", "BNP 파리바 서브프라임 쇼크", "모기지 펀드 환매 중단 → 글로벌 금융위기 서막",         "🏦", "down"),
    ("2007-10-09", "S&P 1,565 역대 최고",      "금융위기 직전 고점 → 이후 -57% 대폭락",               "🏔️", "down"),
    # 2008
    ("2008-03-16", "베어스턴스 파산 구제",      "JP모건 주당 $2 인수 → 월가 패닉 시작",                "🐻", "down"),
    ("2008-09-15", "리먼 브라더스 파산",        "158년 역사 투자은행 도산 → 글로벌 금융시스템 붕괴",     "💥", "down"),
    ("2008-10-03", "TARP 구제금융 통과",       "$7,000억 금융안정법 → 공포 지속, 바닥은 아직",         "🏛️", "down"),
    ("2008-11-25", "Fed QE1 발표",            "MBS $6,000억 매입 → 양적완화 시대 개막",              "💵", "up"),
    # 2009
    ("2009-03-09", "글로벌 금융위기 바닥",      "S&P 666 역사적 저점 → 10년 강세장 시작",              "🔄", "up"),
    ("2009-06-01", "GM 파산 신청",             "역사상 최대 산업기업 파산 → 정부 구제",                "🚗", "down"),
    # 2010
    ("2010-05-06", "플래시 크래시",            "초고속 매매 → 다우 분 만에 -1,000pt, 즉시 회복",       "⚡", "down"),
    ("2010-11-03", "Fed QE2 발표",            "$6,000억 국채 매입 → 위험자산 랠리",                  "💵", "up"),
    # 2011
    ("2011-08-05", "미국 신용등급 강등",        "S&P, AAA→AA+ 사상 첫 강등 → 시장 패닉",              "📉", "down"),
    ("2011-08-08", "유럽 재정위기 격화",        "이탈리아·스페인 국채 급등 → 글로벌 위험회피",           "🇪🇺", "down"),
    # 2012
    ("2012-07-26", "드라기 'Whatever it takes'", "ECB 유로 사수 선언 → 유럽 위기 전환점",              "🇪🇺", "up"),
    ("2012-09-13", "Fed QE3 발표",            "매월 $400억 MBS 매입 → 무기한 양적완화",              "💵", "up"),
    # 2013
    ("2013-05-22", "테이퍼 탠트럼",            "버냉키 QE 축소 시사 → 금리 급등, 신흥국 패닉",         "📢", "down"),
    ("2013-12-18", "QE3 축소 개시",            "매입 $85B→$75B 감축 시작 → 시장 안도 랠리",           "📉", "up"),
    # 2014
    ("2014-10-15", "글로벌 성장 둔화 공포",     "유가 폭락 시작·유럽 디플레 → S&P -4% 후 V자 반등",     "🌍", "down"),
    ("2014-10-29", "QE3 종료",                "$4.5조 양적완화 종료 → 금리 정상화 기대",              "🛑", "down"),
    # 2015
    ("2015-08-24", "중국발 블랙먼데이",       "위안 절하·중국 증시 폭락 → 글로벌 동반 급락 -3.9%",   "🇨🇳", "down"),
    # 2016
    ("2016-02-11", "유가 폭락 바닥",         "WTI $26 → 에너지·은행주 바닥 형성, S&P 1,829",       "🛢️", "down"),
    ("2016-06-23", "브렉시트 투표",          "영국 EU 탈퇴 결정 → 이틀간 -5.3% 후 빠른 회복",       "🇬🇧", "down"),
    ("2016-11-08", "트럼프 1기 당선",        "감세 기대 → 리플레이션 랠리",                         "🗳️", "up"),
    # 2017
    ("2017-12-22", "TCJA 감세법 서명",       "법인세 35→21% 인하, 기업이익 급증",                   "📝", "up"),
    # 2018
    ("2018-02-05", "VIX 폭발 (볼마겟돈)",    "변동성 상품 붕괴 → 하루 -4%, XIV 청산",               "💣", "down"),
    ("2018-10-01", "미중 무역전쟁 격화",      "관세 확대 → 불확실성 급등, Q4 -14%",                  "⚔️", "down"),
    ("2018-12-24", "파월 피벗",              "금리 인상 중단 시사 → 크리스마스 랠리",                "🔄", "up"),
    # 2019
    ("2019-07-31", "첫 금리인하 (10년만)",    "보험적 인하 25bp → 경기 확장 연장",                   "📉", "up"),
    ("2019-09-17", "레포 시장 위기",          "단기자금 금리 10% 급등 → 긴급 유동성 공급",            "🏧", "down"),
    # 2020
    ("2020-02-20", "코로나19 팬데믹 시작",    "글로벌 봉쇄 → -34% 역대급 폭락",                     "🦠", "down"),
    ("2020-03-23", "무제한 QE 선언",         "Fed 무한 양적완화 → V자 반등 시작",                   "💵", "up"),
    ("2020-11-09", "화이자 백신 발표",        "코로나 백신 성공 → 가치주·소형주 대전환 랠리",         "💉", "up"),
    # 2021
    ("2021-11-22", "인플레 피크 & 긴축 예고", "CPI 7%대, 테이퍼링 예고 → 성장주 하락 전환",           "📉", "down"),
    # 2022
    ("2022-01-26", "Fed 매파 전환",          "'곧 금리 인상' 시사 → 나스닥 -15%",                   "🦅", "down"),
    ("2022-02-24", "러-우 전쟁 개전",         "에너지 위기 → 스태그플레이션 공포",                    "💥", "down"),
    ("2022-03-16", "긴축 사이클 개시",        "첫 25bp 인상 → 11회 연속 인상 시작, 총 525bp",         "⬆️", "down"),
    ("2022-06-13", "S&P 약세장 진입",        "고점 대비 -20% 돌파, 빅테크 폭락",                     "🐻", "down"),
    ("2022-10-13", "CPI 피크아웃",           "인플레 둔화 확인 → 하락장 바닥 형성",                  "📊", "up"),
    ("2022-11-30", "ChatGPT 출시",          "생성형 AI 시대 개막 → AI 투자 광풍의 기폭제",           "🧠", "up"),
    # 2023
    ("2023-01-19", "S&P 강세장 전환",        "전고점 돌파 → 공식 강세장 진입",                       "🐂", "up"),
    ("2023-03-12", "SVB 은행 위기",          "실리콘밸리은행 파산 → 긴급 유동성 투입(BTFP)",          "🏦", "down"),
    ("2023-10-27", "금리 고점 공포",          "10년물 5% 돌파 → S&P 200일선 이탈",                   "📈", "down"),
    # 2024
    ("2024-02-22", "NVIDIA 실적 서프라이즈",   "AI 매출 폭증 → 시총 $2T 돌파, AI 랠리 가속",          "🚀", "up"),
    ("2024-08-05", "엔 캐리트레이드 청산",     "일본 금리인상 → 글로벌 디레버리징, VIX 65",            "🇯🇵", "down"),
    ("2024-09-18", "연준 빅컷 (50bp)",       "금리인하 사이클 개시, 소형주 급등",                    "✂️", "up"),
    ("2024-11-05", "트럼프 2기 당선",         "감세·규제완화 기대 → 지수 역대 신고가",                "🗳️", "up"),
    # 2025
    ("2025-01-27", "DeepSeek AI 쇼크",       "중국 저비용 AI 모델 → 반도체주 폭락 (NVDA -17%)",     "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세",    "전방위 관세 발표 → 이틀간 -10%, VIX 60",              "🚨", "down"),
    ("2025-04-09", "관세 90일 유예",          "트럼프 관세 일시중단 → 역대급 반등 +9.5%",             "🕊️", "up"),
    ("2025-05-12", "미중 제네바 관세 합의",    "상호관세 125→10% 인하 → S&P +3.2%, 무역전쟁 완화",    "🤝", "up"),
    ("2025-07-04", "OBBBA 법안 통과",        "감세 연장·R&D 비용처리 → 기업이익 전망 상향",           "📜", "up"),
    ("2025-10-29", "QT 종료 발표",           "12/1부터 대차대조표 축소 중단",                       "🛑", "up"),
    ("2025-12-11", "RMP 국채매입 재개",       "준비금 관리 매입 개시 → 유동성 확장 전환",              "💰", "up"),
    # 2026
    ("2026-01-28", "FOMC 금리 동결",          "3.50-3.75% 유지, 2명 반대(인하 주장) → 연내 1~2회 인하 전망",  "📌", "up"),
    ("2026-01-28", "S&P 7000 돌파",          "14개월 만에 +1,000pt, AI 슈퍼사이클 & OBBBA 효과",    "🏆", "up"),
    ("2026-01-30", "케빈 워시 Fed 의장 지명",  "트럼프, 파월 후임으로 매파 성향 워시 지명 → 금·은 폭락, 달러 급등", "🦅", "down"),
    ("2026-01-30", "귀금속 대폭락",           "은 -35%, 금 -12% 하루 최대 낙폭 → 위험자산 전면 매도",   "💎", "down"),
    ("2026-02-02", "비트코인 $77K 급락",      "BTC 고점 대비 -40%, 레버리지 청산 $25억 → 크립토 윈터 우려", "₿", "down"),
    ("2026-02-03", "트럼프-인도 관세 합의",    "인도 기본관세 25→18% 인하, 러시아산 원유 구매 중단 조건", "🇮🇳", "up"),
    ("2026-02-05", "BTC $63K·은 재폭락",      "BTC -15% FTX 이후 최악, 은 추가 -17% → 소프트웨어주 -24% YTD", "⚡", "down"),
    ("2026-02-06", "다우 50,000 돌파",        "기술주 반등 +2.2%, S&P +2.0% → 연초 대비 원점 회복",   "🎯", "up"),
    ("2026-02-09", "일본 니케이 사상 최고",    "다카이치 총선 압승 → 니케이 57,650, 글로벌 위험선호 회복", "🇯🇵", "up"),
]

MARKET_PIVOTS_KR = [
    # 2000
    ("2000-01-04", "IT 버블 정점",            "KOSPI 1,059 → 이후 닷컴 붕괴로 -50% 하락",           "💻", "down"),
    ("2000-04-17", "현대그룹 유동성 위기",     "현대건설 부도 위기 → 재벌 구조조정 공포",               "🏗️", "down"),
    # 2001
    ("2001-09-12", "9·11 테러 여파",          "미국 테러 → KOSPI 470선 붕괴, 외국인 대규모 매도",      "🏢", "down"),
    # 2002
    ("2002-10-10", "KOSPI 600선 회복",        "카드채 위기 속 바닥 확인 → 반등 시작",                 "🔄", "up"),
    # 2003
    ("2003-03-12", "카드 대란",               "카드사 유동성 위기 → KOSPI 515 저점, 금융시스템 불안",   "💳", "down"),
    ("2003-08-18", "노무현 카드대란 수습",     "정부 공적자금 투입 → 금융 안정화, 증시 반등",           "🏛️", "up"),
    # 2004
    ("2004-03-12", "노무현 대통령 탄핵",       "헌재 탄핵심판 → KOSPI 급락 후 빠른 회복",              "⚖️", "down"),
    # 2005
    ("2005-11-22", "KOSPI 1,300 돌파",        "중국 특수·수출 호조 → 사상 최고 경신",                 "📈", "up"),
    # 2006
    ("2006-05-12", "글로벌 신흥국 매도",       "미국 금리인상 공포 → KOSPI -10% 조정",                "🌍", "down"),
    # 2007
    ("2007-07-25", "KOSPI 2,000 첫 돌파",     "글로벌 유동성·중국 성장 → 사상 첫 2,000 안착",         "🏆", "up"),
    ("2007-10-31", "KOSPI 2,064 역대 최고",   "서브프라임 위기 직전 고점 → 이후 -54% 폭락",           "🏔️", "down"),
    # 2008
    ("2008-09-16", "리먼 브라더스 파산 여파",   "글로벌 금융위기 → KOSPI 1,400선 붕괴, 원화 1,400원",   "💥", "down"),
    ("2008-10-24", "KOSPI 938 저점",          "패닉셀링 극대화 → 사이드카·서킷브레이커 연속 발동",      "🐻", "down"),
    ("2008-11-03", "한은 기준금리 대폭 인하",   "5.25→4.25% 빅컷 → 이후 2.0%까지 연속 인하",          "✂️", "up"),
    # 2009
    ("2009-03-02", "KOSPI 금융위기 바닥 확인",  "1,000선 회복 시작 → 이후 2년간 +100% 상승",           "🔄", "up"),
    # 2010
    ("2010-11-23", "연평도 포격",              "북한 포격 → KOSPI -2.8%, 지정학 리스크 부각",          "🚀", "down"),
    # 2011
    ("2011-08-09", "미국 신용등급 강등 여파",    "글로벌 패닉 → KOSPI 1,700선 붕괴, 외국인 투매",       "📉", "down"),
    ("2011-09-26", "유럽 재정위기 KOSPI 타격",  "그리스 디폴트 우려 → KOSPI 1,652 연저점",             "🇪🇺", "down"),
    # 2012
    ("2012-07-26", "드라기 유로 사수 선언",     "글로벌 위험선호 회복 → KOSPI 반등, 외국인 순매수 전환",  "🇪🇺", "up"),
    # 2013
    ("2013-05-23", "테이퍼 탠트럼 신흥국 충격",  "Fed QE 축소 시사 → 원화 약세, KOSPI 조정",            "📢", "down"),
    ("2013-09-13", "한국 MSCI 선진국 편입 불발", "7회 연속 탈락 → 코리아 디스카운트 지속",               "🌍", "down"),
    # 2014
    ("2014-04-16", "세월호 참사",              "국가적 비극 → 소비심리 위축, 내수주 하락",              "🖤", "down"),
    ("2014-10-15", "글로벌 성장 둔화 공포",     "유가 폭락·유럽 디플레 → KOSPI 1,900선 이탈",           "🌍", "down"),
    # 2015
    ("2015-08-24", "중국발 블랙먼데이",       "위안 절하 → KOSPI 1,830선 붕괴, 외국인 대량 매도",     "🇨🇳", "down"),
    # 2016
    ("2016-11-08", "트럼프 1기 당선",        "신흥국 자금유출 우려 → KOSPI 2,000선 하회",           "🗳️", "down"),
    ("2016-12-09", "박근혜 탄핵 가결",        "정치 불확실성 해소 기대 → 증시 반등",                 "⚖️", "up"),
    # 2017
    ("2017-05-10", "문재인 대통령 취임",      "경기부양 기대 → KOSPI 2,300 돌파 랠리",              "🏛️", "up"),
    ("2017-09-03", "북한 6차 핵실험",         "지정학 리스크 → KOSPI 급락 후 빠른 회복",             "🚀", "down"),
    # 2018
    ("2018-04-27", "남북 판문점 정상회담",     "한반도 평화 기대 → 코리아 디스카운트 축소",            "🤝", "up"),
    ("2018-10-01", "미중 무역전쟁 격화",      "수출주 직격탄 → KOSPI 2,000선 붕괴",                 "⚔️", "down"),
    # 2019
    ("2019-07-01", "일본 수출규제",           "반도체 소재 수출 제한 → 삼성·SK 타격",                "🇯🇵", "down"),
    # 2020
    ("2020-03-19", "코스피 서킷브레이커",     "코로나 패닉 → KOSPI 1,457 저점, 사이드카 발동",       "🦠", "down"),
    ("2020-03-23", "한은 긴급 기준금리 인하", "0.75%로 빅컷 → 유동성 공급 확대",                    "💵", "up"),
    ("2020-05-28", "동학개미운동",           "개인투자자 대거 유입 → KOSPI 반등 주도",              "🐜", "up"),
    ("2020-11-09", "화이자 백신 발표",        "수출주 회복 기대 → KOSPI 2,500 돌파",                "💉", "up"),
    # 2021
    ("2021-01-07", "KOSPI 3,000 돌파",       "역사상 첫 3,000 안착 → 개인 순매수 주도",             "🏆", "up"),
    ("2021-06-24", "KOSPI 3,300 역대 최고",   "글로벌 유동성 피크 → 바이오·2차전지 과열",             "📈", "up"),
    ("2021-11-22", "긴축 예고 & 하락 전환",   "금리인상 시작 → 성장주·소형주 급락",                   "📉", "down"),
    # 2022
    ("2022-02-24", "러-우 전쟁 개전",         "에너지 수입국 한국 직격 → KOSPI 2,600선 붕괴",        "💥", "down"),
    ("2022-06-23", "한은 빅스텝 (50bp)",      "기준금리 1.75→2.25%, 긴축 가속",                    "⬆️", "down"),
    ("2022-09-26", "KOSPI 2,200 붕괴",       "강달러·긴축 → 연중 최저, 외국인 연속 매도",            "🐻", "down"),
    ("2022-11-30", "ChatGPT 출시",           "AI 수혜주(삼성·SK) 반등 기대감",                     "🧠", "up"),
    # 2023
    ("2023-01-30", "한은 금리 동결 전환",     "3.50% 정점 시사 → 금리 인상 사이클 종료",              "🔄", "up"),
    ("2023-05-30", "KOSPI 2,600 회복",       "반도체 업황 회복 기대 → 삼성전자 주도 반등",            "📊", "up"),
    # 2024
    ("2024-01-02", "밸류업 프로그램 발표",    "PBR 1배 미만 기업 개선 요구 → 저PBR주 급등",           "📋", "up"),
    ("2024-08-05", "엔 캐리트레이드 청산",    "글로벌 디레버리징 → KOSPI -8.8% 블랙먼데이",          "🇯🇵", "down"),
    ("2024-12-03", "윤석열 비상계엄 선포",    "정치 위기 → KOSPI 급락, 원화 1,440원 돌파",           "🚨", "down"),
    ("2024-12-14", "윤석열 탄핵 가결",        "불확실성 정점 후 정치 리스크 일부 해소",               "⚖️", "up"),
    # 2025
    ("2025-01-27", "DeepSeek AI 쇼크",       "중국 AI 충격 → 삼성전자·SK하이닉스 급락",             "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세",    "한국산 제품 25% 관세 → 수출주 폭락, KOSPI -4%",       "🚨", "down"),
    ("2025-04-09", "관세 90일 유예",          "한국 포함 유예 → KOSPI +5% 반등",                    "🕊️", "up"),
    ("2025-05-12", "미중 관세 합의",          "글로벌 무역 완화 → 한국 수출 수혜 기대",               "🤝", "up"),
    ("2025-06-03", "한은 기준금리 2.50% 인하", "경기 부양 위해 추가 인하 → 유동성 확대",              "✂️", "up"),
    # 2026
    ("2026-01-02", "KOSPI 4,300 신고가",      "신년 첫 거래일 +2.3%, 시총 3,500조 돌파 → 삼성·SK 주도",  "🏆", "up"),
    ("2026-01-30", "워시 Fed 의장 지명 쇼크",  "매파 우려 → 귀금속·BTC 폭락, KOSPI 200 변동성 50 돌파", "🦅", "down"),
    ("2026-02-02", "KOSPI -5.26% 급락",       "글로벌 위험자산 매도 → 사이드카 발동, 4,950선 이탈",     "⚡", "down"),
    ("2026-02-03", "KOSPI +6.84% 역대급 반등", "바겐헌팅 + 삼성 HBM4 기대 → 5,288 사상 최고가",        "🔥", "up"),
    ("2026-02-06", "KOSPI 5,089 조정",        "AI 수익성 우려 → 이틀 연속 하락, 외국인 순매도",         "📉", "down"),
    ("2026-02-10", "KOSPI 5,300 회복",        "삼성 HBM4 양산·SK하이닉스 +6% → AI 랠리 재점화",       "📊", "up"),
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 국가별 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COUNTRY_CONFIG = {
    "🇺🇸 미국": {
        "indices": {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",      # 본원통화 (Billions of USD — FRED 단위 그대로)
        "fred_rec": "USREC",          # 경기침체 지표
        "liq_divisor": 1,             # 이미 $B 단위
        "liq_label": "본원통화",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "liq_suffix": "B",
        "events": MARKET_PIVOTS,
        "data_src": "Federal Reserve (FRED) · Yahoo Finance",
    },
    "🇰🇷 대한민국": {
        "indices": {"KOSPI": "^KS11", "KOSDAQ": "^KQ11"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",        # Fed 본원통화 = 글로벌 유동성 지표
        "fred_rec": "USREC",           # 미국 경기침체 (글로벌 영향)
        "liq_divisor": 1,              # 이미 $B 단위
        "liq_label": "글로벌 유동성 (Fed)",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "liq_suffix": "B",
        "events": MARKET_PIVOTS_KR,
        "data_src": "Federal Reserve (FRED) · Yahoo Finance (KRX)",
    },
}


@st.cache_data(ttl=300, show_spinner=False)
def load_data(ticker, fred_liq, fred_rec, liq_divisor):
    try:
        end_dt = datetime.now()
        fetch_start = end_dt - timedelta(days=365 * 27)

        # [A] FRED 데이터 (유동성)
        try:
            fred_codes = [fred_liq]
            if fred_rec:
                fred_codes.append(fred_rec)
            fred_df = web.DataReader(fred_codes, "fred", fetch_start, end_dt).ffill()
            if fred_rec:
                fred_df.columns = ["Liquidity", "Recession"]
            else:
                fred_df.columns = ["Liquidity"]
                fred_df["Recession"] = 0
            fred_df["Liquidity"] = fred_df["Liquidity"] / liq_divisor
        except Exception as e:
            st.error(f"FRED 데이터 로드 실패: {e}")
            return None, None

        # [B] 주가 지수 데이터 (yfinance - OHLC)
        try:
            import yfinance as yf

            # 방법 1: yf.download (auto_adjust=False, multi_level_index=False)
            try:
                yf_data = yf.download(
                    ticker, start=fetch_start, end=end_dt,
                    progress=False, auto_adjust=False, multi_level_index=False
                )
            except TypeError:
                # 구버전 yfinance: multi_level_index 미지원
                yf_data = yf.download(
                    ticker, start=fetch_start, end=end_dt,
                    progress=False, auto_adjust=False
                )

            # MultiIndex 컬럼이 남아있으면 평탄화
            if isinstance(yf_data.columns, pd.MultiIndex):
                yf_data.columns = [col[0] for col in yf_data.columns]

            # 방법 1 실패 시 → 방법 2: yf.Ticker().history() 폴백
            if yf_data.empty:
                t = yf.Ticker(ticker)
                yf_data = t.history(start=fetch_start, end=end_dt, auto_adjust=False)
                if isinstance(yf_data.columns, pd.MultiIndex):
                    yf_data.columns = [col[0] for col in yf_data.columns]

            if yf_data.empty:
                st.error("지수 데이터를 가져오지 못했습니다. (데이터가 비어있음)")
                return None, None

            idx_close = yf_data[['Close']].rename(columns={'Close': 'SP500'})
            ohlc = yf_data[['Open','High','Low','Close','Volume']].copy()

        except Exception as e:
            st.error(f"지수 데이터 로드 실패 (yfinance): {e}")
            return None, None

        # [C] 데이터 통합 및 가공
        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        
        if 'SP500' in df.columns:
            df["Liq_MA"] = df["Liquidity"].rolling(10).mean()
            df["SP_MA"] = df["SP500"].rolling(10).mean()
            df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
            df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        else:
            st.error("데이터 통합 과정에서 주가 컬럼을 생성하지 못했습니다.")
            return None, None

        for c in ["Liquidity", "SP500"]:
            s = df[c].dropna()
            if len(s) > 0:
                df[f"{c}_norm"] = (df[c] - s.min()) / (s.max() - s.min()) * 100
        
        df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])

        cut = end_dt - timedelta(days=365 * 27)
        df = df[df.index >= pd.to_datetime(cut)]
        ohlc = ohlc[ohlc.index >= pd.to_datetime(cut)]
        return df.dropna(subset=["SP500"]), ohlc.dropna(subset=["Close"])

    except Exception as e:
        st.error(f"⚠️ 시스템 오류: {str(e)}")
        return None, None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 크로스에셋 & 매크로 데이터 (Daily Brief / Investment Advice 용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=300, show_spinner=False)
def load_cross_asset_data():
    """금, 은, BTC, ETH, 10Y 국채, DXY, 니케이, 원/달러 등 크로스에셋 실시간 데이터"""
    import yfinance as yf
    end_dt = datetime.now()
    start_6m = end_dt - timedelta(days=180)
    start_1y = end_dt - timedelta(days=365)

    tickers = {
        "gold": "GC=F",        # 금 선물
        "silver": "SI=F",      # 은 선물
        "btc": "BTC-USD",      # 비트코인
        "eth": "ETH-USD",      # 이더리움
        "us10y": "^TNX",       # 미국 10년물 금리
        "us2y": "^IRX",        # 미국 2년물 금리 (단기금리 프록시)
        "dxy": "DX-F",         # 달러 인덱스 (선물)
        "nikkei": "^N225",     # 니케이
        "krw": "KRW=X",       # USD/KRW
        "vix": "^VIX",         # VIX
        "russell": "^RUT",     # Russell 2000
        "dow": "^DJI",         # 다우존스
        "kospi": "^KS11",      # KOSPI
        "xlk": "XLK",          # 기술 섹터 ETF
        "xle": "XLE",          # 에너지 섹터 ETF
        "xlf": "XLF",          # 금융 섹터 ETF
        "xlv": "XLV",          # 헬스케어 섹터 ETF
        "xlu": "XLU",          # 유틸리티 섹터 ETF
        "tlt": "TLT",          # 장기국채 ETF
        "hyg": "HYG",          # 하이일드 채권 ETF
        "oil": "CL=F",         # WTI 원유 선물
        "copper": "HG=F",      # 구리 선물
    }

    result = {}
    for name, ticker in tickers.items():
        try:
            data = yf.download(ticker, start=start_1y, end=end_dt, progress=False, auto_adjust=False)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [col[0] for col in data.columns]
            if not data.empty:
                close = data["Close"].dropna()
                current = close.iloc[-1]
                # 고점 (1년 내)
                high_1y = close.max()
                # 변동률 계산
                chg_1d = ((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(close) > 1 else 0
                chg_1w = ((close.iloc[-1] / close.iloc[-5] - 1) * 100) if len(close) > 5 else 0
                chg_1m = ((close.iloc[-1] / close.iloc[-21] - 1) * 100) if len(close) > 21 else 0
                chg_3m = ((close.iloc[-1] / close.iloc[-63] - 1) * 100) if len(close) > 63 else 0
                chg_ytd = 0
                try:
                    yr_start = close[close.index >= f"{end_dt.year}-01-01"]
                    if len(yr_start) > 0:
                        chg_ytd = ((close.iloc[-1] / yr_start.iloc[0] - 1) * 100)
                except Exception:
                    pass
                chg_from_high = ((current / high_1y - 1) * 100) if high_1y > 0 else 0
                result[name] = {
                    "price": float(current), "high_1y": float(high_1y),
                    "chg_1d": float(chg_1d), "chg_1w": float(chg_1w),
                    "chg_1m": float(chg_1m), "chg_3m": float(chg_3m),
                    "chg_ytd": float(chg_ytd), "chg_from_high": float(chg_from_high),
                }
        except Exception:
            result[name] = None
    return result


@st.cache_data(ttl=300, show_spinner=False)
def load_fed_funds_rate():
    """FRED에서 실효 연방기금금리(DFF) 로드"""
    try:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)
        ff = web.DataReader("DFF", "fred", start_dt, end_dt).ffill()
        current = ff.iloc[-1, 0]
        prev_month = ff.iloc[-21, 0] if len(ff) > 21 else current
        return {"current": float(current), "prev_month": float(prev_month)}
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def load_bok_base_rate():
    """한국은행 기준금리 프록시 — FRED IRSTCI01KRM156N (한국 단기금리)"""
    try:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=730)
        kr = web.DataReader("IRSTCI01KRM156N", "fred", start_dt, end_dt).ffill()
        current = kr.iloc[-1, 0]
        return {"current": float(current)}
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def load_market_news():
    """yfinance를 활용한 주요 시장 관련 뉴스 수집"""
    import yfinance as yf
    news_items = []
    # 주요 지수/자산에서 뉴스 수집
    news_tickers = ["^GSPC", "^IXIC", "GC=F", "BTC-USD", "^KS11"]
    seen_titles = set()
    for ticker_symbol in news_tickers:
        try:
            ticker = yf.Ticker(ticker_symbol)
            if hasattr(ticker, 'news') and ticker.news:
                for item in ticker.news[:5]:
                    content = item.get("content", {})
                    title = content.get("title", "")
                    provider = content.get("provider", {}).get("displayName", "")
                    pub_date = content.get("pubDate", "")
                    canonical_url = content.get("canonicalUrl", {}).get("url", "")
                    # 중복 제거
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        news_items.append({
                            "title": title,
                            "publisher": provider,
                            "link": canonical_url,
                            "published": pub_date,
                            "ticker": ticker_symbol,
                        })
        except Exception:
            continue
    # 최신 순 정렬 후 상위 10개
    return news_items[:10]


def compute_market_sentiment(cross, liq_yoy, liq_3m_chg, sp_1m_chg, sp_yoy, corr_val):
    """복합 시장 센티먼트 점수 계산 (0-100 스케일, Fear ↔ Greed)"""
    scores = []

    # 1. VIX 기반 (0-100, 낮을수록 Greed)
    vix = _safe(cross, "vix")
    if vix > 0:
        vix_score = max(0, min(100, 100 - (vix - 12) * 4))
        scores.append(vix_score)

    # 2. 시장 모멘텀 (1개월 변동)
    mom_score = max(0, min(100, 50 + sp_1m_chg * 5))
    scores.append(mom_score)

    # 3. 고점 대비 거리 (S&P500 YoY)
    yoy_score = max(0, min(100, 50 + sp_yoy * 1.5))
    scores.append(yoy_score)

    # 4. 유동성 추세
    liq_score = max(0, min(100, 50 + liq_3m_chg * 10))
    scores.append(liq_score)

    # 5. 안전자산 vs 위험자산 (금 vs 주식)
    gold_chg = _safe(cross, "gold", "chg_1m")
    safe_haven_score = max(0, min(100, 50 - gold_chg * 3 + sp_1m_chg * 3))
    scores.append(safe_haven_score)

    # 6. 하이일드 스프레드 (HYG 변동 - 하락이면 스프레드 확대)
    hyg_chg = _safe(cross, "hyg", "chg_1m")
    credit_score = max(0, min(100, 50 + hyg_chg * 8))
    scores.append(credit_score)

    # 7. 상관관계 (유동성 장세 여부)
    corr_score = max(0, min(100, 50 + corr_val * 40))
    scores.append(corr_score)

    avg_score = sum(scores) / len(scores) if scores else 50

    if avg_score >= 75:
        label = "극도의 탐욕 (Extreme Greed)"
        color = "#16a34a"
    elif avg_score >= 60:
        label = "탐욕 (Greed)"
        color = "#65a30d"
    elif avg_score >= 45:
        label = "중립 (Neutral)"
        color = "#ca8a04"
    elif avg_score >= 30:
        label = "공포 (Fear)"
        color = "#dc2626"
    else:
        label = "극도의 공포 (Extreme Fear)"
        color = "#991b1b"

    return {"score": round(avg_score, 1), "label": label, "color": color, "components": scores}


def generate_yield_curve_analysis(cross):
    """수익률 곡선(Yield Curve) 분석"""
    us10y = _safe(cross, "us10y")
    us2y = _safe(cross, "us2y")

    if us10y == 0 or us2y == 0:
        return ""

    # us2y(^IRX)는 13주 단기금리이므로 100으로 나눠야 함
    us2y_adj = us2y / 100 if us2y > 10 else us2y
    spread = us10y - us2y_adj

    if spread < -0.5:
        curve_status = "깊은 역전 상태 (Deep Inversion)"
        implication = "경기침체 선행 신호가 강하게 나타나고 있습니다. 역사적으로 역전 후 6~18개월 내 경기둔화가 확인되었습니다."
        risk_level = "높음"
    elif spread < 0:
        curve_status = "역전 상태 (Inverted)"
        implication = "단기금리가 장기금리를 상회하여 경기둔화 우려가 존재합니다. 다만 역전 해소(재정상화) 시점이 더 중요한 시그널입니다."
        risk_level = "경계"
    elif spread < 0.5:
        curve_status = "평탄화 (Flat)"
        implication = "수익률 곡선이 평탄하여 경기 전환 구간에 위치하고 있습니다. 정상화 진행 중이라면 리스크 자산에 점진적으로 긍정적입니다."
        risk_level = "보통"
    else:
        curve_status = "정상 (Normal/Steepening)"
        implication = "장기금리가 단기금리를 상회하는 정상적 수익률 곡선입니다. 경기 확장 기대가 반영되어 있습니다."
        risk_level = "안정"

    return (
        f'<strong>▎수익률 곡선 (Yield Curve) 분석</strong><br>'
        f'10Y-단기금리 스프레드: <span class="hl">{spread:+.2f}%p</span> '
        f'(10Y {us10y:.2f}%, 단기 {us2y_adj:.2f}%)<br>'
        f'상태: <strong>{curve_status}</strong> | 리스크 레벨: {risk_level}<br><br>'
        f'{implication}'
    )


def generate_sector_rotation_analysis(cross):
    """섹터 로테이션 분석 (섹터 ETF 기반)"""
    xlk_chg = _safe(cross, "xlk", "chg_1m")
    xle_chg = _safe(cross, "xle", "chg_1m")
    xlf_chg = _safe(cross, "xlf", "chg_1m")
    xlv_chg = _safe(cross, "xlv", "chg_1m")
    xlu_chg = _safe(cross, "xlu", "chg_1m")

    sectors = [
        ("기술(XLK)", xlk_chg),
        ("에너지(XLE)", xle_chg),
        ("금융(XLF)", xlf_chg),
        ("헬스케어(XLV)", xlv_chg),
        ("유틸리티(XLU)", xlu_chg),
    ]
    sectors_sorted = sorted(sectors, key=lambda x: x[1], reverse=True)

    # 경기 사이클 판단
    defensive = (xlv_chg + xlu_chg) / 2
    cyclical = (xlk_chg + xle_chg + xlf_chg) / 3

    if cyclical > defensive + 2:
        cycle_phase = "확장기 (Expansion)"
        cycle_desc = "경기순환 섹터가 방어 섹터를 아웃퍼폼하고 있어 리스크-온 환경입니다."
    elif defensive > cyclical + 2:
        cycle_phase = "수축기 (Contraction)"
        cycle_desc = "방어 섹터가 경기순환 섹터를 아웃퍼폼하고 있어 리스크-오프 환경입니다."
    else:
        cycle_phase = "전환기 (Transition)"
        cycle_desc = "섹터 간 성과 차이가 뚜렷하지 않아 방향 전환 모색 구간입니다."

    sector_lines = ""
    for name, chg in sectors_sorted:
        arrow = "▲" if chg >= 0 else "▼"
        color = "var(--accent-green)" if chg >= 0 else "var(--accent-red)"
        sector_lines += f'<span style="color:{color}">{arrow}</span> {name}: {chg:+.1f}% &nbsp;&nbsp;'

    return (
        f'<strong>▎섹터 로테이션 분석</strong><br>'
        f'사이클 판단: <strong>{cycle_phase}</strong> — {cycle_desc}<br><br>'
        f'<strong>1개월 섹터별 성과:</strong><br>'
        f'{sector_lines}<br><br>'
        f'<strong>리더:</strong> {sectors_sorted[0][0]} ({sectors_sorted[0][1]:+.1f}%) | '
        f'<strong>래거드:</strong> {sectors_sorted[-1][0]} ({sectors_sorted[-1][1]:+.1f}%)'
    )


def generate_commodity_analysis(cross):
    """원자재 및 실물자산 심층 분석"""
    gold_p = _safe(cross, "gold")
    gold_chg = _safe(cross, "gold", "chg_1m")
    gold_3m = _safe(cross, "gold", "chg_3m")
    silver_p = _safe(cross, "silver")
    silver_chg = _safe(cross, "silver", "chg_1m")
    oil_p = _safe(cross, "oil")
    oil_chg = _safe(cross, "oil", "chg_1m")
    oil_3m = _safe(cross, "oil", "chg_3m")
    copper_p = _safe(cross, "copper")
    copper_chg = _safe(cross, "copper", "chg_1m")
    copper_3m = _safe(cross, "copper", "chg_3m")

    # 금/은 비율 (Gold/Silver Ratio) — 경기 신호
    gs_ratio = gold_p / silver_p if silver_p > 0 else 0
    gs_comment = ""
    if gs_ratio > 85:
        gs_comment = f"금/은 비율 {gs_ratio:.1f}로 극단적 수준 → 경기침체 우려 또는 안전자산 선호가 극대화된 상태입니다."
    elif gs_ratio > 75:
        gs_comment = f"금/은 비율 {gs_ratio:.1f}로 높은 수준 → 리스크 회피 심리가 우세합니다."
    elif gs_ratio > 65:
        gs_comment = f"금/은 비율 {gs_ratio:.1f}로 정상 범위 → 안전자산과 산업 수요가 균형을 이루고 있습니다."
    else:
        gs_comment = f"금/은 비율 {gs_ratio:.1f}로 낮은 수준 → 산업용 수요(은) 강세로 경기 확장 신호입니다."

    # 구리/금 비율 — 경기선행 지표
    cg_ratio_comment = ""
    if copper_p > 0 and gold_p > 0:
        if copper_chg > gold_chg + 2:
            cg_ratio_comment = "구리가 금을 아웃퍼폼 → 리플레이션/경기 확장 베팅이 우세합니다."
        elif gold_chg > copper_chg + 2:
            cg_ratio_comment = "금이 구리를 아웃퍼폼 → 안전자산 선호/디플레이션 우려가 부각되고 있습니다."
        else:
            cg_ratio_comment = "구리와 금이 동조적 움직임 → 인플레이션 기대가 안정적입니다."

    return (
        f'<strong>▎원자재 & 실물자산 분석</strong><br>'
        f'• <strong>금:</strong> ${gold_p:,.0f} (1M {gold_chg:+.1f}%, 3M {gold_3m:+.1f}%) — '
        + ('인플레이션 헤지·안전자산 수요가 견고합니다.' if gold_chg > 0 else '리스크-온 환경에서 안전자산 매력이 약화되었습니다.') + '<br>'
        f'• <strong>원유(WTI):</strong> ${oil_p:,.1f} (1M {oil_chg:+.1f}%, 3M {oil_3m:+.1f}%) — '
        + ('에너지 수요 강세 또는 공급 축소가 가격을 지지합니다.' if oil_chg > 0 else '수요 둔화 또는 공급 과잉 우려가 반영되고 있습니다.') + '<br>'
        f'• <strong>구리:</strong> ${copper_p:,.2f} (1M {copper_chg:+.1f}%, 3M {copper_3m:+.1f}%) — '
        + ('"닥터 코퍼" 상승은 글로벌 경기 회복 기대를 반영합니다.' if copper_chg > 0 else '산업 수요 둔화 우려가 반영되고 있습니다.') + '<br>'
        f'• <strong>은:</strong> ${silver_p:,.1f} (1M {silver_chg:+.1f}%)<br><br>'
        f'{gs_comment}<br>'
        f'{cg_ratio_comment}'
    )


def _safe(d, key, sub="price", fallback=0):
    """크로스에셋 딕셔너리에서 안전하게 값 추출"""
    if d and d.get(key):
        return d[key].get(sub, fallback)
    return fallback


def _chg_arrow(val):
    """변동률에 따라 ▲/▼ 화살표 반환"""
    return "▲" if val >= 0 else "▼"


def _chg_color(val):
    return "var(--accent-green)" if val >= 0 else "var(--accent-red)"


def generate_dynamic_brief(country, df, liq_display, liq_yoy, liq_1m_chg, liq_3m_chg, liq_6m_chg,
                           sp_val, sp_1w_chg, sp_1m_chg, sp_3m_chg, sp_yoy, corr_val,
                           idx_name, cross, fed_rate, bok_rate, news_data=None):
    """Daily Brief 전체를 실시간 데이터 기반으로 동적 생성 (심층 유동성-지수 분석 + 뉴스 요약 포함)"""

    # ── 정책 현황 ──
    if country == "🇺🇸 미국":
        ff_str = f'{fed_rate["current"]:.2f}%' if fed_rate else "N/A"
        ff_prev = fed_rate["prev_month"] if fed_rate else None
        ff_direction = ""
        if fed_rate and ff_prev is not None:
            diff = fed_rate["current"] - ff_prev
            if abs(diff) < 0.01:
                ff_direction = "동결 기조를 유지하고 있습니다."
            elif diff < 0:
                ff_direction = f"전월 대비 {abs(diff):.2f}%p 인하되었습니다."
            else:
                ff_direction = f"전월 대비 {diff:.2f}%p 인상되었습니다."

        us10y = _safe(cross, "us10y")
        us10y_chg = _safe(cross, "us10y", "chg_1m")
        bond_direction = "금리가 상승하여 긴축적 환경" if us10y_chg > 0 else "금리가 하락하여 완화적 환경"

        brief_policy = (
            f'<strong>▎연준 정책 현황</strong><br>'
            f'실효 연방기금금리 <span class="hl">{ff_str}</span>. {ff_direction}<br><br>'
            f'미국 10년물 국채금리는 <span class="hl">{us10y:.2f}%</span>로, '
            f'최근 1개월 {us10y_chg:+.2f}%p 변동하며 {bond_direction}이 형성되고 있습니다.<br><br>'
            f'유동성 지표(본원통화) YoY {liq_yoy:+.1f}% 변동은 '
            + ("연준이 대차대조표를 확장하는 방향으로 움직이고 있음을 시사합니다. " if liq_yoy > 0
               else "연준이 긴축 기조를 유지하며 유동성이 수축하고 있음을 시사합니다. " if liq_yoy < -2
               else "연준의 대차대조표가 안정적으로 유지되고 있음을 시사합니다. ")
            + '시장은 향후 금리 경로에 대해 데이터 의존적 접근을 이어가고 있습니다.'
        )
    else:
        bok_str = f'{bok_rate["current"]:.2f}%' if bok_rate else "N/A"
        krw_rate = _safe(cross, "krw")
        krw_chg = _safe(cross, "krw", "chg_1m")
        krw_direction = "원화가 약세" if krw_chg > 0 else "원화가 강세"

        brief_policy = (
            f'<strong>▎한국은행 통화정책 현황</strong><br>'
            f'한국 단기금리 <span class="hl">{bok_str}</span>. '
            f'글로벌 긴축 완화 흐름과 국내 경기를 감안한 정책 기조가 유지되고 있습니다.<br><br>'
            f'<strong>환율:</strong> 원/달러 <span class="hl">{krw_rate:,.0f}원</span> '
            f'(1개월 {krw_chg:+.1f}%). {krw_direction}를 보이고 있으며, '
            + ("환율 안정과 가계부채 관리가 추가 인하의 핵심 제약 요인입니다." if krw_rate > 1350
               else "환율 안정이 통화정책 운용에 여유를 주고 있습니다.")
            + '<br><br>'
            f'<strong>글로벌 영향:</strong> Fed 본원통화 YoY {liq_yoy:+.1f}% 변동은 '
            f'글로벌 달러 유동성 환경이 '
            + ("신흥국에 우호적으로 전환되고 있음을 의미합니다." if liq_yoy > 0
               else "신흥국 자금 흐름에 부담으로 작용할 수 있음을 의미합니다." if liq_yoy < -2
               else "안정적으로 유지되고 있음을 의미합니다.")
        )

    # ── 유동성 심층 분석 ──
    liq_trend = ""
    if liq_3m_chg > 1:
        liq_trend = "유동성이 뚜렷한 확장 국면에 진입했습니다."
    elif liq_3m_chg > 0:
        liq_trend = "유동성이 완만한 확장 기조를 보이고 있습니다."
    elif liq_3m_chg > -1:
        liq_trend = "유동성이 보합 수준을 유지하고 있습니다."
    else:
        liq_trend = "유동성이 수축 국면에 진입하여 주의가 필요합니다."

    liq_momentum = ""
    if liq_1m_chg > liq_3m_chg / 3:
        liq_momentum = "단기 유동성 모멘텀이 중기 추세를 상회하고 있어 확장 가속 신호입니다."
    elif liq_1m_chg < 0 and liq_3m_chg > 0:
        liq_momentum = "단기 유동성이 둔화되고 있으나 중기 추세는 여전히 양호합니다."
    else:
        liq_momentum = "단기와 중기 유동성 추세가 동조하고 있습니다."

    if country == "🇺🇸 미국":
        brief_liq = (
            f'<strong>▎유동성 데이터 심층 분석</strong><br>'
            f'본원통화 최신치 <span class="hl">{liq_display}</span> '
            f'(YoY {liq_yoy:+.1f}%, 1개월 {liq_1m_chg:+.1f}%, 3개월 {liq_3m_chg:+.1f}%, 6개월 {liq_6m_chg:+.1f}%).<br><br>'
            f'{liq_trend} {liq_momentum}<br><br>'
            f'<strong>핵심 포인트:</strong> '
            + (f'유동성 확장 속도(3개월 {liq_3m_chg:+.1f}%)가 '
               + ("빠르게 진행되어 자산가격 상승을 강하게 지지합니다." if liq_3m_chg > 3
                  else "완만하여 점진적 자산가격 상승을 예상합니다." if liq_3m_chg > 0
                  else "정체/수축 중이어서 자산가격에 하방 압력이 작용할 수 있습니다."))
        )
    else:
        brief_liq = (
            f'<strong>▎유동성 데이터 심층 분석</strong><br>'
            f'Fed 본원통화(글로벌 유동성 지표) 최신치 <span class="hl">{liq_display}</span> '
            f'(YoY {liq_yoy:+.1f}%, 1개월 {liq_1m_chg:+.1f}%, 3개월 {liq_3m_chg:+.1f}%, 6개월 {liq_6m_chg:+.1f}%).<br><br>'
            f'한국 증시는 글로벌 달러 유동성에 높은 민감도를 보입니다. '
            f'{liq_trend}<br><br>'
            f'<strong>핵심 포인트:</strong> 외국인 순매수 복귀 여부와 원화 환율 안정이 '
            f'한국 증시 유동성의 직접적 지표입니다. '
            + (f'현재 글로벌 유동성 확장(3개월 {liq_3m_chg:+.1f}%)은 신흥국 자금 유입에 우호적입니다.'
               if liq_3m_chg > 0 else
               f'현재 글로벌 유동성 수축(3개월 {liq_3m_chg:+.1f}%)은 신흥국 자금 유출 압력을 높입니다.')
        )

    # ── 시장 동향 ──
    # 추가 지수 데이터
    dow_price = _safe(cross, "dow")
    dow_ytd = _safe(cross, "dow", "chg_ytd")
    russell_price = _safe(cross, "russell")
    russell_ytd = _safe(cross, "russell", "chg_ytd")
    vix_price = _safe(cross, "vix")
    vix_chg = _safe(cross, "vix", "chg_1m")
    kospi_price = _safe(cross, "kospi")
    kospi_ytd = _safe(cross, "kospi", "chg_ytd")

    # 시장 레짐 판단
    if sp_1m_chg > 5:
        mkt_regime = "강한 상승 모멘텀이 확인됩니다."
    elif sp_1m_chg > 0:
        mkt_regime = "온건한 상승 흐름이 지속되고 있습니다."
    elif sp_1m_chg > -3:
        mkt_regime = "횡보 또는 약세 조정 국면입니다."
    else:
        mkt_regime = "뚜렷한 하락 압력이 존재합니다."

    vix_comment = ""
    if vix_price > 30:
        vix_comment = f"VIX {vix_price:.1f}로 공포 구간에 진입하여 변동성 확대 주의가 필요합니다."
    elif vix_price > 20:
        vix_comment = f"VIX {vix_price:.1f}로 불안 구간에 위치하며 변동성이 확대되고 있습니다."
    else:
        vix_comment = f"VIX {vix_price:.1f}로 안정적인 시장 환경을 나타내고 있습니다."

    if country == "🇺🇸 미국":
        brief_market = (
            f'<strong>▎시장 동향 & 섹터 분석</strong><br>'
            f'{idx_name} <span class="hl">{sp_val:,.0f}</span> '
            f'(1주 {sp_1w_chg:+.1f}%, 1개월 {sp_1m_chg:+.1f}%, 3개월 {sp_3m_chg:+.1f}%, YoY {sp_yoy:+.1f}%). '
            f'{mkt_regime}<br><br>'
            f'<strong>주요 지수 현황:</strong><br>'
            f'• 다우존스: {dow_price:,.0f} (YTD {dow_ytd:+.1f}%)<br>'
            f'• Russell 2000: {russell_price:,.0f} (YTD {russell_ytd:+.1f}%)<br>'
            f'• {vix_comment}<br><br>'
            + (f'<strong>시장 폭:</strong> Russell 2000 YTD({russell_ytd:+.1f}%)가 '
               + (f'대형주 대비 아웃퍼폼 → 랠리 저변이 확대되고 있습니다.'
                  if russell_ytd > dow_ytd else
                  f'대형주 대비 언더퍼폼 → 대형주 쏠림이 지속되고 있습니다.'))
        )
    else:
        nikkei_price = _safe(cross, "nikkei")
        nikkei_ytd = _safe(cross, "nikkei", "chg_ytd")
        brief_market = (
            f'<strong>▎시장 동향 & 섹터 분석</strong><br>'
            f'{idx_name} <span class="hl">{sp_val:,.0f}</span> '
            f'(1주 {sp_1w_chg:+.1f}%, 1개월 {sp_1m_chg:+.1f}%, 3개월 {sp_3m_chg:+.1f}%, YoY {sp_yoy:+.1f}%). '
            f'{mkt_regime}<br><br>'
            f'<strong>아시아 주요 지수:</strong><br>'
            f'• 니케이: {nikkei_price:,.0f} (YTD {nikkei_ytd:+.1f}%)<br>'
            f'• {vix_comment}<br><br>'
            f'<strong>시장 환경:</strong> '
            + (f'글로벌 유동성 확장과 함께 한국 증시가 강세를 보이고 있습니다. '
               if sp_1m_chg > 0 and liq_3m_chg > 0 else
               f'글로벌 불확실성 속에서 한국 증시가 변동성을 보이고 있습니다. ')
            + (f'원/달러 환율({_safe(cross, "krw"):,.0f}원)과 외국인 수급이 핵심 변수입니다.'
               if cross and cross.get("krw") else
               f'외국인 수급 방향이 핵심 변수입니다.')
        )

    # ── 상관관계 진단 (심층 분석) ──
    # 유동성-지수 선행/후행 관계 분석
    liq_leads_market = ""
    if liq_3m_chg > 1 and sp_1m_chg > 0:
        liq_leads_market = "유동성 확장이 시장 상승을 선행하는 전형적 패턴이 확인됩니다. 유동성이 먼저 움직이고 주가가 1~3개월 뒤따르는 구조입니다."
    elif liq_3m_chg > 1 and sp_1m_chg < 0:
        liq_leads_market = "유동성은 확장 중이나 주가가 조정을 받고 있습니다. 역사적으로 이 괴리는 2~4주 내 주가 반등으로 해소되는 경향이 높습니다 (2019.8, 2023.10 사례)."
    elif liq_3m_chg < -1 and sp_1m_chg > 0:
        liq_leads_market = "유동성은 수축하고 있으나 주가가 아직 상승 관성을 유지하고 있습니다. 실적 장세 가능성이 있으나, 유동성 역풍이 지속되면 3~6개월 내 조정 위험이 높아집니다."
    elif liq_3m_chg < -1 and sp_1m_chg < 0:
        liq_leads_market = "유동성 수축과 주가 하락이 동시에 진행 중입니다. 이는 2022년 상반기와 유사한 패턴으로, 유동성 방향 전환이 확인될 때까지 방어적 포지션이 필요합니다."
    else:
        liq_leads_market = "유동성과 주가가 동조적 흐름을 보이고 있어, 현재 시장은 유동성 환경을 충실히 반영하고 있습니다."

    # 상관계수 변화 방향 감지
    corr_series = df["Corr_90d"].dropna()
    corr_30d_ago = corr_series.iloc[-21] if len(corr_series) > 21 else corr_val
    corr_direction = corr_val - corr_30d_ago
    corr_dir_text = ""
    if abs(corr_direction) > 0.1:
        if corr_direction > 0:
            corr_dir_text = f"상관계수가 1개월 전 대비 <strong>{corr_direction:+.3f}</strong> 상승하며 유동성-주가 동조성이 강화되고 있습니다."
        else:
            corr_dir_text = f"상관계수가 1개월 전 대비 <strong>{corr_direction:+.3f}</strong> 하락하며 유동성-주가 동조성이 약화되고 있습니다."
    else:
        corr_dir_text = f"상관계수 변화({corr_direction:+.3f})가 미미하여 기존 추세가 유지되고 있습니다."

    brief_corr = (
        f'<strong>▎유동성-지수 상관관계 심층 진단</strong><br>'
        f'90일 롤링 상관계수 <span class="hl">{corr_val:.3f}</span>. '
        + ('유동성과 주가가 강한 동행 관계를 유지 중입니다. '
           '이는 중앙은행 유동성 공급이 주가를 직접적으로 지지하는 <strong>"유동성 장세"</strong> 구간임을 의미합니다. '
           '유동성 방향 전환 시 주가도 동반 조정될 수 있어 Fed 정책 변화에 민감하게 대응해야 합니다.'
           if corr_val > 0.5
           else '유동성-주가 동조성이 약화된 구간입니다. '
                '기업실적, 지정학, 섹터 로테이션 등 유동성 외 변수가 주가를 주도하고 있어, '
                '펀더멘털 분석의 비중을 높일 필요가 있습니다.'
           if corr_val > 0
           else '음의 상관으로 전환된 특이 구간입니다. '
                '유동성이 증가하는데 주가가 하락하거나 그 반대 상황으로, '
                '시장이 유동성 외 강력한 악재(지정학, 신용 이벤트 등)에 반응하고 있음을 시사합니다.')
        + f'<br><br>'
        f'<strong>추세 변화:</strong> {corr_dir_text}<br><br>'
        f'<strong>선행/후행 분석:</strong> {liq_leads_market}<br><br>'
        f'<strong>투자 시사점:</strong> '
        + (f'상관계수 {corr_val:.2f} 환경에서 유동성 방향({liq_3m_chg:+.1f}%)이 곧 시장 방향입니다. '
           f'본원통화 증감률 변화를 선행 지표로 활용하세요.'
           if corr_val > 0.5
           else f'상관계수 {corr_val:.2f}로 유동성 외 요인이 지배적입니다. '
                f'실적 시즌, 정책 이벤트, 섹터별 모멘텀에 주목하세요.'
           if corr_val > 0
           else f'음의 상관({corr_val:.2f})은 시장 스트레스 또는 구조적 전환을 시사합니다. '
                f'포지션 축소 후 방향 확인을 권장합니다.')
    )

    # ── 글로벌 크로스에셋 모니터 (완전 동적) ──
    gold_p = _safe(cross, "gold")
    gold_chg = _safe(cross, "gold", "chg_1m")
    gold_high = _safe(cross, "gold", "chg_from_high")
    silver_p = _safe(cross, "silver")
    silver_chg = _safe(cross, "silver", "chg_1m")
    silver_high = _safe(cross, "silver", "chg_from_high")
    btc_p = _safe(cross, "btc")
    btc_chg = _safe(cross, "btc", "chg_1m")
    btc_high = _safe(cross, "btc", "chg_from_high")
    eth_p = _safe(cross, "eth")
    eth_chg = _safe(cross, "eth", "chg_1m")
    us10y_p = _safe(cross, "us10y")
    us10y_chg = _safe(cross, "us10y", "chg_1m")
    dxy_p = _safe(cross, "dxy")
    dxy_chg = _safe(cross, "dxy", "chg_1m")
    nikkei_p = _safe(cross, "nikkei")
    nikkei_chg = _safe(cross, "nikkei", "chg_1m")

    if country == "🇺🇸 미국":
        brief_cross = (
            f'<strong>▎글로벌 크로스에셋 모니터</strong><br>'
            f'• <strong>귀금속:</strong> 금 ${gold_p:,.0f}(1M {gold_chg:+.1f}%, 고점 대비 {gold_high:+.1f}%), '
            f'은 ${silver_p:,.1f}(1M {silver_chg:+.1f}%, 고점 대비 {silver_high:+.1f}%)<br>'
            f'• <strong>크립토:</strong> BTC ${btc_p:,.0f}(1M {btc_chg:+.1f}%, 고점 대비 {btc_high:+.1f}%), '
            f'ETH ${eth_p:,.0f}(1M {eth_chg:+.1f}%)<br>'
            f'• <strong>국채:</strong> 10년물 {us10y_p:.2f}%(1M {us10y_chg:+.2f}%p)'
            + (' → 금리 상승은 성장주에 부담' if us10y_chg > 0 else ' → 금리 하락은 성장주에 우호적') + '<br>'
            f'• <strong>달러:</strong> DXY {dxy_p:.1f}(1M {dxy_chg:+.1f}%)'
            + (' → 달러 강세는 신흥국·원자재에 압박' if dxy_chg > 0 else ' → 달러 약세는 위험자산에 우호적') + '<br>'
            f'• <strong>일본:</strong> 니케이 {nikkei_p:,.0f}(1M {nikkei_chg:+.1f}%)'
        )
    else:
        krw_p = _safe(cross, "krw")
        krw_chg_1m = _safe(cross, "krw", "chg_1m")
        brief_cross = (
            f'<strong>▎글로벌 크로스에셋 모니터</strong><br>'
            f'• <strong>환율:</strong> 원/달러 {krw_p:,.0f}원(1M {krw_chg_1m:+.1f}%)'
            + (' → 원화 약세 지속, 외국인 매도 압력 주의' if krw_chg_1m > 1
               else ' → 원화 강세 전환, 외국인 자금 유입 기대' if krw_chg_1m < -1
               else ' → 환율 안정, 중립적 환경') + '<br>'
            f'• <strong>귀금속:</strong> 금 ${gold_p:,.0f}(1M {gold_chg:+.1f}%, 고점 대비 {gold_high:+.1f}%), '
            f'은 ${silver_p:,.1f}(1M {silver_chg:+.1f}%)<br>'
            f'• <strong>크립토:</strong> BTC ${btc_p:,.0f}(1M {btc_chg:+.1f}%, 고점 대비 {btc_high:+.1f}%)<br>'
            f'• <strong>반도체:</strong> 글로벌 AI 수요 동향 → '
            + ('유동성 확장과 AI 투자 사이클이 반도체 섹터에 우호적입니다.' if liq_3m_chg > 0
               else '유동성 수축 환경에서 반도체 밸류에이션 부담이 존재합니다.') + '<br>'
            f'• <strong>일본:</strong> 니케이 {nikkei_p:,.0f}(1M {nikkei_chg:+.1f}%) → '
            + ('아시아 증시 전반 위험선호 회복 중' if nikkei_chg > 0 else '아시아 증시 위험회피 흐름')
        )

    # ── 수익률 곡선 분석 ──
    brief_yield_curve = generate_yield_curve_analysis(cross)

    # ── 섹터 로테이션 분석 (미국만) ──
    brief_sector_rotation = ""
    if country == "🇺🇸 미국":
        brief_sector_rotation = generate_sector_rotation_analysis(cross)

    # ── 원자재 분석 ──
    brief_commodity = generate_commodity_analysis(cross)

    # ── 시장 센티먼트 ──
    sentiment = compute_market_sentiment(cross, liq_yoy, liq_3m_chg, sp_1m_chg, sp_yoy, corr_val)
    brief_sentiment = (
        f'<strong>▎시장 센티먼트 종합 (Fear & Greed Index)</strong><br>'
        f'<div style="display:flex;align-items:center;gap:12px;margin:8px 0;">'
        f'<div style="font-size:2rem;font-weight:700;color:{sentiment["color"]}">{sentiment["score"]}</div>'
        f'<div>'
        f'<div style="font-weight:600;color:{sentiment["color"]}">{sentiment["label"]}</div>'
        f'<div style="font-size:0.8rem;color:var(--text-muted);">VIX·모멘텀·유동성·안전자산·신용·상관관계 7개 지표 종합</div>'
        f'</div></div>'
        f'<div style="background:linear-gradient(90deg, #991b1b, #dc2626, #ca8a04, #65a30d, #16a34a);'
        f'height:8px;border-radius:4px;position:relative;margin:4px 0 8px 0;">'
        f'<div style="position:absolute;left:{sentiment["score"]}%;top:-4px;width:3px;height:16px;'
        f'background:#1e293b;border-radius:2px;"></div></div>'
        + ('극도의 탐욕 구간은 역사적으로 조정이 임박했을 가능성을 시사합니다. 포지션 축소를 고려하세요.' if sentiment["score"] >= 75
           else '탐욕 구간이지만 추세 지속 가능성이 있습니다. 신규 진입 시 분할 매수 권장.' if sentiment["score"] >= 60
           else '중립적 환경으로 방향성 확인 후 대응하는 것이 유리합니다.' if sentiment["score"] >= 45
           else '공포 구간은 역사적으로 매수 기회가 되었습니다. 단, 추가 하락 가능성에 대비한 분할 매수 접근이 필요합니다.' if sentiment["score"] >= 30
           else '극도의 공포 구간입니다. 역발상 투자 관점에서 기회가 될 수 있으나, 시스템 리스크 확인이 선행되어야 합니다.')
    )

    # ── 신용 시장 모니터 ──
    hyg_chg = _safe(cross, "hyg", "chg_1m")
    hyg_3m = _safe(cross, "hyg", "chg_3m")
    tlt_chg = _safe(cross, "tlt", "chg_1m")
    tlt_3m = _safe(cross, "tlt", "chg_3m")
    brief_credit = (
        f'<strong>▎신용 시장 & 채권 모니터</strong><br>'
        f'• <strong>하이일드 채권(HYG):</strong> 1M {hyg_chg:+.1f}%, 3M {hyg_3m:+.1f}% → '
        + ('신용 스프레드 축소, 리스크 선호 유지' if hyg_chg > 0 else '신용 스프레드 확대 가능성, 위험 신호') + '<br>'
        f'• <strong>장기국채(TLT):</strong> 1M {tlt_chg:+.1f}%, 3M {tlt_3m:+.1f}% → '
        + ('장기채 가격 상승 = 금리 하락 기대 반영' if tlt_chg > 0 else '장기채 가격 하락 = 금리 상승/인플레이션 우려') + '<br><br>'
        + (f'<strong>시사점:</strong> 하이일드와 장기채가 동반 상승 → 골디락스(적정 성장 + 저금리) 환경에 대한 기대가 형성되어 있습니다.'
           if hyg_chg > 0 and tlt_chg > 0
           else f'<strong>시사점:</strong> 하이일드 상승·장기채 하락 → 경기 과열/인플레이션 환경으로 리스크 자산에는 우호적이나 금리 상승 부담이 존재합니다.'
           if hyg_chg > 0 and tlt_chg <= 0
           else f'<strong>시사점:</strong> 하이일드 하락·장기채 상승 → 경기침체 우려로 안전자산 선호가 나타나고 있습니다. 위험 자산 비중 축소를 고려하세요.'
           if hyg_chg <= 0 and tlt_chg > 0
           else f'<strong>시사점:</strong> 하이일드·장기채 동반 하락 → 유동성 위축 또는 포트폴리오 리밸런싱에 의한 매도 압력이 존재합니다.')
    )

    # ── 관련 뉴스 & 이슈 (내용 요약) ──
    brief_news = ""
    if news_data:
        news_lines = []
        for n in news_data[:8]:
            publisher = n.get("publisher", "")
            title = n.get("title", "")
            ticker_src = n.get("ticker", "")
            if title:
                # 뉴스 카테고리 판별
                category = ""
                if any(k in ticker_src for k in ["^GSPC", "^IXIC", "^DJI"]):
                    category = "미국 증시"
                elif "^KS11" in ticker_src:
                    category = "한국 증시"
                elif "GC=F" in ticker_src:
                    category = "귀금속"
                elif "BTC" in ticker_src:
                    category = "크립토"
                else:
                    category = "매크로"

                # 시장 영향도 추론
                impact = ""
                title_lower = title.lower()
                if any(w in title_lower for w in ["surge", "soar", "rally", "jump", "bull", "record", "high", "상승", "급등", "신고"]):
                    impact = '<span style="color:var(--accent-green);font-weight:600;">▲ 긍정적</span>'
                elif any(w in title_lower for w in ["fall", "drop", "crash", "plunge", "bear", "sell", "fear", "하락", "급락", "폭락", "위기"]):
                    impact = '<span style="color:var(--accent-red);font-weight:600;">▼ 부정적</span>'
                elif any(w in title_lower for w in ["fed", "rate", "inflation", "tariff", "금리", "인플레", "관세"]):
                    impact = '<span style="color:var(--accent-amber);font-weight:600;">◆ 정책 변수</span>'
                else:
                    impact = '<span style="color:var(--text-muted);font-weight:600;">— 중립</span>'

                news_lines.append(
                    f'<div style="margin-bottom:6px;padding:6px 8px;background:rgba(0,0,0,0.02);border-radius:6px;">'
                    f'<span style="font-size:0.68rem;color:var(--accent-blue);font-weight:700;">[{category}]</span> '
                    f'<strong>{title}</strong><br>'
                    f'<span style="font-size:0.76rem;color:var(--text-muted);">{publisher} · {impact}</span>'
                    f'</div>'
                )
        if news_lines:
            brief_news = (
                f'<strong>▎관련 뉴스 & 이슈 요약</strong><br>'
                f'<div style="margin-top:6px;">'
                + ''.join(news_lines)
                + '</div>'
            )

    # ── 유동성 레짐 & 시장 단계 분석 ──
    # 유동성 레짐 판별 (4단계)
    if liq_3m_chg > 2 and liq_1m_chg > 0:
        liq_regime = "적극적 확장 (Active Expansion)"
        regime_color = "#16a34a"
        regime_desc = (
            "본원통화가 가속적으로 증가하고 있습니다. "
            "이 레짐에서 주식·크립토·원자재 등 위험자산은 역사적으로 강한 상승세를 보였습니다. "
            "2020년 하반기, 2023년 Q4가 대표적 사례입니다."
        )
        regime_strategy = "위험자산 비중 확대, 성장주·소형주 선호, 채권 듀레이션 축소"
    elif liq_3m_chg > 0 and liq_1m_chg >= -0.5:
        liq_regime = "완만한 확장 (Moderate Expansion)"
        regime_color = "#65a30d"
        regime_desc = (
            "유동성이 점진적으로 증가하고 있습니다. "
            "시장에 우호적이나 폭발적 상승보다는 안정적 우상향을 기대할 수 있습니다. "
            "선별적 위험자산 배분이 유효합니다."
        )
        regime_strategy = "균형 포트폴리오 유지, 퀄리티 성장주 중심, 분할 매수 접근"
    elif liq_3m_chg > -2 and liq_3m_chg <= 0:
        liq_regime = "보합/초기 수축 (Neutral/Early Contraction)"
        regime_color = "#ca8a04"
        regime_desc = (
            "유동성이 보합 또는 초기 수축 단계에 있습니다. "
            "이 구간은 시장 방향성이 불투명하며, 유동성 외 요인(실적·정책)에 민감하게 반응합니다. "
            "변동성 확대에 대비한 포지션 관리가 핵심입니다."
        )
        regime_strategy = "방어적 자산 비중 상향, 현금 비중 확대, 헤지 전략 고려"
    else:
        liq_regime = "적극적 수축 (Active Contraction)"
        regime_color = "#dc2626"
        regime_desc = (
            "본원통화가 뚜렷하게 감소하고 있습니다. "
            "이 레짐에서 위험자산은 역사적으로 큰 조정을 겪었습니다 (2022년 QT 시기). "
            "유동성 방향 전환 신호가 나올 때까지 보수적 운용이 필요합니다."
        )
        regime_strategy = "현금·단기채 비중 극대화, 위험자산 최소화, 역발상 매수는 유동성 전환 확인 후"

    # 유동성-지수 괴리도 (Divergence Score)
    liq_norm_latest = df["Liquidity_norm"].iloc[-1] if "Liquidity_norm" in df.columns else 50
    sp_norm_latest = df["SP500_norm"].iloc[-1] if "SP500_norm" in df.columns else 50
    divergence = sp_norm_latest - liq_norm_latest
    div_comment = ""
    if divergence > 20:
        div_comment = f"주가가 유동성 대비 <strong>과열 상태</strong>(괴리도 {divergence:+.1f}pt)입니다. 유동성 대비 주가가 높아 조정 가능성에 유의하세요."
    elif divergence > 10:
        div_comment = f"주가가 유동성보다 <strong>다소 앞서</strong> 있습니다(괴리도 {divergence:+.1f}pt). 실적 확인을 통한 정당화가 필요합니다."
    elif divergence < -20:
        div_comment = f"주가가 유동성 대비 <strong>과도하게 할인</strong> 상태(괴리도 {divergence:+.1f}pt)입니다. 유동성이 지지하는 가격 대비 저평가 구간으로, 매수 기회일 수 있습니다."
    elif divergence < -10:
        div_comment = f"주가가 유동성보다 <strong>다소 뒤처져</strong> 있습니다(괴리도 {divergence:+.1f}pt). 유동성 지지 수준으로의 회귀를 기대할 수 있습니다."
    else:
        div_comment = f"주가와 유동성이 <strong>균형 상태</strong>(괴리도 {divergence:+.1f}pt)입니다. 유동성 수준에 맞는 적정 가격대입니다."

    brief_regime = (
        f'<strong>▎유동성 레짐 & 시장 단계 분석</strong><br>'
        f'<div style="display:inline-flex;align-items:center;gap:8px;margin:6px 0;">'
        f'<span style="background:{regime_color};color:white;padding:4px 12px;border-radius:6px;'
        f'font-size:0.82rem;font-weight:700;">{liq_regime}</span></div><br><br>'
        f'{regime_desc}<br><br>'
        f'<strong>전략적 대응:</strong> {regime_strategy}<br><br>'
        f'<strong>유동성-지수 괴리도:</strong> {div_comment}'
    )

    return (brief_policy, brief_liq, brief_market, brief_corr, brief_cross,
            brief_yield_curve, brief_sector_rotation, brief_commodity,
            brief_sentiment, brief_credit, brief_news, brief_regime)


def generate_dynamic_advice(country, bullish_count, bearish_count, liq_3m_chg, corr_val, sp_1m_chg,
                            sp_yoy, liq_yoy, cross, sp_val, idx_name, sentiment_data=None):
    """Investment Advice를 실시간 데이터 기반으로 동적 생성 (포트폴리오 배분, 확신도, 역사적 맥락 포함)"""

    if bullish_count >= 3:
        adv_stance = "비중 확대 (Overweight)"
        adv_stance_color = "var(--accent-green)"
        adv_icon = "🟢"
    elif bearish_count >= 2:
        adv_stance = "비중 축소 (Underweight)"
        adv_stance_color = "var(--accent-red)"
        adv_icon = "🔴"
    else:
        adv_stance = "중립 (Neutral)"
        adv_stance_color = "var(--accent-amber)"
        adv_icon = "🟡"

    vix_price = _safe(cross, "vix")
    us10y_p = _safe(cross, "us10y")
    btc_chg = _safe(cross, "btc", "chg_1m")
    gold_chg = _safe(cross, "gold", "chg_1m")
    russell_ytd = _safe(cross, "russell", "chg_ytd")
    dow_ytd = _safe(cross, "dow", "chg_ytd")
    dxy_chg = _safe(cross, "dxy", "chg_1m")

    if country == "🇺🇸 미국":
        # 섹터 전략 - 시장 조건 기반 동적 생성
        sector_ai = (
            f'• <strong>AI/반도체('
            + ("비중확대" if liq_3m_chg > 0 and sp_1m_chg > -3 else "중립") + '):</strong> '
            + ('유동성 확장 + 시장 모멘텀이 AI CapEx 사이클을 지지합니다. ' if liq_3m_chg > 0 and sp_1m_chg > 0
               else '유동성 환경은 우호적이나 시장 모멘텀 둔화로 선별적 접근이 필요합니다. ' if liq_3m_chg > 0
               else '유동성 수축 환경에서 고밸류 성장주 부담이 존재합니다. ')
            + (f'10년물 금리 {us10y_p:.2f}%' + ('는 성장주에 부담 요인입니다.' if us10y_p > 4.5 else '는 아직 성장주에 감내 가능한 수준입니다.') if cross and cross.get("us10y") else '')
        )

        sector_cyclical = (
            f'• <strong>경기순환주('
            + ("비중확대" if dow_ytd > 0 and liq_3m_chg > 0 else "중립") + '):</strong> '
            + (f'다우 YTD {dow_ytd:+.1f}% → ' if cross and cross.get("dow") else '')
            + ('경기순환주 로테이션이 진행 중입니다. 은행·산업재·헬스케어 관심.' if dow_ytd > 0
               else '경기순환주 모멘텀이 약화되고 있어 방어적 접근이 필요합니다.')
        )

        sector_small = (
            f'• <strong>소형주('
            + ("관심" if russell_ytd > 0 else "중립") + '):</strong> '
            + (f'Russell 2000 YTD {russell_ytd:+.1f}%. ' if cross and cross.get("russell") else '')
            + ('금리 인하 기대 시 소형주 추가 상승 여력이 있습니다.' if us10y_p < 4.5 and russell_ytd > 0
               else '금리 부담 속에서 소형주 모멘텀이 제한적입니다.' if us10y_p >= 4.5
               else '소형주 시장 흐름을 면밀히 관찰할 필요가 있습니다.')
        )

        sector_defense = (
            f'• <strong>방어주('
            + ("일부 편입" if vix_price > 20 or sp_1m_chg < -3 else "축소") + '):</strong> '
            + (f'VIX {vix_price:.1f} → ' if cross and cross.get("vix") else '')
            + ('변동성 확대 구간으로 배당·유틸리티 헤지 권장.' if vix_price > 20
               else '변동성이 낮아 방어주 비중을 줄이고 공격적 포지션이 유리합니다.')
        )

        # 리스크 관리 - 동적 생성
        risks = []
        if us10y_p > 4.5:
            risks.append(f'• 금리 리스크: 10년물 {us10y_p:.2f}%로 고금리 지속 → 밸류에이션 멀티플 수축 위험')
        if sp_yoy > 20:
            risks.append(f'• 밸류에이션: {idx_name} YoY {sp_yoy:+.1f}% 급등 후 → 차익실현 압력 상존')
        if vix_price > 25:
            risks.append(f'• 변동성: VIX {vix_price:.1f}로 불안 구간 → 급격한 포지션 조정 가능')
        if btc_chg < -20:
            risks.append(f'• 크립토 연쇄 청산: BTC 1개월 {btc_chg:+.1f}% → 레버리지 해소가 주식시장 전이 가능')
        if dxy_chg > 3:
            risks.append(f'• 달러 강세: DXY 1개월 {dxy_chg:+.1f}% → 다국적 기업 실적 및 신흥국 부담')
        if not risks:
            risks.append('• 현재 주요 리스크 지표는 안정적 수준입니다. 다만 급변 가능성에 대비한 포지션 관리가 필요합니다.')

        # 포트폴리오 배분 추천 (미국)
        if bullish_count >= 3:
            eq_pct, bond_pct, cash_pct, alt_pct = 70, 15, 5, 10
        elif bearish_count >= 2:
            eq_pct, bond_pct, cash_pct, alt_pct = 35, 35, 20, 10
        else:
            eq_pct, bond_pct, cash_pct, alt_pct = 55, 25, 10, 10

        portfolio_alloc = (
            f'<strong>▎추천 포트폴리오 배분</strong><br>'
            f'<div style="display:flex;gap:8px;margin:6px 0;">'
            f'<div style="flex:{eq_pct};background:#3b82f6;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">주식 {eq_pct}%</div>'
            f'<div style="flex:{bond_pct};background:#10b981;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">채권 {bond_pct}%</div>'
            f'<div style="flex:{cash_pct};background:#94a3b8;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">현금 {cash_pct}%</div>'
            f'<div style="flex:{alt_pct};background:#f59e0b;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">대체 {alt_pct}%</div>'
            f'</div>'
            f'주식 내: 성장주 {60 if liq_3m_chg > 0 else 40}% / 가치주 {40 if liq_3m_chg > 0 else 60}% | '
            f'대체자산: 금·원자재·크립토 분산'
        )

        # 확신도 (Conviction Level)
        conviction = min(5, bullish_count + (1 if liq_yoy > 2 else 0) + (1 if sp_1m_chg > 3 else 0))
        if bearish_count >= 2:
            conviction = max(1, 5 - bearish_count - (1 if vix_price > 25 else 0))
        conviction_stars = "★" * conviction + "☆" * (5 - conviction)
        conviction_desc = ["매우 낮음", "낮음", "보통", "높음", "매우 높음"][min(conviction, 4)]

        # 핵심 트리거
        triggers = []
        if us10y_p > 4.0:
            triggers.append(f'10Y 금리 {us10y_p:.2f}% → 4.0% 하회 시 성장주 비중 확대 신호')
        if vix_price > 20:
            triggers.append(f'VIX {vix_price:.1f} → 20 하회 시 포지션 확대 가능')
        elif vix_price < 15:
            triggers.append(f'VIX {vix_price:.1f} → 급등 시 빠른 헤지 필요')
        if liq_3m_chg < 0:
            triggers.append(f'유동성 3M {liq_3m_chg:+.1f}% → 플러스 전환 시 매수 신호')
        if sp_1m_chg > 5:
            triggers.append(f'{idx_name} 1M {sp_1m_chg:+.1f}% 급등 → RSI 과매수 구간 진입 주의')
        if not triggers:
            triggers.append('현재 주요 트리거 이벤트가 없는 안정적 구간입니다. 기존 포지션 유지 권장.')

        # 역사적 유사 환경 분석
        historical = ""
        if liq_3m_chg > 2 and sp_1m_chg > 3:
            historical = "유동성 확장 + 주가 상승 동시 진행은 2020년 하반기, 2023년 말과 유사한 패턴입니다. 이후 수개월간 강세가 이어졌으나, 밸류에이션 부담이 수반되었습니다."
        elif liq_3m_chg < -1 and sp_1m_chg < -3:
            historical = "유동성 수축 + 주가 하락 동시 진행은 2022년 상반기와 유사합니다. 해당 시기 바닥 형성까지 추가 3~6개월이 소요되었습니다."
        elif liq_3m_chg > 0 and sp_1m_chg < 0:
            historical = "유동성 확장 중 주가 조정은 2023년 8~10월 패턴과 유사합니다. 유동성 지지 속 조정은 매수 기회로 작용한 사례가 많습니다."
        elif liq_3m_chg < 0 and sp_1m_chg > 0:
            historical = "유동성 수축에도 주가 상승은 실적 주도 장세를 의미합니다. 다만 유동성 역풍이 지속되면 결국 조정 압력이 가해지는 경향이 있습니다."
        else:
            historical = "현재 혼합적 환경으로, 명확한 방향성보다는 선별적 섹터 접근이 유효한 구간입니다."

        adv_body = (
            f'<strong>▎포지션 전략: <span style="color:{adv_stance_color}">{adv_icon} {adv_stance}</span></strong>'
            f'&nbsp;&nbsp;<span style="font-size:0.85rem;">확신도: <span style="color:#f59e0b;">{conviction_stars}</span> ({conviction_desc})</span><br>'
            f'유동성 {liq_3m_chg:+.1f}%(3M), 상관계수 {corr_val:.2f}, 시장 모멘텀 {sp_1m_chg:+.1f}%(1M) 종합 판단.<br><br>'
            f'{portfolio_alloc}<br><br>'
            f'<strong>▎섹터별 전략</strong><br>'
            f'{sector_ai}<br>'
            f'{sector_cyclical}<br>'
            f'{sector_small}<br>'
            f'{sector_defense}<br><br>'
            f'<strong>▎리스크 관리</strong><br>'
            + '<br>'.join(risks) + '<br><br>'
            f'<strong>▎주요 트리거 & 모니터링 포인트</strong><br>'
            + '<br>'.join([f'• {t}' for t in triggers]) + '<br><br>'
            f'<strong>▎역사적 유사 환경 분석</strong><br>'
            f'{historical}'
        )
    else:  # 한국
        krw_p = _safe(cross, "krw")
        krw_chg_1m = _safe(cross, "krw", "chg_1m")
        nikkei_chg = _safe(cross, "nikkei", "chg_1m")

        sector_semi = (
            f'• <strong>반도체('
            + ("핵심 비중확대" if liq_3m_chg > 0 and sp_1m_chg > -5 else "선별적") + '):</strong> '
            + ('글로벌 유동성 확장과 AI 수요 사이클이 메모리 반도체 섹터를 지지합니다.'
               if liq_3m_chg > 0 else
               '유동성 수축 환경이지만 AI 구조적 수요가 반도체 섹터를 지탱합니다.')
        )

        sector_defense_kr = (
            f'• <strong>방산·조선('
            + ("비중확대" if sp_1m_chg > 0 else "중립") + '):</strong> '
            + ('글로벌 방산 수주 호조와 시장 모멘텀이 긍정적입니다.'
               if sp_1m_chg > 0 else
               '방산 펀더멘털은 양호하나 시장 전반의 약세에 유의해야 합니다.')
        )

        sector_battery = (
            f'• <strong>2차전지(중립):</strong> '
            f'글로벌 정책 불확실성 속에서 선별적 접근이 필요합니다.'
        )

        sector_fin = (
            f'• <strong>금융('
            + ("비중확대" if sp_1m_chg > 0 else "중립") + '):</strong> '
            + ('밸류업 프로그램 수혜와 배당 확대 기조가 긍정적입니다. 저PBR 은행주 관심.'
               if sp_1m_chg > -3 else
               '시장 약세 속 방어적 성격의 금융주가 상대적으로 견조할 수 있습니다.')
        )

        risks = []
        if sp_1m_chg > 10:
            risks.append(f'• 과열 경고: {idx_name} 1개월 {sp_1m_chg:+.1f}% 급등 → 단기 차익실현 압력 주의')
        if krw_p > 1400:
            risks.append(f'• 환율: 원/달러 {krw_p:,.0f}원 → 달러 강세 심화 시 외국인 매도 압력 가중')
        elif krw_p > 1300:
            risks.append(f'• 환율: 원/달러 {krw_p:,.0f}원 → 환율 변동성에 대비한 환헤지 고려')
        if vix_price > 25:
            risks.append(f'• 글로벌 변동성: VIX {vix_price:.1f} → 외국인 위험회피 시 한국 증시 민감 반응')
        if btc_chg < -20:
            risks.append(f'• 크립토 하락: BTC 1개월 {btc_chg:+.1f}% → 개인투자자 심리 위축 가능')
        if liq_3m_chg < -1:
            risks.append(f'• 유동성 수축: 글로벌 유동성 3개월 {liq_3m_chg:+.1f}% → 신흥국 자금유출 압력')
        if not risks:
            risks.append('• 현재 주요 리스크 지표는 안정적 수준입니다. 다만 글로벌 변수에 대한 모니터링을 지속하세요.')

        # 포트폴리오 배분 추천 (한국)
        if bullish_count >= 3:
            eq_pct, bond_pct, cash_pct, alt_pct = 65, 15, 10, 10
        elif bearish_count >= 2:
            eq_pct, bond_pct, cash_pct, alt_pct = 30, 35, 25, 10
        else:
            eq_pct, bond_pct, cash_pct, alt_pct = 50, 25, 15, 10

        portfolio_alloc = (
            f'<strong>▎추천 포트폴리오 배분</strong><br>'
            f'<div style="display:flex;gap:8px;margin:6px 0;">'
            f'<div style="flex:{eq_pct};background:#3b82f6;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">주식 {eq_pct}%</div>'
            f'<div style="flex:{bond_pct};background:#10b981;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">채권 {bond_pct}%</div>'
            f'<div style="flex:{cash_pct};background:#94a3b8;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">현금 {cash_pct}%</div>'
            f'<div style="flex:{alt_pct};background:#f59e0b;color:white;text-align:center;padding:6px;border-radius:4px;font-size:0.8rem;">대체 {alt_pct}%</div>'
            f'</div>'
            f'주식 내: 대형주 {60 if sp_1m_chg > 0 else 70}% / 중소형주 {40 if sp_1m_chg > 0 else 30}% | '
            f'달러 헤지 비율: {70 if krw_p > 1350 else 50 if krw_p > 1250 else 30}% 권장'
        )

        # 확신도
        conviction = min(5, bullish_count + (1 if liq_yoy > 2 else 0) + (1 if sp_1m_chg > 3 else 0))
        if bearish_count >= 2:
            conviction = max(1, 5 - bearish_count - (1 if krw_p > 1400 else 0))
        conviction_stars = "★" * conviction + "☆" * (5 - conviction)
        conviction_desc = ["매우 낮음", "낮음", "보통", "높음", "매우 높음"][min(conviction, 4)]

        # 핵심 트리거 (한국)
        triggers = []
        if krw_p > 1350:
            triggers.append(f'환율 {krw_p:,.0f}원 → 1,300원 하회 시 외국인 매수 유입 가속 기대')
        if liq_3m_chg < 0:
            triggers.append(f'글로벌 유동성 3M {liq_3m_chg:+.1f}% → 플러스 전환 시 신흥국 자금 유입 기대')
        if vix_price > 20:
            triggers.append(f'VIX {vix_price:.1f} → 20 하회 시 외국인 위험선호 복원 가능')
        if sp_1m_chg > 5:
            triggers.append(f'{idx_name} 1M {sp_1m_chg:+.1f}% 급등 → 단기 과열 후 외국인 차익실현 주의')
        if nikkei_chg > 5:
            triggers.append(f'니케이 1M {nikkei_chg:+.1f}% → 아시아 자금 흐름 변화 모니터링')
        if not triggers:
            triggers.append('현재 주요 트리거 이벤트가 없는 안정적 구간입니다. 기존 포지션 유지 권장.')

        # 역사적 유사 환경 (한국)
        historical = ""
        if liq_3m_chg > 0 and sp_1m_chg > 3 and krw_p < 1300:
            historical = "유동성 확장 + 원화 강세 + 주가 상승은 2021년 상반기와 유사합니다. 외국인 순매수 지속 가능성이 높은 환경입니다."
        elif liq_3m_chg < -1 and krw_p > 1350:
            historical = "유동성 수축 + 원화 약세는 2022년 환경과 유사합니다. 외국인 매도가 지속될 수 있어 방어적 포지셔닝이 필요합니다."
        elif sp_1m_chg < -5:
            historical = "급격한 시장 하락 후에는 2020년 3월, 2022년 10월처럼 정책 대응이 촉발되는 경향이 있습니다. 낙폭 과대 우량주에 주목하세요."
        else:
            historical = "현재 한국 증시는 글로벌 유동성, 환율, 외국인 수급의 삼각 함수로 움직이고 있습니다. 방향성 확인 후 단계적 접근이 유효합니다."

        adv_body = (
            f'<strong>▎포지션 전략: <span style="color:{adv_stance_color}">{adv_icon} {adv_stance}</span></strong>'
            f'&nbsp;&nbsp;<span style="font-size:0.85rem;">확신도: <span style="color:#f59e0b;">{conviction_stars}</span> ({conviction_desc})</span><br>'
            f'글로벌 유동성 {liq_3m_chg:+.1f}%(3M), 상관계수 {corr_val:.2f}, 시장 모멘텀 {sp_1m_chg:+.1f}%(1M) 종합 판단.<br><br>'
            f'{portfolio_alloc}<br><br>'
            f'<strong>▎섹터별 전략</strong><br>'
            f'{sector_semi}<br>'
            f'{sector_defense_kr}<br>'
            f'{sector_battery}<br>'
            f'{sector_fin}<br><br>'
            f'<strong>▎리스크 관리</strong><br>'
            + '<br>'.join(risks) + '<br><br>'
            f'<strong>▎주요 트리거 & 모니터링 포인트</strong><br>'
            + '<br>'.join([f'• {t}' for t in triggers]) + '<br><br>'
            f'<strong>▎역사적 유사 환경 분석</strong><br>'
            f'{historical}'
        )

    return adv_body


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 차트 헬퍼
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C = {
    "liq": "#3b82f6", "liq_fill": "rgba(59,130,246,0.06)",
    "sp": "#ef4444", "sp_fill": "rgba(239,68,68,0.04)",
    "corr_pos": "#10b981", "corr_neg": "#ef4444",
    "grid": "rgba(226,232,240,0.6)", "bg": "#ffffff", "paper": "#f8fafc",
    "event": "rgba(148,163,184,0.25)", "rec": "rgba(239,68,68,0.04)",
}
BASE_LAYOUT = dict(
    plot_bgcolor=C["bg"], paper_bgcolor=C["paper"],
    font=dict(family="Pretendard, sans-serif", color="#475569", size=12),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font=dict(color="#1e293b", size=12)),
    # ★ 수정: 상단 여백(t)을 60px로 늘려 툴바 공간 확보
    margin=dict(t=60, b=30, l=40, r=10), dragmode="pan",
)

def add_events_to_fig(fig, dff, events, has_rows=False, min_gap_days=30):
    """이벤트를 차트에 추가. min_gap_days로 최소 간격 제어하여 겹침 방지"""
    prev_dt = None
    for date_str, title, _, emoji, direction in events:
        dt = pd.to_datetime(date_str)
        if dt < dff.index.min() or dt > dff.index.max():
            continue
        # 최소 간격 필터: 이전 이벤트와 너무 가까우면 스킵
        if prev_dt and (dt - prev_dt).days < min_gap_days:
            continue
        prev_dt = dt
        kw = dict(row="all", col=1) if has_rows else {}
        fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color=C["event"], **kw)
        clr = "#10b981" if direction == "up" else "#ef4444"
        fig.add_annotation(x=dt, y=1.04, yref="paper", text=f"{emoji} {title}",
            showarrow=False, font=dict(size=11, color=clr), textangle=-38, xanchor="left")

def add_recession(fig, dff, has_rows=False):
    rec_idx = dff[dff["Recession"] == 1].index
    if rec_idx.empty:
        return
    groups, start = [], rec_idx[0]
    for i in range(1, len(rec_idx)):
        if (rec_idx[i] - rec_idx[i - 1]).days > 5:
            groups.append((start, rec_idx[i - 1])); start = rec_idx[i]
    groups.append((start, rec_idx[-1]))
    for s, e in groups:
        kw = dict(row="all", col=1) if has_rows else {}
        fig.add_vrect(x0=s, x1=e, fillcolor=C["rec"], layer="below", line_width=0, **kw)

def ax(extra=None):
    d = dict(gridcolor=C["grid"], linecolor="#e2e8f0", tickfont=dict(size=10), showgrid=True, zeroline=False)
    if extra: d.update(extra)
    return d


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헤더
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<a href="#main-content" class="skip-link">본문으로 건너뛰기</a>
<header role="banner">
<div class="page-header">
    <div class="page-header-icon" aria-hidden="true">📊</div>
    <h1 class="page-title">유동성 × 시장 분석기</h1>
</div>
<p class="page-desc">
    중앙은행 통화량과 주가지수의 상관관계를 분석합니다.<br>
    유동성 흐름이 주가에 미치는 영향을 시각적으로 확인하세요.
</p>
</header>
<div id="main-content"></div>
""", unsafe_allow_html=True)

# 새로고침 상태 바
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
next_str = NEXT_REFRESH_TIME.strftime("%H:%M:%S KST")
st.markdown(
    f'<div class="refresh-bar" role="status" aria-live="polite" aria-label="실시간 갱신 상태">'
    f'<span class="refresh-dot" aria-hidden="true"></span>'
    f'<span>실시간 갱신: <time datetime="{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}">{now_str}</time> · 다음 업데이트: {next_str} (5분 간격)</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 레이아웃 컨테이너 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
kpi_container = st.container()
brief_container = st.container()
st.write("") # 간격

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 통합 컨트롤 바 (국가 · 지수 · 기간 · 봉주기 · 이벤트)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1, 1])
with ctrl1:
    country = st.selectbox("🌍 국가", list(COUNTRY_CONFIG.keys()), index=0)
CC = COUNTRY_CONFIG[country]
IDX_OPTIONS = CC["indices"]

# 국가 변경 시 지수 키 초기화
if st.session_state.get("_prev_country") != country:
    st.session_state["_prev_country"] = country
    st.session_state["idx_select"] = list(IDX_OPTIONS.keys())[CC["default_idx"]]

with ctrl2:
    idx_name = st.selectbox("📈 지수", list(IDX_OPTIONS.keys()), key="idx_select")
    idx_ticker = IDX_OPTIONS[idx_name]
with ctrl3:
    period = st.selectbox("📅 기간", ["3년", "5년", "7년", "10년", "전체"], index=3)
with ctrl4:
    tf = st.selectbox("🕯️ 봉", ["일봉", "주봉", "월봉"], index=1, key="candle_tf")
with ctrl5:
    show_events = st.toggle("📌 이벤트", value=False)

period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 27}
period_years = period_map[period]
cutoff = datetime.now() - timedelta(days=365 * period_years)

with st.spinner(f"{CC['liq_label']} & {idx_name} 데이터를 불러오는 중..."):
    df, ohlc_raw = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])
    cross_data = load_cross_asset_data()
    fed_rate_data = load_fed_funds_rate()
    bok_rate_data = load_bok_base_rate()
    news_data = load_market_news()

if df is None or df.empty:
    st.error("데이터를 불러올 수 없습니다. 잠시 후 새로고침 해주세요.")
    st.stop()

ALL_EVENTS = sorted(CC["events"], key=lambda x: x[0])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with kpi_container:
    latest = df.dropna(subset=["Liquidity", "SP500"]).iloc[-1]
    liq_val = latest["Liquidity"]
    sp_val = latest["SP500"]
    liq_yoy = latest["Liq_YoY"] if pd.notna(latest.get("Liq_YoY")) else 0
    sp_yoy = latest["SP_YoY"] if pd.notna(latest.get("SP_YoY")) else 0
    corr_val = df["Corr_90d"].dropna().iloc[-1] if len(df["Corr_90d"].dropna()) > 0 else 0

    def delta_html(val):
        cls = "up" if val >= 0 else "down"
        arrow = "▲" if val >= 0 else "▼"
        direction = "상승" if val >= 0 else "하락"
        return f'<div class="kpi-delta {cls}" aria-label="전년 대비 {val:+.1f}% {direction}">{arrow} YoY {val:+.1f}%</div>'

    corr_cls = "up" if corr_val >= 0.3 else "down"
    corr_desc = "강한 양의 상관" if corr_val >= 0.5 else ("약한 양의 상관" if corr_val >= 0 else "음의 상관")

    liq_display = f"{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}"

    st.markdown(f"""
    <section aria-label="핵심 지표 요약">
    <h2 class="sr-only">핵심 지표 (KPI)</h2>
    <div class="kpi-grid" role="list">
        <div class="kpi blue" role="listitem" aria-label="{CC['liq_label']}: {liq_display}, 전년 대비 {liq_yoy:+.1f}%">
            <div class="kpi-label"><span aria-hidden="true">💵</span> {CC['liq_label']}</div>
            <div class="kpi-value">{liq_display}</div>
            {delta_html(liq_yoy)}
        </div>
        <div class="kpi red" role="listitem" aria-label="{idx_name}: {sp_val:,.0f}, 전년 대비 {sp_yoy:+.1f}%">
            <div class="kpi-label"><span aria-hidden="true">📈</span> {idx_name}</div>
            <div class="kpi-value">{sp_val:,.0f}</div>
            {delta_html(sp_yoy)}
        </div>
        <div class="kpi green" role="listitem" aria-label="90일 상관계수: {corr_val:.3f}, {corr_desc}">
            <div class="kpi-label"><span aria-hidden="true">🔗</span> 90일 상관계수</div>
            <div class="kpi-value">{corr_val:.3f}</div>
            <div class="kpi-delta {corr_cls}">{corr_desc}</div>
        </div>
        <div class="kpi purple" role="listitem" aria-label="데이터 범위: {df.index.min().strftime('%Y.%m')}부터 {df.index.max().strftime('%Y.%m')}까지, 총 {len(df):,}일">
            <div class="kpi-label"><span aria-hidden="true">📅</span> 데이터 범위</div>
            <div class="kpi-value" style="font-size:1.05rem">{df.index.min().strftime('%Y.%m')} – {df.index.max().strftime('%Y.%m')}</div>
            <div class="kpi-delta up">{len(df):,}일</div>
        </div>
    </div>
    </section>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Daily Brief (실시간 데이터 기반 동적 생성)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with brief_container:
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    liq_3m = df["Liquidity"].dropna()
    liq_3m_chg = ((liq_3m.iloc[-1] - liq_3m.iloc[-63]) / liq_3m.iloc[-63] * 100) if len(liq_3m) > 63 else 0
    liq_6m = df["Liquidity"].dropna()
    liq_6m_chg = ((liq_6m.iloc[-1] - liq_6m.iloc[-126]) / liq_6m.iloc[-126] * 100) if len(liq_6m) > 126 else 0
    sp_1m = df["SP500"].dropna()
    sp_1m_chg = ((sp_1m.iloc[-1] - sp_1m.iloc[-21]) / sp_1m.iloc[-21] * 100) if len(sp_1m) > 21 else 0
    sp_3m = df["SP500"].dropna()
    sp_3m_chg = ((sp_3m.iloc[-1] - sp_3m.iloc[-63]) / sp_3m.iloc[-63] * 100) if len(sp_3m) > 63 else 0
    sp_1w = df["SP500"].dropna()
    sp_1w_chg = ((sp_1w.iloc[-1] - sp_1w.iloc[-5]) / sp_1w.iloc[-5] * 100) if len(sp_1w) > 5 else 0

    # 추가 지표: 유동성 모멘텀 (단기 vs 장기)
    liq_1m_chg = ((liq_3m.iloc[-1] - liq_3m.iloc[-21]) / liq_3m.iloc[-21] * 100) if len(liq_3m) > 21 else 0

    # 시그널 판정 (다층 분석)
    bullish_count = 0
    bearish_count = 0
    if corr_val > 0.5: bullish_count += 1
    elif corr_val < 0: bearish_count += 1
    if liq_3m_chg > 0: bullish_count += 1
    elif liq_3m_chg < -1: bearish_count += 1
    if sp_1m_chg > 0: bullish_count += 1
    elif sp_1m_chg < -3: bearish_count += 1
    if liq_yoy > 0: bullish_count += 1
    elif liq_yoy < -2: bearish_count += 1

    if bullish_count >= 3:
        signal_class, signal_text = "signal-bullish", "🟢 유동성 확장 + 강한 상관 + 시장 모멘텀 → 상승 추세 지지"
    elif bearish_count >= 2:
        signal_class, signal_text = "signal-bearish", "🔴 유동성 수축 또는 상관 이탈 → 하방 리스크 경계"
    else:
        signal_class, signal_text = "signal-neutral", "🟡 혼합 시그널 → 방향성 모색 중, 변동성 확대 주의"

    # 동적 Daily Brief 생성 (확장판)
    (brief_policy, brief_liq, brief_market, brief_corr, brief_cross,
     brief_yield_curve, brief_sector_rotation, brief_commodity,
     brief_sentiment, brief_credit, brief_news, brief_regime) = generate_dynamic_brief(
        country, df, liq_display, liq_yoy, liq_1m_chg, liq_3m_chg, liq_6m_chg,
        sp_val, sp_1w_chg, sp_1m_chg, sp_3m_chg, sp_yoy, corr_val,
        idx_name, cross_data, fed_rate_data, bok_rate_data, news_data
    )

    # 센티먼트 데이터 (Advice에서도 활용)
    sentiment_data = compute_market_sentiment(cross_data, liq_yoy, liq_3m_chg, sp_1m_chg, sp_yoy, corr_val)

    # 종합 시그널 생성 + 확장된 Daily Brief
    brief_extra_sections = ""
    if brief_regime:
        brief_extra_sections += f'<hr class="report-divider">{brief_regime}'
    if brief_sentiment:
        brief_extra_sections += f'<hr class="report-divider">{brief_sentiment}'
    if brief_yield_curve:
        brief_extra_sections += f'<hr class="report-divider">{brief_yield_curve}'
    if brief_credit:
        brief_extra_sections += f'<hr class="report-divider">{brief_credit}'
    if brief_sector_rotation:
        brief_extra_sections += f'<hr class="report-divider">{brief_sector_rotation}'
    if brief_commodity:
        brief_extra_sections += f'<hr class="report-divider">{brief_commodity}'
    if brief_news:
        brief_extra_sections += f'<hr class="report-divider">{brief_news}'

    st.markdown(
        f'<article role="article" aria-label="일일 시장 브리핑">'
        f'<div class="report-box">'
        f'<div class="report-header">'
        f'<span class="report-badge">Daily Brief</span>'
        f'<time class="report-date" datetime="{datetime.now().strftime("%Y-%m-%dT%H:%M")}">{today_str} {datetime.now().strftime("%H:%M")} 기준 · 5분 간격 실시간 갱신</time></div>'
        f'<h2 class="report-title"><span aria-hidden="true">📋</span> 유동성 × 시장 실시간 브리핑</h2>'
        f'<div class="report-body">'
        f'{brief_policy}'
        f'<hr class="report-divider" aria-hidden="true">'
        f'{brief_liq}'
        f'<hr class="report-divider" aria-hidden="true">'
        f'{brief_market}'
        f'<hr class="report-divider" aria-hidden="true">'
        f'{brief_corr}'
        f'<hr class="report-divider" aria-hidden="true">'
        f'{brief_cross}'
        f'{brief_extra_sections}'
        f'</div>'
        f'<div class="report-signal {signal_class}" role="status" aria-live="polite">{signal_text}</div>'
        f'<div style="margin-top:0.5rem;padding:6px 12px;font-size:0.72rem;color:var(--text-muted);'
        f'border-top:1px solid rgba(0,0,0,0.06);text-align:right;">'
        f'데이터 소스: FRED, Yahoo Finance, yfinance News API | 실시간 갱신: 5분 간격</div>'
        f'</div>'
        f'</article>',
        unsafe_allow_html=True,
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 투자 조언 (Investment Advice — 실시간 데이터 기반 동적 생성, 확장판)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    adv_body = generate_dynamic_advice(
        country, bullish_count, bearish_count, liq_3m_chg, corr_val, sp_1m_chg,
        sp_yoy, liq_yoy, cross_data, sp_val, idx_name, sentiment_data
    )

    st.markdown(
        f'<article role="article" aria-label="투자 전략 가이드">'
        f'<div class="report-box" style="background:linear-gradient(135deg, #fef3c7, #fef9c3); border-color:#fbbf24;">'
        f'<div class="report-header">'
        f'<span class="report-badge" style="background:#f59e0b;">Investment Advice</span>'
        f'<time class="report-date" datetime="{datetime.now().strftime("%Y-%m-%dT%H:%M")}">{today_str} {datetime.now().strftime("%H:%M")} 기준 · 5분 간격 실시간 갱신</time></div>'
        f'<h2 class="report-title"><span aria-hidden="true">💡</span> 투자 전략 가이드</h2>'
        f'<div class="report-body">'
        f'{adv_body}'
        f'</div>'
        f'<div role="alert" style="margin-top:0.8rem; padding:8px 14px; background:rgba(245,158,11,0.08); '
        f'border:1px solid rgba(245,158,11,0.2); border-radius:8px; '
        f'font-size:0.78rem; color:var(--text-muted); line-height:1.6;">'
        f'<span aria-hidden="true">⚠️</span> 본 투자 조언은 유동성·상관관계·모멘텀·센티먼트·섹터 로테이션·원자재·신용시장 데이터에 기반한 정량적 분석이며, '
        f'개별 종목 추천이 아닙니다. 투자 의사결정은 개인의 위험 허용 범위, 투자 목표, '
        f'재무 상황을 종합적으로 고려하여 내려야 합니다. 필요 시 전문 재무상담사와 상의하세요.'
        f'</div>'
        f'</div>'
        f'</article>',
        unsafe_allow_html=True,
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 차트 (TradingView Lightweight Charts)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
dff = df[df.index >= pd.to_datetime(cutoff)].copy()

# ── OHLC 리샘플 ──
def resample_ohlc(ohlc_df, rule):
    return ohlc_df.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

ohlc_filtered = ohlc_raw[ohlc_raw.index >= pd.to_datetime(cutoff)].copy()

if tf == "주봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "W")
elif tf == "월봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "ME")
else:
    ohlc_chart = ohlc_filtered.copy()

# 이동평균
for ma_len in [20, 60, 120]:
    ohlc_chart[f"MA{ma_len}"] = ohlc_chart["Close"].rolling(ma_len).mean()

# ── 유동성 데이터를 캔들 타임프레임에 맞춰 리샘플 ──
liq_series_raw = dff["Liq_MA"].dropna()
if tf == "주봉":
    liq_resampled = liq_series_raw.resample("W").last().dropna()
elif tf == "월봉":
    liq_resampled = liq_series_raw.resample("ME").last().dropna()
else:
    liq_resampled = liq_series_raw.copy()

# ━━━━ 핵심: 순차 인덱스 방식으로 시간축 균일화 ━━━━
# lightweight-charts는 날짜 간격에 비례해 봉 간격을 배치하므로
# 주봉(7일)·월봉(30일)은 일봉 대비 넓게 퍼짐.
# → 모든 봉을 연속 "가상 일봉 날짜"로 매핑하여 균일 간격 보장.
candle_dates = ohlc_chart.index.tolist()           # 실제 날짜 (화면 표시용)
n_candles = len(candle_dates)

# 가상 날짜: 2000-01-03(월요일)부터 영업일 연속 배정
virtual_base = pd.Timestamp("2000-01-03")
virtual_dates = pd.bdate_range(start=virtual_base, periods=n_candles)  # 영업일
real_to_virtual = {candle_dates[i]: virtual_dates[i] for i in range(n_candles)}
virtual_to_real = {virtual_dates[i]: candle_dates[i] for i in range(n_candles)}

def to_lw_time(dt):
    return dt.strftime('%Y-%m-%d')

# ── 캔들 데이터 (가상 날짜 사용) ──
candle_data = []
for i, (dt, row) in enumerate(ohlc_chart.iterrows()):
    candle_data.append({
        "time": to_lw_time(virtual_dates[i]),
        "open": round(float(row["Open"]), 2),
        "high": round(float(row["High"]), 2),
        "low": round(float(row["Low"]), 2),
        "close": round(float(row["Close"]), 2),
    })

# ── 거래량 데이터 ──
volume_data = []
for i, (dt, row) in enumerate(ohlc_chart.iterrows()):
    is_up = row["Close"] >= row["Open"]
    volume_data.append({
        "time": to_lw_time(virtual_dates[i]),
        "value": float(row["Volume"]),
        "color": "rgba(16,185,129,0.4)" if is_up else "rgba(239,68,68,0.4)",
    })

# ── 이동평균 데이터 ──
ma_data = {}
for ma_len in [20, 60, 120]:
    col = f"MA{ma_len}"
    items = []
    for i, (dt, row) in enumerate(ohlc_chart.iterrows()):
        v = row.get(col)
        if pd.notna(v):
            items.append({"time": to_lw_time(virtual_dates[i]), "value": round(float(v), 2)})
    ma_data[col] = items

# ── 유동성 데이터 (캔들 날짜에 스냅) ──
liq_data = []
for i, cdt in enumerate(candle_dates):
    # 캔들 날짜 이하에서 가장 가까운 유동성 값
    mask = liq_resampled.index <= cdt
    if mask.any():
        val = float(liq_resampled[mask].iloc[-1])
        liq_data.append({"time": to_lw_time(virtual_dates[i]), "value": round(val, 2)})

# ── 이벤트 마커 (캔들 날짜에 정확히 스냅) ──
def snap_to_candle(event_dt, candle_index):
    """이벤트 날짜를 가장 가까운 캔들 날짜로 스냅"""
    diffs = abs(candle_index - event_dt)
    nearest_idx = diffs.argmin()
    return nearest_idx

marker_data = []
if show_events:
    gap_map = {"일봉": 10, "주봉": 4, "월봉": 2}
    min_gap_bars = gap_map.get(tf, 5)  # 봉 개수 기준 최소 간격
    prev_bar_idx = -999
    for date_str, title, desc, emoji, direction in ALL_EVENTS:
        evt_dt = pd.to_datetime(date_str)
        if evt_dt < candle_dates[0] - timedelta(days=35) or evt_dt > candle_dates[-1] + timedelta(days=35):
            continue
        bar_idx = snap_to_candle(evt_dt, ohlc_chart.index)
        if abs(bar_idx - prev_bar_idx) < min_gap_bars:
            continue
        prev_bar_idx = bar_idx
        if 0 <= bar_idx < n_candles:
            marker_data.append({
                "time": to_lw_time(virtual_dates[bar_idx]),
                "position": "aboveBar" if direction == "up" else "belowBar",
                "color": "#10b981" if direction == "up" else "#ef4444",
                "shape": "arrowUp" if direction == "up" else "arrowDown",
                "text": f"{emoji} {title}",
            })

# ── 실제↔가상 날짜 매핑 (JS에서 tooltip용) ──
date_label_map = {}
for i in range(n_candles):
    vk = to_lw_time(virtual_dates[i])
    rk = candle_dates[i].strftime('%Y-%m-%d')
    date_label_map[vk] = rk

# ── JSON 직렬화 ──
candle_json = json.dumps(candle_data)
volume_json = json.dumps(volume_data)
ma20_json = json.dumps(ma_data.get("MA20", []))
ma60_json = json.dumps(ma_data.get("MA60", []))
ma120_json = json.dumps(ma_data.get("MA120", []))
liq_json = json.dumps(liq_data)
marker_json = json.dumps(marker_data)
date_map_json = json.dumps(date_label_map)

# 차트 설정
chart_height = 650
liq_label = CC["liq_label"]
liq_suffix = CC["liq_suffix"]
default_bar_spacing = 6  # 모든 타임프레임 동일 (균일 간격이므로)

# ── Lightweight Charts HTML ──
lw_html = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: transparent; overflow:hidden; }}

  #chart-wrapper {{
    position: relative;
    width: 100%;
    height: {chart_height}px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    overflow: hidden;
  }}

  /* ── 상단 OHLC 정보 오버레이 ── */
  #info-overlay {{
    position: absolute;
    top: 10px; left: 14px;
    z-index: 10;
    pointer-events: none;
    font-family: 'SF Mono', 'Cascadia Code', 'IBM Plex Mono', 'Consolas', monospace;
  }}
  #info-title {{
    font-size: 13px; font-weight: 700;
    color: #1e293b;
    margin-bottom: 3px;
    display: flex; align-items: center; gap: 8px;
  }}
  #info-title .idx-name {{ font-family: 'Pretendard', sans-serif; }}
  #info-title .idx-tf {{ font-size: 11px; color: #94a3b8; font-weight: 500; }}
  #info-title .idx-date {{ font-size: 11px; color: #64748b; font-weight: 500; }}
  #info-ohlc {{
    display: flex; flex-wrap: wrap; gap: 3px 10px;
    font-size: 11.5px; color: #64748b;
    line-height: 1.55;
  }}
  #info-ohlc .label {{ color: #94a3b8; font-weight: 500; }}
  #info-ohlc .val {{ font-weight: 600; }}

  #ma-legend {{
    display: flex; gap: 10px;
    font-size: 10.5px; margin-top: 2px;
  }}
  #ma-legend span {{ display:flex; align-items:center; gap:3px; }}
  #ma-legend .dot {{ width:8px; height:3px; border-radius:2px; display:inline-block; }}
  .ma20-dot {{ background:#f59e0b; }}
  .ma60-dot {{ background:#3b82f6; }}
  .ma120-dot {{ background:#8b5cf6; }}
  .liq-dot {{ background:rgba(59,130,246,0.5); width:12px!important; height:8px!important; border-radius:3px!important; }}

  #vol-label {{
    position: absolute;
    bottom: 6px; left: 14px;
    font-size: 10px; color: #94a3b8;
    z-index: 10; pointer-events: none;
    font-family: 'SF Mono', monospace;
  }}

  /* ── 모바일 ── */
  @media (max-width: 768px) {{
    #info-overlay {{ top: 6px; left: 8px; }}
    #info-title {{ font-size: 12px; }}
    #info-ohlc {{ font-size: 10px; gap: 2px 7px; }}
    #ma-legend {{ font-size: 9.5px; gap: 5px; }}
    #vol-label {{ font-size: 8.5px; }}
  }}
  @media (max-width: 480px) {{
    #info-ohlc {{ font-size: 9px; gap: 1px 5px; }}
    #ma-legend {{ font-size: 8.5px; gap: 3px; flex-wrap: wrap; }}
  }}
</style>
</head>
<body>
<div id="chart-wrapper" role="figure" aria-label="{idx_name} {tf} 가격 차트 - 캔들스틱, 이동평균선, 유동성 오버레이 포함">
  <div id="info-overlay" aria-live="polite" aria-atomic="true">
    <div id="info-title">
      <span class="idx-name">{idx_name}</span>
      <span class="idx-tf">{tf}</span>
      <span class="idx-date" id="v-date"></span>
    </div>
    <div id="info-ohlc">
      <span><abbr class="label" title="시가">시</abbr> <span class="val" id="v-open">-</span></span>
      <span><abbr class="label" title="고가">고</abbr> <span class="val" id="v-high">-</span></span>
      <span><abbr class="label" title="저가">저</abbr> <span class="val" id="v-low">-</span></span>
      <span><abbr class="label" title="종가">종</abbr> <span class="val" id="v-close">-</span></span>
      <span id="v-chg-wrap"><span class="val" id="v-chg" aria-label="전일 대비 변동률">-</span></span>
      <span><span class="label">거래량</span> <span class="val" id="v-vol">-</span></span>
      <span><span class="label">{liq_label}</span> <span class="val" id="v-liq" style="color:#3b82f6">-</span></span>
    </div>
    <div id="ma-legend" aria-label="이동평균선 범례">
      <span><span class="dot ma20-dot" aria-hidden="true"></span><span id="v-ma20" style="color:#f59e0b">MA20 -</span></span>
      <span><span class="dot ma60-dot" aria-hidden="true"></span><span id="v-ma60" style="color:#3b82f6">MA60 -</span></span>
      <span><span class="dot ma120-dot" aria-hidden="true"></span><span id="v-ma120" style="color:#8b5cf6">MA120 -</span></span>
      <span><span class="dot liq-dot" aria-hidden="true"></span><span style="color:rgba(59,130,246,0.7);">{liq_label}</span></span>
    </div>
  </div>
  <div id="vol-label" aria-hidden="true">Volume</div>
  <div id="chart-container" role="img" aria-label="{idx_name} {tf} 인터랙티브 차트" tabindex="0"></div>
</div>

<script>
(function() {{
  const wrapper = document.getElementById('chart-wrapper');
  const container = document.getElementById('chart-container');
  container.style.width = '100%';
  container.style.height = '{chart_height}px';

  // 실제 날짜 매핑
  const dateMap = {date_map_json};

  // ── 차트 생성 ──
  const chart = LightweightCharts.createChart(container, {{
    width: wrapper.clientWidth,
    height: {chart_height},
    layout: {{
      background: {{ type: 'solid', color: '#ffffff' }},
      textColor: '#64748b',
      fontFamily: "'SF Mono', 'Consolas', monospace",
      fontSize: 11,
    }},
    grid: {{
      vertLines: {{ color: 'rgba(226,232,240,0.4)', style: 1 }},
      horzLines: {{ color: 'rgba(226,232,240,0.4)', style: 1 }},
    }},
    crosshair: {{
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: {{
        width: 1, color: 'rgba(100,116,139,0.35)',
        style: LightweightCharts.LineStyle.Dashed,
        labelVisible: false,
      }},
      horzLine: {{
        width: 1, color: 'rgba(100,116,139,0.35)',
        style: LightweightCharts.LineStyle.Dashed,
        labelBackgroundColor: '#475569',
      }},
    }},
    rightPriceScale: {{
      borderColor: '#e2e8f0',
      scaleMargins: {{ top: 0.08, bottom: 0.25 }},
      autoScale: true,
    }},
    timeScale: {{
      borderColor: '#e2e8f0',
      timeVisible: false,
      secondsVisible: false,
      rightOffset: 3,
      barSpacing: {default_bar_spacing},
      minBarSpacing: 0.5,
      fixLeftEdge: false,
      fixRightEdge: false,
      tickMarkFormatter: function(time) {{
        // 가상날짜 → 실제날짜 변환하여 표시
        const key = time.year + '-' +
          String(time.month).padStart(2,'0') + '-' +
          String(time.day).padStart(2,'0');
        const real = dateMap[key];
        if (real) {{
          const parts = real.split('-');
          return parts[0].slice(2) + '/' + parts[1];
        }}
        return '';
      }},
    }},
    handleScroll: {{
      mouseWheel: true,
      pressedMouseMove: true,
      horzTouchDrag: true,
      vertTouchDrag: false,
    }},
    handleScale: {{
      axisPressedMouseMove: true,
      mouseWheel: true,
      pinch: true,
    }},
    localization: {{
      timeFormatter: function(time) {{
        const key = time.year + '-' +
          String(time.month).padStart(2,'0') + '-' +
          String(time.day).padStart(2,'0');
        return dateMap[key] || key;
      }},
    }},
  }});

  // ── 캔들스틱 ──
  const candleSeries = chart.addCandlestickSeries({{
    upColor: '#10b981',
    downColor: '#ef4444',
    borderUpColor: '#10b981',
    borderDownColor: '#ef4444',
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444',
    priceFormat: {{ type: 'price', precision: 0, minMove: 1 }},
  }});
  const candleData = {candle_json};
  candleSeries.setData(candleData);

  // 마커 (이벤트) — 캔들 날짜에 정확히 스냅됨
  const markers = {marker_json};
  if (markers.length > 0) {{
    candleSeries.setMarkers(markers);
  }}

  // ── 이동평균선 ──
  const ma20Series = chart.addLineSeries({{
    color: '#f59e0b', lineWidth: 1.5, lineStyle: 0,
    priceLineVisible: false, lastValueVisible: false,
    crosshairMarkerVisible: false,
  }});
  ma20Series.setData({ma20_json});

  const ma60Series = chart.addLineSeries({{
    color: '#3b82f6', lineWidth: 1.5, lineStyle: 0,
    priceLineVisible: false, lastValueVisible: false,
    crosshairMarkerVisible: false,
  }});
  ma60Series.setData({ma60_json});

  const ma120Series = chart.addLineSeries({{
    color: '#8b5cf6', lineWidth: 1.5, lineStyle: 0,
    priceLineVisible: false, lastValueVisible: false,
    crosshairMarkerVisible: false,
  }});
  ma120Series.setData({ma120_json});

  // ── 유동성 (별도 price scale, 영역 차트) ──
  const liqSeries = chart.addAreaSeries({{
    topColor: 'rgba(59,130,246,0.12)',
    bottomColor: 'rgba(59,130,246,0.01)',
    lineColor: 'rgba(59,130,246,0.45)',
    lineWidth: 1.5,
    priceScaleId: 'liq',
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: false,
    priceFormat: {{ type: 'custom', formatter: (p) => p.toLocaleString() + '{liq_suffix}' }},
  }});
  chart.priceScale('liq').applyOptions({{
    scaleMargins: {{ top: 0.50, bottom: 0.25 }},
    borderVisible: false,
    visible: false,
  }});
  liqSeries.setData({liq_json});

  // ── 거래량 히스토그램 ──
  const volumeSeries = chart.addHistogramSeries({{
    priceFormat: {{ type: 'volume' }},
    priceScaleId: 'vol',
    priceLineVisible: false,
    lastValueVisible: false,
  }});
  chart.priceScale('vol').applyOptions({{
    scaleMargins: {{ top: 0.82, bottom: 0 }},
    borderVisible: false,
    visible: false,
  }});
  volumeSeries.setData({volume_json});

  // ── 크로스헤어 실시간 정보 ──
  const fmt = (n) => n != null ? n.toLocaleString(undefined, {{maximumFractionDigits:0}}) : '-';
  const fmtVol = (n) => {{
    if (n == null) return '-';
    if (n >= 1e9) return (n/1e9).toFixed(1) + 'B';
    if (n >= 1e6) return (n/1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n/1e3).toFixed(1) + 'K';
    return n.toFixed(0);
  }};

  const ma20Map = new Map({ma20_json}.map(d => [d.time, d.value]));
  const ma60Map = new Map({ma60_json}.map(d => [d.time, d.value]));
  const ma120Map = new Map({ma120_json}.map(d => [d.time, d.value]));
  const liqMap = new Map({liq_json}.map(d => [d.time, d.value]));
  const volMap = new Map({volume_json}.map(d => [d.time, d.value]));
  const candleMap = new Map(candleData.map(d => [d.time, d]));

  function timeToKey(t) {{
    if (typeof t === 'string') return t;
    if (t && t.year) return t.year + '-' + String(t.month).padStart(2,'0') + '-' + String(t.day).padStart(2,'0');
    return null;
  }}

  function updateInfo(param) {{
    let t;
    if (param && param.time) {{
      t = timeToKey(param.time);
    }} else if (candleData.length > 0) {{
      t = candleData[candleData.length - 1].time;
    }} else {{ return; }}
    if (!t) return;

    const candle = candleMap.get(t);
    if (!candle) return;

    // 실제 날짜 표시
    const realDate = dateMap[t] || t;
    document.getElementById('v-date').textContent = realDate;

    const o = candle.open, h = candle.high, l = candle.low, c = candle.close;
    const isUp = c >= o;
    const clr = isUp ? '#10b981' : '#ef4444';

    document.getElementById('v-open').textContent = fmt(o);
    document.getElementById('v-high').textContent = fmt(h);
    document.getElementById('v-high').style.color = '#10b981';
    document.getElementById('v-low').textContent = fmt(l);
    document.getElementById('v-low').style.color = '#ef4444';
    document.getElementById('v-close').textContent = fmt(c);
    document.getElementById('v-close').style.color = clr;

    // 전봉 대비 변화율
    const idx = candleData.findIndex(d => d.time === t);
    if (idx > 0) {{
      const prevC = candleData[idx-1].close;
      const chg = ((c - prevC) / prevC * 100);
      const arrow = chg >= 0 ? '▲' : '▼';
      document.getElementById('v-chg').textContent = arrow + ' ' + Math.abs(chg).toFixed(2) + '%';
      document.getElementById('v-chg').style.color = chg >= 0 ? '#10b981' : '#ef4444';
    }}

    const v = volMap.get(t);
    document.getElementById('v-vol').textContent = fmtVol(v);

    const liqVal = liqMap.get(t);
    document.getElementById('v-liq').textContent = liqVal ? fmt(liqVal) + '{liq_suffix}' : '-';

    const m20 = ma20Map.get(t);
    document.getElementById('v-ma20').textContent = 'MA20 ' + (m20 ? fmt(m20) : '-');
    const m60 = ma60Map.get(t);
    document.getElementById('v-ma60').textContent = 'MA60 ' + (m60 ? fmt(m60) : '-');
    const m120 = ma120Map.get(t);
    document.getElementById('v-ma120').textContent = 'MA120 ' + (m120 ? fmt(m120) : '-');
  }}

  chart.subscribeCrosshairMove(updateInfo);
  updateInfo(null);

  // ── 반응형 리사이즈 ──
  const resizeObserver = new ResizeObserver(entries => {{
    for (const entry of entries) {{
      chart.applyOptions({{ width: entry.contentRect.width }});
    }}
  }});
  resizeObserver.observe(wrapper);

  // 초기 뷰: 전체 데이터 표시
  chart.timeScale().fitContent();
}})();
</script>
</body>
</html>
"""

# ── Streamlit에 HTML 삽입 ──
components.html(lw_html, height=chart_height + 10, scrolling=False)

# 최근 캔들 요약
if len(ohlc_chart) >= 2:
    last = ohlc_chart.iloc[-1]
    prev = ohlc_chart.iloc[-2]
    chg = (last["Close"] - prev["Close"]) / prev["Close"] * 100
    chg_arrow = "▲" if chg >= 0 else "▼"
    chg_color = "green" if chg >= 0 else "red"
    chg_direction = "상승" if chg >= 0 else "하락"
    st.markdown(
        f'<div class="guide-box" role="status" aria-label="최근 {tf} 요약: 종가 {last["Close"]:,.0f}, {chg_direction} {abs(chg):.2f}%">'
        f'<span aria-hidden="true">🕯️</span> <strong>최근 {tf}:</strong> '
        f'시 <strong>{last["Open"]:,.0f}</strong> · '
        f'고 <strong>{last["High"]:,.0f}</strong> · '
        f'저 <strong>{last["Low"]:,.0f}</strong> · '
        f'종 <strong>{last["Close"]:,.0f}</strong> '
        f'<span style="color:var(--accent-{chg_color})">{chg_arrow} {chg:+.2f}%<span class="sr-only"> ({chg_direction})</span></span>'
        f'<br>'
        f'이평선: <span style="color:#f59e0b">MA20</span> · '
        f'<span style="color:#3b82f6">MA60</span> · '
        f'<span style="color:#8b5cf6">MA120</span> · '
        f'<span style="color:rgba(59,130,246,0.6)">파란 영역</span> = {CC["liq_label"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 이벤트 타임라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
event_count = sum(1 for d,_,_,_,_ in ALL_EVENTS if pd.to_datetime(d) >= dff.index.min())
st.markdown(f"""<section aria-label="주요 매크로 이벤트 타임라인"><div class="card">
    <h2 class="card-title"><span class="dot" style="background:var(--accent-blue)" aria-hidden="true"></span> 주요 매크로 이벤트 타임라인 ({event_count} 이벤트)</h2>
""", unsafe_allow_html=True)

tl_html = '<div class="timeline" role="list" aria-label="이벤트 목록">'
for date_str, title, desc, emoji, direction in reversed(ALL_EVENTS):
    dt = pd.to_datetime(date_str)
    if dt < dff.index.min():
        continue
    dir_cls = "up" if direction == "up" else "down"
    dir_label = "상승" if direction == "up" else "하락"
    tl_html += f"""
    <div class="tl-item" role="listitem" aria-label="{date_str}: {title} - {dir_label}">
        <time class="tl-date" datetime="{date_str}">{date_str}</time>
        <div class="tl-icon" aria-hidden="true">{emoji}</div>
        <div class="tl-content">
            <div class="tl-title">{title}</div>
            <div class="tl-desc">{desc}</div>
        </div>
        <div class="tl-dir {dir_cls}" aria-label="시장 방향: {dir_label}">{dir_label}</div>
    </div>"""
tl_html += "</div>"
st.markdown(tl_html + "</div></section>", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f'<footer role="contentinfo" class="app-footer">'
    f'데이터: {CC["data_src"]} · 업데이트: <time datetime="{df.index.max().strftime("%Y-%m-%d")}">{df.index.max().strftime("%Y-%m-%d")}</time>'
    f'<br>실시간 갱신: 5분 간격 · 본 페이지는 투자 조언이 아닙니다'
    f'</footer>',
    unsafe_allow_html=True,
)