from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .user import User

# Base Project Schema
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

# Project Creation Schema
class ProjectCreate(ProjectBase):
    pass

# Project Update Schema
class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

# Project Response Schema
class Project(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    owner: Optional[User] = None
    
    class Config:
        from_attributes = True

# Project Member Schemas
class ProjectMemberBase(BaseModel):
    role: str = Field(default="member", pattern="^(owner|admin|member)$")

class ProjectMemberCreate(ProjectMemberBase):
    user_id: int

class ProjectMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, pattern="^(owner|admin|member)$")

class ProjectMember(ProjectMemberBase):
    id: int
    project_id: int
    user_id: int
    joined_at: datetime
    user: Optional[User] = None
    
    class Config:
        from_attributes = True

# Project with Members Schema
class ProjectWithMembers(Project):
    members: List[ProjectMember] = []

# Project Invitation Schema
class ProjectInvitation(BaseModel):
    email: str
    role: str = Field(default="member", pattern="^(admin|member)$")