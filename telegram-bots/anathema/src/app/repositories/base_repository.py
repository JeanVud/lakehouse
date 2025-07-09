"""
Base repository class for database operations
"""
from typing import List, Optional, TypeVar, Generic, Type
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from core.database import get_db_session
from app.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[T]):
        self.model = model
    
    def create(self, **kwargs) -> T:
        """Create a new record"""
        with get_db_session() as session:
            instance = self.model(**kwargs)
            session.add(instance)
            session.commit()
            session.refresh(instance)
            return instance
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get record by ID"""
        with get_db_session() as session:
            return session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all records with optional pagination"""
        with get_db_session() as session:
            query = session.query(self.model)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update a record"""
        with get_db_session() as session:
            instance = session.query(self.model).filter(self.model.id == id).first()
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                session.commit()
                session.refresh(instance)
            return instance
    
    def delete(self, id: int) -> bool:
        """Delete a record"""
        with get_db_session() as session:
            instance = session.query(self.model).filter(self.model.id == id).first()
            if instance:
                session.delete(instance)
                session.commit()
                return True
            return False
    
    def count(self) -> int:
        """Count total records"""
        with get_db_session() as session:
            return session.query(self.model).count()
    
    def exists(self, id: int) -> bool:
        """Check if record exists"""
        with get_db_session() as session:
            return session.query(self.model).filter(self.model.id == id).first() is not None 