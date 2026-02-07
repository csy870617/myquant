import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(page_title="유동성 × 시장 분석기", page_icon="📊", layout="wide")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침 (PST 09:00/18:00 + KST 09:00/18:00 = 하루 4회)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from zoneinfo import ZoneInfo

def get_next_refresh():
    """다음 새로고침 시각까지 남은 초 계산 (PST 09/18 + KST 09/18)"""
    utc_now = datetime.now(ZoneInfo("UTC"))

    # PST (UTC-8) 09:00, 18:00 → UTC 17:00, 02:00(+1)
    # KST (UTC+9) 09:00, 18:00 → UTC 00:00, 09:00
    # UTC 기준 정렬: 00:00, 02:00, 09:00, 17:00
    utc_hours = [0, 2, 9, 17]

    targets = []
    for h in utc_hours:
        t = utc_now.replace(hour=h, minute=0, second=0, microsecond=0)
        if t <= utc_now:
            t += timedelta(days=1)
        targets.append(t)

    next_t = min(targets)
    secs = max(int((next_t - utc_now).total_seconds()), 60)

    # 표시용: 로컬 시간으로 변환
    local_next = next_t.astimezone(ZoneInfo("Asia/Seoul"))
    return local_next, secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()

# 자동 새로고침 메타 태그 (밀리초 단위)
# 최대 1시간 단위로 체크, 정시에 가까워지면 짧아짐
auto_interval = min(REFRESH_SECS * 1000, 3600_000)
st.markdown(
    f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS
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
.block-container { padding: 1.5rem 2rem 3rem; max-width: 1280px; }

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
[data-testid="stRadio"] > div { gap: 0.3rem !important; }
.app-footer { text-align:center; color:var(--text-muted); font-size:0.75rem; margin-top:2rem; padding:1rem; border-top:1px solid var(--border); }

/* ── Plotly 차트 ── */
.js-plotly-plot, .plotly, .js-plotly-plot .plotly,
[data-testid="stPlotlyChart"], [data-testid="stPlotlyChart"] > div,
.stPlotlyChart, .stPlotlyChart > div > div > div {
    touch-action: none !important;
    -webkit-touch-callout: none;
}
.modebar { opacity: 0.7 !important; }
.modebar:hover { opacity: 1 !important; }
.modebar-btn { font-size: 16px !important; }
.modebar-group { padding: 0 2px !important; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   모바일 반응형 (≤768px)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
@media (max-width: 768px) {
    /* 레이아웃 */
    .block-container { padding: 1rem 0.6rem 2rem !important; }

    /* 헤더 축소 */
    .page-header { gap: 10px; margin-bottom: 0.2rem; }
    .page-header-icon { width: 36px; height: 36px; font-size: 1.1rem; border-radius: 10px; }
    .page-title { font-size: 1.2rem; }
    .page-desc { font-size: 0.8rem; margin-bottom: 0.8rem; line-height: 1.5; }

    /* 새로고침 바 */
    .refresh-bar { font-size: 0.68rem; padding: 5px 10px; gap: 4px; }

    /* 컨트롤 바: 5개 → 2줄 래핑 (3+2) */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.3rem !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 0 0 30% !important;
        min-width: 30% !important;
        max-width: 48% !important;
    }
    .stSelectbox { margin-bottom: -0.3rem !important; }
    .stRadio { margin-bottom: -0.3rem !important; }
    .stSelectbox > div > div { min-height: 34px !important; font-size: 0.82rem !important; }
    .stSelectbox label, .stMultiSelect label, .stSlider label, .stRadio label {
        font-size: 0.72rem !important;
    }
    [data-testid="stRadio"] label { font-size: 0.78rem !important; padding: 0.2rem 0.4rem !important; }

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

    /* ★ 차트 넓고 크게 */
    [data-testid="stPlotlyChart"] {
        margin-left: -0.6rem !important;
        margin-right: -0.6rem !important;
        width: calc(100% + 1.2rem) !important;
    }

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

    /* Plotly 모드바 모바일 */
    .modebar { opacity: 1 !important; }
    .modebar-btn { font-size: 18px !important; padding: 4px !important; }
}

/* ━━ 초소형 화면 (≤480px) ━━ */
@media (max-width: 480px) {
    .block-container { padding: 0.7rem 0.4rem 1.5rem !important; }
    .page-header-icon { width: 32px; height: 32px; font-size: 1rem; }
    .page-title { font-size: 1.05rem; letter-spacing: -0.3px; }
    .page-desc { font-size: 0.75rem; margin-bottom: 0.6rem; }
    .kpi-value { font-size: 0.95rem; }
    .kpi-label { font-size: 0.6rem; letter-spacing: 0.3px; }
    .report-title { font-size: 0.88rem; }
    .report-body { font-size: 0.78rem; line-height: 1.6; }

    /* 차트 풀블리드 */
    [data-testid="stPlotlyChart"] {
        margin-left: -0.4rem !important;
        margin-right: -0.4rem !important;
        width: calc(100% + 0.8rem) !important;
    }

    .tl-date { min-width: 60px; font-size: 0.62rem; }
    .tl-desc { display: none; }
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 & 이벤트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
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
    ("2026-01-28", "S&P 7000 돌파",          "14개월 만에 +1,000pt, AI 슈퍼사이클 & OBBBA 효과",    "🏆", "up"),
]

MARKET_PIVOTS_KR = [
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
        fetch_start = end_dt - timedelta(days=365 * 14)

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
            yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
            
            if yf_data.empty:
                st.error("지수 데이터를 가져오지 못했습니다. (데이터가 비어있음)")
                return None, None
            
            if isinstance(yf_data.columns, pd.MultiIndex):
                idx_close = yf_data['Close'][[ticker]].rename(columns={ticker: 'SP500'})
                ohlc = yf_data[[('Open',ticker),('High',ticker),('Low',ticker),('Close',ticker),('Volume',ticker)]].copy()
                ohlc.columns = ['Open','High','Low','Close','Volume']
            else:
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

        cut = end_dt - timedelta(days=365 * 12)
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
    margin=dict(t=50, b=30, l=45, r=15), dragmode="pan",
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
# 통합 컨트롤 바 (국가 · 지수 · 기간 · 봉주기 · 이벤트)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1.1, 1.1, 1.1, 1.8, 0.7])
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
    tf = st.radio("🕯️ 봉", ["일봉", "주봉", "월봉"], horizontal=True, key="candle_tf", index=2)
with ctrl5:
    show_events = st.toggle("📌 이벤트", value=True)

period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 12}
period_years = period_map[period]
cutoff = datetime.now() - timedelta(days=365 * period_years)

with st.spinner(f"{CC['liq_label']} & {idx_name} 데이터를 불러오는 중..."):
    df, ohlc_raw = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])

