"""
AI Brain - Claude API integration for intelligence and reasoning
"""
import os
import anthropic
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class AIBrain:
    """AI reasoning engine using Claude"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
        self.max_tokens = 4096
        
        # System prompt that defines the agent's personality and capabilities
        self.system_prompt = """You are a personal life assistant agent with access to various tools and plugins. Your role is to:

1. Help users manage their daily life through natural conversation
2. Remember important information about the user and their preferences
3. Be proactive in offering helpful suggestions and reminders
4. Use available plugins and tools to execute actions, not just provide information
5. Maintain context across conversations
6. Be concise but friendly - avoid over-explaining
7. When you need to use a plugin or tool, do it naturally without announcing "I'll use X plugin"

You have access to:
- Personal memory (remember and recall user information)
- Smart reminders (time-based, location-based, context-based)
- Calendar management
- Financial tracking
- Relationship management
- And more plugins as they're enabled

Always be helpful, proactive, and natural in your communication. Think of yourself as a capable personal assistant who knows the user well."""
    
    async def think(
        self, 
        message: str, 
        context: Dict[str, Any],
        available_plugins: List[str] = None
    ) -> str:
        """
        Process message and generate response
        
        Args:
            message: User message
            context: Conversation context (history, user info, etc.)
            available_plugins: List of available plugin names
            
        Returns:
            AI response
        """
        # Build conversation history
        messages = self._build_messages(message, context)
        
        # Add plugin information to system prompt if provided
        system_prompt = self.system_prompt
        if available_plugins:
            plugin_info = f"\n\nAvailable plugins: {', '.join(available_plugins)}"
            system_prompt += plugin_info
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"AI brain error: {e}", exc_info=True)
            return "I apologize, I'm having trouble processing that right now. Please try again."
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """
        Analyze user intent to determine which plugins should handle the message
        
        Args:
            message: User message
            
        Returns:
            Dict with intent analysis
        """
        prompt = f"""Analyze this message and determine the user's intent:
        
Message: "{message}"

Respond with JSON only:
{{
    "primary_intent": "category of intent (memory, reminder, calendar, financial, etc.)",
    "action_type": "query, create, update, delete, or general",
    "entities": ["list", "of", "key", "entities"],
    "urgency": "low, medium, or high",
    "requires_context": true/false
}}"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text.strip()
            # Clean up markdown code blocks if present
            result = result.replace('```json\n', '').replace('```', '').strip()
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Intent analysis error: {e}")
            return {
                "primary_intent": "general",
                "action_type": "query",
                "entities": [],
                "urgency": "medium",
                "requires_context": False
            }
    
    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """
        Summarize a conversation for memory storage
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Summary string
        """
        # Format messages
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        ])
        
        prompt = f"""Summarize this conversation, extracting key information that should be remembered:

{conversation_text}

Focus on:
- Important facts about the user
- Decisions made
- Commitments or plans
- Preferences stated
- Any actionable items

Provide a concise summary (2-3 sentences)."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Unable to summarize conversation."
    
    def _build_messages(self, current_message: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Build message list for API call"""
        messages = []
        
        # Add recent conversation history if available
        history = context.get('history', [])
        for msg in history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.get('role', 'user'),
                "content": msg.get('content', '')
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    async def extract_structured_data(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from text according to schema
        
        Args:
            text: Text to extract from
            schema: JSON schema describing expected structure
            
        Returns:
            Extracted data as dict
        """
        prompt = f"""Extract structured data from this text according to the schema:

Text: "{text}"

Schema: {json.dumps(schema, indent=2)}

Respond with JSON only, matching the schema structure."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text.strip()
            result = result.replace('```json\n', '').replace('```', '').strip()
            
            return json.loads(result)
            
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            return {}
