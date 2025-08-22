# Taskly 实时协同看板系统 - 后端API文档

## 概述

Taskly Backend 是一个基于 FastAPI + MySQL 的实时协同看板系统后端，支持多用户协作、实时数据同步和完整的任务管理功能。

## 技术栈

- **FastAPI** - 现代异步 Web 框架
- **MySQL** - 主数据库
- **SQLAlchemy** - ORM
- **WebSocket** - 实时通信
- **JWT** - 身份认证
- **Redis** - 缓存（可选）
- **bcrypt** - 密码加密

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- Redis (可选，用于缓存)

### 快速启动

1. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

2. **数据库配置**
确保MySQL服务正在运行，并创建数据库：
```sql
CREATE DATABASE test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **初始化数据库**
```bash
python init_database.py
```

4. **启动服务**
```bash
python start_server.py
```

服务将在以下地址启动：
- API服务: http://localhost:8000
- API文档: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/api/v1/ws/project/{project_id}

## API 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: `/api/v1`
- **文档地址**: `http://localhost:8000/docs`
- **健康检查**: `http://localhost:8000/health`

## 默认账户

系统初始化时会创建以下默认账户：

- **管理员**: admin@example.com / 123456
- **测试用户**: john@example.com / 123456

## 认证

所有 API 请求都需要在 Header 中包含 JWT Token：

```
Authorization: Bearer <your-jwt-token>
```

### 获取 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-email@example.com&password=your-password"
```

## API 端点

### 认证相关

#### 用户注册
- **POST** `/api/v1/auth/register`
- **描述**: 注册新用户
- **请求体**:
  ```json
  {
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "password": "password123"
  }
  ```

#### 用户登录
- **POST** `/api/v1/auth/login`
- **描述**: 用户登录获取 Token
- **请求体**: form data
  - username: 邮箱
  - password: 密码

#### 获取当前用户信息
- **GET** `/api/v1/auth/me`
- **描述**: 获取当前登录用户信息
- **认证**: 需要登录

### 用户管理

#### 获取用户列表
- **GET** `/api/v1/users/`
- **描述**: 获取用户列表（仅超级用户）
- **认证**: 需要超级用户权限
- **查询参数**:
  - skip: 跳过数量
  - limit: 限制数量

#### 获取用户详情
- **GET** `/api/v1/users/{user_id}`
- **描述**: 获取用户详情
- **认证**: 需要登录

#### 更新用户信息
- **PUT** `/api/v1/users/{user_id}`
- **描述**: 更新用户信息
- **认证**: 需要登录

### 项目管理

#### 获取项目列表
- **GET** `/api/v1/projects/`
- **描述**: 获取用户的项目列表
- **认证**: 需要登录

#### 创建项目
- **POST** `/api/v1/projects/`
- **描述**: 创建新项目
- **认证**: 需要登录
- **请求体**:
  ```json
  {
    "name": "我的项目",
    "description": "项目描述"
  }
  ```

#### 获取项目详情
- **GET** `/api/v1/projects/{project_id}`
- **描述**: 获取项目详情
- **认证**: 需要登录且有权限

#### 更新项目
- **PUT** `/api/v1/projects/{project_id}`
- **描述**: 更新项目信息
- **认证**: 需要登录且为项目所有者

#### 删除项目
- **DELETE** `/api/v1/projects/{project_id}`
- **描述**: 删除项目
- **认证**: 需要登录且为项目所有者

#### 添加项目成员
- **POST** `/api/v1/projects/{project_id}/members`
- **描述**: 添加项目成员
- **认证**: 需要登录且为项目所有者
- **请求体**:
  ```json
  {
    "user_id": 1,
    "role": "member"
  }
  ```

#### 移除项目成员
- **DELETE** `/api/v1/projects/{project_id}/members/{user_id}`
- **描述**: 移除项目成员
- **认证**: 需要登录且为项目所有者

### 列表管理

#### 获取列表列表
- **GET** `/api/v1/lists/?project_id={project_id}`
- **描述**: 获取项目的列表
- **认证**: 需要登录且有权限

#### 创建列表
- **POST** `/api/v1/lists/?project_id={project_id}`
- **描述**: 创建新列表
- **认证**: 需要登录且有权限
- **请求体**:
  ```json
  {
    "name": "待办",
    "position": 0
  }
  ```

#### 更新列表
- **PUT** `/api/v1/lists/{list_id}`
- **描述**: 更新列表信息
- **认证**: 需要登录且为看板所有者

#### 删除列表
- **DELETE** `/api/v1/lists/{list_id}`
- **描述**: 删除列表
- **认证**: 需要登录且为看板所有者

#### 移动列表
- **POST** `/api/v1/lists/{list_id}/move`
- **描述**: 移动列表位置
- **认证**: 需要登录且为看板所有者
- **请求体**:
  ```json
  {
    "new_position": 1
  }
  ```

### 卡片管理

#### 获取卡片列表
- **GET** `/api/v1/cards/?list_id={list_id}`
- **描述**: 获取列表的卡片
- **认证**: 需要登录且有权限

#### 创建卡片
- **POST** `/api/v1/cards/`
- **描述**: 创建新卡片
- **认证**: 需要登录且有权限
- **请求体**:
  ```json
  {
    "title": "新任务",
    "description": "任务描述",
    "position": 0,
    "due_date": "2024-12-31T23:59:59",
    "labels": ["重要", "紧急"],
    "list_id": 1,
    "assigned_user_id": 1
  }
  ```

#### 更新卡片
- **PUT** `/api/v1/cards/{card_id}`
- **描述**: 更新卡片信息
- **认证**: 需要登录且有权限

#### 删除卡片
- **DELETE** `/api/v1/cards/{card_id}`
- **描述**: 删除卡片
- **认证**: 需要登录且有权限

#### 移动卡片
- **POST** `/api/v1/cards/move`
- **描述**: 移动卡片到其他列表
- **认证**: 需要登录且有权限
- **请求体**:
  ```json
  {
    "source_list_id": 1,
    "target_list_id": 2,
    "new_position": 0,
    "card_id": 1
  }
  ```

## WebSocket 实时通信

### 连接地址
- **WebSocket**: `ws://localhost:8000/api/v1/ws/project/{project_id}`

