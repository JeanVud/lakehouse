from abc import ABC, abstractmethod
from typing import Dict, List
from utils import send_message

class BaseCommand(ABC):
    """Base class for all command handlers"""
    
    def __init__(self):
        self.command_name = self.__class__.__name__.lower().replace('command', '')
    
    @abstractmethod
    async def handle_command(self, chat_id: int, session_data: Dict):
        """Handle the initial command"""
        pass
    
    @abstractmethod
    async def handle_session_continuation(self, chat_id: int, text: str, session_data: Dict) -> Dict:
        """Handle user input during an active session"""
        pass
    
    async def parse_command_args(self, args: List[str]) -> Dict:
        """Parse command arguments and return session data. Override in subclasses if needed."""
        return {}
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML"):
        """Send message to Telegram chat"""
        await send_message(chat_id, text, parse_mode)
    
    def get_command_name(self) -> str:
        """Get the command name for this handler"""
        return self.command_name 