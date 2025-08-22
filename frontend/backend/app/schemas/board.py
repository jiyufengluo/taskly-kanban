from pydantic import BaseModel, Field
from typing import Optional, List as ListType
from datetime import datetime
from .project import Project

# Base Board Schema
class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

# Board Creation Schema
class BoardCreate(BoardBase):
    project_id: int

# Board Update Schema
class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

# Board Response Schema
class Board(BoardBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    project: Optional[Project] = None
    
    class Config:
        from_attributes = True

# Base List Schema
class ListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    position: int = Field(default=0, ge=0)

# List Creation Schema
class ListCreate(ListBase):
    board_id: int

# List Update Schema
class ListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    position: Optional[int] = Field(None, ge=0)

# List Response Schema
class List(ListBase):
    id: int
    board_id: int
    created_at: datetime
    updated_at: datetime
    board: Optional[Board] = None
    
    class Config:
        from_attributes = True

# List Position Update Schema
class ListPositionUpdate(BaseModel):
    position: int = Field(..., ge=0)

# Board with Lists Schema
class BoardWithLists(Board):
    lists: ListType[List] = []