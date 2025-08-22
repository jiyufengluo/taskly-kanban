import json
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from fastapi.routing import APIRouter
from app.core.security import jwt_manager
from app.core.database import get_db
from app.models.models import User
from app.core.deps import get_optional_user
from app.models.schemas import WebSocketMessage, ProjectUpdateMessage, ListUpdateMessage, CardUpdateMessage
from datetime import datetime
import asyncio

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.user_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, project_id: int):
        """连接WebSocket"""
        await websocket.accept()
        
        # 将用户添加到项目连接组
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        
        # 记录用户连接
        self.user_connections[user_id] = websocket
        
        # 发送连接成功消息
        await self.send_personal_message({
            "type": "connection_established",
            "payload": {
                "message": "WebSocket连接成功",
                "project_id": project_id,
                "user_id": user_id
            },
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # 广播用户加入消息
        await self.broadcast_to_project(project_id, {
            "type": "user_joined",
            "payload": {
                "user_id": user_id,
                "project_id": project_id
            },
            "timestamp": datetime.now().isoformat()
        }, exclude_user=user_id)
    
    def disconnect(self, websocket: WebSocket, user_id: int, project_id: int):
        """断开WebSocket连接"""
        # 从项目连接组中移除
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        
        # 从用户连接中移除
        if user_id in self.user_connections:
            del self.user_connections[user_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            pass
    
    async def broadcast_to_project(self, project_id: int, message: dict, exclude_user: int = None):
        """向项目所有连接广播消息"""
        if project_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[project_id].remove(conn)
    
    async def broadcast_to_all_projects(self, message: dict):
        """向所有项目广播消息"""
        for project_id, connections in self.active_connections.items():
            disconnected = []
            for connection in connections:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                connections.remove(conn)
    
    def get_project_connections(self, project_id: int) -> int:
        """获取项目连接数"""
        return len(self.active_connections.get(project_id, []))
    
    def get_total_connections(self) -> int:
        """获取总连接数"""
        return sum(len(connections) for connections in self.active_connections.values())


# 创建全局连接管理器
manager = ConnectionManager()


@router.websocket("/project/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str = Query(...),
    db=Depends(get_db)
):
    """WebSocket端点"""
    # 验证token
    try:
        payload = jwt_manager.verify_token(token)
        user_id = int(payload.get("sub"))
        if user_id is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # 验证用户存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # 连接WebSocket
    await manager.connect(websocket, user_id, project_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # 处理不同类型的消息
                await handle_websocket_message(message, user_id, project_id, db)
                
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "payload": {
                        "message": "Invalid JSON format"
                    },
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            except Exception as e:
                await manager.send_personal_message({
                    "type": "error",
                    "payload": {
                        "message": f"Error processing message: {str(e)}"
                    },
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, project_id)
        # 广播用户离开消息
        await manager.broadcast_to_project(project_id, {
            "type": "user_left",
            "payload": {
                "user_id": user_id,
                "project_id": project_id
            },
            "timestamp": datetime.now().isoformat()
        })


async def handle_websocket_message(message: dict, user_id: int, project_id: int, db):
    """处理WebSocket消息"""
    message_type = message.get("type")
    payload = message.get("payload", {})
    
    # 广播消息给项目其他成员
    broadcast_message = {
        "type": message_type,
        "payload": payload,
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id
    }
    
    if message_type == "project_updated":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "list_added":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "list_updated":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "list_deleted":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "card_added":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "card_updated":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "card_deleted":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "card_moved":
        await manager.broadcast_to_project(project_id, broadcast_message, exclude_user=user_id)
    elif message_type == "ping":
        # 心跳消息
        await manager.send_personal_message({
            "type": "pong",
            "payload": {
                "timestamp": datetime.now().isoformat()
            },
            "user_id": user_id
        }, manager.user_connections.get(user_id))
    else:
        # 未知消息类型
        websocket = manager.user_connections.get(user_id)
        if websocket:
            await manager.send_personal_message({
                "type": "error",
                "payload": {
                    "message": f"Unknown message type: {message_type}"
                },
                "timestamp": datetime.now().isoformat()
            }, websocket)


# 获取连接统计信息
@router.get("/stats")
async def get_connection_stats():
    """获取WebSocket连接统计"""
    return {
        "total_connections": manager.get_total_connections(),
        "project_connections": {
            str(project_id): len(connections) 
            for project_id, connections in manager.active_connections.items()
        }
    }