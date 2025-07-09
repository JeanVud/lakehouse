"""
Database connection and session management
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Optional
from core.config import POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Keep instances bound after commit
)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    # Keep instances bound to session after commit
    session.expunge_on_commit = False
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def init_database():
    """Initialize database tables using SQLAlchemy models"""
    try:
        # Import all models to ensure they're registered with SQLAlchemy
        from app.models.base import Base
        from app.models.reminder import Reminder  # Import all models here
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully using SQLAlchemy models")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        return False

def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        with get_db_session() as session:
            result = session.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def setup_database():
    """Complete database setup process"""
    logger.info("🔧 Setting up database...")
    
    # Check PostgreSQL connection
    if not check_database_connection():
        logger.error("❌ Cannot connect to PostgreSQL. Please ensure it's running.")
        return False
    
    # Create tables using SQLAlchemy
    logger.info("📋 Creating database tables using SQLAlchemy models...")
    if init_database():
        logger.info("✅ Database setup completed successfully")
        return True
    
    logger.error("❌ Failed to setup database")
    return False 