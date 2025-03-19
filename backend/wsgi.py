from app import create_app

app = create_app()  # 调用工厂函数生成实例

if __name__ == "__main__":
    app.run()