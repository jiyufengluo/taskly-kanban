#!/usr/bin/env python3
"""
数据库连接测试脚本
"""

import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def test_database_connection():
    """测试数据库连接"""
    print("🔍 测试数据库连接...")
    
    try:
        # 创建数据库引擎
        engine = create_engine(settings.database_url)
        
        # 测试连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ 数据库连接成功")
            print(f"📊 PostgreSQL 版本: {version}")
            
            # 测试表是否存在
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 现有表: {tables}")
            
            return True
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_redis_connection():
    """测试Redis连接"""
    print("🔍 测试Redis连接...")
    
    try:
        import redis
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        print(f"✅ Redis连接成功")
        print(f"📊 Redis URL: {settings.redis_url}")
        return True
        
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Taskly Backend 连接测试")
    print("=" * 50)
    
    db_ok = test_database_connection()
    print()
    redis_ok = test_redis_connection()
    print()
    
    if db_ok and redis_ok:
        print("🎉 所有连接测试通过！")
        print("📝 现在可以启动后端服务了")
        print("💡 运行命令: python run_simple.py")
    else:
        print("❌ 连接测试失败，请检查配置")
        sys.exit(1)

if __name__ == "__main__":
    main()