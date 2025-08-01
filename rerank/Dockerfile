FROM python:3.10

# 1. 通用环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple

# 2. 工作目录
WORKDIR /app

# 3. 安装 uv 并同步依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv \
 && uv sync --no-cache

# 4. 复制项目代码
COPY . .

# 5. 暴露端口 & 启动
EXPOSE 8089
CMD ["sh", "-c", "uv run python server.py"]
