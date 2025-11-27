"""
Smart Reminders Plugin - Intelligent reminder management
"""
from core.plugin import Plugin
from core.models import Reminder
from core.database import get_db
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import re
from dateutil import parser as dateparser
import pytz


class SmartRemindersPlugin(Plugin):
    """Create and manage smart reminders"""
    
    name = "Smart Reminders"
    description = "Set time-based, location-based, and context-aware reminders"
    version = "1.0.0"
    priority = 20
    
    keywords = [
        "remind", "reminder", "alert", "notify",
        "don't forget", "make sure", "scheduled"
    ]
    
    async def initialize(self):
        """Initialize plugin"""
        user_timezone = self.agent.current_user.get('timezone', 'UTC') if self.agent.current_user else 'UTC'
        self.timezone = pytz.timezone(user_timezone)
        self.logger.info(f"{self.name} initialized")
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """Check if message is about reminders"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Handle reminder-related messages"""
        message_lower = message.lower()
        
        # Check for list/show reminders
        if any(word in message_lower for word in ["list", "show", "what", "my reminders"]):
            return await self._list_reminders()
        
        # Check for delete/cancel
        if any(word in message_lower for word in ["delete", "cancel", "remove"]):
            return await self._delete_reminder(message)
        
        # Otherwise, create new reminder
        return await self._create_reminder(message)
    
    async def _create_reminder(self, message: str) -> str:
        """Create new reminder"""
        try:
            # Extract reminder details
            details = await self._extract_reminder_details(message)
            
            if not details.get('time') and not details.get('context_trigger'):
                return "I need to know when to remind you. Try: 'Remind me to call mom tomorrow at 2pm' or 'Remind me next time I talk to Jake'"
            
            # Create reminder
            with get_db() as db:
                reminder = Reminder(
                    user_id=self.agent.current_user_id,
                    title=details.get('title', 'Reminder'),
                    description=details.get('description', ''),
                    reminder_time=details.get('time'),
                    recurring=details.get('recurring', False),
                    recurrence_pattern=details.get('pattern'),
                    context_trigger=details.get('context_trigger')
                )
                db.add(reminder)
                db.commit()
                db.refresh(reminder)
            
            # Format response
            if details.get('time'):
                time_str = details['time'].strftime('%B %d at %I:%M %p')
                response = f"[OK] Reminder set for {time_str}"
            else:
                response = f"[OK] Reminder set for when {details['context_trigger']}"
            
            if details.get('recurring'):
                response += f" (repeats {details['pattern']})"
            
            self.logger.info(f"Created reminder: {details.get('title')}")
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to create reminder: {e}")
            return "I had trouble creating that reminder. Try being more specific about when you want to be reminded."
    
    async def _extract_reminder_details(self, message: str) -> Dict[str, Any]:
        """Extract reminder details from message using AI"""
        schema = {
            "title": "string - brief title",
            "description": "string - full description",
            "time": "ISO datetime string or null",
            "recurring": "boolean",
            "pattern": "string - daily/weekly/monthly or null",
            "context_trigger": "string - person/location/event or null"
        }
        
        details = await self.agent.ai_brain.extract_structured_data(message, schema)
        
        # Parse time if provided
        if details.get('time'):
            try:
                # Parse relative times
                details['time'] = dateparser.parse(details['time'])
                if details['time']:
                    # Localize to user's timezone
                    if details['time'].tzinfo is None:
                        details['time'] = self.timezone.localize(details['time'])
            except Exception as e:
                self.logger.warning(f"Failed to parse time: {e}")
                details['time'] = None
        
        return details
    
    async def _list_reminders(self) -> str:
        """List active reminders"""
        try:
            with get_db() as db:
                reminders = db.query(Reminder).filter(
                    Reminder.user_id == self.agent.current_user_id,
                    Reminder.completed == False
                ).order_by(Reminder.reminder_time).all()
                
                if not reminders:
                    return "You don't have any active reminders."
                
                response = "📋 **Your Reminders:**\n\n"
                for i, reminder in enumerate(reminders, 1):
                    if reminder.reminder_time:
                        time_str = reminder.reminder_time.strftime('%b %d at %I:%M %p')
                        response += f"{i}. {reminder.title} - {time_str}\n"
                    else:
                        response += f"{i}. {reminder.title} - when {reminder.context_trigger}\n"
                
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to list reminders: {e}")
            return "I had trouble fetching your reminders."
    
    async def _delete_reminder(self, message: str) -> str:
        """Delete a reminder"""
        # Simplified - in production would use AI to identify which reminder
        return "Which reminder would you like to delete? You can say the number from the list or describe it."
    
    async def check_due_reminders(self) -> list:
        """Check for due reminders (called by scheduler)"""
        try:
            with get_db() as db:
                now = datetime.utcnow()
                
                reminders = db.query(Reminder).filter(
                    Reminder.user_id == self.agent.current_user_id,
                    Reminder.completed == False,
                    Reminder.reminder_time <= now
                ).all()
                
                due_reminders = []
                for reminder in reminders:
                    due_reminders.append({
                        'title': reminder.title,
                        'description': reminder.description,
                        'id': reminder.id
                    })
                    
                    # Mark as completed or reschedule if recurring
                    if reminder.recurring:
                        reminder.reminder_time = self._calculate_next_occurrence(
                            reminder.reminder_time,
                            reminder.recurrence_pattern
                        )
                    else:
                        reminder.completed = True
                
                db.commit()
                return due_reminders
                
        except Exception as e:
            self.logger.error(f"Failed to check reminders: {e}")
            return []
    
    def _calculate_next_occurrence(self, current_time: datetime, pattern: str) -> datetime:
        """Calculate next occurrence for recurring reminder"""
        if pattern == 'daily':
            return current_time + timedelta(days=1)
        elif pattern == 'weekly':
            return current_time + timedelta(weeks=1)
        elif pattern == 'monthly':
            return current_time + timedelta(days=30)
        else:
            return current_time + timedelta(days=1)
    
    def get_commands(self) -> Dict[str, str]:
        """Get available commands"""
        return {
            "remind me to [task] at [time]": "Create time-based reminder",
            "remind me to [task] when [context]": "Create context-based reminder",
            "list reminders": "Show all active reminders",
            "delete reminder [number]": "Remove a reminder"
        }
