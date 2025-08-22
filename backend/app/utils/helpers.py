import re
from datetime import datetime, timedelta
from typing import Optional
import json


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> dict:
    """验证密码强度"""
    errors = []
    
    if len(password) < 8:
        errors.append("密码长度至少8位")
    
    if not re.search(r'[A-Z]', password):
        errors.append("密码必须包含大写字母")
    
    if not re.search(r'[a-z]', password):
        errors.append("密码必须包含小写字母")
    
    if not re.search(r'\d', password):
        errors.append("密码必须包含数字")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("密码必须包含特殊字符")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }


def generate_board_invite_code() -> str:
    """生成看板邀请码"""
    import uuid
    return str(uuid.uuid4())[:8].upper()


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_time_ago(dt: datetime) -> str:
    """获取相对时间"""
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "刚刚"
    elif diff < timedelta(hours=1):
        return f"{diff.seconds // 60}分钟前"
    elif diff < timedelta(days=1):
        return f"{diff.seconds // 3600}小时前"
    elif diff < timedelta(days=30):
        return f"{diff.days}天前"
    elif diff < timedelta(days=365):
        return f"{diff.days // 30}个月前"
    else:
        return f"{diff.days // 365}年前"


def sanitize_html(html: str) -> str:
    """清理HTML内容"""
    import re
    # 移除危险标签
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed']
    for tag in dangerous_tags:
        html = re.sub(f'<{tag}.*?>.*?</{tag}>', '', html, flags=re.IGNORECASE | re.DOTALL)
    
    # 移除危险属性
    dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout']
    for attr in dangerous_attrs:
        html = re.sub(f'{attr}=".*?"', '', html, flags=re.IGNORECASE)
    
    return html


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def parse_labels(labels_str: str) -> list:
    """解析标签字符串"""
    if not labels_str:
        return []
    
    try:
        if isinstance(labels_str, str):
            return json.loads(labels_str)
        elif isinstance(labels_str, list):
            return labels_str
        else:
            return []
    except json.JSONDecodeError:
        return []


def serialize_labels(labels: list) -> str:
    """序列化标签列表"""
    return json.dumps(labels, ensure_ascii=False)


def calculate_board_progress(board_id: int, db) -> dict:
    """计算看板进度"""
    from app.models.models import List, Card
    
    # 获取看板的所有列表和卡片
    lists = db.query(List).filter(List.board_id == board_id).all()
    
    total_cards = 0
    completed_cards = 0
    
    for lst in lists:
        cards = db.query(Card).filter(Card.list_id == lst.id).all()
        total_cards += len(cards)
        
        # 假设最后一个列表是"已完成"
        if lst.name in ["已完成", "Done", "完成"]:
            completed_cards += len(cards)
    
    progress = (completed_cards / total_cards * 100) if total_cards > 0 else 0
    
    return {
        "total_cards": total_cards,
        "completed_cards": completed_cards,
        "progress": round(progress, 2)
    }


def get_user_statistics(user_id: int, db) -> dict:
    """获取用户统计信息"""
    from app.models.models import Board, Card, ActivityLog
    
    # 用户拥有的看板数量
    owned_boards = db.query(Board).filter(Board.owner_id == user_id).count()
    
    # 用户参与的看板数量
    participated_boards = db.query(Board).filter(
        Board.members.any(id=user_id)
    ).count()
    
    # 用户被分配的卡片数量
    assigned_cards = db.query(Card).filter(Card.assigned_user_id == user_id).count()
    
    # 用户完成的卡片数量
    completed_cards = db.query(Card).join(List).join(Board).filter(
        Card.assigned_user_id == user_id,
        List.name.in_(["已完成", "Done", "完成"])
    ).count()
    
    # 用户活动数量
    activities = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).count()
    
    return {
        "owned_boards": owned_boards,
        "participated_boards": participated_boards,
        "assigned_cards": assigned_cards,
        "completed_cards": completed_cards,
        "total_activities": activities
    }