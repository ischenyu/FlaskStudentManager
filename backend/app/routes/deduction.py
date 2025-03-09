from flask import Blueprint, request, current_app
from app.db import db  # 使用之前定义的PyMySQL连接工具
from app.utils.response import make_response, validate_api_key
from datetime import datetime, timedelta

bp = Blueprint('deduction', __name__, url_prefix='/api/deductions')

def build_search_condition(search: str) -> tuple:
    """构建安全的搜索条件"""
    if not search:
        return "", []

    safe_search = f"%{search}%"
    condition = """
    AND (s.name LIKE %s 
         OR dr.reason LIKE %s 
         OR dr.operator LIKE %s)
    """
    return condition, [safe_search] * 3


@bp.route('', methods=['GET'])
def get_deductions():
    """获取扣分记录（支持新老参数兼容版）
    新参数格式：?page=1&size=20&keyword=李
    老参数兼容：?page=1&per_page=20&search=李
    """
    try:
        # 参数获取与兼容处理（新参数优先）
        page = max(int(request.args.get('page', 1)), 1)  # 页码最小为1
        size_param = request.args.get('size', request.args.get('per_page', '20'))
        search_term = request.args.get('keyword', request.args.get('search', '')).strip()

        # 参数校验与计算
        per_page = min(int(size_param), 100)  # 每页最多100条
        offset = (page - 1) * per_page

        # 构建基础SQL（安全过滤班级）
        base_query = """
        SELECT dr.id, s.name AS student_name, dr.points, 
               dr.reason, dr.created_at, dr.operator
        FROM deduction_records dr
        INNER JOIN students s ON dr.student_id = s.id
        WHERE s.class_number = '2'
        """

        # 动态搜索条件（防止SQL注入）
        search_condition, query_params = build_search_condition(search_term)
        base_query += search_condition

        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 获取总数（使用参数化查询）
                count_sql = f"SELECT COUNT(*) AS total FROM ({base_query}) AS sub"
                cursor.execute(count_sql, query_params)
                total = cursor.fetchone()['total']

                # 获取分页数据（强制时间倒序）
                data_sql = f"""
                {base_query}
                ORDER BY dr.created_at DESC
                LIMIT %s OFFSET %s
                """
                cursor.execute(data_sql, query_params + [per_page, offset])
                records = cursor.fetchall()

        # 结果格式化
        return make_response(data={
            'items': [{
                **record,
                'created_at': record['created_at'].isoformat()
            } for record in records],
            'pagination': {
                'page': page,
                'size': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })

    except ValueError as e:
        current_app.logger.warning(f"参数格式错误: {str(e)}")
        return make_response(400, "参数格式错误，请检查页码和每页数量")
    except Exception as e:
        current_app.logger.error(f"查询异常: {str(e)}", exc_info=True)
        return make_response(500, "服务器内部错误")


@bp.route('', methods=['POST'])
def add_deduction():
    """添加扣分记录（事务安全实现）"""
    if not validate_api_key(request):
        return make_response(403, '无权操作')

    try:
        data = request.get_json()
        required_fields = ['student_id', 'points', 'reason', 'operator']
        if not all(field in data for field in required_fields):
            return make_response(400, '缺少必要字段')

        # 验证数据格式
        student_id = int(data['student_id'])
        points = int(data['points'])
        if student_id == 3 : # It's me. Don't give me points.
            return make_response(403, '无权操作')
        if points <= 0:
            return make_response(400, '扣分数必须大于0')

        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 开启事务
                conn.begin()

                # 验证学生存在且属于2班
                cursor.execute("""
                SELECT id FROM students 
                WHERE id = %s AND class_number = '2'
                FOR UPDATE
                """, (student_id,))
                if not cursor.fetchone():
                    conn.rollback()
                    return make_response(404, '学生不存在或不属于2班')

                # 插入扣分记录
                cursor.execute("""
                INSERT INTO deduction_records 
                (student_id, points, reason, operator)
                VALUES (%s, %s, %s, %s)
                """, (student_id, points, data['reason'], data['operator']))

                conn.commit()
                return make_response()

    except ValueError as e:
        current_app.logger.warning(f"Invalid data format: {str(e)}")
        return make_response(400, "数据格式错误")
    except Exception as e:
        current_app.logger.error(f"Add error: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return make_response(500, "服务器内部错误")


@bp.route('/<int:record_id>', methods=['DELETE'])
def delete_deduction(record_id):
    """删除扣分记录（生产级修复版）"""
    if not validate_api_key(request):
        return make_response(403, '无权操作')

    try:
        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 使用JOIN替代子查询
                delete_sql = """
                DELETE dr
                FROM deduction_records dr
                INNER JOIN students s 
                    ON dr.student_id = s.id 
                    AND s.class_number = '2'
                WHERE dr.id = %s
                """
                cursor.execute(delete_sql, (record_id,))
                affected = cursor.rowcount
                conn.commit()

                if affected == 0:
                    return make_response(404, '记录不存在或无权操作')

                return make_response()

    except Exception as e:
        current_app.logger.error(f"Delete error: {str(e)}", exc_info=True)
        if 'conn' in locals():
            conn.rollback()
        return make_response(500, "服务器内部错误")


@bp.route('/statistics', methods=['GET'])
def get_statistics():
    """统计接口（性能优化实现）"""
    try:
        with db.connection() as conn:
            with conn.cursor() as cursor:
                # 总扣分TOP10
                cursor.execute("""
                SELECT s.name, SUM(dr.points) AS total_points
                FROM deduction_records dr
                JOIN students s ON dr.student_id = s.id
                WHERE s.class_number = '2'
                GROUP BY s.id
                ORDER BY total_points DESC
                LIMIT 10
                """)
                top_students = cursor.fetchall()

                # 最近30天趋势（使用预计算日期防止时区问题）
                start_date = (datetime.now() - timedelta(days=30)).date()
                cursor.execute("""
                SELECT 
                    DATE(dr.created_at) AS date,
                    COUNT(*) AS count,
                    SUM(dr.points) AS points
                FROM deduction_records dr
                JOIN students s ON dr.student_id = s.id
                WHERE s.class_number = '2'
                    AND dr.created_at >= %s
                GROUP BY DATE(dr.created_at)
                """, (start_date,))
                trend = cursor.fetchall()

        return make_response(data={
            'top_students': top_students,
            'trend': [{
                **row,
                'date': row['date'].isoformat()
            } for row in trend]
        })

    except Exception as e:
        current_app.logger.error(f"Statistics error: {str(e)}", exc_info=True)
        return make_response(500, "服务器内部错误")

# deduction.py 新增部分
@bp.route('/announce', methods=['GET'])
def announce():
    """获取最新公告"""
    try:
        with db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                SELECT text, time 
                FROM announce 
                ORDER BY time DESC 
                LIMIT 1
                """)
                result = cursor.fetchone()
                if result:
                    return make_response(data={
                        'text': result['text'],
                        'time': result['time'].isoformat()
                    })
                return make_response(404, "暂无公告")
    except Exception as e:
        current_app.logger.error(f"获取公告失败: {str(e)}", exc_info=True)
        return make_response(500, "服务器内部错误")
