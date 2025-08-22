#!/usr/bin/env python3
"""
创建管理员账号脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from app.models.user import User
from app.core.auth import get_password_hash
from app.core.config import settings

def create_admin_user():
    """创建管理员用户"""
    # 管理员信息
    admin_data = {
        "username": "admin",
        "email": "admin@taskly.com",
        "password": "admin123",  # 默认密码，建议后续修改
        "full_name": "系统管理员"
    }
    
    # 创建同步数据库引擎
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    
    # 创建数据库会话
    with SessionLocal() as session:
        try:
            # 检查管理员是否已存在
            existing_user = session.execute(
                select(User).where(User.username == admin_data["username"])
            ).scalar_one_or_none()
            
            if existing_user:
                print(f"管理员用户 '{admin_data['username']}' 已存在")
                print(f"用户ID: {existing_user.id}")
                print(f"邮箱: {existing_user.email}")
                print(f"创建时间: {existing_user.created_at}")
                return existing_user
            
            # 创建新的管理员用户
            hashed_password = get_password_hash(admin_data["password"])
            
            admin_user = User(
                username=admin_data["username"],
                email=admin_data["email"],
                hashed_password=hashed_password,
                full_name=admin_data["full_name"],
                is_active=True,
                is_verified=True  # 管理员默认已验证
            )
            
            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)
            
            print("✅ 管理员账号创建成功!")
            print(f"用户名: {admin_user.username}")
            print(f"邮箱: {admin_user.email}")
            print(f"密码: {admin_data['password']}")
            print(f"用户ID: {admin_user.id}")
            print(f"创建时间: {admin_user.created_at}")
            
            return admin_user
            
        except Exception as e:
            session.rollback()
            print(f"❌ 创建管理员账号失败: {e}")
            raise

if __name__ == "__main__":
    print("正在创建管理员账号...")
    create_admin_user()
    print("完成!")