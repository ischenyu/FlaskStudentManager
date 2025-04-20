from flask import Flask
from config import config
from app.extensions import db, migrate
from flask_cors import CORS


def create_app(config_name='production'):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图
    from app.routes.deduction import bp as deduction_bp
    from app.routes.student import bp as student_bp
    from app.routes.system import bp as system_bp
    app.register_blueprint(deduction_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(system_bp)

    # 生产环境健康检查
    @app.route('/health')
    def health_check():
        return 'OK'

    return app
