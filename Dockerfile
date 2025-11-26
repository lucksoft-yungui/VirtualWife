# ---------- Frontend build (Next.js) ----------
FROM node:16.20-bullseye AS frontend-builder
WORKDIR /app/domain-chatvrm
COPY domain-chatvrm/package*.json ./
RUN npm ci --legacy-peer-deps
COPY domain-chatvrm .
RUN npm run build && npm prune --production

# ---------- Backend base (dependencies cache) ----------
FROM python:3.10-slim AS backend-builder
WORKDIR /app/domain-chatbot
COPY domain-chatbot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Final runtime (single container with reverse proxy) ----------
FROM node:16.20-bullseye

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=VirtualWife.settings \
    NEXT_TELEMETRY_DISABLED=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
    PIP_TRUSTED_HOST=mirrors.aliyun.com \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

# 基础工具与进程管理（使用国内镜像以避免拉取失败）
RUN sed -i 's@deb.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list && \
    sed -i 's@security.debian.org@mirrors.aliyun.com@g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 python3-venv python3-distutils python3-dev \
        build-essential libffi-dev curl ca-certificates nginx supervisor && \
    rm -rf /var/lib/apt/lists/*

# ---- 前端产物 ----
COPY --from=frontend-builder /app/domain-chatvrm/.next ./domain-chatvrm/.next
COPY --from=frontend-builder /app/domain-chatvrm/public ./domain-chatvrm/public
COPY --from=frontend-builder /app/domain-chatvrm/package.json ./domain-chatvrm/package.json
COPY --from=frontend-builder /app/domain-chatvrm/package-lock.json ./domain-chatvrm/package-lock.json
COPY --from=frontend-builder /app/domain-chatvrm/node_modules ./domain-chatvrm/node_modules

# ---- 后端代码 ----
COPY domain-chatbot ./domain-chatbot

# 安装后端依赖到独立 venv（prefer-binary 避免 gevent 等包源码编译失败）
RUN python3 -m venv /opt/venv && \
    PIP_PREFER_BINARY=1 /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel "Cython<3" && \
    PIP_PREFER_BINARY=1 /opt/venv/bin/pip install --no-cache-dir --prefer-binary -r domain-chatbot/requirements.txt
ENV PATH="/opt/venv/bin:${PATH}"

# Nginx / Supervisor 配置与启动脚本
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/start-backend.sh /usr/local/bin/start-backend.sh
RUN chmod +x /usr/local/bin/start-backend.sh

# 默认仅暴露一条对外端口
EXPOSE 8080

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
