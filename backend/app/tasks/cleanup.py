from celery import current_task
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.redis import redis_client
from app.models.models import ActivityLog
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery_app.task
def cleanup_old_activity_logs() -> Dict[str, Any]:
    """清理旧的活动日志"""
    try:
        db = SessionLocal()
        
        # 删除30天前的活动日志
        cutoff_date = datetime.now() - timedelta(days=30)
        
        # 查询要删除的日志数量
        logs_to_delete = db.query(ActivityLog).filter(
            ActivityLog.created_at < cutoff_date
        ).count()
        
        # 删除旧日志
        deleted_count = db.query(ActivityLog).filter(
            ActivityLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"清理了 {deleted_count} 条旧活动日志")
        
        return {
            "status": "success",
            "message": f"成功清理了 {deleted_count} 条旧活动日志",
            "logs_to_delete": logs_to_delete,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    except Exception as e:
        logger.error(f"清理活动日志失败: {str(e)}")
        return {
            "status": "error",
            "message": f"清理活动日志失败: {str(e)}"
        }
    finally:
        db.close()


@celery_app.task
def cleanup_expired_cache() -> Dict[str, Any]:
    """清理过期的缓存"""
    try:
        # 获取所有键
        all_keys = redis_client.keys("*")
        
        expired_keys = []
        cleaned_keys = []
        
        for key in all_keys:
            try:
                # 检查键的过期时间
                ttl = redis_client.ttl(key)
                
                # 如果键没有过期时间或已过期，删除它
                if ttl == -1:  # 没有过期时间
                    # 对于用户相关的缓存，设置过期时间
                    if key.startswith(("user:", "boards:", "lists:", "cards:", "notifications:")):
                        redis_client.expire(key, 24 * 60 * 60)  # 24小时
                        cleaned_keys.append(key)
                elif ttl == -2:  # 已过期
                    expired_keys.append(key)
                
            except Exception as e:
                logger.warning(f"检查键 {key} 的过期时间失败: {str(e)}")
        
        # 删除已过期的键
        if expired_keys:
            redis_client.delete(*expired_keys)
        
        logger.info(f"清理了 {len(expired_keys)} 个过期缓存键，设置了 {len(cleaned_keys)} 个键的过期时间")
        
        return {
            "status": "success",
            "message": f"成功清理了 {len(expired_keys)} 个过期缓存键",
            "expired_keys": len(expired_keys),
            "cleaned_keys": len(cleaned_keys),
            "total_keys": len(all_keys)
        }
    
    except Exception as e:
        logger.error(f"清理缓存失败: {str(e)}")
        return {
            "status": "error",
            "message": f"清理缓存失败: {str(e)}"
        }


@celery_app.task
def cleanup_inactive_users() -> Dict[str, Any]:
    """清理不活跃用户（可选任务）"""
    try:
        db = SessionLocal()
        
        # 查找6个月未登录的用户
        cutoff_date = datetime.now() - timedelta(days=180)
        
        from app.models.models import User
        
        inactive_users = db.query(User).filter(
            User.updated_at < cutoff_date,
            User.is_active == True
        ).all()
        
        deactivated_count = 0
        for user in inactive_users:
            # 检查用户是否是任何看板的所有者
            if not user.owned_boards:
                user.is_active = False
                deactivated_count += 1
        
        db.commit()
        
        logger.info(f"停用了 {deactivated_count} 个不活跃用户")
        
        return {
            "status": "success",
            "message": f"成功停用了 {deactivated_count} 个不活跃用户",
            "inactive_users_found": len(inactive_users),
            "deactivated_count": deactivated_count,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    except Exception as e:
        logger.error(f"清理不活跃用户失败: {str(e)}")
        return {
            "status": "error",
            "message": f"清理不活跃用户失败: {str(e)}"
        }
    finally:
        db.close()


@celery_app.task
def generate_daily_report() -> Dict[str, Any]:
    """生成每日报告（可选任务）"""
    try:
        db = SessionLocal()
        
        from app.models.models import User, Board, Card, ActivityLog
        
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 统计数据
        stats = {
            "date": today.isoformat(),
            "new_users": db.query(User).filter(User.created_at >= today_start).count(),
            "new_boards": db.query(Board).filter(Board.created_at >= today_start).count(),
            "new_cards": db.query(Card).filter(Card.created_at >= today_start).count(),
            "active_users": db.query(ActivityLog).filter(
                ActivityLog.created_at >= today_start,
                ActivityLog.created_at <= today_end
            ).distinct(ActivityLog.user_id).count(),
            "total_activities": db.query(ActivityLog).filter(
                ActivityLog.created_at >= today_start,
                ActivityLog.created_at <= today_end
            ).count()
        }
        
        # 将报告存储到Redis
        report_key = f"daily_report:{today.isoformat()}"
        redis_client.setex(report_key, 7 * 24 * 60 * 60, json.dumps(stats, ensure_ascii=False))
        
        logger.info(f"生成每日报告: {stats}")
        
        return {
            "status": "success",
            "message": "每日报告生成成功",
            "stats": stats
        }
    
    except Exception as e:
        logger.error(f"生成每日报告失败: {str(e)}")
        return {
            "status": "error",
            "message": f"生成每日报告失败: {str(e)}"
        }
    finally:
        db.close()