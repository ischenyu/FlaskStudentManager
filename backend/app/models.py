from datetime import datetime
from app.extensions import db

# 确保每个模型都定义主键
class Student(db.Model):
    __tablename__ = 'students'  # 注意这里必须是复数形式且保持唯一
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 明确主键
    name = db.Column(db.String(20), nullable=False, index=True)
    class_number = db.Column(db.String(10), default='2', nullable=False)
    gender = db.Column(db.String(2), comment='性别')
    student_number = db.Column(db.String(10), unique=True, comment='学号')

class DeductionRecord(db.Model):
    __tablename__ = 'deduction_records'
    id = db.Column(db.Integer, primary_key=True)  # 主键必须存在
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    operator = db.Column(db.String(20), nullable=False)

    student = db.relationship('Student', backref='deductions')

class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    id = db.Column(db.Integer, primary_key=True)  # 主键必须存在
    operator = db.Column(db.String(20), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
