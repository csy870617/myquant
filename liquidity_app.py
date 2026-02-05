import setuptools
import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# CSS 로드 함수
def local_css(file_name):
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

st.set_page_config(page_title="Global Liquidity & KOSPI Tracker", layout="wide")
local_css("style.css")

# --- 통합 데이터 엔진 ---
@st.cache_data(ttl=3600)
def get_combined_market_data():
    try:
        start = datetime(2000, 1, 1)
        end = datetime.now()
        
        # 1. FRED에서 유동성 데이터 수집
        liq_symbols = {'WALCL': 'Fed', 'WDTGAL': 'TGA', 'RRPONTSYD': 'RRP'}
        df_liq = web.DataReader(list(liq_symbols.keys()), 'fred', start, end).ffill()
        df_liq.columns = [liq_symbols[col] for col in df_liq.columns]
        df_liq['Net_Liquidity'] = (df_liq['Fed'] / 1000) - df_liq['TGA'].fillna(0) - df_liq['RRP'].fillna(0)
        
        # 2. Yahoo Finance에서 주가지수 수집 (코스피 포함)
        idx_symbols = {
            '^GSPC': 'S&P 500', 
            '^IXIC': 'NASDAQ', 
            '^DJI': 'DOW JONES', 
            '^KS11': 'KOSPI'
        }
        df_idx = yf.download(list(idx_symbols.keys()), start=start, end=end)['Close']
        df_idx = df_idx.rename(columns=idx_symbols)
        
        # 데이터 병합 및 정제
        df = pd.concat([df_liq[['Net_Liquidity']], df_idx], axis=1).ffill()
        df_smooth = df.rolling(window=20).mean().dropna(subset=['S&P 500', 'KOSPI'], how='all')
        
        return df_smooth
    except Exception as e:
        st.error(f"데이터 로드 에러: {e}")
        return None

# --- 화면 구성 ---
st.markdown('<p class="main-title">🇰🇷 Global Liquidity & KOSPI Terminal</p>', unsafe_allow_html=True)

df_plot = get_combined_market_data()

if df_plot is not None:
    # --- 사이드바 컨트롤 ---
    st.sidebar.header("⚙️ 분석 설정")
    use_log = st.sidebar.toggle("Y축 로그 스케일(Log Scale) 적용", value=True)
    show_events = st.sidebar.checkbox("주요 경제 이벤트 표시", value=True)
    selected_indices = st.sidebar.multiselect(
        "비교 지수 선택:", 
        ['S&P 500', 'NASDAQ', 'DOW JONES', 'KOSPI'], 
        default=['S&P 500', 'KOSPI']
    )

    latest_date = df_plot.index[-1].strftime('%Y-%m-%d')
    st.markdown(f'<div class="update-bar">📅 데이터 기준일: {latest_date} | 코스피 통합 분석 모드</div>', unsafe_allow_html=True)

    # 메인 차트 구성 (이중 Y축)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # 미국 순유동성 (왼쪽 Y축)
    fig.add_trace(go.Scatter(
        x=df_plot.index, y=df_plot['Net_Liquidity'], 
        name="US Net Liquidity ($B)", fill='tozeroy', 
        line=dict(color='rgba(59, 130, 246, 0.3)', width=1)
    ), secondary_y=False)
    
    # 지수별 색상
    colors = {'S&P 500': '#ef4444', 'NASDAQ': '#10b981', 'DOW JONES': '#f59e0b', 'KOSPI': '#8b5cf6'} # 코스피는 보라색
    
    for idx in selected_indices:
        fig.add_trace(go.Scatter(
            x=df_plot.index, y=df_plot[idx], 
            name=idx, line=dict(color=colors[idx], width=2)
        ), secondary_y=True)

    # 이벤트 표시
    if show_events:
        modern_events = [
            ("2008-09-15", "리먼 사산"), ("2020-03-15", "코로나19 QE"),
            ("2022-03-16", "금리 인상 시작"), ("2023-03-10", "SVB 사태")
        ]
        for date_str, text in modern_events:
            ev_date = pd.to_datetime(date_str)
            if ev_date >= df_plot.index[0]:
                fig.add_vline(x=ev_date, line_width=1, line_dash="dash", line_color="gray")
                fig.add_annotation(x=ev_date, y=1.05, yref="paper", text=text, showarrow=False, textangle=-45)

    # 로그 스케일 및 레이아웃
    y_type = "log" if use_log else "linear"
    fig.update_yaxes(type=y_type, secondary_y=True, title_text="Stock Indices Value")
    fig.update_yaxes(type=y_type, secondary_y=False, title_text="US Net Liquidity ($B)")
    
    fig.update_layout(hovermode="x unified", height=700, margin=dict(t=80),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    
    st.plotly_chart(fig, use_container_width=True)

    # 한국 시장 특화 분석 가이드
    with st.expander("🇰🇷 코스피와 미국 유동성 분석 팁"):
        st.write("""
        1. **달러 유동성 커플링:** 한국 증시는 외국인 자금 비중이 높아 미국의 순유동성이 증가할 때 코스피도 강한 탄력을 받는 경향이 있습니다.
        2. **선행 지표:** 미국 유동성이 먼저 꺾이면, 신흥국 시장인 코스피에서 자금이 먼저 빠져나가는 '카나리아' 역할을 하기도 합니다.
        3. **환율 변수:** 현재 차트는 원화 지수(KOSPI)와 달러 유동성을 비교하므로, 환율 급등기에는 일시적인 괴리가 발생할 수 있음을 유의하세요.
        """)
else:
    st.error("데이터를 가져오는 데 실패했습니다.")