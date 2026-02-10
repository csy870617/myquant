import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import json
from zoneinfo import ZoneInfo

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
# 자동 새로고침 (PST 09:00/18:00 + KST 09:00/18:00 = 하루 4회)
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

auto_interval = min(REFRESH_SECS * 1000, 3600_000)
st.markdown(
    f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">',
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
    --text-primary: #1e293b; --text-secondary: #64748b; --text-muted: #94a3b8;
    --accent-blue: #3b82f6; --accent-red: #ef4444; --accent-green: #10b981;
    --accent-purple: #8b5cf6; --accent-amber: #f59e0b;
}
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg) !important; color: var(--text-primary);
}
[data-testid="stHeader"] { background: transparent !important; }

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
    .page-desc { font-size: 0.75rem; margin-bottom: 0.6rem; }
    .kpi-value { font-size: 0.95rem; }
    .kpi-label { font-size: 0.6rem; letter-spacing: 0.3px; }
    .report-title { font-size: 0.88rem; }
    .report-body { font-size: 0.78rem; line-height: 1.6; }
    .tl-date { min-width: 60px; font-size: 0.62rem; }
    .tl-desc { display: none; }
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


@st.cache_data(ttl=3600, show_spinner=False)
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
<div class="page-header">
    <div class="page-header-icon">📊</div>
    <div class="page-title">유동성 × 시장 분석기</div>
</div>
<div class="page-desc">
    중앙은행 통화량과 주가지수의 상관관계를 분석합니다.<br>
    유동성 흐름이 주가에 미치는 영향을 시각적으로 확인하세요.
