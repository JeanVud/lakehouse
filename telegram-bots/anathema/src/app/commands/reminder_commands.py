"""
Reminder commands using SQLAlchemy repository pattern
"""
from app.commands.base_commands import handler
from app.services.telegram_service import send_message
from core.utils import logger
from core.config import TELEGRAM_BOT_TOKEN
from app.repositories.reminder_repository import ReminderRepository

# Create repository instance
reminder_repo = ReminderRepository()

@handler.command("reminderadd", "Add a new reminder/todo item")
def reminder_add_command(chat_id: int, args: str = ""):
    if not args.strip():
        send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Please provide reminder text.\nUsage: `/reminderadd Buy groceries tomorrow`")
        return
    
    try:
        reminder_text = args.strip()
        
        # Add reminder to database using repository
        reminder = reminder_repo.create(
            chat_id=chat_id,
            text=reminder_text
        )
        
        # Get reminder count for this chat
        count = reminder_repo.count_by_chat_id(chat_id)
        
        success_message = f"""
✅ **Reminder Added Successfully!**

📝 **Text:** {reminder_text}
🆔 **ID:** {reminder.id}
📊 **Total reminders:** {count}

Your reminder has been saved to the database.
        """
        send_message(TELEGRAM_BOT_TOKEN, chat_id, success_message.strip())
        
    except Exception as e:
        logger.error(f"Error adding reminder: {e}")
        send_message(TELEGRAM_BOT_TOKEN, chat_id, f"❌ Failed to add reminder: {str(e)}")

@handler.command("reminderlist", "List all your reminders")
def reminder_list_command(chat_id: int, args: str = ""):
    try:
        # Parse arguments for filtering
        show_completed = False
        if args.strip().lower() in ['all', 'completed', 'done']:
            show_completed = None  # Show all reminders
        elif args.strip().lower() in ['completed', 'done']:
            show_completed = True  # Show only completed
        
        # Get reminders from database using repository
        if show_completed is None:
            reminders = reminder_repo.get_by_chat_id(chat_id)
        elif show_completed:
            reminders = reminder_repo.get_completed_by_chat_id(chat_id)
        else:
            reminders = reminder_repo.get_active_by_chat_id(chat_id)
        
        if not reminders:
            if show_completed is True:
                message = "📋 **No completed reminders found.**\n\nUse `/reminderlist` to see active reminders."
            elif show_completed is False:
                message = "📋 **No active reminders found.**\n\nUse `/reminderadd <text>` to add a new reminder."
                # message = "No active reminders found."
            else:
                message = "📋 **No reminders found.**\n\nUse `/reminderadd <text>` to add your first reminder."
            
            send_message(TELEGRAM_BOT_TOKEN, chat_id, message)
            return
        
        # Format reminders list
        message_lines = ["📋 **Your Reminders:**\n"]
        
        for i, reminder in enumerate(reminders, 1):
            status = "✅" if reminder.completed else "⏳"
            text = reminder.text
            reminder_id = reminder.id
            created_at = reminder.created_at
            
            # Format date
            try:
                date_str = created_at.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = str(created_at)[:16]
            
            message_lines.append(f"{i}. {status} **{text}**")
            message_lines.append(f"   🆔 {reminder_id} | 📅 {date_str}\n")
        
        # Add usage instructions
        message_lines.append("\n**Usage:**")
        message_lines.append("• `/reminderlist` - Show active reminders")
        message_lines.append("• `/reminderlist all` - Show all reminders")
        message_lines.append("• `/reminderlist completed` - Show completed reminders")
        
        message = "\n".join(message_lines)
        
        # Split long messages if needed (Telegram has 4096 character limit)
        if len(message) > 4000:
            # Send first part
            send_message(TELEGRAM_BOT_TOKEN, chat_id, message[:4000])
            # Send remaining part
            remaining = message[4000:]
            if remaining.strip():
                send_message(TELEGRAM_BOT_TOKEN, chat_id, remaining)
        else:
            send_message(TELEGRAM_BOT_TOKEN, chat_id, message)
            
    except Exception as e:
        logger.error(f"Error listing reminders: {e}")
        send_message(TELEGRAM_BOT_TOKEN, chat_id, f"❌ Failed to list reminders: {str(e)}")

