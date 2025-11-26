#!/bin/sh
set -e

cd /app/domain-chatbot

# 初始化数据库
/opt/venv/bin/python manage.py migrate --noinput

# 确保静态/临时目录存在
mkdir -p tmp media logs db

# 启动 ASGI 服务器（含 WebSocket）
/opt/venv/bin/daphne -b 0.0.0.0 -p 8000 VirtualWife.asgi:application
