from celery import current_task
from app.core.celery_app import celery_app
from app.core.redis import redis_client
from app.core.database import SessionLocal
from app.models.models import ActivityLog, User
from app.services.activity_service import get_board_activities
from typing import Dict, Any, List
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification(
    self,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """发送通知任务"""
    try:
        # 创建通知数据
        notification = {
            "id": f"notification_{user_id}_{datetime.now().timestamp()}",
            "user_id": user_id,
            "type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "created_at": datetime.now().isoformat(),
            "read": False
        }
        
        # 将通知存储到Redis
        redis_key = f"notifications:{user_id}"
        redis_client.lpush(redis_key, json.dumps(notification, ensure_ascii=False))
        
        # 限制通知数量（保留最近100条）
        redis_client.ltrim(redis_key, 0, 99)
        
        # 设置过期时间（30天）
        redis_client.expire(redis_key, 30 * 24 * 60 * 60)
        
        logger.info(f"通知发送成功: 用户 {user_id} - {title}")
        
        return {
            "status": "success",
            "message": "通知发送成功",
            "user_id": user_id,
            "notification_id": notification["id"]
        }
    
    except Exception as e:
        logger.error(f"通知发送失败: {str(e)}")
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            logger.info(f"通知发送失败，正在重试 (尝试 {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
        
        return {
            "status": "failed",
            "message": f"通知发送失败: {str(e)}",
            "user_id": user_id
        }


@celery_app.task
def send_board_activity_notification(
    user_id: int,
    board_id: int,
    activity_type: str,
    activity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """发送看板活动通知"""
    title_map = {
        "card_created": "新卡片已创建",
        "card_updated": "卡片已更新",
        "card_moved": "卡片已移动",
        "card_deleted": "卡片已删除",
        "list_created": "新列表已创建",
        "list_updated": "列表已更新",
        "list_deleted": "列表已删除",
        "board_updated": "看板已更新",
        "member_added": "新成员已加入",
        "member_removed": "成员已移除"
    }
    
    title = title_map.get(activity_type, "看板活动")
    message = activity_data.get("message", f"看板 {board_id} 有新的活动")
    
    return send_notification.delay(
        user_id=user_id,
        notification_type="board_activity",
        title=title,
        message=message,
        data={
            "board_id": board_id,
            "activity_type": activity_type,
            "activity_data": activity_data
        }
    )


@celery_app.task
def send_assignment_notification(
    user_id: int,
    card_id: int,
    card_title: str,
    board_id: int,
    assigner_name: str
) -> Dict[str, Any]:
    """发送任务分配通知"""
    title = "新任务已分配给您"
    message = f"{assigner_name} 将任务 '{card_title}' 分配给了您"
    
    return send_notification.delay(
        user_id=user_id,
        notification_type="assignment",
        title=title,
        message=message,
        data={
            "card_id": card_id,
            "card_title": card_title,
            "board_id": board_id,
            "assigner_name": assigner_name
        }
    )


@celery_app.task
def send_due_date_notification(
    user_id: int,
    card_id: int,
    card_title: str,
    board_id: int,
    due_date: str,
    days_left: int
) -> Dict[str, Any]:
    """发送截止日期提醒通知"""
    if days_left <= 0:
        title = "任务已过期"
        message = f"任务 '{card_title}' 已过期，请尽快处理"
    elif days_left == 1:
        title = "任务即将到期"
        message = f"任务 '{card_title}' 将在明天到期"
    else:
        title = "任务截止日期提醒"
        message = f"任务 '{card_title}' 将在 {days_left} 天后到期"
    
    return send_notification.delay(
        user_id=user_id,
        notification_type="due_date",
        title=title,
        message=message,
        data={
            "card_id": card_id,
            "card_title": card_title,
            "board_id": board_id,
            "due_date": due_date,
            "days_left": days_left
        }
    )


@celery_app.task
def process_activity_log(activity_log_id: int) -> Dict[str, Any]:
    """处理活动日志并发送相关通知"""
    try:
        db = SessionLocal()
        
        # 获取活动日志
        activity_log = db.query(ActivityLog).filter(ActivityLog.id == activity_log_id).first()
        if not activity_log:
            return {"status": "error", "message": "Activity log not found"}
        
        # 获取用户信息
        user = db.query(User).filter(User.id == activity_log.user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # 根据活动类型处理
        if activity_log.entity_type == "card":
            await process_card_activity(db, activity_log, user)
        elif activity_log.entity_type == "board":
            await process_board_activity(db, activity_log, user)
        
        return {"status": "success", "message": "Activity log processed successfully"}
    
    except Exception as e:
        logger.error(f"处理活动日志失败: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


async def process_card_activity(db, activity_log, user):
    """处理卡片活动"""
    from app.models.models import Card, List, Board
    
    card = db.query(Card).filter(Card.id == activity_log.entity_id).first()
    if not card:
        return
    
    lst = db.query(List).filter(List.id == card.list_id).first()
    if not lst:
        return
    
    board = db.query(Board).filter(Board.id == lst.board_id).first()
    if not board:
        return
    
    # 通知看板成员（除了操作者）
    for member in board.members:
        if member.id != activity_log.user_id:
            send_board_activity_notification.delay(
                user_id=member.id,
                board_id=board.id,
                activity_type=f"card_{activity_log.action_type}",
                activity_data={
                    "message": f"{user.username} {activity_log.action_type}了卡片 '{card.title}'",
                    "card_id": card.id,
                    "card_title": card.title,
                    "user_name": user.username
                }
            )
    
    # 如果卡片被分配给用户，通知该用户
    if card.assigned_user_id and card.assigned_user_id != activity_log.user_id:
        send_assignment_notification.delay(
            user_id=card.assigned_user_id,
            card_id=card.id,
            card_title=card.title,
            board_id=board.id,
            assigner_name=user.username
        )


async def process_board_activity(db, activity_log, user):
    """处理看板活动"""
    from app.models.models import Board
    
    board = db.query(Board).filter(Board.id == activity_log.entity_id).first()
    if not board:
        return
    
    # 通知看板成员（除了操作者）
    for member in board.members:
        if member.id != activity_log.user_id:
            send_board_activity_notification.delay(
                user_id=member.id,
                board_id=board.id,
                activity_type=f"board_{activity_log.action_type}",
                activity_data={
                    "message": f"{user.username} {activity_log.action_type}了看板 '{board.name}'",
                    "board_name": board.name,
                    "user_name": user.username
                }
            )