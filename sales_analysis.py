import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from io import StringIO
import contextlib


@st.cache_data
def generate_data():
    """生成示例销售数据"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    data = {
        '日期': dates,
        '销售额': np.random.normal(1000, 100, len(dates)),
        '访问量': np.random.normal(500, 50, len(dates)),
        '转化率': np.random.uniform(0.1, 0.3, len(dates))
    }
    return pd.DataFrame(data)


def show_metrics(df):
    """显示关键指标"""
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


def show_charts(df):
    """显示销售图表"""
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


def show_code_editor(df):
    """显示代码编辑器"""
    st.subheader("📝 Python代码编辑器")

    with st.expander("查看可用数据和函数说明"):
        st.markdown("""
        ### 可用数据
        - `df`: 销售数据DataFrame，包含以下列：
            - 日期
            - 销售额
            - 访问量
            - 转化率
        
        ### 可用库
        - `pandas as pd`: 数据处理
        - `numpy as np`: 数学计算
        - `plotly.express as px`: 绘图
        
        ### 示例代码
        ```python
        # 计算每月销售额
        monthly_sales = df.groupby(df['日期'].dt.month)['销售额'].sum()
        st.write("月度销售额：", monthly_sales)
        
        # 绘制自定义图表
        fig = px.bar(monthly_sales, title="月度销售额分布")
        st.plotly_chart(fig)
        ```
        """)

    # 默认代码
    default_code = '''# 在这里编写您的Python代码
# 可用数据：df (销售数据DataFrame)
# 示例：计算每月销售额
monthly_sales = df.groupby(df['日期'].dt.month)['销售额'].sum()
st.write("月度销售额：", monthly_sales)

# 绘制图表
fig = px.bar(monthly_sales, title="月度销售额分布")
st.plotly_chart(fig)
'''

    # 代码输入区域
    code = st.text_area("输入Python代码", value=default_code, height=300)

    # 执行代码按钮
    if st.button("运行代码"):
        try:
            # 创建本地环境
            local_dict = {
                'pd': pd,
                'np': np,
                'px': px,
                'df': df,
                'st': st,
            }

            # 捕获输出
            with contextlib.redirect_stdout(StringIO()) as output:
                # 执行代码
                exec(code, local_dict)

            # 显示输出
            output_str = output.getvalue()
            if output_str:
                st.text("输出:")
                st.code(output_str)

        except Exception as e:
            st.error(f"代码执行出错: {str(e)}")


def show_filters(df):
    """显示筛选条件"""
    if st.button("显示筛选条件", key="show_filters"):
        with st.sidebar:
            st.header("📈 筛选条件")
            return st.date_input(
                "选择日期范围",
                value=(df['日期'].min(), df['日期'].max()),
                min_value=df['日期'].min(),
                max_value=df['日期'].max()
            )
    return None


def show_sales_analysis():
    """显示销售数据分析"""
    # 获取数据
    df = generate_data()

    # 显示关键指标
    show_metrics(df)

    # 显示图表
    show_charts(df)

    # 显示原始数据
    st.subheader("原始数据")
    st.dataframe(df.style.highlight_max(axis=0), use_container_width=True)

    # 显示代码编辑器
    show_code_editor(df)

    # 显示筛选条件
    date_range = show_filters(df)
