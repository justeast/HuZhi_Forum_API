# 使用 Python 3.12 slim 版本作为基础镜像
FROM python:3.12-slim

# 设置环境变量
# 防止 Python 生成 .pyc 文件
ENV PYTHONDONTWRITEBYTECODE=1
# 防止 Python 缓冲 stdout 和 stderr
ENV PYTHONUNBUFFERED=1
# 告诉 uv 使用系统环境
ENV UV_SYSTEM_PYTHON=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖 (mysqlclient 需要这些编译工具)
# 大陆服务器构建时，先切换 Debian 软件源，避免 deb.debian.org 超时
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|http://deb.debian.org/debian|https://mirrors.aliyun.com/debian|g' /etc/apt/sources.list.d/debian.sources; \
        sed -i 's|http://security.debian.org/debian-security|https://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources; \
        sed -i 's|http://deb.debian.org/debian-security|https://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list.d/debian.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
        sed -i 's|http://deb.debian.org/debian|https://mirrors.aliyun.com/debian|g' /etc/apt/sources.list; \
        sed -i 's|http://security.debian.org/debian-security|https://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list; \
        sed -i 's|http://deb.debian.org/debian-security|https://mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list; \
    fi \
    && apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*


# 从官方镜像中复制 uv 工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 1. 优先复制依赖定义文件 (利用 Docker 缓存层)
COPY pyproject.toml uv.lock ./

# 2. 安装依赖
# --frozen: 严格依照 lock 文件安装
# --no-dev: 生产环境不需要安装开发依赖
RUN uv sync --frozen --no-dev

# 3. 复制项目代码
COPY . .


# 暴露端口 (仅用于文档说明)
EXPOSE 8013

# 启动命令
# 使用 daphne 启动 ASGI 应用
CMD ["daphne", "-b", "0.0.0.0", "-p", "8013", "config.asgi:application"]