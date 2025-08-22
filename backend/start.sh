#!/bin/bash

# Taskly Backend 启动脚本

set -e

echo "🚀 启动 Taskly Backend..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
mkdir -p ssl
mkdir -p logs

# 复制环境配置文件（如果不存在）
if [ ! -f .env ]; then
    echo "📝 创建环境配置文件..."
    cat > .env << EOF
# 应用配置
APP_NAME=Taskly Backend
DEBUG=True
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://root:123456@postgres:5432/SyncBoard

# Redis配置
REDIS_URL=redis://redis:6379

# JWT配置
SECRET_KEY=your-secret-key-change-in-production-please-use-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS配置
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# Celery配置
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# WebSocket配置
WEBSOCKET_MAX_CONNECTIONS=1000
EOF
    echo "✅ 环境配置文件已创建: .env"
fi

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose down --remove-orphans 2>/dev/null || true
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 检查健康状态
echo "🏥 检查健康状态..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 应用服务正常运行"
else
    echo "⚠️  应用服务可能还在启动中，请稍等..."
fi

# 显示访问信息
echo ""
echo "🎉 Taskly Backend 启动完成！"
echo ""
echo "📊 服务信息:"
echo "   • API 文档: http://localhost:8000/docs"
echo "   • 健康检查: http://localhost:8000/health"
echo "   • 应用地址: http://localhost:8000"
echo ""
echo "🔧 管理命令:"
echo "   • 查看日志: docker-compose logs -f"
echo "   • 停止服务: docker-compose down"
echo "   • 重启服务: docker-compose restart"
echo ""
echo "📱 前端配置:"
echo "   • API 地址: http://localhost:8000/api/v1"
echo "   • WebSocket: ws://localhost:8000/api/v1/ws"
echo ""

# 显示实时日志（可选）
read -p "是否显示实时日志？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f
fi