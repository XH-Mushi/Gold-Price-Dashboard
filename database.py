import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st


def init_db():
    """初始化数据库，创建必要的表"""
    conn = sqlite3.connect('gold_prices.db')
    cursor = conn.cursor()

    # 创建黄金价格表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gold_prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        international_price_usd REAL,
        international_price_cny REAL,
        china_price_cny REAL,
        usd_cny_rate REAL,
        premium_rate REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()


def save_gold_price(date, international_price_usd, international_price_cny,
                    china_price_cny, usd_cny_rate, premium_rate):
    """保存黄金价格数据到数据库"""
    conn = sqlite3.connect('gold_prices.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO gold_prices 
        (date, international_price_usd, international_price_cny, 
         china_price_cny, usd_cny_rate, premium_rate)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (date, international_price_usd, international_price_cny,
              china_price_cny, usd_cny_rate, premium_rate))

        conn.commit()
        st.success("数据已成功保存到数据库")
    except Exception as e:
        st.error(f"保存数据时出错: {str(e)}")
    finally:
        conn.close()


def get_gold_prices(start_date=None, end_date=None):
    """获取指定日期范围内的黄金价格数据"""
    conn = sqlite3.connect('gold_prices.db')

    try:
        query = "SELECT * FROM gold_prices"
        params = []

        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " WHERE date >= ?"
            params.append(start_date)
        elif end_date:
            query += " WHERE date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC"

        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"获取数据时出错: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_latest_gold_price():
    """获取最新的黄金价格数据"""
    conn = sqlite3.connect('gold_prices.db')

    try:
        query = "SELECT * FROM gold_prices ORDER BY date DESC LIMIT 1"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"获取最新数据时出错: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_price_history(days=30):
    """获取最近N天的价格历史"""
    conn = sqlite3.connect('gold_prices.db')

    try:
        query = f"SELECT * FROM gold_prices ORDER BY date DESC LIMIT {days}"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"获取历史数据时出错: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()


def clear_old_data(days_to_keep=365):
    """清理超过指定天数的旧数据"""
    conn = sqlite3.connect('gold_prices.db')
    cursor = conn.cursor()

    try:
        # 计算要保留的日期
        cutoff_date = (datetime.now() -
                       pd.Timedelta(days=days_to_keep)).strftime('%Y-%m-%d')

        cursor.execute(
            "DELETE FROM gold_prices WHERE date < ?", (cutoff_date,))
        conn.commit()
        st.success(f"已清理{cutoff_date}之前的数据")
    except Exception as e:
        st.error(f"清理数据时出错: {str(e)}")
    finally:
        conn.close()
