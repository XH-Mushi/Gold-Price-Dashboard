import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

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

# 获取黄金价格数据


@st.cache_data
def get_gold_data():
    try:
        gold = yf.download('GC=F', start='2023-01-01',
                           end=datetime.now().strftime('%Y-%m-%d'))
        gold.reset_index(inplace=True)  # 将日期从索引转换为列
        return gold
    except Exception as e:
        st.error(f"获取黄金数据时出错: {str(e)}")
        return pd.DataFrame()


df = generate_data()
gold_df = get_gold_data()

if gold_df.empty:
    st.error("无法获取黄金价格数据，请检查网络连接或稍后再试。")
else:
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
        st.header("🌍 全球黄金价格分析")

        try:
            # 黄金价格指标
            col1, col2, col3 = st.columns(3)

            with col1:
                # 确保转换为浮点数
                current_price = float(gold_df['Close'].iloc[-1])
                previous_price = float(gold_df['Close'].iloc[-2])
                price_change = (
                    (current_price - previous_price) / previous_price * 100)

                st.metric(
                    label="当前黄金价格",
                    value=f"${current_price:,.2f}",
                    delta=f"{price_change:+.2f}%"
                )

            with col2:
                # 确保转换为浮点数
                avg_30d = float(gold_df['Close'].tail(30).mean())
                avg_60d = float(gold_df['Close'].tail(60).head(30).mean())
                avg_change = ((avg_30d - avg_60d) / avg_60d * 100)

                st.metric(
                    label="30天平均价格",
                    value=f"${avg_30d:,.2f}",
                    delta=f"{avg_change:+.2f}%"
                )

            with col3:
                # 确保转换为浮点数
                high_price = float(gold_df['High'].max())
                low_price = float(gold_df['Low'].min())
                range_percent = ((high_price - low_price) / low_price * 100)

                st.metric(
                    label="年度最高价格",
                    value=f"${high_price:,.2f}",
                    delta=f"{range_percent:+.2f}%"
                )

            # 黄金价格趋势图
            st.subheader("黄金价格走势")
            fig_gold = px.line(gold_df, x='Date', y=['Open', 'Close', 'High', 'Low'],
                               title='黄金价格历史走势',
                               labels={'value': '价格 (USD)', 'variable': '价格类型'})
            st.plotly_chart(fig_gold, use_container_width=True)

            # 成交量分析
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("每日成交量")
                fig_volume = px.bar(gold_df, x='Date', y='Volume',
                                    title='黄金交易成交量')
                st.plotly_chart(fig_volume, use_container_width=True)

            with col_right:
                st.subheader("价格波动性")
                gold_df['波动幅度'] = (gold_df['High'] - gold_df['Low']
                                   ) / gold_df['Low'] * 100
                fig_volatility = px.line(gold_df, x='Date', y='波动幅度',
                                         title='日内价格波动幅度 (%)')
                st.plotly_chart(fig_volatility, use_container_width=True)

            # 显示原始数据
            st.subheader("黄金价格原始数据")
            st.dataframe(gold_df.style.highlight_max(
                axis=0), use_container_width=True)

        except Exception as e:
            st.error(f"处理黄金价格数据时出错: {str(e)}")