if df is None or df.empty:
    st.error("데이터를 불러올 수 없습니다. 잠시 후 새로고침 해주세요.")
    st.stop()

# ── 자동 이벤트 감지: OHLC ±3% 일변동 자동 추가 ──
def detect_auto_events(ohlc_df, base_events, threshold=0.05):
    if ohlc_df is None or ohlc_df.empty or len(ohlc_df) < 2:
        return []
    daily_ret = ohlc_df["Close"].pct_change()
    existing_dates = {pd.to_datetime(d).date() for d, *_ in base_events}
    auto = []
    for dt_idx, ret in daily_ret.items():
        if pd.isna(ret) or dt_idx.date() in existing_dates:
            continue
        if abs(ret) < threshold:
            continue
        pct = ret * 100
        if ret > 0:
            auto.append((dt_idx.strftime("%Y-%m-%d"),
                f"급등 {pct:+.1f}%", f"하루 {pct:+.1f}% 변동", "🔥", "up"))
        else:
            auto.append((dt_idx.strftime("%Y-%m-%d"),
                f"급락 {pct:+.1f}%", f"하루 {pct:+.1f}% 변동", "⚡", "down"))
        existing_dates.add(dt_idx.date())
    return auto

BASE_EVENTS = CC["events"]
AUTO_EVENTS = detect_auto_events(ohlc_raw, BASE_EVENTS)
ALL_EVENTS = sorted(BASE_EVENTS + AUTO_EVENTS, key=lambda x: x[0])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KPI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
# Daily Brief (국가별 동적 생성)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
today_str = datetime.now().strftime("%Y년 %m월 %d일")
liq_3m = df["Liquidity"].dropna()
liq_3m_chg = ((liq_3m.iloc[-1] - liq_3m.iloc[-63]) / liq_3m.iloc[-63] * 100) if len(liq_3m) > 63 else 0
sp_1m = df["SP500"].dropna()
sp_1m_chg = ((sp_1m.iloc[-1] - sp_1m.iloc[-21]) / sp_1m.iloc[-21] * 100) if len(sp_1m) > 21 else 0

if corr_val > 0.5 and liq_3m_chg > 0:
    signal_class, signal_text = "signal-bullish", "🟢 유동성 확장 + 강한 상관 → 주가 상승 지지"
elif corr_val < 0 or liq_3m_chg < -1:
    signal_class, signal_text = "signal-bearish", "🔴 유동성 수축 또는 상관 이탈 → 경계 필요"