</div>
""", unsafe_allow_html=True)

# 새로고침 상태 바
now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
next_str = NEXT_REFRESH_TIME.strftime("%m/%d %H:%M KST")
st.markdown(
    f'<div class="refresh-bar">'
    f'<span class="refresh-dot"></span>'
    f'갱신: {now_str} · 다음: {next_str}'
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
        return f'<div class="kpi-delta {cls}">{arrow} YoY {val:+.1f}%</div>'

    corr_cls = "up" if corr_val >= 0.3 else "down"
    corr_desc = "강한 양의 상관" if corr_val >= 0.5 else ("약한 양의 상관" if corr_val >= 0 else "음의 상관")

    liq_display = f"{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}"

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi blue">
            <div class="kpi-label">💵 {CC['liq_label']}</div>
            <div class="kpi-value">{liq_display}</div>
            {delta_html(liq_yoy)}
        </div>
        <div class="kpi red">
            <div class="kpi-label">📈 {idx_name}</div>
            <div class="kpi-value">{sp_val:,.0f}</div>
            {delta_html(sp_yoy)}
        </div>
        <div class="kpi green">
            <div class="kpi-label">🔗 90일 상관계수</div>
            <div class="kpi-value">{corr_val:.3f}</div>
            <div class="kpi-delta {corr_cls}">{corr_desc}</div>
        </div>
        <div class="kpi purple">
            <div class="kpi-label">📅 데이터 범위</div>
            <div class="kpi-value" style="font-size:1.05rem">{df.index.min().strftime('%Y.%m')} – {df.index.max().strftime('%Y.%m')}</div>
            <div class="kpi-delta up">{len(df):,}일</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Daily Brief (상세 버전)
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

    if country == "🇺🇸 미국":
        brief_policy = (
            '<strong>▎연준 정책 현황</strong><br>'
            '연방기금금리 <span class="hl">3.50–3.75%</span> 유지 (1/28 FOMC). '
            '만장일치가 아닌 10-2 표결로, <strong>미런·월러 이사가 25bp 인하를 주장</strong>하며 내부 균열이 확인되었습니다. '
            '파월 의장은 기자회견에서 "현 정책이 유의하게 긴축적이라 보기 어렵다"고 발언, '
            '데이터 의존적 접근을 재확인했습니다.<br><br>'
            'QT는 12/1에 공식 종료되었고, 12/12부터 <strong>준비금 관리 매입(RMP)</strong>으로 국채 매입을 재개하여 '
            '사실상 대차대조표 확장으로 전환했습니다. '
            'NY연은 윌리엄스 총재는 "이는 정책 스탠스 변화가 아닌 충분한 준비금 유지를 위한 기술적 조치"라고 강조했으나, '
            '시장은 유동성 공급 확대로 해석하고 있습니다.<br><br>'
            '<strong>차기 의장 이슈:</strong> 파월 임기 만료(5/15)를 앞두고 트럼프 대통령이 '
            '<strong>케빈 워시(Kevin Warsh)</strong>를 1/30 차기 의장으로 지명했습니다. '
            '워시는 2008년 위기 당시 매파적 입장으로 알려져 있으나, 최근에는 AI 생산성 향상을 근거로 '
            '금리 인하를 지지하는 방향으로 선회했습니다. '
            '틸리스 상원의원이 파월 대상 DOJ 수사 해결 전까지 인준 반대를 선언하여 '
            '상원 인준 과정에 불확실성이 존재합니다. '
            '시장은 여름 이후 1~2회 추가 인하를 가격에 반영 중입니다.'
        )
        brief_liq = (
            f'<strong>▎유동성 데이터 심층 분석</strong><br>'
            f'본원통화 최신치 <span class="hl">{liq_display}</span> '
            f'(YoY {liq_yoy:+.1f}%, 1개월 {liq_1m_chg:+.1f}%, 3개월 {liq_3m_chg:+.1f}%, 6개월 {liq_6m_chg:+.1f}%).<br><br>'
            f'QT 종료(12/1)와 RMP 개시(12/12)로 유동성 바닥이 확인되었으며, '
            f'완만한 확장 국면에 진입했습니다. '
            f'12월 말 연말 자금수요에 대응하여 Standing Repo Facility에서 $746억이 공급된 후 '
            f'1/5까지 전액 상환되어, 단기자금시장은 안정적으로 작동 중입니다.<br><br>'
            f'<strong>핵심 포인트:</strong> 유동성 확장 속도가 2020-2021년 "무한 QE" 시기보다 '
            f'현저히 느리므로, 과거와 같은 자산가격 급등보다는 점진적 상승을 예상합니다. '
            f'RRP(역레포) 잔고 감소와 TGA(재무부 일반계좌) 변동이 단기 유동성의 핵심 변수입니다.'
        )
        brief_market = (
            f'<strong>▎시장 동향 & 섹터 분석</strong><br>'
            f'{idx_name} <span class="hl">{sp_val:,.0f}</span> '
            f'(1주 {sp_1w_chg:+.1f}%, 1개월 {sp_1m_chg:+.1f}%, 3개월 {sp_3m_chg:+.1f}%, YoY {sp_yoy:+.1f}%).<br><br>'
            f'<strong>최근 주요 흐름:</strong><br>'
            f'• 다우 50,000 역사적 돌파(2/6) → 경기순환주 로테이션 진행<br>'
            f'• 등가중 S&P 500이 시총가중 S&P 대비 아웃퍼폼(+5% vs +2% YTD) → 랠리 저변 확대<br>'
            f'• Mag7 실적 혼조: 구글·아마존 AI CapEx $185B·$200B 발표로 투자자 불안 가중<br>'
            f'• 소프트웨어 섹터 -24% YTD: Anthropic Claude Cowork 등 AI 에이전트 위협으로 급락<br>'
            f'• 비트코인 -50% (고점 $126K→$62K), 은 -40%, 금 -15% → 위험자산 전면 디레버리징<br><br>'
            f'<strong>밸류에이션:</strong> S&P 500 선행 P/E 22.2배(5년 평균 20배), 중간선거 해 평균 -18% 조정 이력. '
            f'AI 기업이익 성장(2026E +12%)이 고밸류를 지지하나, 집중도 리스크(상위 10종목 비중 35%+) 상존.'
        )
    else:  # 한국
        brief_policy = (
            '<strong>▎한국은행 통화정책 현황</strong><br>'
            '기준금리 <span class="hl">2.50%</span> (2025/6 인하 이후 유지). '
            '글로벌 긴축 완화 흐름에 맞춰 한은도 완화적 기조를 유지 중이며, '
            '원/달러 환율 안정과 가계부채 관리가 추가 인하의 핵심 제약 요인입니다.<br><br>'
            '<strong>글로벌 정책 영향:</strong> 미 연준의 케빈 워시 차기 의장 지명(1/30)이 '
            '매파적으로 해석되며 달러 강세→원화 약세 압력이 가중되었습니다. '
            '한은의 추가 인하 여력이 제한될 수 있으나, 내수 경기 둔화 시 '
            '하반기 1회 추가 인하 가능성이 열려 있습니다.<br><br>'
            '<strong>이재명 정부 정책:</strong> "KOSPI 5,000" 국정과제 목표가 조기 달성되었으며, '
            '밸류업 프로그램 2.0, 공매도 재개 관리 등 자본시장 친화 정책이 지속되고 있습니다. '
            '한미 관세 합의(2025년)로 수출 환경이 안정적이나, '
            '신용거래융자 잔고 30.5조원(사상 최대)이 과열 시그널로 주시됩니다.'
        )
        brief_liq = (
            f'<strong>▎유동성 데이터 심층 분석</strong><br>'
            f'Fed 본원통화(글로벌 유동성 지표) 최신치 <span class="hl">{liq_display}</span> '
            f'(YoY {liq_yoy:+.1f}%, 1개월 {liq_1m_chg:+.1f}%, 3개월 {liq_3m_chg:+.1f}%, 6개월 {liq_6m_chg:+.1f}%).<br><br>'
            f'한국 증시는 글로벌 달러 유동성에 높은 민감도를 보입니다. '
            f'Fed의 QT 종료와 RMP 개시로 글로벌 유동성 바닥이 형성된 것은 '
            f'신흥국 자금 흐름에 우호적입니다.<br><br>'
            f'<strong>핵심 포인트:</strong> 외국인 순매수 복귀 여부와 원화 환율 안정이 '
            f'한국 증시 유동성의 직접적 지표입니다. '
            f'최근 기관·외국인의 반도체 섹터 집중 매수가 확인되며, '
            f'연기금(NPS)의 환헤지 프로그램 재개 논의도 원화 안정에 긍정적입니다.'
        )
        brief_market = (
            f'<strong>▎시장 동향 & 섹터 분석</strong><br>'
            f'{idx_name} <span class="hl">{sp_val:,.0f}</span> '
            f'(1주 {sp_1w_chg:+.1f}%, 1개월 {sp_1m_chg:+.1f}%, 3개월 {sp_3m_chg:+.1f}%, YoY {sp_yoy:+.1f}%).<br><br>'
            f'<strong>최근 주요 흐름:</strong><br>'
            f'• KOSPI 5,300 사상 최고가 경신(2/10) → 2025년 저점 대비 +132% 상승<br>'
            f'• 삼성전자 HBM4 양산 개시(2월) → NVIDIA 차세대 GPU 납품 확정, SK하이닉스 +6%<br>'
            f'• 워시 지명 쇼크(1/30) → 하루 -5.26% 후 익일 +6.84% 역대급 V자 반등<br>'
            f'• KOSPI 200 변동성지수 50 돌파 → 6년 래 최고, 신용융자 30.5조원 사상 최대<br>'
            f'• 코리아 디스카운트 해소 진행: 시총 3,500조원 돌파, PBR 1.2배로 상승<br><br>'
            f'<strong>리스크:</strong> RSI·스토캐스틱 과매수 구간 진입, 레버리지 과열 경고. '
            f'단기 5,000선 지지 테스트 가능성 상존. 중국 제조업 PMI 둔화도 부담.'
        )

    brief_corr = (
        f'<strong>▎상관관계 진단</strong><br>'
        f'90일 롤링 상관계수 <span class="hl">{corr_val:.3f}</span>. '
        + ('유동성과 주가가 강한 동행 관계를 유지 중입니다. '
           '이는 중앙은행 유동성 공급이 주가를 직접적으로 지지하는 "유동성 장세" 구간임을 의미합니다. '
           '유동성 방향 전환 시 주가도 동반 조정될 수 있어 Fed 정책 변화에 민감하게 대응해야 합니다.'
           if corr_val > 0.5
           else '유동성-주가 동조성이 약화된 구간입니다. '
                '기업실적, 지정학, 섹터 로테이션 등 유동성 외 변수가 주가를 주도하고 있어, '
                '펀더멘털 분석의 비중을 높일 필요가 있습니다.'
           if corr_val > 0
           else '음의 상관으로 전환된 특이 구간입니다. '
                '유동성이 증가하는데 주가가 하락하거나 그 반대 상황으로, '
                '시장이 유동성 외 강력한 악재(지정학, 신용 이벤트 등)에 반응하고 있음을 시사합니다.')
    )

    # ── 글로벌 크로스에셋 모니터 ──
    if country == "🇺🇸 미국":
        brief_cross = (
            '<strong>▎글로벌 크로스에셋 모니터</strong><br>'
            '• <strong>귀금속:</strong> 금 $4,850(-15% 고점 대비), 은 $64(-55% 고점 대비). '
            '워시 지명 후 달러 강세에 따른 급락 후 변동성 극심. CME 증거금 인상 반복<br>'
            '• <strong>크립토:</strong> BTC $69K(-45% 고점), ETH -55%. '
            '"디지털 금" 내러티브 붕괴, ETF 자금유출 지속. 마이클 버리 "담보 사망 소용돌이" 경고<br>'
            '• <strong>국채:</strong> 10년물 4.0% 부근. 약한 소매판매 → 금리인하 기대 2회 이상으로 상향<br>'
            '• <strong>달러:</strong> DXY 강세. 워시 지명 + 관세 정책 → 신흥국 통화 압박<br>'
            '• <strong>일본:</strong> 니케이 57,650 사상 최고. 다카이치 총선 압승 → "다카이치 트레이드" 가속'
        )
    else:
        brief_cross = (
            '<strong>▎글로벌 크로스에셋 모니터</strong><br>'
            '• <strong>환율:</strong> 원/달러 1,350원대. 달러 강세 지속 중이나 NPS 환헤지 논의로 급등 제한<br>'
            '• <strong>귀금속:</strong> 금 $4,850(-15% 고점 대비), 은 $64(-55%). '
            '글로벌 위험자산 디레버리징 영향<br>'
            '• <strong>크립토:</strong> BTC $69K(-45% 고점). 한국 개인투자자 손실 확대 우려<br>'
            '• <strong>반도체:</strong> TSMC 1월 매출 호조 → 글로벌 AI 수요 건재 확인. 삼성 HBM4 양산이 핵심 촉매<br>'
            '• <strong>일본:</strong> 니케이 57,650 사상 최고 → 아시아 증시 전반 위험선호 회복 중'
        )

    # 종합 시그널 생성
    st.markdown(
        f'<div class="report-box">'
        f'<div class="report-header">'
        f'<span class="report-badge">Daily Brief</span>'
        f'<span class="report-date">{today_str} 기준</span></div>'
        f'<div class="report-title">📋 오늘의 유동성 &amp; 시장 브리핑</div>'
        f'<div class="report-body">'
        f'{brief_policy}'
        f'<hr class="report-divider">'
        f'{brief_liq}'
        f'<hr class="report-divider">'
        f'{brief_market}'
        f'<hr class="report-divider">'
        f'{brief_corr}'
        f'<hr class="report-divider">'
        f'{brief_cross}'
        f'</div>'
        f'<div class="report-signal {signal_class}">{signal_text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 투자 조언 (Investment Advice)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # 동적 분석 기반 투자 전략 생성
    if country == "🇺🇸 미국":
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

        adv_body = (
            f'<strong>▎포지션 전략: <span style="color:{adv_stance_color}">{adv_icon} {adv_stance}</span></strong><br>'
            f'유동성 {liq_3m_chg:+.1f}%(3M), 상관계수 {corr_val:.2f}, 시장 모멘텀 {sp_1m_chg:+.1f}%(1M) 종합 판단.<br><br>'
            f'<strong>▎섹터별 전략</strong><br>'
            f'• <strong>AI/반도체(비중확대):</strong> NVIDIA·Broadcom 중심 AI CapEx 사이클 지속. '
            f'다만 소프트웨어 섹터는 AI 에이전트 위협으로 약세 → 선별적 접근 필요<br>'
            f'• <strong>경기순환주(비중확대):</strong> 다우 50K 돌파, 등가중 S&P 아웃퍼폼 → '
            f'은행·산업재·헬스케어로 로테이션 진행 중<br>'
            f'• <strong>소형주(관심):</strong> Russell 2000 YTD +3% S&P 아웃퍼폼. '
            f'금리 인하 기대 + OBBBA 감세 수혜 → 하반기 추가 상승 여력<br>'
            f'• <strong>방어주(일부 편입):</strong> 중간선거 해 평균 -18% 조정 이력. '
            f'배당·유틸리티로 변동성 헤지 권장<br><br>'
            f'<strong>▎리스크 관리</strong><br>'
            f'• 워시 인준 불확실성: 틸리스 의원 반대 → 의장 공백 시 변동성 확대 가능<br>'
            f'• 밸류에이션: 선행 P/E 22.2배, CAPE 39배 → 역사적 고점권. '
            f'실적 미달 시 급격한 멀티플 수축 위험<br>'
            f'• 크립토·귀금속 연쇄 청산: BTC -50%, 은 -55% → '
            f'레버리지 해소가 주식시장으로 전이될 가능성 모니터링<br>'
            f'• <strong>핵심 지지선:</strong> S&P 6,800 / 나스닥 22,000 이탈 시 추가 하방 열림'
        )
    else:  # 한국
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

        adv_body = (
            f'<strong>▎포지션 전략: <span style="color:{adv_stance_color}">{adv_icon} {adv_stance}</span></strong><br>'
            f'글로벌 유동성 {liq_3m_chg:+.1f}%(3M), 상관계수 {corr_val:.2f}, 시장 모멘텀 {sp_1m_chg:+.1f}%(1M) 종합 판단.<br><br>'
            f'<strong>▎섹터별 전략</strong><br>'
            f'• <strong>반도체(핵심 비중확대):</strong> 삼성전자 HBM4 양산·NVIDIA 납품 확정, '
            f'SK하이닉스 HBM3E 풀가동 → AI 메모리 슈퍼사이클의 최대 수혜<br>'
            f'• <strong>방산·조선(비중확대):</strong> 한화에어로스페이스, HD현대중공업 등 '
            f'글로벌 방산 수주 호조 지속. 트럼프 방위비 증액 기조 수혜<br>'
            f'• <strong>2차전지(중립):</strong> 미국 IRA 보조금 불확실성, 중국 LFP 가격 경쟁 → '
            f'LG에너지솔루션·삼성SDI 선별적 접근<br>'
            f'• <strong>금융(비중확대):</strong> 밸류업 프로그램 수혜, 배당 확대 기조. '
            f'저PBR 은행주 → KB금융·하나금융 관심<br><br>'
            f'<strong>▎리스크 관리</strong><br>'
            f'• 과열 경고: RSI 과매수, 신용융자 30.5조원 사상 최대 → 급락 시 반대매매 연쇄 위험<br>'
            f'• 환율: 원/달러 1,350원대 → 워시 인준 시 달러 강세 심화 가능. 환헤지 고려<br>'
            f'• 중국 경기: 제조업 PMI 둔화 → 한국 수출에 직접 영향<br>'
            f'• <strong>핵심 지지선:</strong> KOSPI 5,000 심리적 지지 / 4,800 기술적 지지 이탈 시 추가 조정'
        )

    st.markdown(
        f'<div class="report-box" style="background:linear-gradient(135deg, #fef3c7, #fef9c3); border-color:#fbbf24;">'
        f'<div class="report-header">'
        f'<span class="report-badge" style="background:#f59e0b;">Investment Advice</span>'
        f'<span class="report-date">{today_str} 기준 · 유동성 데이터 기반 분석</span></div>'
        f'<div class="report-title">💡 투자 전략 가이드</div>'
        f'<div class="report-body">'
        f'{adv_body}'
        f'</div>'
        f'<div style="margin-top:0.8rem; padding:8px 14px; background:rgba(245,158,11,0.08); '
        f'border:1px solid rgba(245,158,11,0.2); border-radius:8px; '
        f'font-size:0.78rem; color:var(--text-muted); line-height:1.6;">'
        f'⚠️ 본 투자 조언은 유동성·상관관계·모멘텀 데이터에 기반한 정량적 분석이며, '
        f'개별 종목 추천이 아닙니다. 투자 의사결정은 개인의 위험 허용 범위, 투자 목표, '
        f'재무 상황을 종합적으로 고려하여 내려야 합니다. 필요 시 전문 재무상담사와 상의하세요.'
        f'</div>'
        f'</div>',
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
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
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
<div id="chart-wrapper">
  <div id="info-overlay">
    <div id="info-title">
      <span class="idx-name">{idx_name}</span>
      <span class="idx-tf">{tf}</span>
      <span class="idx-date" id="v-date"></span>
    </div>
    <div id="info-ohlc">
      <span><span class="label">시</span> <span class="val" id="v-open">-</span></span>
      <span><span class="label">고</span> <span class="val" id="v-high">-</span></span>
      <span><span class="label">저</span> <span class="val" id="v-low">-</span></span>
      <span><span class="label">종</span> <span class="val" id="v-close">-</span></span>
      <span id="v-chg-wrap"><span class="val" id="v-chg">-</span></span>
      <span><span class="label">거래량</span> <span class="val" id="v-vol">-</span></span>
      <span><span class="label">{liq_label}</span> <span class="val" id="v-liq" style="color:#3b82f6">-</span></span>
    </div>
    <div id="ma-legend">
      <span><span class="dot ma20-dot"></span><span id="v-ma20" style="color:#f59e0b">MA20 -</span></span>
      <span><span class="dot ma60-dot"></span><span id="v-ma60" style="color:#3b82f6">MA60 -</span></span>
      <span><span class="dot ma120-dot"></span><span id="v-ma120" style="color:#8b5cf6">MA120 -</span></span>
      <span><span class="dot liq-dot"></span><span style="color:rgba(59,130,246,0.7);">{liq_label}</span></span>
    </div>
  </div>
  <div id="vol-label">Volume</div>
  <div id="chart-container"></div>
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
    st.markdown(
        f'<div class="guide-box">'
        f'🕯️ <strong>최근 {tf}:</strong> '
        f'시 <strong>{last["Open"]:,.0f}</strong> · '
        f'고 <strong>{last["High"]:,.0f}</strong> · '
        f'저 <strong>{last["Low"]:,.0f}</strong> · '
        f'종 <strong>{last["Close"]:,.0f}</strong> '
        f'<span style="color:var(--accent-{chg_color})">{chg_arrow} {chg:+.2f}%</span>'
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
st.markdown("""<div class="card">
    <div class="card-title"><span class="dot" style="background:var(--accent-blue)"></span> 주요 매크로 이벤트 타임라인 ({} 이벤트)</div>
""".format(sum(1 for d,_,_,_,_ in ALL_EVENTS if pd.to_datetime(d) >= dff.index.min())), unsafe_allow_html=True)

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
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f'<div class="app-footer">'
    f'데이터: {CC["data_src"]} · 업데이트: {df.index.max().strftime("%Y-%m-%d")}'
    f'<br>자동 갱신 4회/일 (PST·KST 09/18시) · 본 페이지는 투자 조언이 아닙니다'
    f'</div>',
    unsafe_allow_html=True,
)