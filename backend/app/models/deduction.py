from app.db import db
from datetime import datetime


class DeductionManager:
    @staticmethod
    def init_tables():
        """初始化数据库表结构"""
        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 创建学生表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(20) NOT NULL,
                    class_number VARCHAR(10) DEFAULT '2',
                    student_number VARCHAR(10) UNIQUE,
                    gender ENUM('男','女')
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

                # 创建扣分表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS deduction_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT NOT NULL,
                    points INT NOT NULL CHECK(points > 0),
                    reason VARCHAR(200) NOT NULL,
                    operator VARCHAR(20) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()

    @classmethod
    def search_students(cls, search: str, page: int, per_page: int):
        """搜索学生（带分页）"""
        offset = (page - 1) * per_page
        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 参数化查询防止SQL注入
                base_sql = """
                SELECT s.id, s.name, s.student_number, 
                       SUM(d.points) AS total_deduction
                FROM students s
                LEFT JOIN deduction_records d ON s.id = d.student_id
                WHERE s.class_number = '2' 
                """
                params = []

                if search:
                    base_sql += " AND s.name LIKE %s"
                    params.append(f"%{search}%")

                base_sql += " GROUP BY s.id ORDER BY s.id LIMIT %s OFFSET %s"
                params.extend([per_page, offset])

                cursor.execute(base_sql, params)
                return cursor.fetchall()
