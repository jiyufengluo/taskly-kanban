from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# 用户相关schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


# 项目相关schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: UserResponse
    members: List['ProjectMemberResponse'] = []
    
    class Config:
        from_attributes = True


class ProjectMemberBase(BaseModel):
    role: str = 'member'


class ProjectMemberCreate(ProjectMemberBase):
    project_id: int
    user_id: int


class ProjectMemberResponse(ProjectMemberBase):
    id: int
    project_id: int
    user_id: int
    joined_at: datetime
    user: UserResponse
    
    class Config:
        from_attributes = True


# 列表相关schemas
class ListBase(BaseModel):
    name: str
    position: int = 0


class ListCreate(ListBase):
    project_id: int


class ListUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None


class ListResponse(ListBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    cards: List['CardResponse'] = []
    
    class Config:
        from_attributes = True


# 卡片相关schemas
class CardBase(BaseModel):
    title: str
    description: Optional[str] = None
    position: int = 0
    due_date: Optional[datetime] = None


class CardCreate(CardBase):
    list_id: int


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None
    due_date: Optional[datetime] = None


class CardResponse(CardBase):
    id: int
    list_id: int
    created_at: datetime
    updated_at: datetime
    labels: List['CardLabelResponse'] = []
    assignments: List['CardAssignmentResponse'] = []
    
    class Config:
        from_attributes = True


class CardLabelBase(BaseModel):
    label: str
    color: str = '#007bff'


class CardLabelCreate(CardLabelBase):
    card_id: int


class CardLabelResponse(CardLabelBase):
    id: int
    card_id: int
    
    class Config:
        from_attributes = True


class CardAssignmentBase(BaseModel):
    pass


class CardAssignmentCreate(CardAssignmentBase):
    card_id: int
    user_id: int


class CardAssignmentResponse(CardAssignmentBase):
    id: int
    card_id: int
    user_id: int
    assigned_at: datetime
    user: UserResponse
    
    class Config:
        from_attributes = True


# 卡片移动schemas
class CardMoveRequest(BaseModel):
    source_list_id: int
    target_list_id: int
    new_position: int


# 活动日志schemas
class ActivityLogResponse(BaseModel):
    id: int
    action_type: str
    entity_type: str
    entity_id: int
    changes: Optional[str] = None
    user_id: int
    created_at: datetime
    user: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


# WebSocket消息schemas
class WebSocketMessage(BaseModel):
    type: str
    payload: dict
    timestamp: datetime
    user_id: int


class ProjectUpdateMessage(BaseModel):
    project_id: int
    action: str  # created, updated, deleted
    data: dict


class ListUpdateMessage(BaseModel):
    project_id: int
    list_id: int
    action: str  # created, updated, deleted, moved
    data: dict


class CardUpdateMessage(BaseModel):
    project_id: int
    list_id: int
    card_id: int
    action: str  # created, updated, deleted, moved
    data: dict