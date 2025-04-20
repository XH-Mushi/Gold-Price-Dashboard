import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import requests
import plotly.graph_objects as go
from database import init_db, save_gold_price, get_latest_gold_price, get_price_history
import time
import random

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
            time.sleep(delay + random.uniform(1, 3))

            # 设置请求头，模拟浏览器行为
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            # 使用download函数获取数据
            data = yf.download(
                symbol,
                start=(datetime.now() - timedelta(days=5)
                       ).strftime('%Y-%m-%d'),
                end=datetime.now().strftime('%Y-%m-%d'),
                progress=False,
                ignore_tz=True,
                timeout=30
            )

            if not data.empty:
                return data

        except Exception as e:
            if attempt < retries - 1:  # 如果还有重试次数
                st.warning(f"第{attempt + 1}次尝试失败: {str(e)}，等待后重试...")
                time.sleep(delay * (attempt + 2))  # 递增延时
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
        # 确保结束日期不超过今天
        current_date = datetime.now()
        end_date = current_date.replace(
            hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)

        st.info(
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
            st.info(f"获取到黄金数据: {len(gold_data)}条记录")
            if not gold_data.empty:
                st.info(
                    f"黄金数据日期范围: {gold_data.index.min().strftime('%Y-%m-%d')} 到 {gold_data.index.max().strftime('%Y-%m-%d')}")
                st.info(f"黄金数据列: {gold_data.columns.tolist()}")
                # 安全地检查和显示数据类型
                if 'Close' in gold_data.columns:
                    try:
                        # 使用dtypes字典而不是直接访问dtype属性
                        st.info(f"黄金收盘价数据类型: {gold_data.dtypes['Close']}")
                    except Exception as e:
                        st.warning(f"无法获取黄金收盘价数据类型: {str(e)}")
                # 显示部分样本数据
                st.info(f"黄金数据样本: \n{gold_data.head(2)}")

            if gold_data.empty:
                st.warning("无法获取黄金期货数据，尝试获取黄金现货数据...")
                gold_data = yf.download(
                    "XAUUSD=X",  # 黄金现货
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    progress=False
                )

                # 调试信息
                st.info(f"获取到黄金现货数据: {len(gold_data)}条记录")
                if not gold_data.empty:
                    st.info(
                        f"黄金现货数据日期范围: {gold_data.index.min().strftime('%Y-%m-%d')} 到 {gold_data.index.max().strftime('%Y-%m-%d')}")
        except Exception as e:
            st.error(f"获取黄金价格数据失败: {str(e)}")
            import traceback
            st.error(f"获取黄金数据错误详情: {traceback.format_exc()}")
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
            st.info(f"获取到汇率数据: {len(usd_cny_data)}条记录")
            if not usd_cny_data.empty:
                st.info(
                    f"汇率数据日期范围: {usd_cny_data.index.min().strftime('%Y-%m-%d')} 到 {usd_cny_data.index.max().strftime('%Y-%m-%d')}")
                st.info(f"汇率数据列: {usd_cny_data.columns.tolist()}")
                # 安全地检查和显示数据类型
                if 'Close' in usd_cny_data.columns:
                    try:
                        # 使用dtypes字典而不是直接访问dtype属性
                        st.info(f"汇率收盘价数据类型: {usd_cny_data.dtypes['Close']}")
                    except Exception as e:
                        st.warning(f"无法获取汇率收盘价数据类型: {str(e)}")
        except Exception as e:
            st.error(f"获取汇率数据失败: {str(e)}")
            import traceback
            st.error(f"获取汇率数据错误详情: {traceback.format_exc()}")
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
            st.warning(
                f"发现并移除黄金数据中的未来日期: {[d.strftime('%Y-%m-%d') for d in future_dates_gold]}")
            gold_data = gold_data.loc[gold_data.index.date <= today]

        if future_dates_cny:
            st.warning(
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
                            st.info(
                                f"日期 {date.strftime('%Y-%m-%d')} 的黄金价格原始值: {gold_price}, 类型: {type(gold_price)}")

                        gold_price_usd = float(gold_price)

                        usd_cny_rate_raw = usd_cny_data.loc[date, 'Close']
                        # 只打印一次详细信息，避免刷屏
                        if len(historical_data) < 2:
                            st.info(
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
                        st.warning(error_msg)
                        problem_dates.append(
                            {"date": date.strftime('%Y-%m-%d'), "error": str(e)})
                        continue
                else:
                    st.warning(f"日期 {date.strftime('%Y-%m-%d')} 在汇率数据中不存在")
            except Exception as e:
                st.error(f"处理日期 {date} 时发生意外错误: {str(e)}")
                continue

        # 显示所有问题日期的汇总
        if problem_dates:
            st.warning(f"共有 {len(problem_dates)} 个日期处理出错")
            problem_df = pd.DataFrame(problem_dates)
            st.dataframe(problem_df)

        df = pd.DataFrame(historical_data)

        # 调试信息
        st.info(f"处理后的历史数据: {len(df)}条记录")
        if not df.empty:
            st.info(f"历史数据日期范围: {df['date'].min()} 到 {df['date'].max()}")

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


def clear_cache():
    """清除所有缓存的数据"""
    get_gold_data.clear()
    get_usd_cny_rate.clear()
    get_historical_gold_data.clear()
    get_china_gold_price.clear()
    create_gold_price_chart.clear()


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

    # 显示历史数据
    st.subheader("历史数据")
    history_days = st.slider("显示最近多少天的数据", 7, 365, 30)
    history_data = get_historical_gold_data(history_days)

    if not history_data.empty:
        # 使用缓存的图表
        fig = create_gold_price_chart(history_data)
        st.plotly_chart(fig, use_container_width=True)

        # 显示数据表格
        st.dataframe(history_data[['date', 'international_price_usd', 'international_price_cny',
                                  'china_price_cny', 'usd_cny_rate', 'premium_rate']])
    else:
        st.info("暂无历史数据")

    # 显示数据统计
    st.subheader("数据统计")
    if not history_data.empty:
        stats = history_data.describe()
        st.dataframe(stats)
    else:
        st.info("暂无统计数据")
