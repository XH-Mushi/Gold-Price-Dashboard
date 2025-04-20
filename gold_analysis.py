import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import requests
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from database import init_db, save_gold_price, get_latest_gold_price, get_price_history
import time
import random
import scipy.stats as stats
from statsmodels.tsa.seasonal import seasonal_decompose

# 初始化数据库
init_db()

# MetalpriceAPI配置
METAL_PRICE_API_KEY = "YOUR_API_KEY"  # 需要替换为您的API密钥
METAL_PRICE_API_BASE_URL = "https://api.metalpriceapi.com/v1"


def safe_download(symbol, retries=3, delay=2):
    """安全地下载数据，包含重试和延时"""
    for attempt in range(retries):
        try:
            # 随机延时避免被检测为爬虫
            time.sleep(delay + random.uniform(0.5, 1.5))

            # 设置请求头，模拟浏览器行为
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # 使用download函数获取数据
            # 设置较短的超时时间，避免长时间等待
            data = yf.download(
                symbol,
                start=(datetime.now() - timedelta(days=5)
                       ).strftime('%Y-%m-%d'),
                end=datetime.now().strftime('%Y-%m-%d'),
                progress=False,
                ignore_tz=True,
                threads=False,  # 禁用多线程可能更稳定
                timeout=10
            )

            if not data.empty:
                return data

        except Exception as e:
            if attempt < retries - 1:  # 如果还有重试次数
                st.warning(f"第{attempt + 1}次尝试失败: {str(e)}，等待后重试...")
                time.sleep(delay * (attempt + 1))  # 递增延时
            else:
                st.error(f"下载失败: {str(e)}")
    return pd.DataFrame()  # 返回空DataFrame表示失败


@st.cache_data(ttl=24*3600)  # 缓存24小时
def get_gold_data():
    """获取黄金价格数据"""
    try:
        # 首先尝试从数据库获取最新数据
        latest_data = get_latest_gold_price()
        if not latest_data.empty:
            latest_date = pd.to_datetime(latest_data['date'].iloc[0])
            if latest_date.date() == datetime.now().date():
                st.success("使用今日缓存的黄金价格数据")
                return latest_data['international_price_usd'].iloc[0], None

        # 尝试从Yahoo Finance获取数据
        st.info("正在从Yahoo Finance获取黄金价格数据...")

        # 优先尝试黄金期货和现货
        primary_symbols = [
            "GC=F",     # 黄金期货
            "XAUUSD=X"  # 黄金现货
        ]

        # 备用的ETF数据源
        backup_symbols = [
            ("GLD", 10),    # SPDR黄金ETF (1/10盎司)
            ("IAU", 100),   # iShares黄金ETF (1/100盎司)
            ("SGOL", 10),   # Aberdeen Standard Physical Gold Shares ETF (1/10盎司)
            ("GLDM", 50),   # SPDR Gold MiniShares Trust (1/50盎司)
            ("BAR", 50),    # GraniteShares Gold Trust (1/50盎司)
            ("AAAU", 10),   # Goldman Sachs Physical Gold ETF (1/10盎司)
        ]

        # 首先尝试主要数据源
        for symbol in primary_symbols:
            st.info(f"尝试从{symbol}获取数据...")
            data = safe_download(symbol)

            if not data.empty:
                try:
                    current_price = float(
                        data['Close'].iloc[-1].item())  # 使用.item()避免警告
                    st.success(f"成功从{symbol}获取黄金价格数据: ${current_price:.2f}/盎司")
                    return current_price, data
                except Exception as e:
                    st.warning(f"数据格式错误: {str(e)}")
                    continue

        # 如果主要数据源都失败，尝试ETF
        for symbol, multiplier in backup_symbols:
            st.info(f"尝试从{symbol}获取数据...")
            data = safe_download(symbol)

            if not data.empty:
                try:
                    current_price = float(
                        data['Close'].iloc[-1].item()) * multiplier  # 使用.item()避免警告
                    st.success(f"成功从{symbol}获取黄金价格数据: ${current_price:.2f}/盎司")
                    return current_price, data
                except Exception as e:
                    st.warning(f"数据格式错误: {str(e)}")
                    continue

        st.error("所有数据源都获取失败")
        return None, None

    except Exception as e:
        st.error(f"获取黄金数据时出错: {str(e)}")
        st.info("可能的原因：\n1. API暂时不可用\n2. 网络连接问题\n3. 数据格式发生变化")
        return None, None


