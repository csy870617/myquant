import setuptools
import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 1. [Design] 고급 CSS 스타일 주입 ---
def inject_pro_css():
    st.markdown("""
        <style>
        /* 기본 폰트 및 배경 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', sans-serif;
            background-color: #f1f5f9; /* 연한 그레이 블루 배경 */
        }

        /* 메트릭 카드 개별 스타일 */
        div[data-testid="stMetric"] {
            background: white;
            border-radius: 12px;
            padding: 20px 25px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            transition: transform 0.2s ease-in-out;
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            border-color: #3b82f6;
        }

        /* 제목 스타일 */
        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            color: #1e293b;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }

        /* 섹션 구분선 및 헤더 */
        .section-header {
            border-left: 5px solid #3b82f6;
            padding-left: 15px;
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-size: 1.25rem;
            font-weight: 600;
            color: #334155;
        }

        /* 탭 디자인 커스텀 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: white;
            border-radius: 8px 8px 0px 0px;
            gap: 1px;
            padding-left: 20px;
            padding-right: 20px;
        }

        .stTabs [aria-selected="true"] {
            background-color: #eff6ff !important;
            border-bottom: 3px solid #3b82f6 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. [Logic] 데이터 분석 엔진 (기존 정교화 모델) ---
@st.cache_data(ttl=3600)
def get_pro_data():
    try:
        end = datetime.now()
        start = end - timedelta(days=365 * 5)
        symbols = {'WALCL': 'Fed', 'WDTGAL': 'TGA', 'RRPONTSYD': 'RRP', 'SP500': 'SP500'}
        df = web.DataReader(list(symbols.keys()), 'fred', start, end).ffill()
        df.columns = [symbols[col] for col in df.columns]
        
        # 가공
        df['Net_Liq'] = (df['Fed'] / 1000) - df['TGA'] - df['RRP']
        df = df.rolling(window=4).mean().dropna() # 4주 이동평균
        
        # 인덱스 (최근 2년 기준)
        window = 104
        df['Liq_Idx'] = df['Net_Liq'].rolling(window=window).apply(lambda x: (x[-1]-x.min())/(x.max()-x.min())*100 if x.max()!=x.min() else 50)
        df['Overheat'] = (df['SP500']/df['Net_Liq']).rolling(window=window).apply(lambda x: (x[-1]-x.min())/(x.max()-x.min())*100 if x.max()!=x.min() else 50)
        
        return df
    except Exception as e:
        st.error(f"데이터 수집 에러: {e}")
        return None

# --- 3. [View] 화면 렌더링 ---
st.set_page_config(page_title="Liquidity Quant Terminal", layout="wide")
inject_pro_css()

st.markdown('<p class="main-title">🌊 Liquidity Quant Terminal</p>', unsafe_allow_html=True)
st.markdown("미 연준 순유동성 기반 중장기 마켓 타이밍 보조 도구")

data = get_pro_data()

if data is not None:
    curr = data.iloc[-1]
    prev = data.iloc[-5]
    
    # 1. 최상단 메트릭 섹션
    st.markdown('<div class="section-header">Market Snapshot</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("시장 과열도 (Overheat)", f"{curr['Overheat']:.1f}%", f"{curr['Overheat']-prev['Overheat']:.1f}%", delta_color="inverse")
    with c2:
        st.metric("유동성 지수 (Liquidity)", f"{curr['Liq_Idx']:.1f}%", f"{curr['Liq_Idx']-prev['Liq_Idx']:.1f}%")
    with c3:
        st.metric("순유동성 ($B)", f"{curr['Net_Liq']:,.1f}", f"{curr['Net_Liq']-prev['Net_Liq']:,.1f}B")
    with c4:
        st.metric("S&P 500 Index", f"{curr['SP500']:,.0f}", f"{curr['SP500']-prev['SP500']:,.0f}")

    # 2. 메인 차트 섹션 (탭 구성)
    st.markdown('<div class="section-header">Advanced Analysis</div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["📈 유동성 vs 주가 괴리율", "🧭 위험 판단 가이드"])
    
    with t1:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=data.index, y=data['Net_Liq'], name="Net Liquidity", fill='tozeroy', line=dict(color='#3b82f6', width=1.5)), secondary_y=False)
        fig.add_trace(go.Scatter(x=data.index, y=data['SP500'], name="S&P 500", line=dict(color='#ef4444', width=2.5)), secondary_y=True)
        
        fig.update_layout(
            hovermode="x unified",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        # 과열도에 따른 시각적 진단 카드
        score = curr['Overheat']
        if score > 80:
            st.error(f"### 🚨 위험: 과열 지수 {score:.1f}% - 유동성 대비 주가가 지나치게 비쌉니다.")
        elif score < 30:
            st.success(f"### ✅ 기회: 과열 지수 {score:.1f}% - 유동성 대비 주가가 저렴하거나 매집하기 좋은 시점입니다.")
        else:
            st.info(f"### ℹ️ 중립: 과열 지수 {score:.1f}% - 주가가 자금력 범위 내에서 움직이고 있습니다.")

else:
    st.warning("데이터를 불러오는 중입니다. 잠시만 기다려주세요...")