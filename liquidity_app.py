import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 페이지 설정 (즐겨찾기 아이콘 적용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="유동성 × 시장 분석기", 
    page_icon="icon.png",  
    layout="wide"
)

# 로고 적용
try:
    st.logo("icon.png")
except Exception:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침 (로직 유지)
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
    local_next = next_t.astimezone(ZoneInfo("Asia/Seoul"))
    return local_next, secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()
st.markdown(
    f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ★ 디자인 전면 수정 (CSS)
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
    --accent-warn: #F59E0B;
    --border-color: rgba(229, 231, 235, 0.8);
    --shadow-soft: 0 10px 40px -10px rgba(0,0,0,0.05);
    --shadow-hover: 0 20px 40px -10px rgba(0,0,0,0.1);
    --radius-l: 24px;
    --radius-m: 16px;
    --radius-s: 12px;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', sans-serif;
    background-color: var(--bg-color) !important;
    color: var(--text-main);
}

/* 상단 헤더 숨김 및 패딩 조정 */
[data-testid="stHeader"] { background: transparent !important; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 1400px;
}

/* ── Typography & Header ── */
.header-container {
    display: flex; flex-direction: column; align-items: flex-start;
    margin-bottom: 2rem; position: relative;
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
.header-desc {
    font-size: 1rem; color: var(--text-sub); font-weight: 400; line-height: 1.5;
}

/* ── Bento Grid System ── */
.bento-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;
}
.bento-card {
    background: var(--card-bg);
    border-radius: var(--radius-l);
    padding: 1.5rem;
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-soft);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    position: relative; overflow: hidden;
    display: flex; flex-direction: column; justify-content: space-between;
}
.bento-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-hover);
    border-color: rgba(59,130,246,0.3);
}

/* KPI Styles */
.kpi-title {
    font-size: 0.8rem; font-weight: 600; color: var(--text-sub);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;
    display: flex; align-items: center; gap: 6px;
}
.kpi-metric {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem; font-weight: 700; color: var(--text-main);
    letter-spacing: -0.04em; margin-bottom: 4px;
}
.kpi-sub {
    font-size: 0.85rem; font-weight: 500; display: flex; align-items: center; gap: 4px;
}
.trend-up { color: var(--accent-success); background: rgba(16,185,129,0.1); padding: 2px 8px; border-radius: 6px; }
.trend-down { color: var(--accent-danger); background: rgba(239,68,68,0.1); padding: 2px 8px; border-radius: 6px; }