@st.cache_data(ttl=24*3600)  # 缓存24小时
def get_usd_cny_rate():
    """获取美元兑人民币汇率"""
    try:
        st.info("正在获取美元兑人民币汇率...")

        # 尝试不同的汇率数据源
        exchange_symbols = [
            "CNY=X",     # 美元/人民币
            "USDCNY=X",  # 美元/人民币 (替代)
            "CNH=F"      # 离岸人民币期货
        ]

        for symbol in exchange_symbols:
            st.info(f"尝试从{symbol}获取汇率...")
            data = safe_download(symbol)

            if not data.empty:
                try:
                    # 使用.item()避免警告
                    rate = float(data['Close'].iloc[-1].item())
                    if symbol == "CNH=F":
                        rate = 1 / rate  # 转换为直接汇率
                    st.success(f"成功从{symbol}获取汇率数据: {rate:.4f}")
                    return rate
                except Exception as e:
                    st.warning(f"数据格式错误: {str(e)}")
                    continue

        # 如果所有API都失败，使用备用值
        st.warning("无法获取实时汇率，使用默认汇率7.2")
        return 7.2

    except Exception as e:
        st.error(f"获取汇率数据时出错: {str(e)}")
        st.info("使用默认汇率7.2")
        return 7.2


@st.cache_data(ttl=24*3600)  # 缓存24小时
def get_historical_gold_data(days):
    """获取历史黄金价格数据"""
    try:
        # 创建调试信息的expander，默认收起
        debug_expander = st.expander("调试信息（点击展开）", expanded=False)

        # 确保结束日期不超过今天
        current_date = datetime.now()
        end_date = current_date.replace(
            hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)

        debug_expander.info(
            f"获取从 {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} 的历史数据")

        # 尝试获取黄金价格历史数据
        try:
            gold_data = yf.download(
                "GC=F",  # 黄金期货
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                progress=False
            )

            # 调试信息
            debug_expander.info(f"获取到黄金数据: {len(gold_data)}条记录")
            if not gold_data.empty:
                debug_expander.info(
                    f"黄金数据日期范围: {gold_data.index.min().strftime('%Y-%m-%d')} 到 {gold_data.index.max().strftime('%Y-%m-%d')}")
                debug_expander.info(f"黄金数据列: {gold_data.columns.tolist()}")
                # 安全地检查和显示数据类型
                if 'Close' in gold_data.columns:
                    try:
                        # 使用dtypes字典而不是直接访问dtype属性
                        debug_expander.info(
                            f"黄金收盘价数据类型: {gold_data.dtypes['Close']}")
                    except Exception as e:
                        debug_expander.warning(f"无法获取黄金收盘价数据类型: {str(e)}")
                # 显示部分样本数据
                debug_expander.info(f"黄金数据样本: \n{gold_data.head(2)}")

            if gold_data.empty:
                debug_expander.warning("无法获取黄金期货数据，尝试获取黄金现货数据...")
                gold_data = yf.download(
                    "XAUUSD=X",  # 黄金现货
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    progress=False
                )

                # 调试信息
                debug_expander.info(f"获取到黄金现货数据: {len(gold_data)}条记录")
                if not gold_data.empty:
                    debug_expander.info(
                        f"黄金现货数据日期范围: {gold_data.index.min().strftime('%Y-%m-%d')} 到 {gold_data.index.max().strftime('%Y-%m-%d')}")
        except Exception as e:
            st.error(f"获取黄金价格数据失败: {str(e)}")
            import traceback
            debug_expander.error(f"获取黄金数据错误详情: {traceback.format_exc()}")
            return pd.DataFrame()

        # 获取汇率历史数据
        try:
            usd_cny_data = yf.download(
                "CNY=X",  # 美元兑人民币汇率
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                progress=False
            )

            # 调试信息
            debug_expander.info(f"获取到汇率数据: {len(usd_cny_data)}条记录")
            if not usd_cny_data.empty:
                debug_expander.info(
                    f"汇率数据日期范围: {usd_cny_data.index.min().strftime('%Y-%m-%d')} 到 {usd_cny_data.index.max().strftime('%Y-%m-%d')}")
                debug_expander.info(f"汇率数据列: {usd_cny_data.columns.tolist()}")
                # 安全地检查和显示数据类型
                if 'Close' in usd_cny_data.columns:
                    try:
                        # 使用dtypes字典而不是直接访问dtype属性
                        debug_expander.info(
                            f"汇率收盘价数据类型: {usd_cny_data.dtypes['Close']}")
                    except Exception as e:
                        debug_expander.warning(f"无法获取汇率收盘价数据类型: {str(e)}")
        except Exception as e:
            st.error(f"获取汇率数据失败: {str(e)}")
            import traceback
            debug_expander.error(f"获取汇率数据错误详情: {traceback.format_exc()}")
            return pd.DataFrame()

        if gold_data.empty or usd_cny_data.empty:
            st.error("无法获取完整的历史数据")
            return pd.DataFrame()

        # 检查并过滤掉未来日期
        today = current_date.date()
        future_dates_gold = [
            date for date in gold_data.index if date.date() > today]
        future_dates_cny = [
            date for date in usd_cny_data.index if date.date() > today]

        if future_dates_gold:
            debug_expander.warning(
                f"发现并移除黄金数据中的未来日期: {[d.strftime('%Y-%m-%d') for d in future_dates_gold]}")
            gold_data = gold_data.loc[gold_data.index.date <= today]

        if future_dates_cny:
            debug_expander.warning(
                f"发现并移除汇率数据中的未来日期: {[d.strftime('%Y-%m-%d') for d in future_dates_cny]}")
            usd_cny_data = usd_cny_data.loc[usd_cny_data.index.date <= today]

        # 准备数据
        historical_data = []
        problem_dates = []

        for date in gold_data.index:
            try:
                # 检查该日期是否在汇率数据中
                if date in usd_cny_data.index:
                    try:
                        # 详细记录每一步操作和数据类型
                        gold_price = gold_data.loc[date, 'Close']
                        # 只打印一次详细信息，避免刷屏
                        if len(historical_data) < 2:
                            debug_expander.info(
                                f"日期 {date.strftime('%Y-%m-%d')} 的黄金价格原始值: {gold_price}, 类型: {type(gold_price)}")

                        gold_price_usd = float(gold_price)

                        usd_cny_rate_raw = usd_cny_data.loc[date, 'Close']
                        # 只打印一次详细信息，避免刷屏
                        if len(historical_data) < 2:
                            debug_expander.info(
                                f"日期 {date.strftime('%Y-%m-%d')} 的汇率原始值: {usd_cny_rate_raw}, 类型: {type(usd_cny_rate_raw)}")

                        usd_cny_rate = float(usd_cny_rate_raw)
                        gold_price_cny = gold_price_usd * usd_cny_rate

                        historical_data.append({
                            "date": date.strftime('%Y-%m-%d'),
                            "international_price_usd": gold_price_usd,
                            "international_price_cny": gold_price_cny,
                            "china_price_cny": gold_price_cny * 1.03,  # 假设3%溢价
                            "usd_cny_rate": usd_cny_rate,
                            "premium_rate": 1.03
                        })
                    except Exception as e:
                        error_msg = f"处理 {date.strftime('%Y-%m-%d')} 的数据时出错: {str(e)}"
                        debug_expander.warning(error_msg)
                        problem_dates.append(
                            {"date": date.strftime('%Y-%m-%d'), "error": str(e)})
                        continue
                else:
                    debug_expander.warning(
                        f"日期 {date.strftime('%Y-%m-%d')} 在汇率数据中不存在")
            except Exception as e:
                debug_expander.error(f"处理日期 {date} 时发生意外错误: {str(e)}")
                continue

        # 显示所有问题日期的汇总
        if problem_dates:
            debug_expander.warning(f"共有 {len(problem_dates)} 个日期处理出错")
            problem_df = pd.DataFrame(problem_dates)
            debug_expander.dataframe(problem_df)

        df = pd.DataFrame(historical_data)

        # 调试信息
        debug_expander.info(f"处理后的历史数据: {len(df)}条记录")
        if not df.empty:
            debug_expander.info(
                f"历史数据日期范围: {df['date'].min()} 到 {df['date'].max()}")

        if df.empty:
            st.warning("在指定时间范围内没有找到有效数据")
            return pd.DataFrame()

        # 最后排序确保数据按日期顺序
        df = df.sort_values(by='date')
        return df

    except Exception as e:
        st.error(f"获取历史数据时出错: {str(e)}")
        st.info("请确保选择的日期范围有效，且不超过今天的日期")
        import traceback
        st.error(f"详细错误信息: {traceback.format_exc()}")
        return pd.DataFrame()


