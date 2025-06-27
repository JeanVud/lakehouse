from datetime import datetime, timedelta
from typing import Dict, Optional
from utils import logger

class Session:
    def __init__(self, command: str, data: dict, expires_at: datetime):
        self.command = command
        self.data = data
        self.expires_at = expires_at

class SessionManager:
    def __init__(self, command_registry=None):
        self.sessions: Dict[int, Session] = {}
        self.command_registry = command_registry
    
    def create_session(self, chat_id: int, command_name: str, session_data: Dict) -> bool:
        """Create a session if the command needs one"""
        if self.command_registry and self.command_registry.needs_session(command_name):
            timeout_minutes = self.command_registry.get_timeout_minutes(command_name)
            expires_at = datetime.now() + timedelta(minutes=timeout_minutes)
            self.sessions[chat_id] = Session(command_name, session_data, expires_at)
            logger.info(f"📝 Created session for user {chat_id} with command {command_name}")
            return True
        return False
    
    def get_session(self, chat_id: int) -> Optional[Session]:
        """Get active session for a user"""
        return self.sessions.get(chat_id)
    
    def is_session_expired(self, session: Session) -> bool:
        """Check if a session has expired"""
        return datetime.now() > session.expires_at
    
    def remove_session(self, chat_id: int) -> bool:
        """Remove a session"""
        if chat_id in self.sessions:
            del self.sessions[chat_id]
            logger.info(f"🗑️ Removed session for user {chat_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove all expired sessions"""
        current_time = datetime.now()
        expired_users = []
        
        for chat_id, session in self.sessions.items():
            if current_time > session.expires_at:
                expired_users.append(chat_id)
        
        for chat_id in expired_users:
            del self.sessions[chat_id]
            logger.info(f"🧹 Cleaned up expired session for user {chat_id}")
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions) 