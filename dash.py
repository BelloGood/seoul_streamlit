import pandas as pd
import numpy as np
import requests
import json
from pandas import json_normalize
import os
import webbrowser
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
sns.set_theme(style='whitegrid', font_scale=1.5)
sns.set_palette('Set2', n_colors=10)
plt.rc('font', family='AppleGothic')
plt.rc('axes', unicode_minus=False)
import streamlit as st

st.set_page_config(page_title='조별과제(이형호, 김보람)',
                   page_icon='\U0001F4DD', layout='wide')

@st.cache_data
def load_data():
    return pd.read_excel('data/2022년 서울시 주거실태조사 마이크로데이터.xlsx',
                         usecols=['SIGUNGU', 'Q7', 'Q12_1', 'Q21_1_A', 'Q25_1', 'Q25_2', 'Q46_A3_1', 'Q46_A4_1', 'Q46_1', 'Q49_1_6', 'Q50_1', 'Q52_4'])

uploaded_file = st.file_uploader("파일을 업로드하세요", type=["xlsx"])
if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.dataframe(df)

df = load_data()

my_df = df.copy()  # df를 복사하여 my_df 생성

st.title("서울시 주거실태조사")

if st.button('새로고침'):
    st.rerun()

st.sidebar.title("조건 필터")

# 좌측 메뉴 option1
st.sidebar.header('유형분류')
my_df['Q46_1_category'] = my_df['Q46_1'].apply(lambda x: '1인가구' if x == 1 else '다가구')
option01 = st.sidebar.multiselect('가구유형', my_df['Q46_1_category'].unique(), default=my_df['Q46_1_category'].unique(), key='option01_key')
my_df = my_df[my_df['Q46_1_category'].isin(option01)]

# 좌측 메뉴 option2
q7_mapping = {
    1: "자가",
    2: "전세",
    3: "보증금 있는 월세",
    4: "보증금 없는 월세",
    5: "사글세 또는 연세",
    6: "일세",
    7: "무상"
}
my_df['Q7'] = my_df['Q7'].map(q7_mapping)  # 원본 데이터에 매핑 적용
option02 = st.sidebar.multiselect('점유형태', my_df['Q7'].unique(), default=my_df['Q7'].unique(), key='option02_key')
my_df = my_df[my_df['Q7'].isin(option02)]

# 좌측 메뉴 option3
def categorize_area(value):
    if pd.isna(value):
        return '결측치'
    elif value <= 10:
        return '10평미만'
    elif value <= 20:
        return '10평대'
    elif value <= 30:
        return '20평대'
    elif value <= 40:
        return '30평대'
    elif value <= 50:
        return '40평대'
    elif value <= 60:
        return '50평대'
    elif value <= 70:
        return '60평대'
    elif value == 9999999: 
        return '모름'
    else:
        return '70평이상'

my_df['Q21_1_A_category'] = my_df['Q21_1_A'].apply(categorize_area)
option03 = st.sidebar.multiselect('거주평수', my_df['Q21_1_A_category'].unique(), default=my_df['Q21_1_A_category'].unique(), key='option03_key')
my_df = my_df[my_df['Q21_1_A_category'].isin(option03)]

# 'SIGUNGU' 값을 대치
sigungu_mapping = {
    1: "강남구", 2: "강동구", 3: "강북구", 4: "강서구", 5: "관악구",
    6: "광진구", 7: "구로구", 8: "금천구", 9: "노원구", 10: "도봉구",
    11: "동대문구", 12: "동작구", 13: "마포구", 14: "서대문구", 15: "서초구",
    16: "성동구", 17: "성북구", 18: "송파구", 19: "양천구", 20: "영등포구",
    21: "용산구", 22: "은평구", 23: "종로구", 24: "중구", 25: "중랑구"
}

my_df['SIGUNGU'] = my_df['SIGUNGU'].map(sigungu_mapping)

# 'SIGUNGU'를 기준으로 'Q25_2' 만족도를 그룹화하여 평균 계산
map_df = my_df.groupby('SIGUNGU')['Q25_2'].mean().reset_index()


# 2. GeoJSON 데이터 로드
state_geo = 'https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json'

# 3. Choropleth Map 데이터 준비
choropleth_data = map_df.rename(columns={"SIGUNGU": "구"})

# 4. Plotly Express를 사용한 Choropleth Map 생성
fig = px.choropleth(
    choropleth_data,
    geojson=state_geo,
    locations="구",
    featureidkey="properties.name",
    color="Q25_2",
    color_continuous_scale=["red", "yellow", "green", "darkgreen"],
    range_color=(1, 4),
    labels={"Q25_2": "만족도"},
    title="서울시 구별 만족도"
)

# 지도 스타일 조정
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0}, height=600)

# 구 이름을 지도에 추가
for i, row in choropleth_data.iterrows():
    fig.add_scattergeo(
        geojson=state_geo,
        locations=[row['구']],
        text=row['구'],
        mode='text',
        featureidkey="properties.name",
        showlegend=False,  # 이전에는 True로 설정되어 있었습니다.
        hoverinfo='none',  # 마우스 오버시 정보 제외
        textfont=dict(color='white')  # 텍스트 색상을 흰색으로 변경
    )
# 5. Streamlit에 지도 표시
st.plotly_chart(fig, use_container_width=True)

# 칼럼명 매핑 딕셔너리
칼럼_매핑 = {
    'SIGUNGU': '시군구',
    'Q4': '주택유형',
    'Q7': '점유형태',
    'Q8_2': '생애최초',
    'Q11': '자가마련',
    'Q12_1': '주택가격',
    'Q19': '신축여부',
    'Q21_1_A': '면적',
    'Q25_1': '주택만족',
    'Q25_2': '환경만족',
    'Q26_1': '이사',
    'Q39': '주거지원',
    'Q39_1': '주거지원',
    'Q46_A1_1': '구성원',
    'Q46_A2_1': '출생년도',
    'Q46_A3_1': '나이',
    'Q46_A4_1': '성별',
    'Q46_1': '가구수',
    'Q46_1_category': '가구유형',
    'Q21_1_A_category': '거주평수',
    'Q47_1': '결혼연도',
    'Q49_1_6': '월소득',
    'Q50_1': '월지출',
    'Q52_1': '부동산',
    'Q52_1_1': '주택',
    'Q52_4': '총자산'
}

# 데이터프레임의 칼럼명을 변경
my_df.rename(columns=칼럼_매핑, inplace=True)

# # 중복된 칼럼명 제거
# df = df.loc[:, ~df.columns.duplicated()]

st.text('데이터 표')
st.dataframe(my_df)