/* ── Report Card (Modern Chat Bubble Style) ── */
.report-container {
    background: #FFFFFF;
    border-radius: var(--radius-l);
    border: 1px solid var(--border-color);
    padding: 2rem; margin-bottom: 24px;
    box-shadow: var(--shadow-soft);
}
.report-top {
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px dashed var(--border-color); padding-bottom: 1.2rem; margin-bottom: 1.2rem;
}
.report-hl {
    background: linear-gradient(90deg, rgba(59,130,246,0.1), transparent);
    color: var(--accent-primary); padding: 2px 6px; border-radius: 4px; font-weight: 700;
}
.signal-badge {
    padding: 6px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;
    display: inline-flex; align-items: center; gap: 6px;
}
.sig-bull { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
.sig-bear { background: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; }
.sig-neu  { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }

/* ── Timeline (Modern Track) ── */
.timeline-track {
    position: relative; padding-left: 24px; margin-top: 1rem;
}
.timeline-track::before {
    content: ''; position: absolute; left: 6px; top: 0; bottom: 0;
    width: 2px; background: #E5E7EB; border-radius: 2px;
}
.tl-card {
    position: relative; background: #fff; margin-bottom: 16px;
    padding: 16px; border-radius: var(--radius-m);
    border: 1px solid var(--border-color);
    transition: transform 0.2s;
}
.tl-card:hover { background: #FAFAFA; }
.tl-dot {
    position: absolute; left: -23px; top: 20px;
    width: 10px; height: 10px; background: #fff;
    border: 2px solid var(--accent-primary); border-radius: 50%;
    z-index: 2;
}
.tl-date {
    font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-sub); margin-bottom: 4px;
}
.tl-head {
    display: flex; justify-content: space-between; align-items: flex-start;
}
.tl-tag {
    font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 100px; text-transform: uppercase;
}
.tag-up { background: #ECFDF5; color: #059669; }
.tag-down { background: #FEF2F2; color: #DC2626; }

/* ── Control Bar Styling ── */
div[data-testid="stHorizontalBlock"] {
    background: white; padding: 12px; border-radius: 16px;
    border: 1px solid var(--border-color); box-shadow: var(--shadow-soft);
    align-items: center;
}
.stSelectbox label { font-size: 0.75rem !important; font-weight: 700 !important; color: #9CA3AF !important; }
.stSelectbox div[data-baseweb="select"] > div {
    background-color: #F9FAFB !important; border: 1px solid #E5E7EB !important; border-radius: 8px !important;
}

/* ── Chart Container ── */
.chart-wrapper {
    background: white; border-radius: var(--radius-l);
    border: 1px solid var(--border-color); padding: 16px;
    box-shadow: var(--shadow-soft);
}

/* ── Refresh Bar ── */
.status-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: #fff; border: 1px solid #E5E7EB;
    padding: 6px 16px; border-radius: 100px;
    font-size: 0.75rem; color: var(--text-sub); font-weight: 500;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03); margin-bottom: 1.5rem;
}
.status-dot { width: 8px; height: 8px; background: #10B981; border-radius: 50%; animation: pulse 2s infinite; }

/* Mobile Optimization */
@media (max-width: 768px) {
    .bento-grid { grid-template-columns: repeat(2, 1fr); }
    .header-title { font-size: 1.6rem; }
    .kpi-metric { font-size: 1.4rem; }
}
@media (max-width: 480px) {
    .bento-grid { grid-template-columns: 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 & 이벤트 로드 (변경 없음)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# (기존 데이터 정의 코드 생략 없이 그대로 유지한다고 가정)
MARKET_PIVOTS = [
    ("2015-08-24", "중국발 블랙먼데이", "위안 절하·중국 증시 폭락 → 글로벌 동반 급락 -3.9%", "🇨🇳", "down"),
    ("2016-02-11", "유가 폭락 바닥", "WTI $26 → 에너지·은행주 바닥 형성, S&P 1,829", "🛢️", "down"),
    ("2016-06-23", "브렉시트 투표", "영국 EU 탈퇴 결정 → 이틀간 -5.3% 후 빠른 회복", "🇬🇧", "down"),
    ("2016-11-08", "트럼프 1기 당선", "감세 기대 → 리플레이션 랠리", "🗳️", "up"),
    ("2017-12-22", "TCJA 감세법 서명", "법인세 35→21% 인하, 기업이익 급증", "📝", "up"),
    ("2018-02-05", "VIX 폭발 (볼마겟돈)", "변동성 상품 붕괴 → 하루 -4%, XIV 청산", "💣", "down"),
    ("2018-10-01", "미중 무역전쟁 격화", "관세 확대 → 불확실성 급등, Q4 -14%", "⚔️", "down"),
    ("2018-12-24", "파월 피벗", "금리 인상 중단 시사 → 크리스마스 랠리", "🔄", "up"),
    ("2019-07-31", "첫 금리인하 (10년만)", "보험적 인하 25bp → 경기 확장 연장", "📉", "up"),
    ("2019-09-17", "레포 시장 위기", "단기자금 금리 10% 급등 → 긴급 유동성 공급", "🏧", "down"),
    ("2020-02-20", "코로나19 팬데믹 시작", "글로벌 봉쇄 → -34% 역대급 폭락", "🦠", "down"),
    ("2020-03-23", "무제한 QE 선언", "Fed 무한 양적완화 → V자 반등 시작", "💵", "up"),
    ("2020-11-09", "화이자 백신 발표", "코로나 백신 성공 → 가치주·소형주 대전환 랠리", "💉", "up"),
    ("2021-11-22", "인플레 피크 & 긴축 예고", "CPI 7%대, 테이퍼링 예고 → 성장주 하락 전환", "📉", "down"),
    ("2022-01-26", "Fed 매파 전환", "'곧 금리 인상' 시사 → 나스닥 -15%", "🦅", "down"),
    ("2022-02-24", "러-우 전쟁 개전", "에너지 위기 → 스태그플레이션 공포", "💥", "down"),
    ("2022-03-16", "긴축 사이클 개시", "첫 25bp 인상 → 11회 연속 인상 시작, 총 525bp", "⬆️", "down"),
    ("2022-06-13", "S&P 약세장 진입", "고점 대비 -20% 돌파, 빅테크 폭락", "🐻", "down"),
    ("2022-10-13", "CPI 피크아웃", "인플레 둔화 확인 → 하락장 바닥 형성", "📊", "up"),
    ("2022-11-30", "ChatGPT 출시", "생성형 AI 시대 개막 → AI 투자 광풍의 기폭제", "🧠", "up"),
    ("2023-01-19", "S&P 강세장 전환", "전고점 돌파 → 공식 강세장 진입", "🐂", "up"),
    ("2023-03-12", "SVB 은행 위기", "실리콘밸리은행 파산 → 긴급 유동성 투입(BTFP)", "🏦", "down"),
    ("2023-10-27", "금리 고점 공포", "10년물 5% 돌파 → S&P 200일선 이탈", "📈", "down"),
    ("2024-02-22", "NVIDIA 실적 서프라이즈", "AI 매출 폭증 → 시총 $2T 돌파, AI 랠리 가속", "🚀", "up"),
    ("2024-08-05", "엔 캐리트레이드 청산", "일본 금리인상 → 글로벌 디레버리징, VIX 65", "🇯🇵", "down"),
    ("2024-09-18", "연준 빅컷 (50bp)", "금리인하 사이클 개시, 소형주 급등", "✂️", "up"),
    ("2024-11-05", "트럼프 2기 당선", "감세·규제완화 기대 → 지수 역대 신고가", "🗳️", "up"),
    ("2025-01-27", "DeepSeek AI 쇼크", "중국 저비용 AI 모델 → 반도체주 폭락 (NVDA -17%)", "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세", "전방위 관세 발표 → 이틀간 -10%, VIX 60", "🚨", "down"),
    ("2025-04-09", "관세 90일 유예", "트럼프 관세 일시중단 → 역대급 반등 +9.5%", "🕊️", "up"),
    ("2025-05-12", "미중 제네바 관세 합의", "상호관세 125→10% 인하 → S&P +3.2%, 무역전쟁 완화", "🤝", "up"),
    ("2025-07-04", "OBBBA 법안 통과", "감세 연장·R&D 비용처리 → 기업이익 전망 상향", "📜", "up"),
    ("2025-10-29", "QT 종료 발표", "12/1부터 대차대조표 축소 중단", "🛑", "up"),
    ("2025-12-11", "RMP 국채매입 재개", "준비금 관리 매입 개시 → 유동성 확장 전환", "💰", "up"),
    ("2026-01-28", "S&P 7000 돌파", "14개월 만에 +1,000pt, AI 슈퍼사이클 & OBBBA 효과", "🏆", "up"),
]
MARKET_PIVOTS_KR = [
    ("2015-08-24", "중국발 블랙먼데이", "위안 절하 → KOSPI 1,830선 붕괴, 외국인 대량 매도", "🇨🇳", "down"),
    ("2016-11-08", "트럼프 1기 당선", "신흥국 자금유출 우려 → KOSPI 2,000선 하회", "🗳️", "down"),
    ("2016-12-09", "박근혜 탄핵 가결", "정치 불확실성 해소 기대 → 증시 반등", "⚖️", "up"),
    ("2017-05-10", "문재인 대통령 취임", "경기부양 기대 → KOSPI 2,300 돌파 랠리", "🏛️", "up"),
    ("2017-09-03", "북한 6차 핵실험", "지정학 리스크 → KOSPI 급락 후 빠른 회복", "🚀", "down"),
    ("2018-04-27", "남북 판문점 정상회담", "한반도 평화 기대 → 코리아 디스카운트 축소", "🤝", "up"),
    ("2018-10-01", "미중 무역전쟁 격화", "수출주 직격탄 → KOSPI 2,000선 붕괴", "⚔️", "down"),
    ("2019-07-01", "일본 수출규제", "반도체 소재 수출 제한 → 삼성·SK 타격", "🇯🇵", "down"),
    ("2020-03-19", "코스피 서킷브레이커", "코로나 패닉 → KOSPI 1,457 저점, 사이드카 발동", "🦠", "down"),
    ("2020-03-23", "한은 긴급 기준금리 인하", "0.75%로 빅컷 → 유동성 공급 확대", "💵", "up"),
    ("2020-05-28", "동학개미운동", "개인투자자 대거 유입 → KOSPI 반등 주도", "🐜", "up"),
    ("2020-11-09", "화이자 백신 발표", "수출주 회복 기대 → KOSPI 2,500 돌파", "💉", "up"),
    ("2021-01-07", "KOSPI 3,000 돌파", "역사상 첫 3,000 안착 → 개인 순매수 주도", "🏆", "up"),
    ("2021-06-24", "KOSPI 3,300 역대 최고", "글로벌 유동성 피크 → 바이오·2차전지 과열", "📈", "up"),
    ("2021-11-22", "긴축 예고 & 하락 전환", "금리인상 시작 → 성장주·소형주 급락", "📉", "down"),
    ("2022-02-24", "러-우 전쟁 개전", "에너지 수입국 한국 직격 → KOSPI 2,600선 붕괴", "💥", "down"),
    ("2022-06-23", "한은 빅스텝 (50bp)", "기준금리 1.75→2.25%, 긴축 가속", "⬆️", "down"),
    ("2022-09-26", "KOSPI 2,200 붕괴", "강달러·긴축 → 연중 최저, 외국인 연속 매도", "🐻", "down"),
    ("2022-11-30", "ChatGPT 출시", "AI 수혜주(삼성·SK) 반등 기대감", "🧠", "up"),
    ("2023-01-30", "한은 금리 동결 전환", "3.50% 정점 시사 → 금리 인상 사이클 종료", "🔄", "up"),
    ("2023-05-30", "KOSPI 2,600 회복", "반도체 업황 회복 기대 → 삼성전자 주도 반등", "📊", "up"),
    ("2024-01-02", "밸류업 프로그램 발표", "PBR 1배 미만 기업 개선 요구 → 저PBR주 급등", "📋", "up"),
    ("2024-08-05", "엔 캐리트레이드 청산", "글로벌 디레버리징 → KOSPI -8.8% 블랙먼데이", "🇯🇵", "down"),
    ("2024-12-03", "윤석열 비상계엄 선포", "정치 위기 → KOSPI 급락, 원화 1,440원 돌파", "🚨", "down"),
    ("2024-12-14", "윤석열 탄핵 가결", "불확실성 정점 후 정치 리스크 일부 해소", "⚖️", "up"),
    ("2025-01-27", "DeepSeek AI 쇼크", "중국 AI 충격 → 삼성전자·SK하이닉스 급락", "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세", "한국산 제품 25% 관세 → 수출주 폭락, KOSPI -4%", "🚨", "down"),
    ("2025-04-09", "관세 90일 유예", "한국 포함 유예 → KOSPI +5% 반등", "🕊️", "up"),
    ("2025-05-12", "미중 관세 합의", "글로벌 무역 완화 → 한국 수출 수혜 기대", "🤝", "up"),
    ("2025-06-03", "한은 기준금리 2.50% 인하", "경기 부양 위해 추가 인하 → 유동성 확대", "✂️", "up"),
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
        "data_src": "Federal Reserve (FRED) · Yahoo Finance",
    },
    "🇰🇷 대한민국": {
        "indices": {"KOSPI": "^KS11", "KOSDAQ": "^KQ11"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",        
        "fred_rec": "USREC",           
        "liq_divisor": 1,              
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
            return None, None

        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        if 'SP500' in df.columns:
            df["Liq_MA"] = df["Liquidity"].rolling(10).mean()
            df["SP_MA"] = df["SP500"].rolling(10).mean()
            df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
            df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        else:
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
        return None, None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 차트 헬퍼 (모던 컬러 적용)
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
# 헤더 섹션 (New Design)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div class="header-container">
    <div class="header-badge">QUANT / MACRO INTELLIGENCE</div>
    <div class="header-title">LIQUIDITY & MARKET</div>
    <div class="header-desc">
        중앙은행 본원통화와 주가지수의 상관관계를 실시간으로 추적합니다.<br>
        유동성 사이클의 변곡점을 시각적으로 확인하세요.
    </div>
</div>
""", unsafe_allow_html=True)

# 상태바
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
# 컨트롤 바 (스타일만 변경, 로직 동일)
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
    period = st.selectbox("분석 기간", ["3년", "5년", "7년", "10년", "전체"], index=3)
with ctrl4:
    tf = st.selectbox("캔들 주기", ["일봉", "주봉", "월봉"], index=2)
with ctrl5:
    st.write("") 
    st.write("")
    show_events = st.toggle("이벤트", value=True)

period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 12}
period_years = period_map[period]
cutoff = datetime.now() - timedelta(days=365 * period_years)

with st.spinner("데이터 동기화 중..."):
    df, ohlc_raw = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])

if df is None or df.empty:
    st.error("데이터 로드 실패")
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
# KPI (Bento Cards)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with kpi_container:
    latest = df.dropna(subset=["Liquidity", "SP500"]).iloc[-1]
    liq_val, sp_val = latest["Liquidity"], latest["SP500"]
    liq_yoy = latest["Liq_YoY"] if pd.notna(latest.get("Liq_YoY")) else 0
    sp_yoy = latest["SP_YoY"] if pd.notna(latest.get("SP_YoY")) else 0
    corr_val = df["Corr_90d"].dropna().iloc[-1] if len(df["Corr_90d"].dropna()) > 0 else 0

    def trend_badge(val):
        cls = "trend-up" if val >= 0 else "trend-down"
        txt = f"▲ {val:+.1f}%" if val >= 0 else f"▼ {val:+.1f}%"
        return f'<span class="{cls}">{txt}</span>'

    liq_display = f"{CC['liq_prefix']}{liq_val:,.0f}"
    corr_cls = "trend-up" if corr_val >= 0 else "trend-down"
    
    st.markdown(f"""
    <div class="bento-grid">
        <div class="bento-card">
            <div>
                <div class="kpi-title">💵 {CC['liq_label']}</div>
                <div class="kpi-metric">{liq_display}</div>
            </div>
            <div class="kpi-sub">{trend_badge(liq_yoy)} <span style="color:#9CA3AF; font-size:0.75rem;">vs 1yr</span></div>
        </div>
        <div class="bento-card">
            <div>
                <div class="kpi-title">📈 {idx_name}</div>
                <div class="kpi-metric">{sp_val:,.0f}</div>
            </div>
            <div class="kpi-sub">{trend_badge(sp_yoy)} <span style="color:#9CA3AF; font-size:0.75rem;">vs 1yr</span></div>
        </div>
        <div class="bento-card">
            <div>
                <div class="kpi-title">🔗 90일 상관계수</div>
                <div class="kpi-metric" style="color:{'#10B981' if corr_val>0 else '#EF4444'}">{corr_val:.3f}</div>
            </div>
            <div class="kpi-sub"><span style="color:#6B7280; font-size:0.8rem;">{'양의 상관' if corr_val > 0 else '음의 상관'}</span></div>
        </div>
        <div class="bento-card">
            <div>
                <div class="kpi-title">📅 데이터 범위</div>
                <div class="kpi-metric" style="font-size:1.4rem">{df.index.min().strftime('%y.%m')} — {df.index.max().strftime('%y.%m')}</div>
            </div>
            <div class="kpi-sub"><span class="trend-up" style="color:#3B82F6; background:rgba(59,130,246,0.1)">{len(df):,} Trading Days</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Daily Brief (Modern Chat Style)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with brief_container:
    # (로직 동일)
    liq_3m = df["Liquidity"].dropna()
    liq_3m_chg = ((liq_3m.iloc[-1] - liq_3m.iloc[-63]) / liq_3m.iloc[-63] * 100) if len(liq_3m) > 63 else 0
    sp_1m = df["SP500"].dropna()
    sp_1m_chg = ((sp_1m.iloc[-1] - sp_1m.iloc[-21]) / sp_1m.iloc[-21] * 100) if len(sp_1m) > 21 else 0

    if corr_val > 0.5 and liq_3m_chg > 0:
        sig_cls, sig_txt = "sig-bull", "BULLISH: 유동성 확장 동조"
    elif corr_val < 0 or liq_3m_chg < -1:
        sig_cls, sig_txt = "sig-bear", "BEARISH/CAUTION: 이탈 징후"
    else:
        sig_cls, sig_txt = "sig-neu", "NEUTRAL: 방향성 탐색"

    # 텍스트 생성 로직 (동일)
    if country == "🇺🇸 미국":
        brief_body = (
            f"연준(Fed)의 정책 기조와 시장 반응을 요약합니다.<br><br>"
            f"• <strong>유동성:</strong> 본원통화는 <span class='report-hl'>{liq_display}</span> 수준이며, 3개월간 <span class='report-hl'>{liq_3m_chg:+.1f}%</span> 변동했습니다. "
            f"RMP 및 대차대조표 정책 변화를 주시해야 합니다.<br>"
            f"• <strong>시장:</strong> {idx_name} 지수는 <span class='report-hl'>{sp_val:,.0f}</span>포인트로 마감했습니다. (MoM {sp_1m_chg:+.1f}%)"
        )
    else:
        brief_body = (
            f"한국 시장과 글로벌 유동성의 연동성을 요약합니다.<br><br>"
            f"• <strong>매크로:</strong> Fed 유동성은 <span class='report-hl'>{liq_display}</span>이며 3개월 변동폭은 <span class='report-hl'>{liq_3m_chg:+.1f}%</span>입니다. 원/달러 환율 및 한은 정책이 주요 변수입니다.<br>"
            f"• <strong>시장:</strong> {idx_name} 지수는 <span class='report-hl'>{sp_val:,.0f}</span>포인트를 기록 중입니다."
        )

    st.markdown(f"""
    <div class="report-container">
        <div class="report-top">
            <div style="font-weight:800; font-size:1.1rem; display:flex; align-items:center; gap:8px;">
                <span style="font-size:1.5rem;">💬</span> AI Market Insight
            </div>
            <div class="signal-badge {sig_cls}">{sig_txt}</div>
        </div>
        <div style="line-height:1.8; color:#374151; font-size:0.95rem;">
            {brief_body}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 차트 (Clean Modern)
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

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.8, 0.2], specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

# Liquidity (Area)
liq_series = dff["Liq_MA"].dropna()
fig.add_trace(go.Scatter(
    x=liq_series.index, y=liq_series, name=CC['liq_label'],
    fill="tozeroy", fillcolor=C["liq_fill"], line=dict(color=C["liq"], width=2),
    hovertemplate="%{y:,.0f}"
), row=1, col=1, secondary_y=True)

# Candle
fig.add_trace(go.Candlestick(
    x=ohlc_chart.index, open=ohlc_chart["Open"], high=ohlc_chart["High"],
    low=ohlc_chart["Low"], close=ohlc_chart["Close"],
    increasing_line_color="#10B981", increasing_fillcolor="#10B981",
    decreasing_line_color="#EF4444", decreasing_fillcolor="#EF4444",
    name=idx_name, whiskerwidth=0.4
), row=1, col=1)

# MA
ma_colors = {"MA20": "#F59E0B", "MA60": "#8B5CF6", "MA120": "#6B7280"}
for ma, clr in ma_colors.items():
    s = ohlc_chart[ma].dropna()
    if len(s) > 0: fig.add_trace(go.Scatter(x=s.index, y=s, name=ma, line=dict(color=clr, width=1.5)), row=1, col=1)

# Volume
fig.add_trace(go.Bar(x=ohlc_chart.index, y=ohlc_chart["Volume"], marker_color=vol_colors, opacity=0.4, showlegend=False), row=2, col=1)

# Event Markers
if show_events:
    gap_map = {"일봉": 14, "주봉": 45, "월봉": 120}
    min_gap = gap_map.get(tf, 30)
    prev_dt = None
    for date_str, title, _, emoji, direction in ALL_EVENTS:
        dt = pd.to_datetime(date_str)
        if dt < ohlc_chart.index.min() or dt > ohlc_chart.index.max(): continue
        if prev_dt and (dt - prev_dt).days < min_gap: continue
        prev_dt = dt
        fig.add_vline(x=dt, line_width=1, line_dash="solid", line_color="rgba(0,0,0,0.1)", row="all", col=1)
        # fig.add_annotation(x=dt, y=1.03, yref="paper", text=emoji, showarrow=False, font=dict(size=16))

add_recession(fig, dff, True)

# Layout Update
fig.update_layout(**BASE_LAYOUT, height=650, showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"))

# Axes
fig.update_xaxes(ax(), row=1, col=1)
fig.update_xaxes(ax(), row=2, col=1)
fig.update_yaxes(ax(dict(ticklabelposition="outside", automargin=True)), row=1, col=1, secondary_y=False)
fig.update_yaxes(ax(dict(showgrid=False, tickfont=dict(color=C["liq"]), ticklabelposition="inside")), row=1, col=1, secondary_y=True)
fig.update_yaxes(ax(dict(tickformat=".2s")), row=2, col=1)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True) # End chart wrapper

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Timeline (Clean Track Style)
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
        <div class="tl-head">
            <div class="tl-date">{date_str}</div>
            <div class="tl-tag {tag_cls}">{emoji} {direction.upper()}</div>
        </div>
        <div style="font-weight:700; margin-bottom:4px;">{title}</div>
        <div style="font-size:0.85rem; color:#6B7280;">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Footer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div style="text-align:center; margin-top:3rem; padding:2rem; border-top:1px solid #E5E7EB; color:#9CA3AF; font-size:0.8rem;">
    <strong>Data Source:</strong> FRED (Federal Reserve Economic Data) · Yahoo Finance<br>
    This dashboard is for informational purposes only. Investment decisions should be made based on your own due diligence.
</div>
""", unsafe_allow_html=True)