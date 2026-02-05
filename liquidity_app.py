import setuptools  # Python 3.12+ 버전의 distutils 에러 방지용
import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 1. 기본 설정 ---
st.set_page_config(page_title="Quant Liquidity Pro", layout="wide")
LOOKBACK_YEARS = 5
INDEX_WINDOW = 104  # 최근 2년(104주) 기준 상대적 위치 계산

# --- 2. 데이터 수집 함수 (에러 방지 로직 포함) ---
@st.cache_data(ttl=3600)
def get_combined_data():
    try:
        end = datetime.now()
        start = end - timedelta(days=365 * LOOKBACK_YEARS)
        
        # FRED 데이터 심볼: 자산(WALCL), 재무부(WDTGAL), 역레포(RRPONTSYD), S&P500(SP500)
        symbols = {
            'WALCL': 'Fed_Assets', 
            'WDTGAL': 'TGA', 
            'RRPONTSYD': 'RRP',
            'SP500': 'SP500'
        }
        
        # 데이터 수집
        df = web.DataReader(list(symbols.keys()), 'fred', start, end)
        df.columns = [symbols[col] for col in df.columns]
        
        # 주말/공휴일 결측치 채우기 및 4주 이동평균으로 노이즈 제거
        df = df.ffill()
        df['Fed_Assets'] = (df['Fed_Assets'] / 1000).rolling(window=4).mean()
        df['TGA'] = df['TGA'].rolling(window=4).mean()
        df['RRP'] = df['RRP'].rolling(window=4).mean()
        df['SP500'] = df['SP500'].rolling(window=4).mean()
        
        # 순유동성(Net Liquidity) 계산
        df['Net_Liquidity'] = df['Fed_Assets'] - df['TGA'] - df['RRP']
        
        # 유동성 지수화 (Rolling Percentile)
        df['Liquidity_Index'] = df['Net_Liquidity'].rolling(window=INDEX_WINDOW).apply(
            lambda x: (x[-1] - x.min()) / (x.max() - x.min()) * 100 if (x.max() != x.min()) else 50
        )
        
        # 시장 과열도(Divergence) 지수: S&P 500 / Net_Liquidity 비율
        df['Ratio'] = df['SP500'] / df['Net_Liquidity']
        df['Overheat_Index'] = df['Ratio'].rolling(window=INDEX_WINDOW).apply(
            lambda x: (x[-1] - x.min()) / (x.max() - x.min()) * 100 if (x.max() != x.min()) else 50
        )
        
        return df.dropna()
    except Exception as e:
        st.error(f"데이터 수집 중 에러가 발생했습니다: {e}")
        return None

# --- 3. 메인 화면 구성 ---
st.title("🛡️ 퀀트 유동성 & 시장 과열 분석기")
st.markdown("가장 신뢰받는 연준(Fed) 대차대조표 데이터를 기반으로 시장의 실제 자금력을 분석합니다.")

# 데이터 불러오기 시도
with st.spinner('FRED 서버에서 최신 데이터를 분석 중입니다...'):
    data = get_combined_data()

if data is not None:
    curr = data.iloc[-1]
    prev = data.iloc[-5]  # 약 한 달 전 데이터
    
    # 상단 핵심 메트릭
    col1, col2, col3 = st.columns(3)
    
    # 과열 지수는 높을수록 위험하므로 상승 시 빨간색 표시
    col1.metric("시장 과열 지수 (0-100)", f"{curr['Overheat_Index']:.1f}", 
                f"{curr['Overheat_Index'] - prev['Overheat_Index']:.1f}", delta_color="inverse")
    col2.metric("순유동성 지수", f"{curr['Liquidity_Index']:.1f}", 
                f"{curr['Liquidity_Index'] - prev['Liquidity_Index']:.1f}")
    col3.metric("S&P 500 (평균)", f"{curr['SP500']:,.0f}")

    st.divider()

    # 차트 1: 유동성과 지수 괴리도 (가장 중요한 차트)
    st.subheader("📊 유동성(공급) vs S&P 500(가격) 추이")
    
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # 순유동성 (파란색 영역)
    fig.add_trace(go.Scatter(x=data.index, y=data['Net_Liquidity'], name="Net Liquidity ($B)", 
                             fill='tozeroy', line=dict(color='royalblue', width=1)), secondary_y=False)
    # S&P 500 (빨간색 선)
    fig.add_trace(go.Scatter(x=data.index, y=data['SP500'], name="S&P 500 Index", 
                             line=dict(color='firebrick', width=3)), secondary_y=True)
    
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title_text="Liquidity ($ Billions)", secondary_y=False)
    fig.update_yaxes(title_text="S&P 500 Price", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    # 차트 2: 과열 지수 게이지
    st.subheader("🚨 현재 시장 위험 판단")
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = curr['Overheat_Index'],
        gauge = {
            'axis': {'range': [0, 100]},
            'steps': [
                {'range': [0, 30], 'color': "rgba(0, 255, 0, 0.3)"},
                {'range': [30, 70], 'color': "rgba(255, 255, 0, 0.3)"},
                {'range': [70, 100], 'color': "rgba(255, 0, 0, 0.3)"}],
            'bar': {'color': "black"}}))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # 판단 가이드
    if curr['Overheat_Index'] > 80:
        st.warning("⚠️ **주의:** 현재 유동성 대비 주가가 역사적 고점 부근입니다. 현금 비중 확대를 고려할 시점입니다.")
    elif curr['Overheat_Index'] < 30:
        st.info("✅ **기회:** 유동성 대비 주가가 충분히 낮아졌습니다. 중장기 매집에 우호적인 환경입니다.")
    else:
        st.write("ℹ️ **중립:** 시장은 현재 가용 유동성 범위 내에서 적정 가치를 형성하고 있습니다.")

else:
    st.error("데이터를 불러올 수 없습니다. 터미널의 에러 로그를 확인하거나 잠시 후 다시 시도해 주세요.")