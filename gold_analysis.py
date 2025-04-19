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

        # 黄金价格趋势图 - 使用更美观的配置
        st.subheader("黄金价格走势")

        # 创建一个干净的数据副本用于绘图
        plot_df = gold_df.copy()

        # 确保 'Date' 列是正确的格式
        if 'Date' in plot_df.columns:
            # 创建更美观的图表
            fig = go.Figure()

            # 分别添加每条线，使用更好的颜色和样式
            fig.add_trace(go.Scatter(
                x=plot_df['Date'],
                y=plot_df['Open'],
                mode='lines',
                name='开盘价',
                line=dict(color='#48AAAD', width=1.5)
            ))

            fig.add_trace(go.Scatter(
                x=plot_df['Date'],
                y=plot_df['Close'],
                mode='lines',
                name='收盘价',
                line=dict(color='#1E3888', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=plot_df['Date'],
                y=plot_df['High'],
                mode='lines',
                name='最高价',
                line=dict(color='#47A025', width=1.5, dash='dot')
            ))

            fig.add_trace(go.Scatter(
                x=plot_df['Date'],
                y=plot_df['Low'],
                mode='lines',
                name='最低价',
                line=dict(color='#FF0000', width=1.5, dash='dot')
            ))

            # 添加移动平均线
            if len(plot_df) >= 30:
                ma30 = plot_df['Close'].rolling(window=30).mean()
                fig.add_trace(go.Scatter(
                    x=plot_df['Date'],
                    y=ma30,
                    mode='lines',
                    name='30日均线',
                    line=dict(color='#9C179E', width=2.5, dash='dashdot')
                ))

            # 优化布局
            fig.update_layout(
                title={
                    'text': '黄金价格历史走势',
                    'font': {'size': 24, 'color': '#1f77b4'},
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                xaxis_title='日期',
                yaxis_title='价格 (USD)',
                legend_title='价格类型',
                hovermode='x unified',
                plot_bgcolor='rgba(240,240,240,0.2)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(150,150,150,0.2)',
                    tickformat='%Y-%m-%d'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(150,150,150,0.2)',
                    tickprefix='$',
                    tickformat=',.2f'
                ),
                autosize=True,
                height=500,
                margin=dict(l=40, r=40, t=60, b=40)
            )

            # 设置悬停信息格式
            fig.update_traces(
                hovertemplate='%{y:$,.2f}<extra></extra>'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("数据中缺少'Date'列，无法创建趋势图")

        # 成交量分析和价格波动性
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("每日成交量")
            if 'Date' in plot_df.columns and 'Volume' in plot_df.columns:
                # 计算成交量移动平均线
                plot_df['Volume_MA10'] = plot_df['Volume'].rolling(
                    window=10).mean()

                volume_fig = go.Figure()
                # 添加成交量柱状图
                volume_fig.add_trace(go.Bar(
                    x=plot_df['Date'],
                    y=plot_df['Volume'],
                    name='成交量',
                    marker_color='rgba(58, 71, 80, 0.6)'
                ))

                # 添加10日移动平均线
                if len(plot_df) >= 10:
                    volume_fig.add_trace(go.Scatter(
                        x=plot_df['Date'],
                        y=plot_df['Volume_MA10'],
                        name='10日均线',
                        line=dict(color='red', width=2)
                    ))

                # 优化布局
                volume_fig.update_layout(
                    title='黄金交易成交量',
                    xaxis_title='日期',
                    yaxis_title='成交量',
                    plot_bgcolor='rgba(240,240,240,0.2)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(150,150,150,0.2)'
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(150,150,150,0.2)'
                    ),
                    height=350,
                    legend=dict(orientation="h", yanchor="bottom",
                                y=1.02, xanchor="right", x=1),
                    margin=dict(l=40, r=40, t=60, b=40)
                )
                st.plotly_chart(volume_fig, use_container_width=True)
            else:
                st.error("数据中缺少必要的列，无法创建成交量图表")

        with col_right:
            st.subheader("价格波动性")
            try:
                # 安全地计算波动幅度
                plot_df['波动幅度'] = 0.0

                # 计算每日波动幅度百分比
                for i in range(len(plot_df)):
                    low_value = plot_df['Low'].iloc[i]
                    if isinstance(low_value, pd.Series):
                        low_value = low_value.iloc[0]

                    high_value = plot_df['High'].iloc[i]
                    if isinstance(high_value, pd.Series):
                        high_value = high_value.iloc[0]

                    if low_value > 0:
                        volatility = (high_value - low_value) / low_value * 100
                        plot_df.at[plot_df.index[i], '波动幅度'] = volatility

                # 计算移动平均波动幅度
                if len(plot_df) >= 14:
                    plot_df['波动幅度_MA14'] = plot_df['波动幅度'].rolling(
                        window=14).mean()

                # 创建波动幅度图表
                volatility_fig = go.Figure()

                # 添加波动幅度线
                volatility_fig.add_trace(go.Scatter(
                    x=plot_df['Date'],
                    y=plot_df['波动幅度'],
                    mode='lines',
                    name='日内波动',
                    line=dict(color='#FF9500', width=1.5)
                ))

                # 添加移动平均线
                if len(plot_df) >= 14 and '波动幅度_MA14' in plot_df.columns:
                    volatility_fig.add_trace(go.Scatter(
                        x=plot_df['Date'],
                        y=plot_df['波动幅度_MA14'],
                        mode='lines',
                        name='14日均线',
                        line=dict(color='#5D69B1', width=2.5, dash='dash')
                    ))

                # 优化布局
                volatility_fig.update_layout(
                    title='日内价格波动幅度 (%)',
                    xaxis_title='日期',
                    yaxis_title='波动幅度 (%)',
                    plot_bgcolor='rgba(240,240,240,0.2)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(150,150,150,0.2)'
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(150,150,150,0.2)',
                        ticksuffix='%'
                    ),
                    height=350,
                    legend=dict(orientation="h", yanchor="bottom",
                                y=1.02, xanchor="right", x=1),
                    margin=dict(l=40, r=40, t=60, b=40)
                )

                st.plotly_chart(volatility_fig, use_container_width=True)
            except Exception as e:
                st.error(f"创建波动性图表时出错: {str(e)}")
                st.exception(e)

        # 显示原始数据，但使用更好的格式
        with st.expander("点击查看黄金价格原始数据"):
            # 显示最近30天的数据，与更好的格式
            st.write("最近30天黄金价格数据:")
            display_df = gold_df.tail(30).copy()

            # 格式化显示的列
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(
                        lambda x: f"${x:,.2f}")

            if 'Volume' in display_df.columns:
                display_df['Volume'] = display_df['Volume'].apply(
                    lambda x: f"{x:,}")

            if 'Date' in display_df.columns:
                display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')

            st.dataframe(display_df, use_container_width=True)

    except Exception as e:
        # 打印更详细的错误信息
        st.error(f"处理黄金价格数据时出错: {type(e).__name__} - {str(e)}")
        st.exception(e)
