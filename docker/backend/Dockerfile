FROM python:3.12-slim

WORKDIR /app

# 安装 uv（从官方镜像复制，会被缓存）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 安装系统依赖（只在依赖变化时重建）
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖声明文件
COPY backend/pyproject.toml backend/uv.lock ./backend/

# 安装Python依赖（使用缓存挂载，避免重复下载）
RUN --mount=type=cache,target=/root/.cache/uv \
    cd backend && uv sync --frozen --no-dev

# 复制后端代码（最后复制，代码改动只重建这一层）
COPY backend/ ./backend/

EXPOSE 8000

CMD ["uv", "run", "--directory", "backend", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
