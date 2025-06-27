import re
from datetime import datetime, date
from typing import Dict, Optional, List
from .base_command import BaseCommand
from utils import logger

class LogFinanceCommand(BaseCommand):
    """Handler for /log-finance command"""
    
    def __init__(self):
        super().__init__()
        self.default_account_type = "debit card"
    
    async def parse_command_args(self, args: List[str]) -> Dict:
        """Parse /log-finance command arguments"""
        date_param = None
        account_type_param = None
        
        for part in args:
            if part.startswith("date="):
                date_param = part.split("=", 1)[1]
            elif part.startswith("account="):
                account_type_param = part.split("=", 1)[1]
        
        return {
            "date": date_param,
            "account_type": account_type_param
        }
    
    async def handle_command(self, chat_id: int, session_data: Dict):
        """Handle the initial /log-finance command"""
        date_param = session_data.get("date")
        account_type_param = session_data.get("account_type")
        
        # Build the prompt message
        prompt_parts = ["OK, now enter your input in the format: <b>amount, category</b>"]
        
        if not date_param:
            prompt_parts.append("<b>date</b>")
        
        if not account_type_param:
            prompt_parts.append("<b>account_type</b>")
        
        prompt = ", ".join(prompt_parts)
        
        await self.send_message(chat_id, prompt)
    
    async def handle_session_continuation(self, chat_id: int, text: str, session_data: Dict) -> Dict:
        """Handle user input during an active session"""
        
        # Check if user wants to edit
        if text.lower() in ["edit", "change", "no", "n"]:
            await self.send_message(chat_id, "Session ended. Use /log-finance to start a new session.")
            return {"session_ended": True}
        
        # Parse the input
        parsed_data = self.parse_input(text, session_data)
        
        if parsed_data:
            # Format the response
            response = self.format_response(parsed_data)
            await self.send_message(chat_id, response)
            
            # Ask if user wants to edit
            await self.send_message(chat_id, "Is this correct? Reply with 'yes' to confirm or 'edit' to change.")
            
            # Log to console
            self.log_transaction(parsed_data)
            
            return {"session_ended": False}
        else:
            await self.send_message(chat_id, "❌ Invalid format. Please use: amount, category, date (if needed), account_type (if needed)")
            return {"session_ended": False}
    
    def parse_input(self, text: str, session_data: Dict) -> Optional[Dict]:
        """Parse user input and return structured data"""
        try:
            # Split by comma and clean up whitespace
            parts = [part.strip() for part in text.split(',')]
            
            if len(parts) < 2:
                return None
            
            # Extract amount and category (required)
            amount_str = parts[0]
            category = parts[1]
            
            # Parse amount
            amount = self.parse_amount(amount_str)
            if amount is None:
                return None
            
            # Get date (from session or input)
            transaction_date = session_data.get("date")
            if not transaction_date and len(parts) > 2:
                transaction_date = parts[2]
            
            # Default to today if no date provided
            if not transaction_date:
                transaction_date = "today"
            
            # Get account type (from session or input)
            account_type = session_data.get("account_type")
            if not account_type:
                if len(parts) > 3:
                    account_type = parts[3]
                else:
                    account_type = self.default_account_type
            
            return {
                "amount": amount,
                "category": category,
                "date": transaction_date,
                "account_type": account_type
            }
            
        except Exception as e:
            logger.error(f"Error parsing input: {e}")
            return None
    
    def parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[^\d.,]', '', amount_str)
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # European format: 1.234,56
                if cleaned.find(',') > cleaned.find('.'):
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # US format: 1,234.56
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Assume comma is decimal separator if no period
                cleaned = cleaned.replace(',', '.')
            
            return float(cleaned)
        except:
            return None
    
    def format_response(self, data: Dict) -> str:
        """Format the parsed data for display"""
        return f"<b>Transaction recorded:</b>\n" \
               f"💰 Amount: ${data['amount']:.2f}\n" \
               f"📂 Category: {data['category']}\n" \
               f"📅 Date: {data['date']}\n" \
               f"💳 Account: {data['account_type']}"
    
    def log_transaction(self, data: Dict):
        """Log the confirmed transaction to console"""
        logger.info(f"✅ Transaction logged: {data['amount']:.2f}$, {data['category']}, {data['date']}, {data['account_type']}") 