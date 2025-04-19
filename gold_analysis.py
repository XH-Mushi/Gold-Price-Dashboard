import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import numpy as np


@st.cache_data
def get_gold_data():
    try:
        # 下载黄金价格数据
        gold = yf.download('GC=F', start='2023-01-01',
                           end=datetime.now().strftime('%Y-%m-%d'))

        # 检查数据框是否为空
        if gold is None or gold.size == 0:
            st.warning("获取到的黄金数据为空")
            return None

        # 重设索引并返回数据
        gold.reset_index(inplace=True)
        return gold
    except Exception as e:
        st.error(f"获取黄金数据时出错: {str(e)}")
        return None


def show_gold_analysis():
    # 获取黄金数据
    gold_df = get_gold_data()

    # 检查数据是否有效
    if gold_df is None:
        st.error("无法获取黄金价格数据，请检查网络连接或稍后再试。")
        return

    st.header("🌍 全球黄金价格分析")

    try:
        # 确保数据框不为空且有足够的数据行
        if len(gold_df) < 2:
            st.warning("数据量不足，无法进行分析")
            return

        # 预先计算所有需要的数值，确保它们都是标量
        # 当前和前一个收盘价
        current_price = gold_df['Close'].iloc[-1]
        if isinstance(current_price, pd.Series):
            current_price = current_price.iloc[0]

        previous_price = gold_df['Close'].iloc[-2]
        if isinstance(previous_price, pd.Series):
            previous_price = previous_price.iloc[0]

        price_change = ((current_price - previous_price) /
                        previous_price * 100) if previous_price != 0 else 0

        # 计算平均值
        if len(gold_df) >= 30:
            avg_30d = gold_df['Close'].tail(30).mean()
            if isinstance(avg_30d, pd.Series):
                avg_30d = avg_30d.iloc[0]

            if len(gold_df) >= 60:
                avg_60d = gold_df['Close'].tail(60).head(30).mean()
                if isinstance(avg_60d, pd.Series):
                    avg_60d = avg_60d.iloc[0]
            else:
                remaining = len(gold_df) - 30
                if remaining > 0:
                    avg_60d = gold_df['Close'].head(remaining).mean()
                    if isinstance(avg_60d, pd.Series):
                        avg_60d = avg_60d.iloc[0]
                else:
                    avg_60d = avg_30d

            avg_change = ((avg_30d - avg_60d) / avg_60d *
                          100) if avg_60d != 0 else 0
        else:
            avg_30d = None
            avg_change = None

        # 最高和最低价格
        high_price = gold_df['High'].max()
        if isinstance(high_price, pd.Series):
            high_price = high_price.iloc[0]

        low_price = gold_df['Low'].min()
        if isinstance(low_price, pd.Series):
            low_price = low_price.iloc[0]

        range_percent = ((high_price - low_price) /
                         low_price * 100) if low_price != 0 else 0

        # 黄金价格指标
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="当前黄金价格",
                value=f"${current_price:,.2f}",
                delta=f"{price_change:+.2f}%"
            )

        with col2:
            if avg_30d is not None:
                st.metric(
                    label="30天平均价格",
                    value=f"${avg_30d:,.2f}",
                    delta=f"{avg_change:+.2f}%"
                )
            else:
                st.warning("数据不足30天，无法计算平均价格")

        with col3:
            st.metric(
                label="年度最高价格",
                value=f"${high_price:,.2f}",
                delta=f"{range_percent:+.2f}%"
            )

        # 黄金价格趋势图 - 使用更简单的方法创建图表
        st.subheader("黄金价格走势")

        # 创建一个干净的数据副本用于绘图
        plot_df = gold_df.copy()

        # 确保 'Date' 列是正确的格式
        if 'Date' in plot_df.columns:
            # 创建简单的图表，一次只绘制一条线
            fig = go.Figure()

            # 分别添加每条线，以避免DataFrame的布尔值判断问题
            if 'Open' in plot_df.columns:
                fig.add_trace(go.Scatter(
                    x=plot_df['Date'], y=plot_df['Open'], mode='lines', name='Open'))

            if 'Close' in plot_df.columns:
                fig.add_trace(go.Scatter(
                    x=plot_df['Date'], y=plot_df['Close'], mode='lines', name='Close'))

            if 'High' in plot_df.columns:
                fig.add_trace(go.Scatter(
                    x=plot_df['Date'], y=plot_df['High'], mode='lines', name='High'))

            if 'Low' in plot_df.columns:
                fig.add_trace(go.Scatter(
                    x=plot_df['Date'], y=plot_df['Low'], mode='lines', name='Low'))

            fig.update_layout(
                title='黄金价格历史走势',
                xaxis_title='日期',
                yaxis_title='价格 (USD)',
                legend_title='价格类型'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("数据中缺少'Date'列，无法创建趋势图")

        # 成交量分析
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("每日成交量")
            if 'Date' in plot_df.columns and 'Volume' in plot_df.columns:
                volume_fig = go.Figure()
                volume_fig.add_trace(
                    go.Bar(x=plot_df['Date'], y=plot_df['Volume']))
                volume_fig.update_layout(title='黄金交易成交量')
                st.plotly_chart(volume_fig, use_container_width=True)
            else:
                st.error("数据中缺少必要的列，无法创建成交量图表")

        with col_right:
            st.subheader("价格波动性")
            try:
                # 创建一个临时列用于波动幅度，使用更安全的方法
                plot_df['波动幅度'] = 0.0

                # 遍历处理每一行
                for i in range(len(plot_df)):
                    low_value = plot_df['Low'].iloc[i]
                    high_value = plot_df['High'].iloc[i]

                    # 确保处理的是标量值
                    if isinstance(low_value, pd.Series):
                        low_value = low_value.iloc[0]
                    if isinstance(high_value, pd.Series):
                        high_value = high_value.iloc[0]

                    if low_value > 0:
                        volatility = (high_value - low_value) / low_value * 100
                        plot_df.at[plot_df.index[i], '波动幅度'] = volatility

                # 使用更简单的方式创建图表
                if 'Date' in plot_df.columns:
                    volatility_fig = go.Figure()
                    volatility_fig.add_trace(go.Scatter(
                        x=plot_df['Date'],
                        y=plot_df['波动幅度'],
                        mode='lines'
                    ))
                    volatility_fig.update_layout(title='日内价格波动幅度 (%)')
                    st.plotly_chart(volatility_fig, use_container_width=True)
                else:
                    st.error("数据中缺少'Date'列，无法创建波动性图表")
            except Exception as e:
                st.error(f"创建波动性图表时出错: {str(e)}")
                st.exception(e)

        # 显示原始数据
        st.subheader("黄金价格原始数据")
        st.dataframe(gold_df, use_container_width=True)

    except Exception as e:
        # 打印更详细的错误信息
        st.error(f"处理黄金价格数据时出错: {type(e).__name__} - {str(e)}")
        st.exception(e)