@st.cache_data(ttl=24*3600)  # 缓存24小时
def get_china_gold_price(international_price_usd, usd_cny_rate):
    """获取中国黄金价格（模拟）"""
    try:
        # 模拟国内黄金溢价（通常在2-5%之间）
        premium_rate = 1.03  # 3%的溢价
        china_price_cny = float(international_price_usd) * \
            float(usd_cny_rate) * premium_rate
        return china_price_cny, premium_rate
    except Exception as e:
        st.error(f"计算国内金价时出错: {str(e)}")
        return None, None


@st.cache_data(ttl=24*3600)  # 缓存24小时
def create_gold_price_chart(history_data):
    """创建黄金价格走势图"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=history_data['date'],
        y=history_data['china_price_cny']/31.1035,  # 转换为克
        name='国内金价(人民币/克)',
        line=dict(color='gold')
    ))
    fig.add_trace(go.Scatter(
        x=history_data['date'],
        y=history_data['international_price_cny']/31.1035,  # 转换为克
        name='国际金价(人民币/克)',
        line=dict(color='blue')
    ))

    fig.update_layout(
        title='黄金价格走势',
        xaxis_title='日期',
        yaxis_title='价格(人民币/克)',
        hovermode='x unified'
    )
    return fig


@st.cache_data(ttl=24*3600)  # 缓存24小时
def calculate_moving_averages(df, column='international_price_usd'):
    """计算移动平均线"""
    result = df.copy()
    result['MA5'] = result[column].rolling(window=5).mean()
    result['MA10'] = result[column].rolling(window=10).mean()
    result['MA20'] = result[column].rolling(window=20).mean()
    result['MA60'] = result[column].rolling(window=60).mean()
    return result


@st.cache_data(ttl=24*3600)  # 缓存24小时
def calculate_volatility(df, column='international_price_usd', window=20):
    """计算价格波动率"""
    result = df.copy()
    # 计算每日收益率
    result['daily_return'] = result[column].pct_change()
    # 计算滚动波动率 (标准差)
    result['volatility'] = result['daily_return'].rolling(
        window=window).std() * np.sqrt(window)
    return result


@st.cache_data(ttl=24*3600)  # 缓存24小时
def perform_seasonal_analysis(df, column='international_price_usd'):
    """进行季节性分析"""
    if len(df) < 30:  # 至少需要30个数据点
        return None

    # 确保日期是索引且按顺序排列
    df = df.sort_values('date')
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')

    try:
        # 使用加法模型进行季节性分解
        result = seasonal_decompose(df[column], model='additive', period=30)
        return result
    except Exception as e:
        st.warning(f"季节性分析失败: {str(e)}")
        return None


@st.cache_data(ttl=24*3600)  # 缓存24小时
def calculate_rsi(df, column='international_price_usd', periods=14):
    """计算相对强弱指标 (RSI)"""
    result = df.copy()
    # 计算每日价格变化
    delta = result[column].diff()

    # 分离上升和下降的价格变动
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # 计算平均上升和下降
    avg_gain = gain.rolling(window=periods).mean()
    avg_loss = loss.rolling(window=periods).mean()

    # 计算相对强度
    rs = avg_gain / avg_loss

    # 计算RSI
    result['RSI'] = 100 - (100 / (1 + rs))

    return result


@st.cache_data(ttl=24*3600)  # 缓存24小时
def calculate_correlation_matrix(history_data, external_data=None):
    """计算黄金与其他资产的相关性"""
    if external_data is None:
        # 如果没有提供外部数据，只分析内部数据
        corr_columns = ['international_price_usd', 'international_price_cny',
                        'china_price_cny', 'usd_cny_rate']
        corr_data = history_data[corr_columns].corr()
        return corr_data
    else:
        # 这里可以扩展，关联外部数据如股票指数等
        pass


def draw_trend_analysis_chart(ma_data):
    """绘制趋势分析图表"""
    fig = go.Figure()

    # 添加原始价格
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(ma_data['date']),
        y=ma_data['international_price_usd'],
        name='黄金价格(美元/盎司)',
        line=dict(color='gold', width=2)
    ))

    # 添加各种移动平均线
    fig.add_trace(go.Scatter(
        x=pd.to_datetime(ma_data['date']),
        y=ma_data['MA5'],
        name='5日均线',
        line=dict(color='blue', width=1)
    ))

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(ma_data['date']),
        y=ma_data['MA10'],
        name='10日均线',
        line=dict(color='green', width=1)
    ))

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(ma_data['date']),
        y=ma_data['MA20'],
        name='20日均线',
        line=dict(color='red', width=1)
    ))

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(ma_data['date']),
        y=ma_data['MA60'],
        name='60日均线',
        line=dict(color='purple', width=1)
    ))

    fig.update_layout(
        title='黄金价格趋势分析',
        xaxis_title='日期',
        yaxis_title='价格 (美元/盎司)',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def draw_volatility_chart(vol_data):
    """绘制波动率分析图表"""
    # 确保数据中有可用的波动率值
    if vol_data['volatility'].dropna().empty:
        # 创建一个空图表
        fig = go.Figure()
        fig.update_layout(
            title='黄金价格波动性分析 (无可用数据)',
            annotations=[dict(
                text="无可用的波动率数据",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 添加价格
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(vol_data['date']),
            y=vol_data['international_price_usd'],
            name='黄金价格(美元/盎司)',
            line=dict(color='gold', width=2)
        ),
        secondary_y=False
    )

    # 添加波动率
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(vol_data['date']),
            y=vol_data['volatility'] * 100,  # 转换为百分比
            name='价格波动率(%)',
            line=dict(color='red', width=1.5)
        ),
        secondary_y=True
    )

    fig.update_layout(
        title='黄金价格波动性分析',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(title_text='日期')
    fig.update_yaxes(title_text='价格 (美元/盎司)', secondary_y=False)
    fig.update_yaxes(title_text='波动率 (%)', secondary_y=True)

    return fig


def draw_seasonal_chart(seasonal_result, history_data):
    """绘制季节性分析图表"""
    if seasonal_result is None:
        return None

    fig = make_subplots(rows=4, cols=1,
                        subplot_titles=('原始数据', '趋势分量', '季节性分量', '残差分量'),
                        shared_xaxes=True,
                        vertical_spacing=0.05)

    # 转换seasonal_result中的索引为datetime
    observed = seasonal_result.observed
    trend = seasonal_result.trend
    seasonal = seasonal_result.seasonal
    resid = seasonal_result.resid

    # 原始数据
    fig.add_trace(
        go.Scatter(x=observed.index, y=observed,
                   name='原始数据', line=dict(color='gold')),
        row=1, col=1
    )

    # 趋势分量
    fig.add_trace(
        go.Scatter(x=trend.index, y=trend, name='趋势分量',
                   line=dict(color='blue')),
        row=2, col=1
    )

    # 季节性分量
    fig.add_trace(
        go.Scatter(x=seasonal.index, y=seasonal,
                   name='季节性分量', line=dict(color='green')),
        row=3, col=1
    )

    # 残差分量
    fig.add_trace(
        go.Scatter(x=resid.index, y=resid, name='残差分量',
                   line=dict(color='red')),
        row=4, col=1
    )

    fig.update_layout(
        height=800,
        title='黄金价格季节性分解分析',
        hovermode='x unified'
    )

    return fig


def draw_correlation_heatmap(corr_matrix):
    """绘制相关性热力图"""
    fig = px.imshow(corr_matrix,
                    text_auto=True,
                    color_continuous_scale='RdBu_r',
                    zmin=-1, zmax=1,
                    aspect="auto")

    fig.update_layout(
        title='价格数据相关性分析',
        height=500,
        width=600
    )

    return fig


def draw_technical_indicators(tech_data):
    """绘制技术指标图表"""
    # 确保数据中有可用的RSI值
    if tech_data['RSI'].dropna().empty:
        # 创建一个空图表
        fig = go.Figure()
        fig.update_layout(
            title='黄金价格技术指标分析 (无可用数据)',
            annotations=[dict(
                text="无可用的RSI数据",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
        return fig

    fig = make_subplots(rows=2, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.1,
                        row_heights=[0.7, 0.3])

    # 价格图
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(tech_data['date']),
            y=tech_data['international_price_usd'],
            name='价格',
            line=dict(color='gold', width=2)
        ),
        row=1, col=1
    )

    # RSI图
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(tech_data['date']),
            y=tech_data['RSI'],
            name='RSI',
            line=dict(color='blue', width=1.5)
        ),
        row=2, col=1
    )

    # 添加RSI的参考线
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    fig.update_layout(
        title='黄金价格技术指标分析',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1)
    )

    fig.update_xaxes(title_text='日期', row=2, col=1)
    fig.update_yaxes(title_text='价格 (美元/盎司)', row=1, col=1)
    fig.update_yaxes(title_text='RSI', row=2, col=1)

    return fig


def draw_premium_rate_chart(history_data):
    """绘制溢价率变化趋势图"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(history_data['date']),
        y=history_data['premium_rate'] * 100 - 100,  # 转换为溢价百分比
        name='国内溢价率(%)',
        line=dict(color='red')
    ))

    fig.update_layout(
        title='国内黄金溢价率变化趋势',
        xaxis_title='日期',
        yaxis_title='溢价率 (%)',
        hovermode='x unified'
    )

    # 添加基准线（0%溢价）
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    return fig


