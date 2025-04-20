import pandas as pd
from datetime import datetime
import streamlit as st
import mysql.connector
from mysql.connector import Error

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',  # 数据库服务器地址
    'user': 'your_username',  # 数据库用户名
    'password': 'your_password',  # 数据库密码
    'database': 'your_database'  # 数据库名称
}


def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"连接数据库时出错: {str(e)}")
        return None


def init_sales_db():
    """初始化销售数据库，创建必要的表"""
    connection = get_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    try:
        # 创建销售数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date DATE NOT NULL,
            product_name VARCHAR(255) NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            customer_name VARCHAR(255),
            payment_method VARCHAR(50),
            region VARCHAR(100),
            sales_person VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        connection.commit()
        st.success("数据库表创建成功")
    except Error as e:
        st.error(f"创建表时出错: {str(e)}")
    finally:
        cursor.close()
        connection.close()


def save_sales_record(date, product_name, quantity, unit_price, total_amount,
                      customer_name=None, payment_method=None, region=None, sales_person=None):
    """保存销售记录到数据库"""
    connection = get_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    try:
        cursor.execute('''
        INSERT INTO sales 
        (date, product_name, quantity, unit_price, total_amount,
         customer_name, payment_method, region, sales_person)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (date, product_name, quantity, unit_price, total_amount,
              customer_name, payment_method, region, sales_person))

        connection.commit()
        st.success("销售数据已成功保存到数据库")
    except Error as e:
        st.error(f"保存销售数据时出错: {str(e)}")
    finally:
        cursor.close()
        connection.close()


def get_sales_data(start_date=None, end_date=None, region=None, product_name=None):
    """获取指定条件下的销售数据"""
    connection = get_db_connection()
    if not connection:
        return pd.DataFrame()

    try:
        query = "SELECT * FROM sales"
        params = []
        conditions = []

        if start_date and end_date:
            conditions.append("date BETWEEN %s AND %s")
            params.extend([start_date, end_date])
        elif start_date:
            conditions.append("date >= %s")
            params.append(start_date)
        elif end_date:
            conditions.append("date <= %s")
            params.append(end_date)

        if region:
            conditions.append("region = %s")
            params.append(region)

        if product_name:
            conditions.append("product_name = %s")
            params.append(product_name)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY date DESC"

        df = pd.read_sql_query(query, connection, params=params)
        return df
    except Error as e:
        st.error(f"获取销售数据时出错: {str(e)}")
        return pd.DataFrame()
    finally:
        connection.close()


def get_sales_summary():
    """获取销售数据汇总统计"""
    connection = get_db_connection()
    if not connection:
        return None

    try:
        # 获取总销售额
        total_sales_query = "SELECT SUM(total_amount) as total_sales FROM sales"
        total_sales = pd.read_sql_query(total_sales_query, connection)[
            'total_sales'].iloc[0]

        # 获取按产品分类的销售额
        product_sales_query = """
        SELECT product_name, SUM(total_amount) as product_sales
        FROM sales
        GROUP BY product_name
        ORDER BY product_sales DESC
        """
        product_sales = pd.read_sql_query(product_sales_query, connection)

        # 获取按地区分类的销售额
        region_sales_query = """
        SELECT region, SUM(total_amount) as region_sales
        FROM sales
        GROUP BY region
        ORDER BY region_sales DESC
        """
        region_sales = pd.read_sql_query(region_sales_query, connection)

        # 获取按销售人员分类的销售额
        sales_person_query = """
        SELECT sales_person, SUM(total_amount) as sales_person_sales
        FROM sales
        GROUP BY sales_person
        ORDER BY sales_person_sales DESC
        """
        sales_person_sales = pd.read_sql_query(sales_person_query, connection)

        return {
            'total_sales': total_sales,
            'product_sales': product_sales,
            'region_sales': region_sales,
            'sales_person_sales': sales_person_sales
        }
    except Error as e:
        st.error(f"获取销售汇总数据时出错: {str(e)}")
        return None
    finally:
        connection.close()


def get_sales_trend(days=30):
    """获取最近N天的销售趋势"""
    connection = get_db_connection()
    if not connection:
        return pd.DataFrame()

    try:
        query = f"""
        SELECT date, SUM(total_amount) as daily_sales
        FROM sales
        GROUP BY date
        ORDER BY date DESC
        LIMIT {days}
        """
        df = pd.read_sql_query(query, connection)
        return df
    except Error as e:
        st.error(f"获取销售趋势数据时出错: {str(e)}")
        return pd.DataFrame()
    finally:
        connection.close()


def clear_old_sales_data(days_to_keep=365):
    """清理超过指定天数的旧销售数据"""
    connection = get_db_connection()
    if not connection:
        return

    cursor = connection.cursor()

    try:
        # 计算要保留的日期
        cutoff_date = (datetime.now() -
                       pd.Timedelta(days=days_to_keep)).strftime('%Y-%m-%d')

        cursor.execute("DELETE FROM sales WHERE date < %s", (cutoff_date,))
        connection.commit()
        st.success(f"已清理{cutoff_date}之前的销售数据")
    except Error as e:
        st.error(f"清理销售数据时出错: {str(e)}")
    finally:
        cursor.close()
        connection.close()
