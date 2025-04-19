import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from gold_chart import show_gold_chart


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


def show_gold_analysis():
    # Get the gold data
    gold_df = get_gold_data()

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

                # Display metrics
                st.subheader("当前黄金价格")
                st.metric(
                    label="价格 (美元)",
                    value=f"${current_price:,.2f}",
                    delta=f"{price_change_pct:+.2f}%"
                )

            # Show gold price chart
            show_gold_chart(gold_df)

            # Show latest data in a table (更紧凑的设计)
            st.subheader("最近黄金价格数据")

            # Only include important columns and limit to 5 rows
            display_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            recent_data = gold_df.tail(5)[display_cols].copy()

            # Convert dates to string to avoid display issues
            recent_data['Date'] = recent_data['Date'].dt.strftime('%Y-%m-%d')

            # 为表格添加中文列名
            column_names = {
                'Date': '日期',
                'Open': '开盘价',
                'High': '最高价',
                'Low': '最低价',
                'Close': '收盘价',
                'Volume': '成交量'
            }
            recent_data = recent_data.rename(columns=column_names)

            # Show the data
            st.dataframe(recent_data, use_container_width=True, height=200)

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

                # 中文列名
                full_data = full_data.rename(columns=column_names)

                st.dataframe(full_data, use_container_width=True)

    except Exception as e:
        st.error(f"处理黄金价格数据时出错: {str(e)}")
        st.exception(e)
