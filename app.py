import streamlit as st
from gold_analysis import show_gold_analysis
from sales_analysis import show_sales_analysis

# 设置页面配置
st.set_page_config(
    page_title="全球市场数据分析仪表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"  # 设置侧边栏默认收起
)

# 添加标题
st.title("📊 全球市场数据分析仪表板")

# 创建标签页
tab1, tab2 = st.tabs(["🏆 黄金价格分析", "📈 销售数据"])

with tab1:
    show_gold_analysis()

with tab2:
    show_sales_analysis()
