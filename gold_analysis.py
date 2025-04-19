import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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

        # 黄金价格趋势图 - 使用 matplotlib 创建简单可靠的图表
        st.subheader("黄金价格走势")

        # 创建一个干净的数据副本用于绘图
        plot_df = gold_df.copy()

        # 创建黄金价格图表
        plt.figure(figsize=(10, 6))
        plt.plot(plot_df['Date'], plot_df['Open'], label='开盘价', linewidth=1)
        plt.plot(plot_df['Date'], plot_df['Close'], label='收盘价', linewidth=2)
        plt.plot(plot_df['Date'], plot_df['High'],
                 label='最高价', linewidth=1, linestyle='--')
        plt.plot(plot_df['Date'], plot_df['Low'],
                 label='最低价', linewidth=1, linestyle='--')

        # 设置图表样式
        plt.title('黄金价格历史走势')
        plt.xlabel('日期')
        plt.ylabel('价格 (USD)')
        plt.grid(True, alpha=0.3)
        plt.legend()

        # 显示图表
        st.pyplot(plt)

        # 成交量分析
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("每日成交量")

            # 创建成交量图表
            plt.figure(figsize=(8, 4))
            plt.bar(plot_df['Date'], plot_df['Volume'],
                    color='steelblue', alpha=0.7)
            plt.title('黄金交易成交量')
            plt.xlabel('日期')
            plt.ylabel('成交量')
            plt.grid(True, alpha=0.3)

            # 显示图表
            st.pyplot(plt)

        with col_right:
            st.subheader("价格波动性")
            try:
                # 使用向量化操作计算波动幅度
                mask = plot_df['Low'] > 0  # 创建条件掩码
                plot_df['波动幅度'] = 0.0  # 初始化为0

                # 只对 Low > 0 的行应用计算
                volatility = (
                    plot_df.loc[mask, 'High'] - plot_df.loc[mask, 'Low']) / plot_df.loc[mask, 'Low'] * 100
                plot_df.loc[mask, '波动幅度'] = volatility

                # 创建波动幅度图表
                plt.figure(figsize=(8, 4))
                plt.plot(plot_df['Date'], plot_df['波动幅度'],
                         color='orange', linewidth=1.5)
                plt.title('日内价格波动幅度 (%)')
                plt.xlabel('日期')
                plt.ylabel('波动幅度 (%)')
                plt.grid(True, alpha=0.3)

                # 显示图表
                st.pyplot(plt)
            except Exception as e:
                st.error(f"创建波动性图表时出错: {str(e)}")
                st.exception(e)

        # 显示原始数据，用折叠面板包装以减少视觉干扰
        with st.expander("查看黄金价格原始数据"):
            st.dataframe(gold_df, use_container_width=True)

    except Exception as e:
        # 打印更详细的错误信息
        st.error(f"处理黄金价格数据时出错: {type(e).__name__} - {str(e)}")
        st.exception(e)
