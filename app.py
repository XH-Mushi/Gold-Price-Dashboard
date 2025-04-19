import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from gold_analysis import show_gold_analysis

# 设置页面配置
st.set_page_config(
    page_title="全球市场数据分析仪表板",
    page_icon="📊",
    layout="wide"
)

# 添加标题
st.title("📊 全球市场数据分析仪表板")

# 创建示例数据


@st.cache_data
def generate_data():
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    data = {
        '日期': dates,
        '销售额': np.random.normal(1000, 100, len(dates)),
        '访问量': np.random.normal(500, 50, len(dates)),
        '转化率': np.random.uniform(0.1, 0.3, len(dates))
    }
    return pd.DataFrame(data)


df = generate_data()

# 创建标签页
tab1, tab2 = st.tabs(["📈 销售数据", "🏆 黄金价格分析"])

with tab1:
    # 创建侧边栏
    st.sidebar.header("📈 筛选条件")

    # 日期范围选择器
    date_range = st.sidebar.date_input(
        "选择日期范围",
        value=(df['日期'].min(), df['日期'].max()),
        min_value=df['日期'].min(),
        max_value=df['日期'].max()
    )

    # 创建三个指标卡片
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="平均日销售额",
            value=f"¥{df['销售额'].mean():,.2f}",
            delta=f"{((df['销售额'].iloc[-1] - df['销售额'].iloc[0])/df['销售额'].iloc[0]*100):,.2f}%"
        )

    with col2:
        st.metric(
            label="平均日访问量",
            value=f"{df['访问量'].mean():,.0f}",
            delta=f"{((df['访问量'].iloc[-1] - df['访问量'].iloc[0])/df['访问量'].iloc[0]*100):,.2f}%"
        )

    with col3:
        st.metric(
            label="平均转化率",
            value=f"{df['转化率'].mean():.2%}",
            delta=f"{((df['转化率'].iloc[-1] - df['转化率'].iloc[0])/df['转化率'].iloc[0]*100):,.2f}%"
        )

    # 创建图表
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("销售趋势")
        fig_sales = px.line(df, x='日期', y='销售额', title='日销售额趋势')
        st.plotly_chart(fig_sales, use_container_width=True)

    with col_right:
        st.subheader("访问量与转化率关系")
        fig_scatter = px.scatter(df, x='访问量', y='转化率',
                                 title='访问量与转化率散点图',
                                 trendline="ols")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # 显示原始数据
    st.subheader("原始数据")
    st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)

with tab2:
    show_gold_analysis()
