from sqlalchemy.orm import Session
from app.models.models import ActivityLog
import json


def log_activity(
    db: Session,
    user_id: int,
    action_type: str,
    entity_type: str,
    entity_id: int,
    changes: dict = None
):
    """记录活动日志"""
    activity_log = ActivityLog(
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=json.dumps(changes) if changes else None,
        user_id=user_id
    )
    
    db.add(activity_log)
    db.commit()
    
    return activity_log


def get_user_activities(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50
):
    """获取用户活动日志"""
    activities = db.query(ActivityLog).filter(
        ActivityLog.user_id == user_id
    ).order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return activities


def get_board_activities(
    db: Session,
    board_id: int,
    skip: int = 0,
    limit: int = 50
):
    """获取看板活动日志"""
    # 获取看板相关的所有活动
    from app.models.models import List, Card
    
    # 获取看板列表ID
    list_ids = db.query(List.id).filter(List.board_id == board_id).all()
    list_ids = [lid[0] for lid in list_ids]
    
    # 获取看板卡片ID
    card_ids = db.query(Card.id).filter(Card.list_id.in_(list_ids)).all()
    card_ids = [cid[0] for cid in card_ids]
    
    # 查询相关活动
    activities = db.query(ActivityLog).filter(
        (ActivityLog.entity_type == "board") & (ActivityLog.entity_id == board_id) |
        (ActivityLog.entity_type == "list") & (ActivityLog.entity_id.in_(list_ids)) |
        (ActivityLog.entity_type == "card") & (ActivityLog.entity_id.in_(card_ids))
    ).order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return activities