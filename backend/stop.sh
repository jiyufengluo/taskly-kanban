#!/bin/bash

# Taskly Backend 停止脚本

set -e

echo "🛑 停止 Taskly Backend..."

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 停止所有服务
echo "🔄 停止所有服务..."
docker-compose down

# 可选：清理卷（取消注释以清理数据）
# echo "🗑️  清理数据卷..."
# docker-compose down -v

# 可选：清理镜像（取消注释以清理镜像）
# echo "🗑️  清理镜像..."
# docker-compose down --rmi all

echo "✅ Taskly Backend 已停止"