else:
    signal_class, signal_text = "signal-neutral", "🟡 혼합 시그널 → 방향성 주시"

if country == "🇺🇸 미국":
    brief_policy = (
        '<strong>▎연준 정책 현황</strong><br>'
        '연방기금금리 <span class="hl">3.50–3.75%</span> 유지 (1/28 FOMC). '
        'QT는 12/1에 공식 종료되었으며, 12/12부터 <strong>준비금 관리 매입(RMP)</strong>을 통해 국채 매입을 재개하여 '
        '사실상 대차대조표 확장으로 전환했습니다. 파월 의장 임기 만료(5월)를 앞두고 '
        '케빈 워시(Kevin Warsh)가 차기 의장으로 지명되었으며, '
        '시장은 하반기 1~2회 추가 인하를 기대하고 있습니다.'
    )
    brief_liq = (
        f'<strong>▎유동성 데이터</strong><br>'
        f'본원통화 최신치 <span class="hl">{liq_display}</span> (YoY {liq_yoy:+.1f}%). '
        f'3개월 변화율 <span class="hl">{liq_3m_chg:+.1f}%</span>. '
        f'QT 종료와 RMP 개시로 유동성 바닥이 형성되었으며, 완만한 확장 추세에 진입했습니다.'
    )
    brief_market = (
        f'<strong>▎시장 반응</strong><br>'
        f'{idx_name} <span class="hl">{sp_val:,.0f}</span> (1개월 {sp_1m_chg:+.1f}%, YoY {sp_yoy:+.1f}%). '
        f'AI 슈퍼사이클과 OBBBA(감세 연장·R&D 비용처리) 재정부양이 주가를 지지하나, '
        f'높은 밸류에이션(CAPE ~39배)과 시장 집중도 심화가 리스크입니다.'
    )
else:  # 한국
    brief_policy = (
        '<strong>▎한국은행 통화정책 현황</strong><br>'
        '기준금리 <span class="hl">2.50%</span> (2025/6 기준). '
        '글로벌 긴축 완화 흐름에 맞춰 한은도 인하 기조를 유지하고 있으며, '
        '원/달러 환율 안정과 가계부채 관리가 추가 인하의 핵심 변수입니다. '
        '수출 회복과 반도체 업황 개선이 경기 지지 요인입니다.'
    )
    brief_liq = (
        f'<strong>▎유동성 데이터</strong><br>'
        f'Fed 본원통화(글로벌 유동성 지표) 최신치 <span class="hl">{liq_display}</span> (YoY {liq_yoy:+.1f}%). '
        f'3개월 변화율 <span class="hl">{liq_3m_chg:+.1f}%</span>. '
        f'한국 증시는 미 달러 유동성에 높은 민감도를 보이며, Fed 정책 방향이 핵심 변수입니다.'
    )
    brief_market = (
        f'<strong>▎시장 반응</strong><br>'
        f'{idx_name} <span class="hl">{sp_val:,.0f}</span> (1개월 {sp_1m_chg:+.1f}%, YoY {sp_yoy:+.1f}%). '
        f'반도체 수출 호조와 AI 수혜 기대감이 시장을 지지하나, '
        f'미중 관세 리스크와 원화 약세, 코리아 디스카운트가 지속적 부담입니다.'
    )

brief_corr = (
    f'<strong>▎상관관계 진단</strong><br>'
    f'90일 롤링 상관계수 <span class="hl">{corr_val:.3f}</span>. '
    + ('유동성과 주가가 강한 동행 관계를 유지 중입니다.' if corr_val > 0.5
       else '유동성-주가 동조성이 약화된 구간입니다.' if corr_val > 0
       else '음의 상관으로 전환된 특이 구간입니다.')
)

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
    f'</div>'
    f'<div class="report-signal {signal_class}">{signal_text}</div>'
    f'</div>',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 차트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
dff = df[df.index >= pd.to_datetime(cutoff)].copy()

# ── 캔들스틱 OHLC 리샘플 헬퍼 ──
def resample_ohlc(ohlc_df, rule):
    """OHLC를 주봉(W) 또는 월봉(ME)으로 리샘플"""
    return ohlc_df.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

# 기간 필터링된 OHLC 데이터
ohlc_filtered = ohlc_raw[ohlc_raw.index >= pd.to_datetime(cutoff)].copy()

if tf == "주봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "W")
elif tf == "월봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "ME")
else:
    ohlc_chart = ohlc_filtered.copy()

# 이동평균 (20, 60, 120 — 봉 주기에 맞게)
for ma_len in [20, 60, 120]:
    ohlc_chart[f"MA{ma_len}"] = ohlc_chart["Close"].rolling(ma_len).mean()

