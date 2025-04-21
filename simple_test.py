import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def safe_download(symbol):
    """安全地下载数据"""
    try:
        data = yf.download(
            symbol,
            start=(datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            end=datetime.now().strftime('%Y-%m-%d'),
            progress=False
        )
        return data
    except Exception as e:
        st.error(f"下载失败: {str(e)}")
        return pd.DataFrame()


def main():
    st.title("简化版黄金价格查看器")

    with st.expander("调试信息", expanded=True):
        st.write("这是一个简化版应用，用于排查错误")

    st.info("正在尝试获取数据...")

    try:
        # 尝试获取黄金价格
        gold_symbol = "GC=F"  # 黄金期货
        st.write(f"尝试从{gold_symbol}获取数据...")
        gold_data = safe_download(gold_symbol)

        if not gold_data.empty:
            st.success("成功获取黄金数据")
            st.write("数据预览:")
            st.dataframe(gold_data.head())

            # 显示最新价格
            latest_price = gold_data['Close'].iloc[-1]
            st.metric("黄金价格(美元/盎司)", f"${latest_price:.2f}")
        else:
            st.error("获取黄金数据失败")

        # 尝试获取汇率
        rate_symbol = "CNY=X"  # 美元/人民币汇率
        st.write(f"尝试从{rate_symbol}获取数据...")
        rate_data = safe_download(rate_symbol)

        if not rate_data.empty:
            st.success("成功获取汇率数据")
            st.write("数据预览:")
            st.dataframe(rate_data.head())

            # 显示最新汇率
            latest_rate = rate_data['Close'].iloc[-1]
            st.metric("美元兑人民币汇率", f"{latest_rate:.4f}")

            # 计算人民币价格
            if not gold_data.empty:
                rmb_price = latest_price * latest_rate
                st.metric("黄金价格(人民币/盎司)", f"¥{rmb_price:.2f}")
                st.metric("黄金价格(人民币/克)", f"¥{rmb_price/31.1035:.2f}")
        else:
            st.error("获取汇率数据失败")

    except Exception as e:
        st.error(f"运行时错误: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
