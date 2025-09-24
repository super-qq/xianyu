import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"],
        cursorclass=DictCursor
    )

def insert_pre_product(summary, tao_token, price):
    """插入预发布商品数据并返回ID"""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO pre_product (summary, tao_token, price, is_release)
            VALUES (%s, %s, %s, 0)
            """
            cursor.execute(sql, (summary, tao_token, price))
            connection.commit()
            return cursor.lastrowid  # 返回插入的ID
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()
