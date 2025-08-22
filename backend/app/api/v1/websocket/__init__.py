from fastapi import APIRouter
from app.api.v1.websocket.manager import websocket_manager

router = APIRouter()

# 导入WebSocket端点
from app.api.v1.websocket.manager import websocket_endpoint

# 将WebSocket端点添加到路由
router.add_websocket_route("/board/{board_id}", websocket_endpoint)