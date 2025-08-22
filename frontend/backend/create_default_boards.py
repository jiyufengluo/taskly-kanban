#!/usr/bin/env python3
"""
为现有项目创建默认看板的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import Project, Board

def create_default_boards():
    """为没有看板的项目创建默认看板"""
    db: Session = SessionLocal()
    
    try:
        # 查找所有没有看板的项目
        projects_without_boards = db.query(Project).filter(
            ~Project.id.in_(
                db.query(Board.project_id).distinct()
            )
        ).all()
        
        print(f"找到 {len(projects_without_boards)} 个没有看板的项目")
        
        for project in projects_without_boards:
            # 为每个项目创建默认看板
            default_board = Board(
                name=f"{project.name} 看板",
                description="默认看板",
                project_id=project.id
            )
            
            db.add(default_board)
            print(f"为项目 '{project.name}' (ID: {project.id}) 创建了默认看板")
        
        db.commit()
        print("所有默认看板创建完成！")
        
    except Exception as e:
        print(f"创建默认看板时出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_default_boards()