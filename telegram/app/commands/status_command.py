from typing import Dict, List
from .base_command import BaseCommand
from utils import logger

class StatusCommand(BaseCommand):
    """Handler for /status command"""
    
    def __init__(self):
        super().__init__()
    
    async def parse_command_args(self, args: List[str]) -> Dict:
        """Parse /status command arguments"""
        return {}
    
    async def handle_command(self, chat_id: int, session_data: Dict):
        """Handle the /status command"""
        status_text = """
<b>🤖 Bot Status</b>

✅ Bot is running
📊 Active sessions: 0
🕒 Uptime: Online

<b>Available commands:</b>
• /log-finance - Log purchases
• /help - Show help
• /status - Show this status
        """
        
        await self.send_message(chat_id, status_text)
    
    async def handle_session_continuation(self, chat_id: int, text: str, session_data: Dict) -> Dict:
        """Status command doesn't need session continuation"""
        return {"session_ended": True} 