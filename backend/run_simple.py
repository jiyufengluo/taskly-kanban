#!/usr/bin/env python3
"""
Taskly Backend 简单启动脚本
用于快速启动和测试后端服务
"""

import os
import sys
import asyncio
import uvicorn
from app.main_simple import app
from app.core.config import settings

def main():
    """主函数"""
    print("🚀 启动 Taskly Backend...")
    print(f"📊 服务信息:")
    print(f"   • 应用名称: {settings.app_name}")
    print(f"   • 版本: {settings.app_version}")
    print(f"   • 调试模式: {settings.debug}")
    print(f"   • 监听地址: {settings.host}:{settings.port}")
    print(f"   • 数据库: {settings.database_url}")
    print(f"   • Redis: {settings.redis_url}")
    print("")
    print(f"📚 API 文档: http://localhost:{settings.port}/docs")
    print(f"🏥 健康检查: http://localhost:{settings.port}/health")
    print("")
    
    try:
        uvicorn.run(
            "main_simple:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            ws_ping_interval=20,
            ws_ping_timeout=10,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()