# 거래량 색상
vol_colors = ["#ef4444" if c < o else "#10b981"
              for o, c in zip(ohlc_chart["Open"], ohlc_chart["Close"])]

fig_candle = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
    row_heights=[0.75, 0.25],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

# 유동성 (우측 Y축, 배경 영역) — 캔들 뒤에 깔기
liq_series = dff["Liq_MA"].dropna()
liq_hover_fmt = f"%{{y:,.0f}}{CC['liq_suffix']}<extra>{CC['liq_label']}</extra>"
fig_candle.add_trace(go.Scatter(
    x=liq_series.index, y=liq_series, name=f"{CC['liq_label']} ({CC['liq_unit']})",
    fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
    line=dict(color="rgba(59,130,246,0.4)", width=1.5),
    hovertemplate=liq_hover_fmt
), row=1, col=1, secondary_y=True)

# 캔들스틱
fig_candle.add_trace(go.Candlestick(
    x=ohlc_chart.index,
    open=ohlc_chart["Open"], high=ohlc_chart["High"],
    low=ohlc_chart["Low"], close=ohlc_chart["Close"],
    increasing_line_color="#10b981", increasing_fillcolor="#10b981",
    decreasing_line_color="#ef4444", decreasing_fillcolor="#ef4444",
    name=idx_name, whiskerwidth=0.4,
), row=1, col=1)

# 이동평균선
ma_colors = {"MA20": "#f59e0b", "MA60": "#3b82f6", "MA120": "#8b5cf6"}
for ma_name, ma_color in ma_colors.items():
    s = ohlc_chart[ma_name].dropna()
    if len(s) > 0:
        fig_candle.add_trace(go.Scatter(
            x=s.index, y=s, name=ma_name,
            line=dict(color=ma_color, width=1.3),
            hovertemplate="%{y:,.0f}<extra>" + ma_name + "</extra>"
        ), row=1, col=1)

# 거래량
fig_candle.add_trace(go.Bar(
    x=ohlc_chart.index, y=ohlc_chart["Volume"], name="거래량",
    marker_color=vol_colors, opacity=0.5, showlegend=False,
    hovertemplate="%{y:,.0f}<extra>Volume</extra>"
), row=2, col=1)

# 이벤트 표시 (봉 주기에 따라 최소 간격 조절)
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
        fig_candle.add_vline(x=dt, line_width=1, line_dash="dot",
            line_color=C["event"], row="all", col=1)
        clr = "#10b981" if direction == "up" else "#ef4444"
        fig_candle.add_annotation(x=dt, y=1.04, yref="paper",
            text=f"{emoji} {title}", showarrow=False,
            font=dict(size=11, color=clr), textangle=-38, xanchor="left")

# 리세션 음영
add_recession(fig_candle, dff, True)

fig_candle.update_layout(
    **BASE_LAYOUT, height=700, showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="center", x=0.5, font=dict(size=11),
                bgcolor="rgba(0,0,0,0)"),
    xaxis_rangeslider_visible=False,
)
fig_candle.update_xaxes(ax(), row=1, col=1)
fig_candle.update_xaxes(ax(), row=2, col=1)
fig_candle.update_yaxes(ax(dict(title_text=idx_name)), row=1, col=1, secondary_y=False)
# 유동성 Y축 범위 계산: 데이터 하한 기반으로 동적 설정
liq_min_val = liq_series.min()
liq_max_val = liq_series.max()
liq_y_min = liq_min_val * 0.85  # 하한 15% 여유
liq_y_max = liq_y_min + (liq_max_val - liq_y_min) / 0.6  # 변동 시각화 확대

fig_candle.update_yaxes(ax(dict(title_text=f"{CC['liq_label']} ({CC['liq_unit']})",
    title_font=dict(color="#3b82f6"), tickfont=dict(color="#3b82f6", size=10),
    showgrid=False, range=[liq_y_min, liq_y_max])), row=1, col=1, secondary_y=True)
fig_candle.update_yaxes(ax(dict(title_text="거래량", tickformat=".2s", fixedrange=True)), row=2, col=1)

st.plotly_chart(fig_candle, use_container_width=True,
                config={"scrollZoom": True,
                        "displayModeBar": True,
                        "modeBarButtonsToRemove": [
                            "select2d", "lasso2d", "autoScale2d",
                            "hoverClosestCartesian", "hoverCompareCartesian",
                            "toggleSpikelines",
                        ],
                        "displaylogo": False,
                        "responsive": True})

# 모바일 핀치 줌 강제 활성화 (JS 주입)
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
    chg_cls = "up" if chg >= 0 else "down"
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