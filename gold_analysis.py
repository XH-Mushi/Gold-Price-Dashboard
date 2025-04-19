import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import numpy as np
import matplotlib
from matplotlib.font_manager import FontProperties
import matplotlib.dates as mdates

# 设置适用于 Windows 的多种中文字体备选
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei',
                                   'SimSun', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


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

        # 黄金价格趋势图
        st.subheader("黄金价格历史走势")

        # 创建黄金价格图表 (使用英文标签避免字体问题)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(gold_df['Date'].values, gold_df['Open'].values,
                label='Open Price', linewidth=1)
        ax.plot(gold_df['Date'].values, gold_df['Close'].values,
                label='Close Price', linewidth=2)
        ax.plot(gold_df['Date'].values, gold_df['High'].values,
                label='High Price', linewidth=1, linestyle='--')
        ax.plot(gold_df['Date'].values, gold_df['Low'].values,
                label='Low Price', linewidth=1, linestyle='--')

        # 设置图表样式
        ax.set_title('Gold Price History', fontsize=16)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price (USD)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=10)

        # 调整日期格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(
            mdates.MonthLocator(interval=3))  # 每3个月显示一个刻度
        plt.xticks(rotation=45)

        # 调整布局
        plt.tight_layout()

        # 显示图表
        st.pyplot(fig)

        # 成交量分析和波动性
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("每日成交量")

            # 创建成交量图表，使用更简单的方式绘制柱状图
            fig2, ax2 = plt.subplots(figsize=(8, 4))

            # 对数据进行采样，减少数据点数量
            sample_size = max(1, len(gold_df) // 30)  # 减少采样数量

            # 使用简单的索引位置作为x轴，而不是日期
            indices = np.arange(len(gold_df))[::sample_size]
            volumes = gold_df['Volume'].values[::sample_size]

            # 绘制柱状图
            ax2.bar(indices, volumes, width=1, color='steelblue', alpha=0.7)

            # 设置x轴刻度为对应的日期
            sample_dates = gold_df['Date'].iloc[::sample_size]
            date_labels = [d.strftime('%Y-%m') for d in sample_dates]

            # 设置x轴刻度位置和标签
            ax2.set_xticks(indices[::5])  # 每5个点显示一个标签
            ax2.set_xticklabels(date_labels[::5], rotation=45)

            # 设置图表样式
            ax2.set_title('Gold Trading Volume', fontsize=14)
            ax2.set_xlabel('Date', fontsize=10)
            ax2.set_ylabel('Volume', fontsize=10)
            ax2.grid(True, alpha=0.3)

            # 调整布局
            plt.tight_layout()

            # 显示图表
            st.pyplot(fig2)

        with col_right:
            st.subheader("价格波动性")
            try:
                # 使用向量化操作计算波动幅度
                gold_df['Volatility'] = 0.0  # 使用英文列名

                # 安全计算波动幅度
                mask = gold_df['Low'] > 0
                gold_df.loc[mask, 'Volatility'] = ((gold_df.loc[mask, 'High'] - gold_df.loc[mask, 'Low']) /
                                                   gold_df.loc[mask, 'Low'] * 100)

                # 创建波动幅度图表
                fig3, ax3 = plt.subplots(figsize=(8, 4))

                # 绘制折线图
                ax3.plot(
                    gold_df['Date'].values, gold_df['Volatility'].values, color='orange', linewidth=1.5)

                # 设置图表样式
                ax3.set_title('Daily Price Volatility (%)', fontsize=14)
                ax3.set_xlabel('Date', fontsize=10)
                ax3.set_ylabel('Volatility (%)', fontsize=10)
                ax3.grid(True, alpha=0.3)

                # 调整日期格式
                ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
                plt.xticks(rotation=45)

                # 调整布局
                plt.tight_layout()

                # 显示图表
                st.pyplot(fig3)
            except Exception as e:
                st.error(f"创建波动性图表时出错: {str(e)}")
                st.exception(e)

        # 显示原始数据，用折叠面板包装以减少视觉干扰
        with st.expander("查看黄金价格原始数据"):
            # 只显示最近的数据，以减少加载时间
            recent_data = gold_df.tail(100).copy()

            # 格式化日期列
            if 'Date' in recent_data.columns:
                recent_data['Date'] = recent_data['Date'].dt.strftime(
                    '%Y-%m-%d')

            # 显示数据表格
            st.dataframe(recent_data, use_container_width=True)

    except Exception as e:
        # 打印更详细的错误信息
        st.error(f"处理黄金价格数据时出错: {type(e).__name__} - {str(e)}")
        st.exception(e)
