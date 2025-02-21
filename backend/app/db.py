import pymysql
from pymysql import cursors
import os
from contextlib import contextmanager


class MySQLDB:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'db': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'cursorclass': cursors.DictCursor  # 返回字典格式结果
        }

    @contextmanager
    def connection(self):
        conn = pymysql.connect(**self.conn_params)
        try:
            yield conn
        finally:
            conn.close()


db = MySQLDB()
