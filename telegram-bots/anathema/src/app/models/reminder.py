"""
Reminder model for database operations
"""
from sqlalchemy import Column, BigInteger, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .base import BaseModel

class Reminder(BaseModel):
    """Reminder model for storing todo items"""
    __tablename__ = 'reminders'
    
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    text = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Reminder(id={self.id}, chat_id={self.chat_id}, text='{self.text[:50]}...', completed={self.completed})>"
    
    def mark_completed(self):
        """Mark reminder as completed"""
        from datetime import datetime
        self.completed = True
        self.completed_at = datetime.utcnow()
    
    def mark_incomplete(self):
        """Mark reminder as incomplete"""
        self.completed = False
        self.completed_at = None 