def clear_cache():
    """清除所有缓存的数据"""
    get_gold_data.clear()
    get_usd_cny_rate.clear()
    get_historical_gold_data.clear()
    get_china_gold_price.clear()
    create_gold_price_chart.clear()
    calculate_moving_averages.clear()
    calculate_volatility.clear()
    perform_seasonal_analysis.clear()
    calculate_rsi.clear()
    calculate_correlation_matrix.clear()
    draw_trend_analysis_chart.clear()
    draw_volatility_chart.clear()
    draw_seasonal_chart.clear()
    draw_correlation_heatmap.clear()
    draw_technical_indicators.clear()
    draw_premium_rate_chart.clear()


def show_gold_analysis():
    """显示黄金价格分析"""
    st.title("黄金价格分析")

    # 添加刷新按钮
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("实时黄金价格数据")
    with col2:
        if st.button("🔄 手动刷新", help="清除缓存并从Yahoo Finance重新获取数据"):
            clear_cache()
            st.success("正在刷新数据...")
            st.rerun()

    # 获取数据
    international_price_usd, gold_data = get_gold_data()
    usd_cny_rate = get_usd_cny_rate()

    if international_price_usd is None:
        st.error("无法获取黄金价格数据，请稍后再试。")
        st.info("建议：\n1. 检查网络连接\n2. 等待几分钟后刷新页面\n3. 如果问题持续存在，请联系技术支持")
        return

    # 计算人民币价格
    international_price_cny = international_price_usd * usd_cny_rate
    china_price_cny, premium_rate = get_china_gold_price(
        international_price_usd, usd_cny_rate)

    # 保存数据到数据库
    current_date = datetime.now().strftime('%Y-%m-%d')
    save_gold_price(
        date=current_date,
        international_price_usd=international_price_usd,
        international_price_cny=international_price_cny,
        china_price_cny=china_price_cny,
        usd_cny_rate=usd_cny_rate,
        premium_rate=premium_rate
    )

    # 显示当前价格
    price_col1, price_col2 = st.columns(2)
    with price_col1:
        st.metric("国际金价(美元/盎司)", f"${international_price_usd:.2f}")
        st.metric("国际金价(人民币/盎司)", f"¥{international_price_cny:.2f}")
    with price_col2:
        st.metric("国内金价(人民币/克)", f"¥{china_price_cny/31.1035:.2f}")
        st.metric("美元兑人民币汇率", f"{usd_cny_rate:.4f}")

    # 获取历史数据
    st.subheader("历史数据")
    history_days = st.slider("显示最近多少天的数据", 7, 365, 30)
    history_data = get_historical_gold_data(history_days)

    if not history_data.empty:
        # 使用标签页展示不同的图表
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "基础价格图表", "趋势分析", "波动性分析", "技术指标", "季节性分析", "相关性分析"
        ])

        with tab1:
            # 基础价格图表
            st.subheader("基础价格图表")
            fig = create_gold_price_chart(history_data)
            st.plotly_chart(fig, use_container_width=True)

            # 溢价率图表
            st.subheader("国内外价格溢价分析")
            premium_fig = draw_premium_rate_chart(history_data)
            st.plotly_chart(premium_fig, use_container_width=True)

        with tab2:
            # 趋势分析
            st.subheader("价格趋势分析")
            ma_data = calculate_moving_averages(history_data)
            trend_fig = draw_trend_analysis_chart(ma_data)
            st.plotly_chart(trend_fig, use_container_width=True)

            # 显示移动平均线数据
            with st.expander("查看移动平均线数据"):
                st.dataframe(
                    ma_data[['date', 'international_price_usd', 'MA5', 'MA10', 'MA20', 'MA60']])

        with tab3:
            # 波动性分析
            st.subheader("价格波动性分析")

            vol_window = st.slider("波动率计算窗口(天)", 5, 30, 20)
            vol_data = calculate_volatility(history_data, window=vol_window)

            # 检查波动率数据是否为空
            if vol_data['volatility'].dropna().empty:
                st.warning(f"无法计算波动率，可能是因为数据点不足或全为空值。需要至少{vol_window+1}天的数据。")
                st.info("请尝试减小波动率计算窗口或增加历史数据查询天数。")
            else:
                vol_fig = draw_volatility_chart(vol_data)
                st.plotly_chart(vol_fig, use_container_width=True)

                # 分析波动率数据
                recent_vol = vol_data['volatility'].dropna().iloc[-1] * 100
                avg_vol = vol_data['volatility'].dropna().mean() * 100

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("当前波动率(%)", f"{recent_vol:.2f}%",
                              delta=f"{recent_vol - avg_vol:.2f}%",
                              delta_color="inverse")
                with col2:
                    st.metric("平均波动率(%)", f"{avg_vol:.2f}%")

        with tab4:
            # 技术指标分析
            st.subheader("技术指标分析")

            rsi_period = st.slider("RSI计算周期(天)", 7, 21, 14)
            tech_data = calculate_rsi(history_data, periods=rsi_period)

            # 检查RSI数据是否为空
            if tech_data['RSI'].dropna().empty:
                st.warning(f"无法计算RSI，可能是因为数据点不足。需要至少{rsi_period+1}天的数据。")
                st.info("请尝试减小RSI计算周期或增加历史数据查询天数。")
            else:
                tech_fig = draw_technical_indicators(tech_data)
                st.plotly_chart(tech_fig, use_container_width=True)

                # RSI分析
                current_rsi = tech_data['RSI'].dropna().iloc[-1]

                if current_rsi > 70:
                    rsi_conclusion = "RSI值高于70，可能处于超买状态，价格可能会回调"
                    rsi_color = "red"
                elif current_rsi < 30:
                    rsi_conclusion = "RSI值低于30，可能处于超卖状态，价格可能会反弹"
                    rsi_color = "green"
                else:
                    rsi_conclusion = "RSI值在30-70之间，处于中性区间"
                    rsi_color = "gray"

                st.markdown(
                    f"<p style='color:{rsi_color}'><b>RSI分析:</b> {rsi_conclusion}</p>", unsafe_allow_html=True)

        with tab5:
            # 季节性分析
            st.subheader("季节性分析")

            if len(history_data) >= 30:
                seasonal_result = perform_seasonal_analysis(history_data)
                if seasonal_result is not None:
                    seasonal_fig = draw_seasonal_chart(
                        seasonal_result, history_data)
                    st.plotly_chart(seasonal_fig, use_container_width=True)

                    # 提取季节性分量的洞察
                    seasonal_component = seasonal_result.seasonal
                    max_seasonal_effect = seasonal_component.max()
                    min_seasonal_effect = seasonal_component.min()

                    st.markdown(f"""
                    **季节性分析洞察:**
                    - 季节性影响范围: ${min_seasonal_effect:.2f} 到 ${max_seasonal_effect:.2f}
                    - 季节性因素可能会使价格在周期内波动约 ${abs(max_seasonal_effect - min_seasonal_effect):.2f} 美元
                    """)
                else:
                    st.warning("无法执行季节性分析，可能是数据点不足或数据格式不适合")
            else:
                st.warning("季节性分析至少需要30天的数据。请增加历史数据范围。")

        with tab6:
            # 相关性分析
            st.subheader("相关性分析")

            corr_matrix = calculate_correlation_matrix(history_data)
            corr_fig = draw_correlation_heatmap(corr_matrix)
            st.plotly_chart(corr_fig, use_container_width=True)

            # 相关性解释
            st.markdown("""
            **相关性解释:**
            - 1.0表示完全正相关，-1.0表示完全负相关，0表示无相关性
            - 国际金价(美元)与国际金价(人民币)高度相关，但受汇率影响
            - 国内金价与国际金价存在很强的相关性，但溢价率变化会影响相关性强度
            """)

        # 显示数据表格
        with st.expander("查看原始数据表格"):
            st.dataframe(history_data[['date', 'international_price_usd', 'international_price_cny',
                                      'china_price_cny', 'usd_cny_rate', 'premium_rate']])
    else:
        st.info("暂无历史数据")

    # 显示数据统计
    if not history_data.empty:
        st.subheader("数据统计分析")
        with st.expander("查看数据统计"):
            stats = history_data.describe()
            st.dataframe(stats)

            # 添加基本统计指标解释
            st.markdown("""
            **统计指标解释:**
            - **count**: 数据点的数量
            - **mean**: 平均值，表示数据的中心趋势
            - **std**: 标准差，表示数据的离散程度
            - **min/max**: 最小值和最大值，表示数据的范围
            - **25%/50%(中位数)/75%**: 四分位数，表示数据的分布情况
            """)
    else:
        st.info("暂无统计数据")
