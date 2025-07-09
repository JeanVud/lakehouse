"""
Reminder repository for database operations
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import desc
from .base_repository import BaseRepository
from app.models.reminder import Reminder
from core.database import get_db_session

class ReminderRepository(BaseRepository[Reminder]):
    """Repository for reminder operations"""
    
    def __init__(self):
        super().__init__(Reminder)
    
    def get_by_chat_id(self, chat_id: int, completed: Optional[bool] = None, limit: Optional[int] = None) -> List[Reminder]:
        """Get reminders by chat ID with optional completion filter"""
        with get_db_session() as session:
            query = session.query(Reminder).filter(Reminder.chat_id == chat_id)
            
            if completed is not None:
                query = query.filter(Reminder.completed == completed)
            
            query = query.order_by(desc(Reminder.created_at))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def get_active_by_chat_id(self, chat_id: int, limit: Optional[int] = None) -> List[Reminder]:
        """Get active (incomplete) reminders by chat ID"""
        return self.get_by_chat_id(chat_id, completed=False, limit=limit)
    
    def get_completed_by_chat_id(self, chat_id: int, limit: Optional[int] = None) -> List[Reminder]:
        """Get completed reminders by chat ID"""
        return self.get_by_chat_id(chat_id, completed=True, limit=limit)
    
    def count_by_chat_id(self, chat_id: int, completed: Optional[bool] = None) -> int:
        """Count reminders by chat ID with optional completion filter"""
        with get_db_session() as session:
            query = session.query(Reminder).filter(Reminder.chat_id == chat_id)
            
            if completed is not None:
                query = query.filter(Reminder.completed == completed)
            
            return query.count()
    
    def mark_completed(self, reminder_id: int) -> Optional[Reminder]:
        """Mark a reminder as completed"""
        with get_db_session() as session:
            reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
            if reminder:
                reminder.mark_completed()
                session.commit()
                session.refresh(reminder)
            return reminder
    
    def mark_incomplete(self, reminder_id: int) -> Optional[Reminder]:
        """Mark a reminder as incomplete"""
        with get_db_session() as session:
            reminder = session.query(Reminder).filter(Reminder.id == reminder_id).first()
            if reminder:
                reminder.mark_incomplete()
                session.commit()
                session.refresh(reminder)
            return reminder
    
    def search_by_text(self, chat_id: int, search_text: str, limit: Optional[int] = None) -> List[Reminder]:
        """Search reminders by text content"""
        with get_db_session() as session:
            query = session.query(Reminder).filter(
                Reminder.chat_id == chat_id,
                Reminder.text.ilike(f"%{search_text}%")
            ).order_by(desc(Reminder.created_at))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def get_recent_reminders(self, chat_id: int, days: int = 7, limit: Optional[int] = None) -> List[Reminder]:
        """Get recent reminders from the last N days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with get_db_session() as session:
            query = session.query(Reminder).filter(
                Reminder.chat_id == chat_id,
                Reminder.created_at >= cutoff_date
            ).order_by(desc(Reminder.created_at))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
    
    def delete_by_chat_id(self, chat_id: int) -> int:
        """Delete all reminders for a chat ID"""
        with get_db_session() as session:
            count = session.query(Reminder).filter(Reminder.chat_id == chat_id).count()
            session.query(Reminder).filter(Reminder.chat_id == chat_id).delete()
            session.commit()
            return count
    
    def get_statistics(self, chat_id: int) -> dict:
        """Get reminder statistics for a chat"""
        with get_db_session() as session:
            total = session.query(Reminder).filter(Reminder.chat_id == chat_id).count()
            completed = session.query(Reminder).filter(
                Reminder.chat_id == chat_id,
                Reminder.completed == True
            ).count()
            active = total - completed
            
            return {
                "total": total,
                "completed": completed,
                "active": active,
                "completion_rate": (completed / total * 100) if total > 0 else 0
            } 