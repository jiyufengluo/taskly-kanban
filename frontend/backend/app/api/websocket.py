from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.websocket import manager, WebSocketService, verify_project_access
from app.core.auth import verify_token
from app.models import User
import json
import asyncio
from typing import Optional

router = APIRouter()

async def get_current_user_ws(token: str, db: Session) -> Optional[User]:
    """WebSocket认证：从token获取当前用户"""
    try:
        payload = verify_token(token)
        if payload is None:
            return None
        
        username = payload.get("sub")
        if username is None:
            return None
        
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            return None
        
        return user
    except:
        return None

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: int,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket连接端点"""
    # 验证用户身份
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    # 验证项目访问权限
    if not verify_project_access(user.id, project_id, db):
        await websocket.close(code=4003, reason="Forbidden")
        return
    
    # 建立连接
    await manager.connect(websocket, user.id, project_id)
    
    # 发送在线用户列表
    await WebSocketService.send_online_users(project_id, user.id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理不同类型的消息
            await handle_websocket_message(message, user.id, project_id, db)
            
    except WebSocketDisconnect:
        # 断开连接
        manager.disconnect(websocket, user.id, project_id)
        
        # 通知其他用户该用户已离开
        await manager.broadcast_to_project(
            project_id,
            {
                "type": "user_left",
                "user_id": user.id,
                "timestamp": asyncio.get_event_loop().time()
            },
            exclude_user=user.id
        )
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, user.id, project_id)

async def handle_websocket_message(message: dict, user_id: int, project_id: int, db: Session):
    """处理WebSocket消息"""
    message_type = message.get("type")
    data = message.get("data", {})
    
    if message_type == "ping":
        # 心跳检测
        await manager.send_personal_message(
            {"type": "pong", "timestamp": asyncio.get_event_loop().time()},
            user_id,
            project_id
        )
    
    elif message_type == "user_typing":
        # 用户正在输入
        card_id = data.get("card_id")
        is_typing = data.get("is_typing", False)
        if card_id:
            await WebSocketService.handle_user_typing(project_id, card_id, user_id, is_typing)
    
    elif message_type == "request_online_users":
        # 请求在线用户列表
        await WebSocketService.send_online_users(project_id, user_id)
    
    elif message_type == "cursor_position":
        # 光标位置更新（用于协作编辑）
        card_id = data.get("card_id")
        position = data.get("position")
        if card_id and position is not None:
            await manager.broadcast_to_project(
                project_id,
                {
                    "type": "cursor_position",
                    "data": {
                        "card_id": card_id,
                        "position": position
                    },
                    "user_id": user_id,
                    "timestamp": asyncio.get_event_loop().time()
                },
                exclude_user=user_id
            )
    
    elif message_type == "selection_change":
        # 选择区域变化（用于协作编辑）
        card_id = data.get("card_id")
        selection = data.get("selection")
        if card_id and selection:
            await manager.broadcast_to_project(
                project_id,
                {
                    "type": "selection_change",
                    "data": {
                        "card_id": card_id,
                        "selection": selection
                    },
                    "user_id": user_id,
                    "timestamp": asyncio.get_event_loop().time()
                },
                exclude_user=user_id
            )
    
    # 可以添加更多消息类型处理

# 用于在API操作后触发WebSocket通知的辅助函数
class WebSocketNotifier:
    """WebSocket通知器"""
    
    @staticmethod
    async def notify_card_created(project_id: int, card_data: dict, user_id: int):
        """通知卡片创建"""
        await WebSocketService.handle_card_create(project_id, card_data, user_id)
    
    @staticmethod
    async def notify_card_updated(project_id: int, card_data: dict, user_id: int):
        """通知卡片更新"""
        await WebSocketService.handle_card_update(project_id, card_data, user_id)
    
    @staticmethod
    async def notify_card_moved(project_id: int, card_data: dict, user_id: int):
        """通知卡片移动"""
        await WebSocketService.handle_card_move(project_id, card_data, user_id)
    
    @staticmethod
    async def notify_card_deleted(project_id: int, card_id: int, user_id: int):
        """通知卡片删除"""
        await WebSocketService.handle_card_delete(project_id, card_id, user_id)
    
    @staticmethod
    async def notify_list_created(project_id: int, list_data: dict, user_id: int):
        """通知列表创建"""
        await WebSocketService.handle_list_create(project_id, list_data, user_id)
    
    @staticmethod
    async def notify_list_updated(project_id: int, list_data: dict, user_id: int):
        """通知列表更新"""
        await WebSocketService.handle_list_update(project_id, list_data, user_id)
    
    @staticmethod
    async def notify_board_updated(project_id: int, board_data: dict, user_id: int):
        """通知看板更新"""
        await WebSocketService.handle_board_update(project_id, board_data, user_id)

# 导出通知器实例
notifier = WebSocketNotifier()