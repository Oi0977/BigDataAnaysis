# CLAUDE.md

## 项目信息

这是一个抖音电商竞品智能分析与AI素材工厂的大数据项目，用于课程作业/毕业设计。

## 开发环境

- **操作系统**: Windows 11
- **Docker**: Docker Desktop（需要时请提醒我启动）
- **WSL2**: 已安装，但尽量不要使用，优先使用 Windows 原生命令
- **Shell**: 使用 PowerShell 或 CMD，不要使用 Linux 命令

## 语言要求

- 所有对话、解释和代码注释使用中文（简体中文）
- 响应内容使用中文

## 技术栈

- **前端**: Vue3 + ECharts + Vite
- **后端**: FastAPI + Python 3.12
- **大数据**: Kafka + Spark + HDFS + HBase + Elasticsearch
- **部署**: Docker + Docker Compose
- **包管理**: uv (Python包管理器)

## 包管理工具

**重要**: 本项目使用 `uv` 作为Python包管理工具，而不是pip。

### 环境管理

```bash
# 创建虚拟环境
uv venv --python 3.12

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 依赖管理

```bash
# 添加依赖
uv add <package-name>
uv add <package-name>==<version>

# 删除依赖
uv remove <package-name>

# 同步依赖
uv sync

# 查看依赖树
uv tree
```

### 运行命令

```bash
# 在虚拟环境中运行Python脚本
uv run python <script.py>

# 运行FastAPI
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
uv run pytest tests/ -v
```

## 开发规范

### 代码风格

- Python: 遵循PEP 8规范
- Vue: 使用Composition API或Options API（根据组件复杂度选择）
- 命名: 使用有意义的变量名和函数名

### 文件组织

- 后端代码放在 `backend/` 目录
- 前端代码放在 `frontend/` 目录
- Docker配置放在 `docker/` 目录
- Mock数据放在 `mock-data/` 目录

### Git提交

- 使用中文提交信息
- 提交信息格式: `<type>: <description>`
- 类型: feat, fix, docs, style, refactor, test, chore

## 常用命令（Windows PowerShell）

```powershell
# 启动Docker服务（需要先启动Docker Desktop）
docker-compose up -d

# 停止Docker服务
docker-compose down

# 查看日志
docker-compose logs -f

# 生成Mock数据
cd mock-data
uv run python generate_products.py
uv run python generate_reviews.py

# 运行后端
cd backend
uv run uvicorn app.main:app --reload

# 运行前端
cd frontend
npm run dev
```

## 注意事项

1. **使用uv管理依赖**: 不要使用pip，统一使用uv
2. **虚拟环境**: 确保在正确的虚拟环境中运行命令
3. **Docker**: 大数据组件通过Docker部署，运行docker-compose前请提醒我启动Docker Desktop
4. **端口冲突**: 检查端口是否被占用，必要时修改docker-compose.yml中的端口映射
5. **命令环境**: 优先使用Windows PowerShell命令，避免使用Linux/WSL命令
