import setuptools  # Python 3.12+ 환경의 distutils 에러 방지
import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- 1. 외부 CSS 파일을 불러오는 함수 정의 ---
def local_css(file_name):
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ {file_name} 파일을 찾을 수 없습니다. 기본 스타일로 표시합니다.")

# --- 2. 페이지 설정 및 디자인 적용 ---
st.set_page_config(
    page_title="Liquidity Quant Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 파일 적용
local_css("style.css")

# --- 3. 데이터 분석 엔진 (고도화 모델) ---
@st.cache_data(ttl=3600)  # 1시간마다 데이터 갱신
def get_pro_data():
    try:
        # 데이터 기간 설정 (최근 5년)
        end = datetime.now()
        start = end - timedelta(days=365 * 5)
        
        # FRED 심볼: 연준자산(WALCL), 재무부(WDTGAL), 역레포(RRPONTSYD), S&P500(SP500)
        symbols = {
            'WALCL': 'Fed_Assets', 
            'WDTGAL': 'TGA', 
            'RRPONTSYD': 'RRP',
            'SP500': 'SP500'
        }
        
        # 데이터 수집 및 전처리
        df = web.DataReader(list(symbols.keys()), 'fred', start, end).ffill()
        df.columns = [symbols[col] for col in df.columns]
        
        # 1. 단위 표준화 (Billions) 및 노이즈 제거 (4주 이동평균)
        df['Fed_Assets'] = (df['Fed_Assets'] / 1000)
        df = df.rolling(window=4).mean().dropna()
        
        # 2. 실질 순유동성(Net Liquidity) 계산
        # 공식: Fed Assets - TGA - RRP
        df['Net_Liquidity'] = df['Fed_Assets'] - df['TGA'] - df['RRP']
        
        # 3. 유동성 지수 (Rolling 2년 기준 위치)
        window = 104  # 104주 (2년)
        df['Liq_Index'] = df['Net_Liquidity'].rolling(window=window).apply(
            lambda x: (x[-1] - x.min()) / (x.max() - x.min()) * 100 if (x.max() != x.min()) else 50
        )
        
        # 4. 시장 과열도 지수 (S&P 500 / 순유동성 비율의 2년내 위치)
        df['Ratio'] = df['SP500'] / df['Net_Liquidity']
        df['Overheat_Index'] = df['Ratio'].rolling(window=window).apply(
            lambda x: (x[-1] - x.min()) / (x.max() - x.min()) * 100 if (x.max() != x.min()) else 50
        )
        
        return df
    except Exception as e:
        st.error(f"FRED 데이터 수집 중 에러 발생: {e}")
        return None

# --- 4. 메인 화면 구성 (View) ---

# 제목 섹션 (style.css의 .main-title 클래스 사용)
st.markdown('<p class="main-title">🌊 Liquidity Quant Terminal</p>', unsafe_allow_html=True)
st.markdown("전 세계 자금 흐름과 주가지수의 괴리를 분석하여 마켓 타이밍을 보조합니다.")

# 데이터 실행
with st.spinner('실시간 금융 데이터를 분석 중입니다...'):
    data = get_pro_data()

if data is not None:
    curr = data.iloc[-1]
    prev = data.iloc[-5] # 약 한 달 전과 비교
    
    # [A] 마켓 스냅샷 섹션
    st.markdown('<div class="section-header">Market Snapshot</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("시장 과열 지수", f"{curr['Overheat_Index']:.1f}%", 
                  f"{curr['Overheat_Index'] - prev['Overheat_Index']:.1f}%", delta_color="inverse")
    with c2:
        st.metric("순유동성 지수", f"{curr['Liq_Index']:.1f}%", 
                  f"{curr['Liq_Index'] - prev['Liq_Index']:.1f}%")
    with c3:
        st.metric("실질 순유동성", f"${curr['Net_Liquidity']:,.1f}B", 
                  f"{curr['Net_Liquidity'] - prev['Net_Liquidity']:,.1f}B")
    with c4:
        st.metric("S&P 500 (4W MA)", f"{curr['SP500']:,.0f}", 
                  f"{curr['SP500'] - prev['SP500']:,.0f}")

    # [B] 차트 및 심층 분석 섹션
    st.markdown('<div class="section-header">Advanced Chart Analysis</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 유동성 vs 주가", "📉 지표별 트렌드", "🛡️ 투자 진단"])
    
    with tab1:
        # 이중 Y축 차트 (Plotly)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 순유동성 영역 차트
        fig.add_trace(go.Scatter(
            x=data.index, y=data['Net_Liquidity'], 
            name="Net Liquidity ($B)", fill='tozeroy', 
            line=dict(color='#3b82f6', width=1.5)
        ), secondary_y=False)
        
        # S&P 500 선 차트
        fig.add_trace(go.Scatter(
            x=data.index, y=data['SP500'], 
            name="S&P 500 Index", 
            line=dict(color='#ef4444', width=2.5)
        ), secondary_y=True)
        
        fig.update_layout(
            hovermode="x unified",
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### 주요 구성 요소 변화 추이")
        st.line_chart(data[['Fed_Assets', 'TGA', 'RRP']])

    with tab3:
        # 과열도에 따른 투자 가이드 로직
        score = curr['Overheat_Index']
        if score > 80:
            st.error(f"### 🚨 경고: 현재 과열도 {score:.1f}%")
            st.write("유동성 공급량 대비 주가가 역사적 고점 부근입니다. 신규 매수보다는 수익 실현 및 현금 비중 확대를 권장합니다.")
        elif score < 30:
            st.success(f"### ✅ 기회: 현재 과열도 {score:.1f}%")
            st.write("유동성 대비 주가가 충분히 낮거나 저평가된 상태입니다. 중장기적 관점에서 분할 매수가 유효한 구간입니다.")
        else:
            st.info(f"### ℹ️ 중립: 현재 과열도 {score:.1f}%")
            st.write("시장은 현재 가용 자금 범위 내에서 정상적인 흐름을 보이고 있습니다.")

    # [C] 하단 정보 섹션
    st.divider()
    with st.expander("📝 퀀트 모델 산출 공식 정보"):
        st.latex(r"Net\ Liquidity = Fed\ Assets(WALCL) - TGA - RRP")
        st.write("- 모든 데이터는 FRED(Federal Reserve Economic Data) 공식 API를 통해 실시간 수집됩니다.")
        st.write("- 4주 이동평균(4-Week MA)을 적용하여 단기 노이즈를 제거한 중장기 추세를 보여줍니다.")

else:
    st.error("데이터를 수집하지 못했습니다. 잠시 후 새로고침(F5) 해주세요.")