@handler.command("remindercomplete", "Mark a reminder as completed")
def reminder_complete_command(chat_id: int, args: str = ""):
    if not args.strip():
        send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Please provide reminder ID.\nUsage: `/remindercomplete 123`")
        return
    
    try:
        reminder_id = int(args.strip())
        
        # Mark reminder as completed
        reminder = reminder_repo.mark_completed(reminder_id)
        
        if reminder and reminder.chat_id == chat_id:
            success_message = f"""
✅ **Reminder Completed!**

📝 **Text:** {reminder.text}
🆔 **ID:** {reminder.id}
⏰ **Completed at:** {reminder.completed_at.strftime('%Y-%m-%d %H:%M') if reminder.completed_at else 'Now'}
            """
            send_message(TELEGRAM_BOT_TOKEN, chat_id, success_message.strip())
        else:
            send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Reminder not found or doesn't belong to you.")
            
    except ValueError:
        send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Please provide a valid reminder ID (number).")
    except Exception as e:
        logger.error(f"Error completing reminder: {e}")
        send_message(TELEGRAM_BOT_TOKEN, chat_id, f"❌ Failed to complete reminder: {str(e)}")

@handler.command("reminderstats", "Show your reminder statistics")
def reminder_stats_command(chat_id: int, args: str = ""):
    try:
        # Get statistics using repository
        stats = reminder_repo.get_statistics(chat_id)
        
        stats_message = f"""
📊 **Your Reminder Statistics**

📋 **Total reminders:** {stats['total']}
✅ **Completed:** {stats['completed']}
⏳ **Active:** {stats['active']}
📈 **Completion rate:** {stats['completion_rate']:.1f}%

Keep up the good work! 🎉
        """
        send_message(TELEGRAM_BOT_TOKEN, chat_id, stats_message.strip())
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        send_message(TELEGRAM_BOT_TOKEN, chat_id, f"❌ Failed to get statistics: {str(e)}")

@handler.command("remindersearch", "Search reminders by text")
def reminder_search_command(chat_id: int, args: str = ""):
    if not args.strip():
        send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Please provide search text.\nUsage: `/remindersearch groceries`")
        return
    
    try:
        search_text = args.strip()
        
        # Search reminders using repository
        reminders = reminder_repo.search_by_text(chat_id, search_text, limit=10)
        
        if not reminders:
            message = f"🔍 **No reminders found matching '{search_text}'**\n\nTry a different search term or add a new reminder."
            send_message(TELEGRAM_BOT_TOKEN, chat_id, message)
            return
        
        # Format search results
        message_lines = [f"🔍 **Search Results for '{search_text}':**\n"]
        
        for i, reminder in enumerate(reminders, 1):
            status = "✅" if reminder.completed else "⏳"
            text = reminder.text
            reminder_id = reminder.id
            created_at = reminder.created_at
            
            # Format date
            date_str = created_at.strftime('%Y-%m-%d %H:%M')
            
            message_lines.append(f"{i}. {status} **{text}**")
            message_lines.append(f"   🆔 {reminder_id} | 📅 {date_str}\n")
        
        message = "\n".join(message_lines)
        send_message(TELEGRAM_BOT_TOKEN, chat_id, message)
        
    except Exception as e:
        logger.error(f"Error searching reminders: {e}")
        send_message(TELEGRAM_BOT_TOKEN, chat_id, f"❌ Failed to search reminders: {str(e)}")

@handler.command("reminderdelete", "Delete a reminder by ID")
def reminder_delete_command(chat_id: int, args: str = ""):
    if not args.strip():
        send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Please provide reminder ID.\nUsage: `/reminderdelete 123`")
        return
    
    try:
        reminder_id = int(args.strip())
        
        # Get reminder first to check ownership
        reminder = reminder_repo.get_by_id(reminder_id)
        
        if not reminder:
            send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Reminder not found.")
            return
        
        if reminder.chat_id != chat_id:
            send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ You can only delete your own reminders.")
            return
        
        # Delete reminder
        reminder_repo.delete(reminder_id)
        
        success_message = f"""
🗑️ **Reminder Deleted Successfully!**

📝 **Text:** {reminder.text}
🆔 **ID:** {reminder.id}

The reminder has been permanently removed from the database.
        """
        send_message(TELEGRAM_BOT_TOKEN, chat_id, success_message.strip())
        
    except ValueError:
        send_message(TELEGRAM_BOT_TOKEN, chat_id, "❌ Please provide a valid reminder ID (number).")
    except Exception as e:
        logger.error(f"Error deleting reminder: {e}")
        send_message(TELEGRAM_BOT_TOKEN, chat_id, f"❌ Failed to delete reminder: {str(e)}") 