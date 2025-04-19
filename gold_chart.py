import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# 缓存过滤后的数据和图表生成，提高性能


@st.cache_data
def prepare_chart_data(gold_df, time_range):
    """
    预处理并过滤数据，以提高性能
    """
    if gold_df is None or gold_df.empty:
        return None, None, None, None

    # 计算日期范围
    end_date = gold_df['Date'].max()

    if time_range == "3M":
        start_date = end_date - timedelta(days=90)
        title = "Recent 3 Months"
    elif time_range == "6M":
        start_date = end_date - timedelta(days=180)
        title = "Recent 6 Months"
    elif time_range == "1Y":
        start_date = end_date - timedelta(days=365)
        title = "Recent 1 Year"
    else:  # All Data
        start_date = gold_df['Date'].min()
        title = "All Available Data"

    # 过滤数据
    filtered_df = gold_df[gold_df['Date'] >= start_date].copy()

    if filtered_df.empty:
        return None, None, None, None

    # 准备绘图数据
    dates = filtered_df['Date'].tolist()
    prices = []

    # 安全提取价格
    for idx in range(len(filtered_df)):
        price = filtered_df['Close'].iloc[idx]
        if isinstance(price, pd.Series):
            price = price.iloc[0]  # 使用 .iloc[0] 而不是 float()
        prices.append(price)

    # 计算统计数据
    start_price = prices[0]
    end_price = prices[-1]
    price_change = end_price - start_price
    price_change_pct = (price_change / start_price *
                        100) if start_price != 0 else 0

    return filtered_df, dates, prices, title, start_price, end_price, price_change_pct


def show_gold_chart(gold_df):
    """
    显示金价趋势图，带有简约的时间范围选择器
    """
    if gold_df is None or gold_df.empty:
        st.error("无法获取黄金价格数据进行图表展示")
        return

    st.subheader("📈 黄金价格走势")

    # 使用更简约的选择器设计，采用标签页样式而不是单选按钮
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        btn_3m = st.button("3个月", use_container_width=True)
    with col2:
        btn_6m = st.button("6个月", use_container_width=True)
    with col3:
        btn_1y = st.button("1年", use_container_width=True)
    with col4:
        btn_all = st.button("全部数据", use_container_width=True)

    # 确定选择的时间范围
    if btn_3m:
        time_range = "3M"
    elif btn_6m:
        time_range = "6M"
    elif btn_1y:
        time_range = "1Y"
    elif btn_all:
        time_range = "All"
    else:
        # 默认显示3个月
        time_range = "3M"

    # 使用缓存函数处理数据
    result = prepare_chart_data(gold_df, time_range)

    if result is None:
        st.warning("所选时间范围内没有可用数据")
        return

    filtered_df, dates, prices, title, start_price, end_price, price_change_pct = result

    # 创建图表
    try:
        fig, ax = plt.subplots(figsize=(10, 5))  # 减小图表高度

        # 绘制价格线
        ax.plot(dates, prices, 'b-', linewidth=2)

        # 设置图表样式 (保留英文标题避免字体问题)
        ax.set_title(f'Gold Price - {title}', fontsize=14)
        ax.set_xlabel('Date', fontsize=10)
        ax.set_ylabel('Price (USD)', fontsize=10)
        ax.grid(True, alpha=0.3)

        # 根据时间范围格式化x轴
        if time_range == "3M":
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        elif time_range == "6M":
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

        plt.xticks(rotation=45)
        plt.tight_layout()

        # 显示图表
        st.pyplot(fig)

        # 显示价格统计数据（更紧凑的设计）
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            st.metric(
                label="起始价格",
                value=f"${start_price:,.2f}"
            )

        with col2:
            st.metric(
                label="当前价格",
                value=f"${end_price:,.2f}",
                delta=f"{price_change_pct:+.2f}%"
            )

        with col3:
            # 显示当前选择的数据范围信息
            if filtered_df is not None:
                start_date = filtered_df['Date'].min().strftime('%Y-%m-%d')
                end_date = filtered_df['Date'].max().strftime('%Y-%m-%d')
                st.info(
                    f"显示从 {start_date} 到 {end_date} 的数据（共 {len(filtered_df)} 个数据点）")

    except Exception as e:
        st.error(f"生成图表时出错: {str(e)}")
        st.exception(e)
