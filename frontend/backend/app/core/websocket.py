from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, ProjectMember
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接: {user_id: {project_id: [websockets]}}
        self.active_connections: Dict[int, Dict[int, List[WebSocket]]] = {}
        # 存储用户到项目的映射: {user_id: set(project_ids)}
        self.user_projects: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, project_id: int):
        """建立WebSocket连接"""
        await websocket.accept()
        
        # 初始化用户连接字典
        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}
            self.user_projects[user_id] = set()
        
        # 初始化项目连接列表
        if project_id not in self.active_connections[user_id]:
            self.active_connections[user_id][project_id] = []
        
        # 添加连接
        self.active_connections[user_id][project_id].append(websocket)
        self.user_projects[user_id].add(project_id)
        
        # 通知其他用户有新用户加入
        await self.broadcast_to_project(
            project_id,
            {
                "type": "user_joined",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            },
            exclude_user=user_id
        )
    
    def disconnect(self, websocket: WebSocket, user_id: int, project_id: int):
        """断开WebSocket连接"""
        if user_id in self.active_connections:
            if project_id in self.active_connections[user_id]:
                if websocket in self.active_connections[user_id][project_id]:
                    self.active_connections[user_id][project_id].remove(websocket)
                
                # 如果该项目没有连接了，移除项目
                if not self.active_connections[user_id][project_id]:
                    del self.active_connections[user_id][project_id]
                    self.user_projects[user_id].discard(project_id)
            
            # 如果用户没有任何连接了，移除用户
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                del self.user_projects[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int, project_id: int):
        """发送个人消息"""
        if user_id in self.active_connections:
            if project_id in self.active_connections[user_id]:
                connections = self.active_connections[user_id][project_id].copy()
                for connection in connections:
                    try:
                        await connection.send_text(json.dumps(message))
                    except:
                        # 连接已断开，移除它
                        self.active_connections[user_id][project_id].remove(connection)
    
    async def broadcast_to_project(self, project_id: int, message: dict, exclude_user: int = None):
        """向项目中的所有用户广播消息"""
        for user_id, projects in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            if project_id in projects:
                connections = projects[project_id].copy()
                for connection in connections:
                    try:
                        await connection.send_text(json.dumps(message))
                    except:
                        # 连接已断开，移除它
                        projects[project_id].remove(connection)
    
    def get_project_users(self, project_id: int) -> List[int]:
        """获取项目中的在线用户列表"""
        online_users = []
        for user_id, projects in self.active_connections.items():
            if project_id in projects and projects[project_id]:
                online_users.append(user_id)
        return online_users

# 全局连接管理器实例
manager = ConnectionManager()

class WebSocketService:
    """WebSocket服务类"""
    
    @staticmethod
    async def handle_card_update(project_id: int, card_data: dict, user_id: int):
        """处理卡片更新事件"""
        message = {
            "type": "card_updated",
            "data": card_data,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def handle_card_move(project_id: int, card_data: dict, user_id: int):
        """处理卡片移动事件"""
        message = {
            "type": "card_moved",
            "data": card_data,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def handle_card_create(project_id: int, card_data: dict, user_id: int):
        """处理卡片创建事件"""
        message = {
            "type": "card_created",
            "data": card_data,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def handle_card_delete(project_id: int, card_id: int, user_id: int):
        """处理卡片删除事件"""
        message = {
            "type": "card_deleted",
            "data": {"card_id": card_id},
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def handle_list_create(project_id: int, list_data: dict, user_id: int):
        """处理列表创建事件"""
        message = {
            "type": "list_created",
            "data": list_data,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def handle_list_update(project_id: int, list_data: dict, user_id: int):
        """处理列表更新事件"""
        message = {
            "type": "list_updated",
            "data": list_data,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def handle_board_update(project_id: int, board_data: dict, user_id: int):
        """处理看板更新事件"""
        message = {
            "type": "board_updated",
            "data": board_data,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def handle_user_typing(project_id: int, card_id: int, user_id: int, is_typing: bool):
        """处理用户正在输入事件"""
        message = {
            "type": "user_typing",
            "data": {
                "card_id": card_id,
                "is_typing": is_typing
            },
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_project(project_id, message, exclude_user=user_id)
    
    @staticmethod
    async def send_online_users(project_id: int, user_id: int):
        """发送在线用户列表"""
        online_users = manager.get_project_users(project_id)
        message = {
            "type": "online_users",
            "data": {"users": online_users},
            "timestamp": datetime.now().isoformat()
        }
        await manager.send_personal_message(message, user_id, project_id)

def verify_project_access(user_id: int, project_id: int, db: Session) -> bool:
    """验证用户是否有项目访问权限"""
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    return member is not None