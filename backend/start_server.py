#!/usr/bin/env python3
"""
后端服务启动脚本
"""
import uvicorn
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动 Taskly Backend 服务...")
    print("📡 服务地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/api/v1/ws/project/{project_id}")
    print("")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ws_ping_interval=20,
        ws_ping_timeout=10
    )