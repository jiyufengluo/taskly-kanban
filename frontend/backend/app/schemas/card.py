from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .user import User
from .board import List
from app.models.card import Priority

# Base Card Schema
class CardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    position: int = Field(default=0, ge=0)
    priority: Priority = Field(default=Priority.MEDIUM)
    due_date: Optional[datetime] = None

# Card Creation Schema
class CardCreate(CardBase):
    list_id: int
    assignee_id: Optional[int] = None

# Card Update Schema
class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    position: Optional[int] = Field(None, ge=0)
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None

# Card Response Schema
class Card(CardBase):
    id: int
    list_id: int
    creator_id: int
    assignee_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    creator: Optional[User] = None
    assignee: Optional[User] = None
    list: Optional[List] = None
    
    class Config:
        from_attributes = True

# Card Move Schema
class CardMove(BaseModel):
    list_id: int
    position: int = Field(..., ge=0)

# Card Position Update Schema
class CardPositionUpdate(BaseModel):
    position: int = Field(..., ge=0)

# Card Assignment Schema
class CardAssignment(BaseModel):
    assignee_id: Optional[int] = None