### 连接参数
- **token**: JWT 认证令牌 (Query参数)
- **project_id**: 项目ID

### 消息类型

#### 心跳检测
```json
{
  "type": "ping",
  "payload": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 聊天消息
```json
{
  "type": "chat",
  "payload": {
    "message": "Hello World"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 获取在线用户
```json
{
  "type": "get_users",
  "payload": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 服务器推送消息

#### 看板更新
```json
{
  "type": "board_update",
  "payload": {
    "board_id": 1,
    "action": "updated",
    "data": {...}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 列表更新
```json
{
  "type": "list_update",
  "payload": {
    "board_id": 1,
    "list_id": 1,
    "action": "created",
    "data": {...}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 卡片更新
```json
{
  "type": "card_update",
  "payload": {
    "board_id": 1,
    "list_id": 1,
    "card_id": 1,
    "action": "moved",
    "data": {...}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 错误处理

### 错误响应格式
```json
{
  "detail": "错误信息"
}
```

### 常见错误码
- **400**: 请求参数错误
- **401**: 未授权或Token无效
- **403**: 权限不足
- **404**: 资源不存在
- **422**: 数据验证错误
- **500**: 服务器内部错误

## 性能优化

### 缓存策略
- 用户信息缓存：5分钟
- 看板数据缓存：5分钟
- 列表数据缓存：5分钟
- 卡片数据缓存：5分钟

### 数据库优化
- 索引优化
- 连接池管理
- 查询优化

## 监控和日志

### 健康检查
- **端点**: `/health`
- **检查项目**: 数据库连接、Redis连接

### 日志级别
- **DEBUG**: 开发环境详细信息
- **INFO**: 正常操作信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息

## 开发指南

### 本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. **启动服务**
```bash
# 启动数据库和Redis
docker-compose up -d postgres redis

# 启动应用
uvicorn app.main:app --reload

# 启动 Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# 启动 Celery Beat
celery -A app.core.celery_app beat --loglevel=info
```

### 数据库迁移

```bash
# 初始化迁移
alembic init alembic

# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 测试

```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 代码规范

```bash
# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/
mypy app/
```

## 部署

### Docker 部署

```bash
# 构建镜像
docker build -t taskly-backend .

# 运行容器
docker run -p 8000:8000 taskly-backend
```

### Docker Compose 部署

```bash
# 生产环境部署
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 环境变量配置

生产环境需要配置以下环境变量：

```bash
# 应用配置
DEBUG=False
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=postgresql://user:password@host:port/database

# Redis配置
REDIS_URL=redis://host:port

# JWT配置
SECRET_KEY=your-jwt-secret-key
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证数据库连接字符串
   - 确认数据库用户权限

2. **Redis连接失败**
   - 检查Redis服务是否启动
   - 验证Redis连接字符串
   - 确认Redis网络配置

3. **JWT Token 无效**
   - 检查Token是否过期
   - 验证Secret Key配置
   - 确认Token格式正确

4. **WebSocket 连接失败**
   - 检查Token是否有效
   - 验证看板权限
   - 确认网络连接

### 日志查看

```bash
# 查看应用日志
docker-compose logs -f web

# 查看数据库日志
docker-compose logs -f postgres

# 查看Redis日志
docker-compose logs -f redis

# 查看Celery日志
docker-compose logs -f celery-worker
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License