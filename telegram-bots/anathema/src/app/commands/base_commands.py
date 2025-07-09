"""
Advanced command handling system for Telegram bot
"""
import re
from typing import Callable, Dict, Any, Optional
from functools import wraps
from app.services.telegram_service import send_message
from core.utils import logger
from core.config import TELEGRAM_BOT_TOKEN

class CommandHandler:
    """Command handler class with decorator support"""
    
    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.middleware: list[Callable] = []
    
    def command(self, name: str, description: str = ""):
        """Decorator to register a command"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(chat_id: int, args: str = "", **kwargs):
                try:
                    # Run middleware
                    for middleware_func in self.middleware:
                        middleware_func(chat_id, name, args, **kwargs)
                    
                    # Execute command
                    return func(chat_id, args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in command {name}: {e}")
                    send_message(TELEGRAM_BOT_TOKEN, chat_id, f"❌ Error executing command: {str(e)}")
            
            self.commands[name] = wrapper
            wrapper.description = description
            return wrapper
        return decorator
    
    def add_middleware(self, func: Callable):
        """Decorator to add middleware"""
        self.middleware.append(func)
        return func
    
    def execute(self, chat_id: int, text: str, **kwargs):
        """Execute command based on text"""
        command, args = self.parse_command(text)
        
        if not command:
            return False
        
        if command in self.commands:
            self.commands[command](chat_id, args, **kwargs)
            return True
        else:
            self.handle_unknown_command(chat_id, command)
            return True
    
    def parse_command(self, text: str) -> tuple[str, str]:
        """Parse command and arguments from text"""
        command_match = re.match(r'^/(\w+)(?:\s+(.+))?$', text.strip())
        if command_match:
            command = command_match.group(1).lower()
            args = command_match.group(2) or ""
            return command, args
        return "", ""
    
    def handle_unknown_command(self, chat_id: int, command: str):
        """Handle unknown commands"""
        available_commands = list(self.commands.keys())
        unknown_message = f"""
❓ Unknown command: `{command}`

Available commands:
{chr(10).join(f'• /{cmd}' for cmd in available_commands)}

Type `/help` for more information.
        """
        send_message(TELEGRAM_BOT_TOKEN, chat_id, unknown_message.strip())
    
    def _get_command_info(self) -> list:
        """Get list of command information (name, description)"""
        command_info = []
        
        for cmd_name, cmd_func in self.commands.items():
            desc = getattr(cmd_func, 'description', 'No description available')
            command_info.append((cmd_name, desc))
        
        return command_info
    
    def get_help_text(self) -> str:
        """Generate help text from registered commands"""
        help_lines = ["📚 **Available Commands:**\n"]
        
        for cmd_name, desc in self._get_command_info():
            help_lines.append(f"• `/{cmd_name}` - {desc}")
        
        return "\n".join(help_lines)
    
    def get_telegram_commands(self) -> list:
        """Generate command list for Telegram Bot API setMyCommands"""
        telegram_commands = []
        
        for cmd_name, desc in self._get_command_info():
            # Limit description to 256 characters as per Telegram API requirements
            if len(desc) > 256:
                desc = desc[:253] + "..."
            
            telegram_commands.append({
                "command": cmd_name,
                "description": desc
            })
        
        return telegram_commands

# Create global command handler instance
handler = CommandHandler()

# Example middleware for logging
@handler.add_middleware
def log_commands(chat_id: int, command: str, args: str, **kwargs):
    """Log all command executions"""
    logger.info(f"Command executed: /{command} by chat_id {chat_id} with args: '{args}'")

# Example middleware for rate limiting (basic implementation)
@handler.add_middleware
def rate_limit(chat_id: int, command: str, args: str, **kwargs):
    """Basic rate limiting - you can implement more sophisticated logic"""
    # This is a placeholder - implement actual rate limiting logic
    pass

@handler.command("help", "Show detailed help information")
def help_command(chat_id: int, args: str = ""):
    help_text = handler.get_help_text()
    help_text += """

**Usage Examples:**
• `/echo Hello world` - Bot will echo "Hello world"

**Need Support?**
Contact the bot administrator for additional help.
    """
    send_message(TELEGRAM_BOT_TOKEN, chat_id, help_text)

@handler.command("ping", "Test bot response time")
def ping_command(chat_id: int, args: str = ""):
    send_message(TELEGRAM_BOT_TOKEN, chat_id, "🏓 Pong! Bot is responding quickly.")

@handler.command("echo", "Echo back the provided text")
def echo_command(chat_id: int, args: str = ""):
    if not args.strip():
        send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Please provide text to echo.\nUsage: `/echo <your text>`")
        return
    
    send_message(TELEGRAM_BOT_TOKEN, chat_id, f"📢 Echo: {args}")
