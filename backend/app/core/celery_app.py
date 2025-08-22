from celery import Celery
from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "taskly_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.email", "app.tasks.notifications"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟
    task_soft_time_limit=25 * 60,  # 25分钟
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 任务路由
celery_app.conf.task_routes = {
    "app.tasks.email.send_email": {"queue": "email"},
    "app.tasks.notifications.send_notification": {"queue": "notifications"},
    "app.tasks.notifications.process_activity_log": {"queue": "notifications"},
}

# 定时任务配置
celery_app.conf.beat_schedule = {
    "cleanup-old-activity-logs": {
        "task": "app.tasks.cleanup.cleanup_old_activity_logs",
        "schedule": 24 * 60 * 60.0,  # 每24小时执行一次
    },
    "cleanup-expired-cache": {
        "task": "app.tasks.cleanup.cleanup_expired_cache",
        "schedule": 12 * 60 * 60.0,  # 每12小时执行一次
    },
}