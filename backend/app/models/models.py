from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey, Table, Enum, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar_url = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    owned_projects = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user")
    card_assignments = relationship("CardAssignment", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    owner = relationship("User", back_populates="owned_projects")
    members = relationship("ProjectMember", back_populates="project")
    lists = relationship("List", back_populates="project", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum('owner', 'admin', 'member'), default='member')
    joined_at = Column(DateTime, default=func.now())
    
    # 关系
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")


class List(Base):
    __tablename__ = "lists"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="lists")
    cards = relationship("Card", back_populates="list", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("lists.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    due_date = Column(Date)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    list = relationship("List", back_populates="cards")
    labels = relationship("CardLabel", back_populates="card", cascade="all, delete-orphan")
    assignments = relationship("CardAssignment", back_populates="card", cascade="all, delete-orphan")


class CardLabel(Base):
    __tablename__ = "card_labels"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    label = Column(String(50), nullable=False)
    color = Column(String(7), default='#007bff')
    
    # 关系
    card = relationship("Card", back_populates="labels")


class CardAssignment(Base):
    __tablename__ = "card_assignments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=func.now())
    
    # 关系
    card = relationship("Card", back_populates="assignments")
    user = relationship("User", back_populates="card_assignments")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(Enum('project', 'list', 'card', 'label', 'assignment'), nullable=False)
    entity_id = Column(Integer, nullable=False)
    old_values = Column(Text)  # JSON字符串
    new_values = Column(Text)  # JSON字符串
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    project = relationship("Project", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")