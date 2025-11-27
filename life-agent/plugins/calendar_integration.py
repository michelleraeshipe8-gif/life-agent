"""
Calendar Integration Plugin - Manage calendar events
"""
from core.plugin import Plugin
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dateutil import parser as dateparser
import pytz


class CalendarIntegrationPlugin(Plugin):
    """Manage calendar events"""
    
    name = "Calendar Integration"
    description = "View, create, and manage calendar events"
    version = "1.0.0"
    priority = 30
    
    keywords = [
        "calendar", "schedule", "meeting", "event",
        "appointment", "when am i", "what's on my",
        "free time", "available", "busy"
    ]
    
    def __init__(self, agent_core):
        super().__init__(agent_core)
        self.calendar_service = None
    
    async def initialize(self):
        """Initialize calendar service"""
        # Note: Google Calendar integration requires OAuth setup
        # For now, this is a placeholder - would integrate with Google Calendar API
        self.logger.info(f"{self.name} initialized (Note: Google Calendar OAuth needed)")
        self.calendar_enabled = False
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """Check if message is about calendar"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Handle calendar-related messages"""
        message_lower = message.lower()
        
        # Check for view/list events
        if any(word in message_lower for word in ["show", "what", "list", "when am i", "schedule"]):
            return await self._show_events(message)
        
        # Check for create event
        if any(word in message_lower for word in ["add", "create", "schedule", "book", "meeting"]):
            return await self._create_event(message)
        
        # Check for free time
        if any(word in message_lower for word in ["free", "available", "busy"]):
            return await self._find_free_time(message)
        
        return None
    
    async def _show_events(self, query: str) -> str:
        """Show calendar events"""
        if not self.calendar_enabled:
            return await self._manual_calendar_view(query)
        
        # TODO: Integrate with Google Calendar API
        return "Calendar integration coming soon! For now, I can store events locally."
    
    async def _manual_calendar_view(self, query: str) -> str:
        """Manual calendar view using stored data"""
        # Extract time range from query
        time_range = await self._extract_time_range(query)
        
        # Load from plugin data storage
        events = await self.load_data('events') or []
        
        # Filter events by time range
        filtered_events = [
            e for e in events
            if time_range['start'] <= datetime.fromisoformat(e['start']) <= time_range['end']
        ]
        
        if not filtered_events:
            return f"No events scheduled for {self._format_time_range(time_range)}"
        
        response = f"📅 **Events for {self._format_time_range(time_range)}:**\n\n"
        for event in filtered_events:
            start_time = datetime.fromisoformat(event['start'])
            response += f"• {start_time.strftime('%I:%M %p')} - {event['title']}\n"
            if event.get('location'):
                response += f"  📍 {event['location']}\n"
        
        return response
    
    async def _create_event(self, message: str) -> str:
        """Create calendar event"""
        try:
            # Extract event details
            details = await self._extract_event_details(message)
            
            if not details.get('start_time'):
                return "I need to know when the event is. Try: 'Schedule meeting tomorrow at 2pm'"
            
            # Store event
            events = await self.load_data('events') or []
            events.append({
                'id': len(events) + 1,
                'title': details.get('title', 'Untitled Event'),
                'description': details.get('description', ''),
                'start': details['start_time'].isoformat(),
                'end': details.get('end_time', details['start_time'] + timedelta(hours=1)).isoformat(),
                'location': details.get('location', ''),
                'created_at': datetime.utcnow().isoformat()
            })
            await self.store_data('events', events)
            
            start_str = details['start_time'].strftime('%B %d at %I:%M %p')
            response = f"[OK] Event created: {details['title']}\n"
            response += f"📅 {start_str}"
            
            if details.get('location'):
                response += f"\n📍 {details['location']}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to create event: {e}")
            return "I had trouble creating that event. Please try again with more details."
    
    async def _extract_event_details(self, message: str) -> Dict[str, Any]:
        """Extract event details from message"""
        schema = {
            "title": "string - event title",
            "description": "string - event description",
            "start_time": "ISO datetime string",
            "end_time": "ISO datetime string or null",
            "location": "string or null"
        }
        
        details = await self.agent.ai_brain.extract_structured_data(message, schema)
        
        # Parse times
        if details.get('start_time'):
            try:
                details['start_time'] = dateparser.parse(details['start_time'])
            except:
                details['start_time'] = None
        
        if details.get('end_time'):
            try:
                details['end_time'] = dateparser.parse(details['end_time'])
            except:
                details['end_time'] = None
        
        return details
    
    async def _find_free_time(self, query: str) -> str:
        """Find free time slots"""
        events = await self.load_data('events') or []
        
        # Simple implementation - check next 7 days
        today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        free_slots = []
        for day in range(7):
            check_date = today + timedelta(days=day)
            day_events = [
                e for e in events
                if datetime.fromisoformat(e['start']).date() == check_date.date()
            ]
            
            if not day_events:
                free_slots.append(check_date.strftime('%A, %B %d'))
        
        if free_slots:
            response = "🆓 **Free Days:**\n\n"
            for slot in free_slots[:5]:
                response += f"• {slot}\n"
            return response
        else:
            return "You're booked solid for the next week!"
    
    async def _extract_time_range(self, query: str) -> Dict[str, datetime]:
        """Extract time range from query"""
        query_lower = query.lower()
        now = datetime.now()
        
        if "today" in query_lower:
            start = now.replace(hour=0, minute=0, second=0)
            end = now.replace(hour=23, minute=59, second=59)
        elif "tomorrow" in query_lower:
            start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif "week" in query_lower:
            start = now.replace(hour=0, minute=0, second=0)
            end = now + timedelta(days=7)
        else:
            # Default to today
            start = now.replace(hour=0, minute=0, second=0)
            end = now.replace(hour=23, minute=59, second=59)
        
        return {'start': start, 'end': end}
    
    def _format_time_range(self, time_range: Dict[str, datetime]) -> str:
        """Format time range for display"""
        start = time_range['start']
        end = time_range['end']
        
        if start.date() == end.date():
            return start.strftime('%A, %B %d')
        else:
            return f"{start.strftime('%B %d')} - {end.strftime('%B %d')}"
    
    def get_commands(self) -> Dict[str, str]:
        """Get available commands"""
        return {
            "what's on my calendar today": "Show today's events",
            "schedule [event] at [time]": "Create new event",
            "when am I free": "Find available time slots",
            "show my schedule for [timeframe]": "View events for specific period"
        }
