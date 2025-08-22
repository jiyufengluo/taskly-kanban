#!/usr/bin/env python3
"""
数据库初始化脚本
创建数据库表和初始数据
"""

import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.database import Base
from app.models.models import User, Project, List, Card, ProjectMember, CardLabel, CardAssignment, ActivityLog
from app.core.security import password_manager
from sqlalchemy.orm import sessionmaker

def create_database_tables():
    """创建数据库表"""
    print("📊 创建数据库表...")
    
    try:
        # 创建数据库引擎
        engine = create_engine(settings.database_url)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
        
        return engine
        
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        return None

def create_initial_data(engine):
    """创建初始数据"""
    print("📝 创建初始数据...")
    
    try:
        # 创建会话
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 检查是否已有数据
        existing_users = db.query(User).count()
        if existing_users > 0:
            print("ℹ️  数据库中已有数据，跳过初始数据创建")
            return True
        
        # 创建管理员用户
        admin_user = User(
            email="admin@example.com",
            username="admin",
            full_name="Administrator",
            password_hash=password_manager.hash_password("123456")
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # 创建测试用户
        test_user = User(
            email="john@example.com",
            username="john_doe",
            full_name="John Doe",
            password_hash=password_manager.hash_password("123456")
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 创建示例项目
        sample_project = Project(
            name="我的第一个项目",
            description="这是一个示例项目，用于演示Taskly的功能",
            owner_id=admin_user.id
        )
        db.add(sample_project)
        db.commit()
        db.refresh(sample_project)
        
        # 创建项目所有者成员记录
        owner_member = ProjectMember(
            project_id=sample_project.id,
            user_id=admin_user.id,
            role='owner'
        )
        db.add(owner_member)
        
        # 添加测试用户为项目成员
        test_member = ProjectMember(
            project_id=sample_project.id,
            user_id=test_user.id,
            role='member'
        )
        db.add(test_member)
        db.commit()
        
        # 创建默认列表
        default_lists = [
            {"name": "待办", "position": 0},
            {"name": "进行中", "position": 1},
            {"name": "已完成", "position": 2}
        ]
        
        created_lists = []
        for list_data in default_lists:
            new_list = List(
                name=list_data["name"],
                position=list_data["position"],
                project_id=sample_project.id
            )
            db.add(new_list)
            db.commit()
            db.refresh(new_list)
            created_lists.append(new_list)
        
        # 创建示例卡片
        sample_cards = [
            {
                "title": "调研竞争对手",
                "description": "分析前3名竞争对手的产品特点和市场策略",
                "position": 0,
                "list_id": created_lists[0].id,
                "assigned_user_id": test_user.id
            },
            {
                "title": "创建线框图",
                "description": "设计主要页面的线框图，包括首页、看板页面、设置页面",
                "position": 1,
                "list_id": created_lists[0].id,
                "assigned_user_id": admin_user.id
            },
            {
                "title": "搭建开发环境",
                "description": "安装所有必要的开发工具和依赖包",
                "position": 0,
                "list_id": created_lists[1].id,
                "assigned_user_id": admin_user.id
            },
            {
                "title": "项目启动会议",
                "description": "团队首次会议讨论项目目标和时间安排",
                "position": 0,
                "list_id": created_lists[2].id,
                "assigned_user_id": admin_user.id
            }
        ]
        
        for card_data in sample_cards:
            new_card = Card(
                title=card_data["title"],
                description=card_data["description"],
                position=card_data["position"],
                list_id=card_data["list_id"]
            )
            db.add(new_card)
            
            # 创建卡片分配
            if "assigned_user_id" in card_data:
                assignment = CardAssignment(
                    card_id=new_card.id,
                    user_id=card_data["assigned_user_id"]
                )
                db.add(assignment)
        
        db.commit()
        
        print("✅ 初始数据创建成功")
        print(f"📊 创建了 {db.query(User).count()} 个用户")
        print(f"📊 创建了 {db.query(Project).count()} 个项目")
        print(f"📊 创建了 {db.query(List).count()} 个列表")
        print(f"📊 创建了 {db.query(Card).count()} 个卡片")
        
        # 打印登录信息
        print("")
        print("🔑 登录信息:")
        print("   管理员: admin@example.com / 123456")
        print("   测试用户: john@example.com / 123456")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建初始数据失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 Taskly Backend 数据库初始化")
    print("=" * 50)
    
    # 创建数据库表
    engine = create_database_tables()
    if not engine:
        print("❌ 数据库表创建失败")
        sys.exit(1)
    
    print()
    
    # 创建初始数据
    if not create_initial_data(engine):
        print("❌ 初始数据创建失败")
        sys.exit(1)
    
    print("")
    print("🎉 数据库初始化完成！")
    print("💡 现在可以启动后端服务了")
    print("📝 运行命令: python run_simple.py")

if __name__ == "__main__":
    main()