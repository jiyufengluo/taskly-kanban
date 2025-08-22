from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class Priority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, nullable=False, default=0)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign Keys
    list_id = Column(Integer, ForeignKey("lists.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    list = relationship("List", back_populates="cards")
    creator = relationship("User", back_populates="created_cards", foreign_keys=[creator_id])
    assignee = relationship("User", back_populates="assigned_cards", foreign_keys=[assignee_id])
    
    def __repr__(self):
        return f"<Card(id={self.id}, title='{self.title}', list_id={self.list_id}, position={self.position})>"