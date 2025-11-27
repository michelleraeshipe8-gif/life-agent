"""
Relationship Manager Plugin - Track and nurture relationships
"""
from core.plugin import Plugin
from core.models import Contact
from core.database import get_db
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dateutil import parser as dateparser


class RelationshipManagerPlugin(Plugin):
    """Track contacts and relationship interactions"""
    
    name = "Relationship Manager"
    description = "Remember contacts, track interactions, and get relationship insights"
    version = "1.0.0"
    priority = 50
    
    keywords = [
        "contact", "friend", "family", "call", "text",
        "talk to", "message", "birthday", "relationship",
        "haven't talked", "reach out", "check in"
    ]
    
    async def initialize(self):
        """Initialize plugin"""
        self.relationship_types = ['friend', 'family', 'colleague', 'acquaintance', 'other']
        self.logger.info(f"{self.name} initialized")
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """Check if message is about relationships"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Handle relationship-related messages"""
        message_lower = message.lower()
        
        # Check for adding contact
        if any(word in message_lower for word in ["add contact", "new contact", "save contact"]):
            return await self._add_contact(message)
        
        # Check for listing contacts
        if any(word in message_lower for word in ["list contacts", "show contacts", "my contacts"]):
            return await self._list_contacts()
        
        # Check for interaction logging
        if any(word in message_lower for word in ["talked to", "called", "texted", "met with", "saw"]):
            return await self._log_interaction(message)
        
        # Check for relationship insights
        if any(word in message_lower for word in ["haven't talked", "should reach out", "who should i"]):
            return await self._relationship_insights()
        
        # Check for upcoming birthdays
        if "birthday" in message_lower:
            return await self._check_birthdays()
        
        return None
    
    async def _add_contact(self, message: str) -> str:
        """Add new contact"""
        try:
            # Extract contact details
            details = await self._extract_contact_details(message)
            
            if not details.get('name'):
                return "I need at least a name. Try: 'Add contact: John Smith, friend, birthday March 15'"
            
            # Check if contact exists
            with get_db() as db:
                existing = db.query(Contact).filter(
                    Contact.user_id == self.agent.current_user_id,
                    Contact.name == details['name']
                ).first()
                
                if existing:
                    return f"You already have a contact named {details['name']}. Want to update their info?"
                
                # Create new contact
                contact = Contact(
                    user_id=self.agent.current_user_id,
                    name=details['name'],
                    relationship=details.get('relationship', 'other'),
                    phone=details.get('phone'),
                    email=details.get('email'),
                    birthday=details.get('birthday'),
                    notes=details.get('notes', ''),
                    preferences=details.get('preferences', {})
                )
                db.add(contact)
                db.commit()
                db.refresh(contact)
            
            emoji = self._get_relationship_emoji(contact.relationship)
            response = f"[OK] Added {emoji} {contact.name}"
            
            if contact.relationship:
                response += f" ({contact.relationship})"
            if contact.birthday:
                response += f"\n🎂 Birthday: {contact.birthday.strftime('%B %d')}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to add contact: {e}")
            return "I had trouble adding that contact. Please try again."
    
    async def _extract_contact_details(self, message: str) -> Dict[str, Any]:
        """Extract contact details from message"""
        schema = {
            "name": "string - full name",
            "relationship": f"string - one of {self.relationship_types}",
            "phone": "string - phone number or null",
            "email": "string - email address or null",
            "birthday": "string - date (month day) or null",
            "notes": "string - any additional notes",
            "preferences": "object - any preferences mentioned"
        }
        
        details = await self.agent.ai_brain.extract_structured_data(message, schema)
        
        # Parse birthday if provided
        if details.get('birthday'):
            try:
                # Parse date (might just be month/day)
                parsed_date = dateparser.parse(details['birthday'])
                if parsed_date:
                    # Store just month and day, use current year
                    details['birthday'] = parsed_date.replace(year=datetime.now().year)
            except:
                details['birthday'] = None
        
        return details
    
    async def _list_contacts(self) -> str:
        """List all contacts"""
        try:
            with get_db() as db:
                contacts = db.query(Contact).filter(
                    Contact.user_id == self.agent.current_user_id
                ).order_by(Contact.name).all()
                
                if not contacts:
                    return "You don't have any contacts yet. Try: 'Add contact: John Smith, friend'"
                
                # Group by relationship type
                grouped = {}
                for contact in contacts:
                    rel = contact.relationship or 'other'
                    if rel not in grouped:
                        grouped[rel] = []
                    grouped[rel].append(contact)
                
                response = "👥 **Your Contacts:**\n\n"
                
                for rel_type, contacts_list in grouped.items():
                    emoji = self._get_relationship_emoji(rel_type)
                    response += f"**{emoji} {rel_type.title()}** ({len(contacts_list)}):\n"
                    for contact in contacts_list:
                        last_contact = ""
                        if contact.last_contact:
                            days_ago = (datetime.utcnow() - contact.last_contact).days
                            if days_ago == 0:
                                last_contact = " (today)"
                            elif days_ago == 1:
                                last_contact = " (yesterday)"
                            else:
                                last_contact = f" ({days_ago} days ago)"
                        response += f"  • {contact.name}{last_contact}\n"
                    response += "\n"
                
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to list contacts: {e}")
            return "I had trouble fetching your contacts."
    
    async def _log_interaction(self, message: str) -> str:
        """Log interaction with contact"""
        try:
            # Extract contact name and interaction type
            details = await self.agent.ai_brain.extract_structured_data(
                message,
                {
                    "contact_name": "string - person's name",
                    "interaction_type": "string - called/texted/met/etc",
                    "notes": "string - what was discussed"
                }
            )
            
            if not details.get('contact_name'):
                return "Who did you interact with? Try: 'I talked to Sarah today about her new job'"
            
            # Find contact
            with get_db() as db:
                contact = db.query(Contact).filter(
                    Contact.user_id == self.agent.current_user_id,
                    Contact.name.ilike(f"%{details['contact_name']}%")
                ).first()
                
                if not contact:
                    return f"I don't have a contact for {details['contact_name']}. Want to add them first?"
                
                # Update last contact time
                contact.last_contact = datetime.utcnow()
                
                # Add to notes if provided
                if details.get('notes'):
                    current_notes = contact.notes or ""
                    timestamp = datetime.utcnow().strftime('%Y-%m-%d')
                    new_note = f"\n[{timestamp}] {details['notes']}"
                    contact.notes = current_notes + new_note
                
                db.commit()
            
            emoji = self._get_relationship_emoji(contact.relationship)
            return f"[OK] Logged interaction with {emoji} {contact.name}"
            
        except Exception as e:
            self.logger.error(f"Failed to log interaction: {e}")
            return "I had trouble logging that interaction."
    
    async def _relationship_insights(self) -> str:
        """Provide relationship insights"""
        try:
            check_in_days = self.get_config('check_in_interval_days', 14)
            cutoff_date = datetime.utcnow() - timedelta(days=check_in_days)
            
            with get_db() as db:
                # Find contacts not contacted recently
                overdue_contacts = db.query(Contact).filter(
                    Contact.user_id == self.agent.current_user_id,
                    Contact.last_contact < cutoff_date
                ).order_by(Contact.last_contact).limit(5).all()
                
                if not overdue_contacts:
                    return "🎉 You're doing great staying in touch with everyone!"
                
                response = "💡 **Consider Reaching Out:**\n\n"
                response += f"You haven't talked to these people in {check_in_days}+ days:\n\n"
                
                for contact in overdue_contacts:
                    days_ago = (datetime.utcnow() - contact.last_contact).days if contact.last_contact else 999
                    emoji = self._get_relationship_emoji(contact.relationship)
                    response += f"{emoji} **{contact.name}** "
                    
                    if contact.last_contact:
                        response += f"({days_ago} days ago)\n"
                    else:
                        response += "(never logged)\n"
                
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to generate insights: {e}")
            return "I had trouble generating relationship insights."
    
    async def _check_birthdays(self) -> str:
        """Check upcoming birthdays"""
        try:
            reminder_days = self.get_config('birthday_reminder_days', 7)
            today = datetime.utcnow().date()
            
            with get_db() as db:
                contacts_with_birthdays = db.query(Contact).filter(
                    Contact.user_id == self.agent.current_user_id,
                    Contact.birthday.isnot(None)
                ).all()
                
                if not contacts_with_birthdays:
                    return "You don't have any birthdays saved yet."
                
                upcoming = []
                for contact in contacts_with_birthdays:
                    # Get birthday this year
                    bday = contact.birthday.replace(year=today.year)
                    
                    # If birthday already passed, check next year
                    if bday.date() < today:
                        bday = bday.replace(year=today.year + 1)
                    
                    days_until = (bday.date() - today).days
                    
                    if days_until <= reminder_days:
                        upcoming.append((contact, bday, days_until))
                
                if not upcoming:
                    return f"No birthdays in the next {reminder_days} days."
                
                upcoming.sort(key=lambda x: x[2])  # Sort by days until
                
                response = "🎂 **Upcoming Birthdays:**\n\n"
                for contact, bday, days_until in upcoming:
                    emoji = self._get_relationship_emoji(contact.relationship)
                    if days_until == 0:
                        response += f"🎉 {emoji} **{contact.name}** - TODAY!\n"
                    elif days_until == 1:
                        response += f"{emoji} {contact.name} - Tomorrow ({bday.strftime('%B %d')})\n"
                    else:
                        response += f"{emoji} {contact.name} - {days_until} days ({bday.strftime('%B %d')})\n"
                
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to check birthdays: {e}")
            return "I had trouble checking birthdays."
    
    def _get_relationship_emoji(self, relationship: str) -> str:
        """Get emoji for relationship type"""
        emojis = {
            'friend': '👋',
            'family': '👨‍👩‍👧',
            'colleague': '💼',
            'acquaintance': '👤',
            'other': '👥'
        }
        return emojis.get(relationship, '👥')
    
    def get_commands(self) -> Dict[str, str]:
        """Get available commands"""
        return {
            "add contact [name], [relationship]": "Add new contact",
            "list contacts": "Show all contacts",
            "I talked to [name]": "Log interaction",
            "who should I reach out to": "Get relationship insights",
            "upcoming birthdays": "See upcoming birthdays"
        }
