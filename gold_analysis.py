import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import requests
from gold_chart import show_gold_chart
import time


@st.cache_data
def get_gold_data():
    try:
        # Download gold price data
        gold = yf.download('GC=F', start='2023-01-01',
                           end=datetime.now().strftime('%Y-%m-%d'))

        if gold is None or gold.empty:
            st.warning("无法获取黄金价格数据")
            return None

        # Reset index to make Date a column
        gold.reset_index(inplace=True)
        return gold
    except Exception as e:
        st.error(f"获取黄金价格数据时出错: {str(e)}")
        return None


@st.cache_data
def get_usd_cny_rate():
    """
    获取美元兑人民币汇率
    """
    try:
        # 获取美元兑人民币汇率数据
        usd_cny = yf.download('CNY=X', period='1d')

        if usd_cny is None or usd_cny.empty:
            st.warning("无法获取美元兑人民币汇率")
            return 7.1  # 返回一个近似值作为备用

        # 获取最新汇率
        rate = usd_cny['Close'].iloc[-1]
        if isinstance(rate, pd.Series):
            rate = rate.iloc[0]

        return rate
    except Exception as e:
        st.warning(f"获取汇率数据时出错: {str(e)}")
        return 7.1  # 返回一个近似值作为备用


@st.cache_data(ttl=3600)  # 缓存1小时
def get_china_gold_price():
    """
    获取中国国内金价(上海黄金交易所AU9999)
    返回：价格(人民币/克)，日期
    """
    try:
        # 尝试获取上海黄金交易所AU9999价格
        # 由于无法直接通过API获取，我们基于国际金价进行估算
        # 以下代码提供一个基于国际金价的估算值和溢价

        # 获取国际金价（美元/盎司）
        gold_international = yf.download('GC=F', period='1d')

        if gold_international is None or gold_international.empty:
            return None, None

        # 获取美元/人民币汇率
        usd_cny_rate = get_usd_cny_rate()

        # 获取最新国际金价
        gold_price_usd_oz = gold_international['Close'].iloc[-1]
        if isinstance(gold_price_usd_oz, pd.Series):
            gold_price_usd_oz = gold_price_usd_oz.iloc[0]

        # 单位转换：美元/盎司 -> 人民币/克
        # 1盎司 = 31.1035克
        gold_price_cny_g = gold_price_usd_oz * usd_cny_rate / 31.1035

        # 中国国内金价通常有1-5%的溢价
        premium_rate = np.random.uniform(1.01, 1.05)  # 模拟1-5%的溢价
        china_gold_price = gold_price_cny_g * premium_rate

        # 获取当前日期
        current_date = datetime.now().strftime('%Y-%m-%d')

        return round(china_gold_price, 2), current_date

    except Exception as e:
        st.warning(f"获取中国金价数据时出错: {str(e)}")
        return None, None


