from typing import Dict
from .base_command import BaseCommand

class HelpCommand(BaseCommand):
    """Handler for /help command"""
    
    def __init__(self):
        super().__init__()
    
    async def handle_command(self, chat_id: int, session_data: Dict):
        """Handle the /help command"""
        help_text = """
<b>💰 Finance Bot Help</b>

<b>Commands:</b>
• <code>/log-finance</code> - Start logging a purchase
• <code>/help</code> - Show this help message

<b>Usage Examples:</b>
• <code>/log-finance</code> - Start with defaults
• <code>/log-finance date=2024-01-15</code> - Set specific date
• <code>/log-finance account=credit_card</code> - Set account type
• <code>/log-finance date=2024-01-15 account=cash</code> - Set both

<b>Input Format:</b>
<code>amount, category, date (optional), account_type (optional)</code>

<b>Examples:</b>
• <code>30$, food</code>
• <code>50.25, groceries, yesterday, credit card</code>
• <code>100, entertainment, 2024-01-10, cash</code>

<b>Session Management:</b>
• Sessions expire after 5 minutes of inactivity
• Reply with 'edit' to modify your entry
• Reply with 'yes' to confirm and end session
        """
        
        await self.send_message(chat_id, help_text)
        return {"session_ended": True}
    
    async def handle_session_continuation(self, chat_id: int, text: str, session_data: Dict) -> Dict:
        """Help command doesn't need session continuation"""
        return {"session_ended": True} 