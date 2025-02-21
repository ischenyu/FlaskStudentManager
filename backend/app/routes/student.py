from flask import Blueprint, request, current_app
from app.db import db
from app.utils.response import make_response

bp = Blueprint('student', __name__, url_prefix='/api/students')


@bp.route('', methods=['GET'])
def search_students():
    """搜索学生接口（生产级实现）"""
    try:
        # 参数验证
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 100)), 100)
        search = request.args.get('search', '').strip()
        offset = (page - 1) * per_page

        # 构建基础查询（移除了聚合函数）
        base_count_sql = """
               SELECT COUNT(DISTINCT s.id) AS total
               FROM students s
               LEFT JOIN deduction_records dr ON s.id = dr.student_id
               WHERE s.class_number = '2'
               """
        count_params = []

        # 主数据查询（保持原有聚合）
        base_data_sql = """
               SELECT 
                   s.id,
                   s.name,
                   s.student_number,
                   s.gender,
                   COALESCE(SUM(dr.points), 0) AS total_deduction
               FROM students s
               LEFT JOIN deduction_records dr ON s.id = dr.student_id
               WHERE s.class_number = '2'
               """
        data_params = []

        # 添加搜索条件
        if search:
            condition = " AND s.name LIKE %s "
            count_params.append(f"%{search}%")
            data_params.append(f"%{search}%")
            base_count_sql += condition
            base_data_sql += condition

        # 最终数据查询
        final_data_sql = f"""
               {base_data_sql}
               GROUP BY s.id
               ORDER BY s.id
               LIMIT %s OFFSET %s
               """
        data_params.extend([per_page, offset])

        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 获取总数（使用独立查询）
                cursor.execute(base_count_sql, count_params)
                total = cursor.fetchone()['total']

                # 获取分页数据
                cursor.execute(final_data_sql, data_params)
                students = cursor.fetchall()

        # 构建安全查询
        base_sql = """
        SELECT 
            s.id,
            s.name,
            s.student_number,
            s.gender,
            COALESCE(SUM(dr.points), 0) AS total_deduction
        FROM students s
        LEFT JOIN deduction_records dr ON s.id = dr.student_id
        WHERE s.class_number = '2'
        """
        params = []

        # 添加搜索条件
        if search:
            base_sql += " AND s.name LIKE %s "
            params.append(f"%{search}%")

        # 分组和分页
        #final_sql = f"""
        #{base_sql}
        #GROUP BY s.id
        #ORDER BY s.id
        #LIMIT %s OFFSET %s
        #"""
        """params.extend([per_page, offset])

        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 获取总数
                count_sql = f"SELECT COUNT(*) AS total FROM ({base_sql}) AS sub"
                cursor.execute(count_sql, params[:-2])  # 排除分页参数
                total = cursor.fetchone()['total']

                # 获取分页数据
                cursor.execute(final_sql, params)
                students = cursor.fetchall()"""

        return make_response(data={
            'items': [{
                **student,
                # 转换Decimal类型为int
                'total_deduction': int(student['total_deduction'])
            } for student in students],
            'total': total,
            'pages': (total + per_page - 1) // per_page
        })

    except ValueError as e:
        current_app.logger.warning(f"Invalid params: {str(e)}")
        return make_response(400, "参数格式错误")
    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}", exc_info=True)
        return make_response(500, "服务器内部错误")