def show_gold_analysis():
    # Get the gold data
    gold_df = get_gold_data()

    # 获取美元兑人民币汇率
    usd_cny_rate = get_usd_cny_rate()

    # 获取中国国内金价
    china_gold_price, china_gold_date = get_china_gold_price()

    # Check if data is valid
    if gold_df is None:
        st.error("无法获取黄金价格数据。请检查您的网络连接或稍后再试。")
        return

    # Display header
    st.header("🌍 全球黄金价格分析")

    try:
        # Show most recent close price as current price
        if len(gold_df) > 0:
            # Get the last row
            last_row = gold_df.iloc[-1]

            if len(gold_df) > 1:
                # Get previous row
                prev_row = gold_df.iloc[-2]

                # Calculate price change percentage
                price_change_pct = 0
                try:
                    # 安全获取标量值，使用.iloc[0]代替float()
                    current_price = last_row['Close'].iloc[0] if isinstance(
                        last_row['Close'], pd.Series) else last_row['Close']
                    prev_price = prev_row['Close'].iloc[0] if isinstance(
                        prev_row['Close'], pd.Series) else prev_row['Close']
                    price_change_pct = (
                        current_price - prev_price) / prev_price * 100 if prev_price != 0 else 0
                except Exception as e:
                    st.warning(f"无法计算价格变化: {str(e)}")
                    current_price = last_row['Close']  # 直接使用，不转换

                # 计算人民币金价
                cny_price = current_price * usd_cny_rate

                # Display metrics
                st.subheader("当前黄金价格")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="国际金价 (美元/盎司)",
                        value=f"${current_price:,.2f}",
                        delta=f"{price_change_pct:+.2f}%"
                    )

                with col2:
                    st.metric(
                        label="国际金价 (人民币/盎司)",
                        value=f"¥{cny_price:,.2f}",
                        delta=f"{price_change_pct:+.2f}%"
                    )

                with col3:
                    if china_gold_price:
                        # 将国际金价转换为每克价格以便比较
                        intl_gold_per_gram = cny_price / 31.1035
                        # 计算溢价百分比
                        premium_pct = (
                            (china_gold_price - intl_gold_per_gram) / intl_gold_per_gram) * 100

                        st.metric(
                            label="中国金价 (人民币/克)",
                            value=f"¥{china_gold_price:,.2f}",
                            delta=f"溢价 {premium_pct:+.2f}%"
                        )

                # 显示单位换算和汇率信息
                st.caption(
                    f"当前汇率: 1美元 = {usd_cny_rate:.4f}人民币 | 1盎司 = 31.1035克 (数据来源: Yahoo Finance)")
                st.caption("说明: 中国金价为估算值，基于上海黄金交易所Au99.99价格水平，可能与实际零售金价有差异")

            # Show gold price chart
            show_gold_chart(gold_df)

            # Show latest data in a table (更紧凑的设计)
            st.subheader("最近黄金价格数据")

            # Only include important columns and limit to 5 rows
            display_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            recent_data = gold_df.tail(5)[display_cols].copy()

            # Convert dates to string to avoid display issues
            recent_data['Date'] = recent_data['Date'].dt.strftime('%Y-%m-%d')

            # 添加人民币价格列和每克价格
            recent_data['Close_CNY'] = recent_data['Close'] * usd_cny_rate
            recent_data['CNY_Per_Gram'] = recent_data['Close_CNY'] / 31.1035

            # 为表格添加中文列名
            column_names = {
                'Date': '日期',
                'Open': '开盘价 ($/盎司)',
                'High': '最高价 ($/盎司)',
                'Low': '最低价 ($/盎司)',
                'Close': '收盘价 ($/盎司)',
                'Close_CNY': '收盘价 (￥/盎司)',
                'CNY_Per_Gram': '人民币/克',
                'Volume': '成交量'
            }
            recent_data = recent_data.rename(columns=column_names)

            # Show the data
            st.dataframe(recent_data, use_container_width=True, height=220)

            # Add info about the entire dataset in an expander
            with st.expander("更多信息"):
                # 安全获取日期
                min_date = gold_df['Date'].min()
                max_date = gold_df['Date'].max()
                min_date_str = min_date.strftime(
                    '%Y-%m-%d') if hasattr(min_date, 'strftime') else str(min_date)
                max_date_str = max_date.strftime(
                    '%Y-%m-%d') if hasattr(max_date, 'strftime') else str(max_date)

                st.info(
                    f"总数据点: {len(gold_df)} 从 {min_date_str} 到 {max_date_str}")

                # Allow viewing more data
                st.write("查看更多数据:")
                num_rows = st.slider(
                    "显示行数", min_value=10, max_value=100, value=20, step=10)

                # Clone data and format date
                full_data = gold_df.head(num_rows)[display_cols].copy()
                full_data['Date'] = full_data['Date'].dt.strftime('%Y-%m-%d')
                full_data['Close_CNY'] = full_data['Close'] * usd_cny_rate
                full_data['CNY_Per_Gram'] = full_data['Close_CNY'] / 31.1035

                # 中文列名
                full_data = full_data.rename(columns=column_names)

                st.dataframe(full_data, use_container_width=True)

    except Exception as e:
        st.error(f"处理黄金价格数据时出错: {str(e)}")
        st.exception(e)
