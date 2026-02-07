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
# 자동 새로고침 (PST 09:00/18:00 + KST 09:00/18:00 = 하루 4회)
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

auto_interval = min(REFRESH_SECS * 1000, 3600_000)
st.markdown(
    f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS (네이버 증권 스타일)
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
    --up-color: #f73646;   /* 네이버 상승 빨강 */
    --down-color: #335eff; /* 네이버 하락 파랑 */
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', sans-serif;
    background: var(--bg) !important; color: var(--text-primary);
}
[data-testid="stHeader"] { background: transparent !important; }

/* 레이아웃 여백 조정 */
.block-container { 
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 100%;
}

/* ── 네이버 스타일 종목 헤더 ── */
.stock-header-container {
    padding-bottom: 15px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 15px;
}
.stock-title-row {
    display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;
}
.stock-name {
    font-size: 1.5rem; font-weight: 800; color: #111; letter-spacing: -0.5px;
}
.stock-ticker {
    font-size: 0.95rem; color: var(--text-secondary); font-weight: 500;
}
.stock-price-row {
    display: flex; align-items: flex-end; gap: 12px;
}
.stock-price {
    font-family: 'Roboto Mono', sans-serif;
    font-size: 2.4rem; font-weight: 700; letter-spacing: -1px; line-height: 1;
}
.stock-change {
    font-size: 1.1rem; font-weight: 600; padding-bottom: 4px;
}
.c-up { color: var(--up-color); }
.c-down { color: var(--down-color); }
.c-flat { color: #333; }

/* ── KPI 요약 바 (헤더 아래) ── */
.summary-bar {
    display: flex; gap: 15px; overflow-x: auto; padding-bottom: 5px; margin-bottom: 10px;
    font-size: 0.85rem; color: #555;
    -ms-overflow-style: none; scrollbar-width: none; /* 스크롤바 숨김 */
}
.summary-bar::-webkit-scrollbar { display: none; }
.summary-item {
    white-space: nowrap; display: flex; align-items: center; gap: 5px;
    background: #f8f9fa; padding: 6px 12px; border-radius: 18px; border: 1px solid #eee;
}
.summary-label { color: #888; font-weight: 500; }
.summary-value { font-weight: 700; color: #333; }

/* ── 컨트롤 바 스타일 ── */
[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; margin-bottom: 10px; }
.stSelectbox label, .stMultiSelect label, .stRadio label {
    font-size: 0.75rem !important; color: #666 !important;
}
/* Selectbox 등을 네이버 필터처럼 */
.stSelectbox > div > div {
    background-color: #f9f9f9 !important; border: 1px solid #ddd !important; border-radius: 6px !important;
}

/* ── 리포트 박스 (Daily Brief) ── */
.report-box {
    background: #f9fbfc; border: 1px solid #e8ecf2;
    border-radius: 12px; padding: 1.2rem; margin-bottom: 1.2rem; margin-top: 1rem;
}
.report-header { display: flex; align-items: center; gap: 8px; margin-bottom: 0.8rem; }
.report-badge {
    background: #222; color: white; font-size: 0.7rem; font-weight: 700;
    padding: 3px 8px; border-radius: 4px;
}
.report-title { font-size: 1rem; font-weight: 700; color: #333; }
.report-body { font-size: 0.88rem; color: #555; line-height: 1.7; }
.report-body strong { color: #111; }
.hl { background: rgba(0,0,0,0.05); padding: 0 4px; border-radius: 3px; font-weight: 600; }
.report-divider { border-top: 1px dashed #ddd; margin: 10px 0; }

/* ── 타임라인 ── */
.timeline { display: flex; flex-direction: column; gap: 0; border-top: 1px solid #eee; margin-top: 10px; }
.tl-item { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f5f5f5; font-size: 0.88rem; }
.tl-date { color: #999; font-size: 0.8rem; min-width: 75px; }
.tl-content { flex: 1; }
.tl-title { font-weight: 600; color: #333; margin-bottom: 2px; }
.tl-desc { font-size: 0.8rem; color: #666; }
.tl-dir { font-size: 0.75rem; font-weight: 700; }
.tl-dir.up { color: var(--up-color); }
.tl-dir.down { color: var(--down-color); }

/* ── Plotly 차트 ── */
[data-testid="stPlotlyChart"] { width: 100% !important; margin-top: -10px; }
/* 툴바 오버레이 */
.modebar { 
    opacity: 0.8 !important; 
    top: 5px !important; right: 5px !important; bottom: auto !important; left: auto !important;
    background: rgba(255,255,255,0.9) !important; border-radius: 4px;
}

/* 모바일 최적화 */
@media (max-width: 768px) {
    .stock-price { font-size: 2rem; }
    .stock-name { font-size: 1.3rem; }
    .summary-bar { gap: 8px; font-size: 0.75rem; }
    .summary-item { padding: 4px 10px; }
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

        # [A] FRED 데이터
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

        # [B] 주가 데이터
        try:
            import yfinance as yf
            yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
            
            if yf_data.empty:
                st.error("지수 데이터를 가져오지 못했습니다.")
                return None, None
            
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

        # [C] 통합
        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        
        if 'SP500' in df.columns:
            df["Liq_MA"] = df["Liquidity"].rolling(10).mean()
            df["SP_MA"] = df["SP500"].rolling(10).mean()
            df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
            df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        
        df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])

        cut = end_dt - timedelta(days=365 * 12)
        df = df[df.index >= pd.to_datetime(cut)]
        ohlc = ohlc[ohlc.index >= pd.to_datetime(cut)]
        return df.dropna(subset=["SP500"]), ohlc.dropna(subset=["Close"])
        
    except Exception as e:
        st.error(f"시스템 오류: {str(e)}")
        return None, None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 컨트롤 바 (상단 배치)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1, 1])
with ctrl1:
    country = st.selectbox("🌍 국가", list(COUNTRY_CONFIG.keys()), index=0)
CC = COUNTRY_CONFIG[country]
IDX_OPTIONS = CC["indices"]

if st.session_state.get("_prev_country") != country:
    st.session_state["_prev_country"] = country
    st.session_state["idx_select"] = list(IDX_OPTIONS.keys())[CC["default_idx"]]

with ctrl2:
    idx_name = st.selectbox("📈 지수", list(IDX_OPTIONS.keys()), key="idx_select")
    idx_ticker = IDX_OPTIONS[idx_name]
with ctrl3:
    period = st.selectbox("📅 기간", ["3년", "5년", "7년", "10년", "전체"], index=3)
with ctrl4:
    tf = st.selectbox("🕯️ 봉", ["일봉", "주봉", "월봉"], index=2)
with ctrl5:
    show_events = st.toggle("📌 이벤트", value=True)

period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 12}
cutoff = datetime.now() - timedelta(days=365 * period_map[period])

with st.spinner("데이터 로딩중..."):
    df, ohlc_raw = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])

if df is None or df.empty:
    st.stop()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 네이버 스타일 헤더 (종목정보 + 요약)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
latest = df.dropna(subset=["SP500"]).iloc[-1]
prev = df.dropna(subset=["SP500"]).iloc[-2]
cur_price = latest["SP500"]
diff = cur_price - prev["SP500"]
pct = (diff / prev["SP500"]) * 100

color_cls = "c-up" if diff > 0 else "c-down" if diff < 0 else "c-flat"
sign = "+" if diff > 0 else ""
arrow = "▲" if diff > 0 else "▼" if diff < 0 else "-"

# 헤더 출력
st.markdown(f"""
<div class="stock-header-container">
    <div class="stock-title-row">
        <span class="stock-name">{idx_name}</span>
        <span class="stock-ticker">{idx_ticker}</span>
    </div>
    <div class="stock-price-row {color_cls}">
        <span class="stock-price">{cur_price:,.2f}</span>
        <span class="stock-change">{arrow} {abs(diff):,.2f} ({sign}{pct:.2f}%)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI 요약 바 (헤더 바로 아래)
liq_val = latest["Liquidity"]
liq_yoy = latest["Liq_YoY"]
corr_val = df["Corr_90d"].iloc[-1]

st.markdown(f"""
<div class="summary-bar">
    <div class="summary-item">
        <span class="summary-label">{CC['liq_label']}</span>
        <span class="summary-value" style="color:#333">{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}</span>
    </div>
    <div class="summary-item">
        <span class="summary-label">유동성 YoY</span>
        <span class="summary-value" style="color:{'#f73646' if liq_yoy>0 else '#335eff'}">{liq_yoy:+.1f}%</span>
    </div>
    <div class="summary-item">
        <span class="summary-label">상관계수(90일)</span>
        <span class="summary-value" style="color:{'#33bb55' if corr_val>0.5 else '#555'}">{corr_val:.2f}</span>
    </div>
    <div class="summary-item">
        <span class="summary-label">데이터</span>
        <span class="summary-value">{len(df):,}일</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 차트 데이터 준비 (Gap 제거 포함)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 데이터 필터링
dff = df[df.index >= pd.to_datetime(cutoff)].copy()
ohlc_filtered = ohlc_raw[ohlc_raw.index >= pd.to_datetime(cutoff)].copy()

# 2. 리샘플링
def resample_ohlc(ohlc_df, rule):
    return ohlc_df.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

if tf == "주봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "W")
    dff_chart = dff.resample("W").last().dropna()
elif tf == "월봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "ME")
    dff_chart = dff.resample("ME").last().dropna()
else:
    ohlc_chart = ohlc_filtered.copy()
    dff_chart = dff.copy()

# 3. 이동평균선
for ma in [5, 20, 60, 120]:
    ohlc_chart[f"MA{ma}"] = ohlc_chart["Close"].rolling(ma).mean()

# 4. 차트 구성
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02,
    row_heights=[0.8, 0.2],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# (1) 유동성 (영역 차트, 뒤에 깔림)
fig.add_trace(go.Scatter(
    x=dff_chart.index, y=dff_chart["Liquidity"],
    name=CC['liq_label'],
    fill="tozeroy", fillcolor="rgba(59,130,246,0.05)",
    line=dict(color="rgba(59,130,246,0.3)", width=1),
    hoverinfo="skip" # 겹침 방지
), row=1, col=1, secondary_y=True)

# (2) 캔들스틱 (네이버 색상)
fig.add_trace(go.Candlestick(
    x=ohlc_chart.index,
    open=ohlc_chart["Open"], high=ohlc_chart["High"],
    low=ohlc_chart["Low"], close=ohlc_chart["Close"],
    increasing_line_color="#f73646", increasing_fillcolor="#f73646",
    decreasing_line_color="#335eff", decreasing_fillcolor="#335eff",
    name="주가"
), row=1, col=1)

# (3) 이동평균선
ma_colors = {5: "#999", 20: "#f5a623", 60: "#33bb55", 120: "#aa55ff"}
for ma, color in ma_colors.items():
    if f"MA{ma}" in ohlc_chart.columns:
        fig.add_trace(go.Scatter(
            x=ohlc_chart.index, y=ohlc_chart[f"MA{ma}"],
            mode='lines', line=dict(color=color, width=1),
            name=f"{ma}선"
        ), row=1, col=1)

# (4) 거래량
vol_colors = ["#f73646" if c > o else "#335eff" for o, c in zip(ohlc_chart["Open"], ohlc_chart["Close"])]
fig.add_trace(go.Bar(
    x=ohlc_chart.index, y=ohlc_chart["Volume"],
    marker_color=vol_colors, showlegend=False,
    name="거래량"
), row=2, col=1)

# (5) 이벤트 마커
if show_events:
    # 이벤트 자동 감지 등 기존 로직 활용
    ALL_EVENTS = sorted(CC["events"] + detect_auto_events(ohlc_raw, CC["events"]), key=lambda x: x[0])
    prev_dt = None
    min_gap = {"일봉": 10, "주봉": 40, "월봉": 100}.get(tf, 20)
    
    for date_str, title, _, emoji, direction in ALL_EVENTS:
        dt = pd.to_datetime(date_str)
        if dt < ohlc_chart.index.min() or dt > ohlc_chart.index.max(): continue
        if prev_dt and (dt - prev_dt).days < min_gap: continue
        
        prev_dt = dt
        # 수직선
        fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color="#ccc", row="all", col=1)
        # 텍스트
        clr = "#f73646" if direction == "up" else "#335eff"
        fig.add_annotation(x=dt, y=1.02, yref="paper", text=f"{emoji}", 
                           showarrow=False, font=dict(size=14), row=1, col=1)

# (6) 리세션
add_recession(fig, dff, True)

# (7) 레이아웃 설정
layout_opts = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(t=40, b=20, l=10, r=50), # 우측 여백 확보 (Y축)
    height=600,
    hovermode="x unified",
    dragmode="pan",
    showlegend=True,
    legend=dict(
        orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01,
        bgcolor="rgba(255,255,255,0.6)", bordercolor="#eee", borderwidth=1, font=dict(size=10)
    ),
    xaxis_rangeslider_visible=False,
)

# ★ 핵심: 주말 Gap 제거 (rangebreaks)
# 일봉일 때만 적용 (주봉/월봉은 이미 연속됨)
if tf == "일봉":
    # 1. 간단한 주말 제거 (토, 일)
    rangebreaks = [dict(bounds=["sat", "mon"])] 
    layout_opts["xaxis"] = dict(rangebreaks=rangebreaks)

fig.update_layout(**layout_opts)

# 축 설정
fig.update_xaxes(gridcolor="#f5f5f5", showgrid=True, row=1, col=1)
fig.update_xaxes(gridcolor="#f5f5f5", showgrid=True, row=2, col=1)

# Y축 (오른쪽 배치 - 네이버 스타일)
fig.update_yaxes(
    side="right", 
    gridcolor="#f5f5f5", showgrid=True,
    tickfont=dict(color="#333", size=11),
    ticklabelposition="outside", 
    zeroline=False,
    row=1, col=1, secondary_y=False
)
# 유동성 축 (왼쪽, 숨김 혹은 작게)
fig.update_yaxes(visible=False, row=1, col=1, secondary_y=True)
# 거래량 축 (오른쪽, 간소화)
fig.update_yaxes(side="right", showgrid=False, tickformat=".2s", row=2, col=1)

# Config
config = {
    'displayModeBar': True,
    'scrollZoom': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d']
}

st.plotly_chart(fig, use_container_width=True, config=config)

# 모바일 핀치 줌 JS
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    var plot = document.querySelector('.js-plotly-plot');
    if(plot) { plot.style.touchAction = 'none'; }
});
</script>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하단 Daily Brief (기존 로직 유지)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# (기존 코드의 Daily Brief 로직을 그대로 사용하되 디자인만 CSS로 변경됨)
with brief_container:
    # ... (기존 Daily Brief 로직과 동일, 위에서 정의한 컨테이너에 내용 채움)
    pass 

# (Daily Brief 내용을 여기에 다시 채워줍니다 - 코드 중복 방지를 위해 위쪽 로직이 실행됨)
# 실제로는 위쪽 'with brief_container' 블록에서 이미 렌더링 됩니다.
# 다만, 순서상 차트 아래에 배치하고 싶다면 컨테이너 순서를 조정하면 됩니다.
# 현재 코드 구조상: 헤더 -> KPI바 -> (컨트롤) -> (차트) -> Daily Brief 순서가 자연스럽습니다.
# 기존 코드의 Daily Brief는 위쪽에서 이미 렌더링 되었습니다.
# 네이버 스타일에서는 차트 아래에 뉴스가 나오므로, Brief를 차트 아래로 옮기겠습니다.

st.markdown("---") # 구분선

# Daily Brief 다시 렌더링 (위쪽 로직 복사)
today_str = datetime.now().strftime("%Y년 %m월 %d일")
liq_3m_chg = ((latest["Liquidity"] - df["Liquidity"].iloc[-63]) / df["Liquidity"].iloc[-63] * 100) if len(df) > 63 else 0
sp_1m_chg = ((latest["SP500"] - df["SP500"].iloc[-21]) / df["SP500"].iloc[-21] * 100) if len(df) > 21 else 0

if country == "🇺🇸 미국":
    brief_content = f"""
    <strong>🇺🇸 미국 시장 브리핑 ({today_str})</strong><br>
    최근 3개월간 <strong>{CC['liq_label']}</strong>는 <span class="hl">{liq_3m_chg:+.1f}%</span> 변동했습니다.
    시장 지수는 1개월간 <span class="hl">{sp_1m_chg:+.1f}%</span> 움직였습니다.
    연준의 정책 변화와 유동성 흐름이 주가에 미치는 영향을 주시하세요. 
    상관계수가 {corr_val:.2f}로, 유동성과 주가의 동행성이 {'높습니다' if corr_val > 0.5 else '낮습니다'}.
    """
else:
    brief_content = f"""
    <strong>🇰🇷 한국 시장 브리핑 ({today_str})</strong><br>
    글로벌 유동성(Fed)은 최근 3개월 <span class="hl">{liq_3m_chg:+.1f}%</span> 변동했습니다.
    한국 증시는 대외 변수에 민감하게 반응하며, 최근 1개월 <span class="hl">{sp_1m_chg:+.1f}%</span>의 등락을 보였습니다.
    """

st.markdown(f"""
<div class="report-box">
    <div class="report-header">
        <span class="report-badge">Brief</span>
        <span class="report-title">Market Insight</span>
    </div>
    <div class="report-body">
        {brief_content}
    </div>
</div>
""", unsafe_allow_html=True)

# 타임라인 (하단 배치)
st.markdown('<div style="font-weight:700; font-size:1.1rem; margin-top:20px;">📅 주요 이벤트 타임라인</div>', unsafe_allow_html=True)
tl_html = '<div class="timeline">'
for date_str, title, desc, emoji, direction in reversed(ALL_EVENTS):
    if pd.to_datetime(date_str) < dff.index.min(): continue
    dir_cls = "up" if direction == "up" else "down"
    tl_html += f"""
    <div class="tl-item">
        <div class="tl-date">{date_str}</div>
        <div class="tl-content">
            <div class="tl-title">{emoji} {title} <span class="tl-dir {dir_cls}">●</span></div>
            <div class="tl-desc">{desc}</div>
        </div>
    </div>"""
tl_html += "</div>"
st.markdown(tl_html, unsafe_allow_html=True)

# 푸터
st.markdown(
    f'<div class="app-footer" style="margin-top:30px; color:#999; font-size:0.8rem; text-align:center;">'
    f'Data Source: {CC["data_src"]} <br> 본 페이지는 투자 조언을 제공하지 않습니다.'
    f'</div>',
    unsafe_allow_html=True,
)