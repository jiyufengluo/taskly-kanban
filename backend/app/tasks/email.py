import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import current_task
from app.core.celery_app import celery_app
from app.core.config import settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email(
    self,
    to_email: str,
    subject: str,
    body: str,
    html_body: str = None,
    from_email: str = None
) -> Dict[str, Any]:
    """发送邮件任务"""
    try:
        # 邮件服务器配置
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "your-email@gmail.com"  # 在实际项目中应该从配置中获取
        smtp_password = "your-app-password"    # 在实际项目中应该从配置中获取
        
        if from_email is None:
            from_email = smtp_username
        
        # 创建邮件消息
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = from_email
        message["To"] = to_email
        
        # 添加文本内容
        text_part = MIMEText(body, "plain", "utf-8")
        message.attach(text_part)
        
        # 添加HTML内容（如果有）
        if html_body:
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)
        
        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        logger.info(f"邮件发送成功: {to_email} - {subject}")
        
        return {
            "status": "success",
            "message": "邮件发送成功",
            "to_email": to_email,
            "subject": subject
        }
    
    except Exception as e:
        logger.error(f"邮件发送失败: {str(e)}")
        
        # 重试逻辑
        if self.request.retries < self.max_retries:
            logger.info(f"邮件发送失败，正在重试 (尝试 {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            "status": "failed",
            "message": f"邮件发送失败: {str(e)}",
            "to_email": to_email,
            "subject": subject
        }


@celery_app.task
def send_welcome_email(user_email: str, user_name: str) -> Dict[str, Any]:
    """发送欢迎邮件"""
    subject = "欢迎使用 Taskly!"
    body = f"""
    亲爱的 {user_name}，
    
    欢迎加入 Taskly！我们很高兴您能成为我们的一员。
    
    Taskly 是一个强大的任务管理和协作平台，帮助您和您的团队更高效地工作。
    
    主要功能：
    • 看板式任务管理
    • 实时协作
    • 团队沟通
    • 数据分析
    
    如果您有任何问题或需要帮助，请随时联系我们的支持团队。
    
    祝您使用愉快！
    
    Taskly 团队
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>亲爱的 {user_name}，</h2>
        <p>欢迎加入 <strong>Taskly</strong>！我们很高兴您能成为我们的一员。</p>
        
        <p>Taskly 是一个强大的任务管理和协作平台，帮助您和您的团队更高效地工作。</p>
        
        <h3>主要功能：</h3>
        <ul>
            <li>看板式任务管理</li>
            <li>实时协作</li>
            <li>团队沟通</li>
            <li>数据分析</li>
        </ul>
        
        <p>如果您有任何问题或需要帮助，请随时联系我们的支持团队。</p>
        
        <p>祝您使用愉快！</p>
        
        <p><strong>Taskly 团队</strong></p>
    </body>
    </html>
    """
    
    return send_email.delay(user_email, subject, body, html_body)


@celery_app.task
def send_password_reset_email(user_email: str, user_name: str, reset_token: str) -> Dict[str, Any]:
    """发送密码重置邮件"""
    subject = "Taskly 密码重置"
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    
    body = f"""
    亲爱的 {user_name}，
    
    我们收到了您重置密码的请求。
    
    请点击以下链接重置您的密码：
    {reset_link}
    
    如果您没有请求重置密码，请忽略此邮件。
    
    此链接将在 24 小时后失效。
    
    Taskly 团队
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>亲爱的 {user_name}，</h2>
        <p>我们收到了您重置密码的请求。</p>
        
        <p>请点击以下链接重置您的密码：</p>
        <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">重置密码</a></p>
        
        <p>如果您没有请求重置密码，请忽略此邮件。</p>
        
        <p><strong>此链接将在 24 小时后失效。</strong></p>
        
        <p>Taskly 团队</p>
    </body>
    </html>
    """
    
    return send_email.delay(user_email, subject, body, html_body)


@celery_app.task
def send_board_invitation_email(
    user_email: str, 
    user_name: str, 
    inviter_name: str, 
    board_name: str,
    board_link: str
) -> Dict[str, Any]:
    """发送看板邀请邮件"""
    subject = f"{inviter_name} 邀请您加入看板: {board_name}"
    
    body = f"""
    亲爱的 {user_name}，
    
    {inviter_name} 邀请您加入看板 "{board_name}"。
    
    请点击以下链接查看看板：
    {board_link}
    
    如果您不想加入此看板，请忽略此邮件。
    
    Taskly 团队
    """
    
    html_body = f"""
    <html>
    <body>
        <h2>亲爱的 {user_name}，</h2>
        <p><strong>{inviter_name}</strong> 邀请您加入看板 "<strong>{board_name}</strong>"。</p>
        
        <p>请点击以下链接查看看板：</p>
        <p><a href="{board_link}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">查看看板</a></p>
        
        <p>如果您不想加入此看板，请忽略此邮件。</p>
        
        <p>Taskly 团队</p>
    </body>
    </html>
    """
    
    return send_email.delay(user_email, subject, body, html_body)