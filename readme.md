# 🎓 学生扣分管理系统

![Vue](https://img.shields.io/badge/Vue-3.3.4-brightgreen)
![Flask](https://img.shields.io/badge/Flask-3.1.0-blue)
![MySQL](https://img.shields.io/badge/MySQL-8.3-orange)
[![Docker Image CI](https://github.com/ischenyu/FlaskStudentManager/actions/workflows/docker-image.yml/badge.svg?branch=master)](https://github.com/ischenyu/FlaskStudentManager/actions/workflows/docker-image.yml)

> 基于 Vue3 + Flask 的班级学生行为量化管理系统，提供扣分记录、数据统计、公告发布等功能

## 🌟 功能特性

### 📊 核心功能
| 功能模块       | 功能描述                              |
|----------------|-------------------------------------|
| 扣分记录管理    | 增删查改学生扣分记录，支持模糊搜索       |
| 数据可视化      | 折线图展示扣分趋势，TOP榜显示重点学生    |
| 公告系统        | Markdown格式公告弹窗，支持多端展示      |
| 权限验证        | API密钥验证机制保障数据安全            |

### 🛠 技术亮点
```text
📦 前端技术栈
- Vue3 + Composition API
- Ant Design Vue 组件库
- VueUse / Axios / Marked
- 响应式布局（适配PC/移动端）

⚙️ 后端技术栈
- Flask RESTful API
- PyMySQL 数据库操作
- JWT 令牌验证（预留接口）
- Nginx 反向代理配置
```

## 🚀 快速开始

### 环境要求
- Node.js 16+
- Python 3.9+
- MySQL 8.0+

### 📥 安装步骤

```bash
# 克隆项目
git clone https://github.com/ischenyu/FlaskStudentManager.git
cd FlaskStudentManager

# 前端依赖
cd fronted
npm install

# 后端依赖
cd ../backend
pip install -r requirements.txt
```

### 🛠 数据库配置

1. 创建MySQL数据库
```sql
CREATE DATABASE student DEFAULT CHARSET=utf8mb4;
```

2. 导入初始化数据
```bash
mysql -u root -p student < backend/student.sql
```

### ⚙️ 配置文件
在 `backend` 目录创建 `.env` 文件：
```ini
# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=student

# API安全配置
API_SECRET_KEY=your_secret_key_here
```

## 🖥 运行项目

### 后端服务
```bash
cd backend
flask run --host=0.0.0.0 --port=5000
```

### 前端服务
```bash
cd fronted
npm run dev
```

访问地址：http://localhost:5173

## 📂 项目结构

```bash
.
├── fronted                # 前端项目
│   ├── src
│   │   ├── assets        # 静态资源
│   │   ├── components    # 通用组件
│   │   ├── electeon      # 客户端
│   │   └── index.js      # 核心逻辑
│
├── backend               # 后端项目
│   ├── app
│   │   ├── routes        # 路由模块
│   │   ├── utils         # 工具函数
│   │   └── __init__.py   # 应用工厂
│   ├── student.sql       # 数据库初始化文件
│   └── requirements.txt  # Python依赖
```

## 📌 注意事项

1. **首次运行前**需确保：
   - MySQL服务已启动并开放3306端口
   - 已安装所有依赖包（前端npm / 后端pip）
   - 数据库账号有建表权限

2. **生产部署建议**：
   - 使用Gunicorn部署Flask应用
   - 配置Nginx反向代理
   - 启用HTTPS加密传输
   - 定期备份数据库

## 🤝 贡献指南

欢迎提交 Issue 或 PR，请遵循以下规范：
1. 新功能开发请新建分支（feat/xxx）
2. Bug修复请关联具体Issue编号
3. 提交前执行代码格式化（前端ESLint / 后端Black）

## 📄 许可证

[MIT License](license) © 2025 Shan Chenyu
