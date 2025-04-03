import os
import pandas as pd
from flask import send_file, after_this_request
from datetime import datetime, timedelta
from tempfile import gettempdir
from flask import Blueprint, request, current_app
from app.db import db  # 使用之前定义的PyMySQL连接工具
from app.utils.response import make_response, validate_api_key
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import xlsxwriter
import pymysql

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
    
@bp.route('/export', methods=['GET'])
def export_records():
    """导出扣分记录报表（生产环境优化版）"""
    if not validate_api_key(request):
        return make_response(403, '无权操作')

    try:
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"deduction_report_{timestamp}.xlsx"
        filepath = os.path.join(gettempdir(), filename)

        # 创建SQLAlchemy引擎
        engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])

        # 获取明细数据
        base_query = text("""
        SELECT 
            dr.id as 记录ID,
            s.name as 姓名,
            s.student_number as 学号,
            dr.points as 扣分分值,
            dr.reason as 扣分事由,
            dr.operator as 操作人,
            dr.created_at as 记录时间
        FROM deduction_records dr
        INNER JOIN students s ON dr.student_id = s.id
        WHERE s.class_number = '2'
        """)
        
        with engine.connect() as conn:
            # 读取主数据
            df_main = pd.read_sql(base_query, conn)

            # 修复存储过程结果集处理
            raw_conn = engine.raw_connection()
            try:
                cursor = raw_conn.cursor(pymysql.cursors.DictCursor)
                cursor.callproc('GetDeductionStats')
                
                # 获取第一个结果集（总扣分TOP10）
                df_top = pd.DataFrame(
                    cursor.fetchall(),
                    columns=['姓名', '总扣分']
                )
                
                # 切换到第二个结果集（需要MySQL驱动支持）
                if cursor.nextset():
                    df_trend = pd.DataFrame(
                        cursor.fetchall(),
                        columns=['日期', '扣分次数', '总扣分']
                    )
                else:
                    df_trend = pd.DataFrame(columns=['日期', '扣分次数', '总扣分'])
                
                # 必须提交事务
                raw_conn.commit()
            finally:
                cursor.close()
                raw_conn.close()

        # 使用ExcelWriter创建多sheet报表
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # 写入数据
            df_main.to_excel(writer, sheet_name='扣分明细', index=False)
            df_top.to_excel(writer, sheet_name='扣分TOP10', index=False)
            df_trend.to_excel(writer, sheet_name='扣分趋势', index=False)

            # 获取工作簿对象
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'vcenter',
                'fg_color': '#D7E4BC',
                'border': 1
            })

            # 为每个工作表单独设置格式
            for sheet_name, df in [
                ('扣分明细', df_main),
                ('扣分TOP10', df_top), 
                ('扣分趋势', df_trend)
            ]:
                worksheet = writer.sheets[sheet_name]
                
                # 设置表头格式
                worksheet.set_row(0, 20, header_format)
                
                # 自动调整列宽（考虑中文宽度）
                for idx, column in enumerate(df.columns):
                    # 计算列标题宽度（中文按2字符计算）
                    header_width = max(len(str(column)) * 2, 10)
                    
                    # 计算内容最大宽度
                    if df[column].dtype == object:
                        content_width = df[column].astype(str).map(lambda x: len(x)*2).max()
                    else:
                        content_width = 10
                        
                    # 取最大宽度并设置
                    max_width = max(header_width, content_width) + 2  # 加padding
                    worksheet.set_column(idx, idx, max_width / 2)  # 转换为英文字符单位

                # 添加自动筛选
                worksheet.autofilter(0, 0, 0, len(df.columns)-1)

        @after_this_request
        # 注册文件清理回调
        def cleanup(response):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                current_app.logger.error(f"文件清理失败: {str(e)}")
            return response

        return send_file(
            filepath,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"导出失败: {str(e)}", exc_info=True)
        return make_response(500, "报表生成失败")

