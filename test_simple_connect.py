import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

st.title("Yahoo Finance连接测试")

st.write("这是一个极简版的测试应用，仅测试与Yahoo Finance的连接。")


@st.cache_data
def get_test_data():
    try:
        st.info("尝试从Yahoo Finance获取数据...")
        # 尝试获取黄金数据，设置非常短的超时
        data = yf.download(
            "GC=F",  # 黄金期货
            start=(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            end=datetime.now().strftime('%Y-%m-%d'),
            progress=False,
            timeout=5,
            threads=False
        )
        if not data.empty:
            return True, data
        return False, None
    except Exception as e:
        return False, str(e)


# 使用按钮触发请求
if st.button("测试连接"):
    success, result = get_test_data()

    if success:
        st.success("成功连接到Yahoo Finance!")
        st.write("获取到的数据:")
        st.dataframe(result.head())
    else:
        st.error("连接失败")
        st.write(f"错误信息: {result}")

        # 提供解决方案
        st.markdown("""
        ### 可能的解决方法:
        1. 检查网络连接
        2. 确认是否可以访问Yahoo Finance网站 (finance.yahoo.com)
        3. 尝试使用VPN或代理
        4. 更新yfinance库: `pip install yfinance --upgrade`
        """)
