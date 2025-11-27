"""
Basic Financial Plugin - Track expenses and income
"""
from core.plugin import Plugin
from core.models import FinancialTransaction
from core.database import get_db
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dateutil import parser as dateparser
from sqlalchemy import func


class BasicFinancialPlugin(Plugin):
    """Track financial transactions and budgets"""
    
    name = "Basic Financial"
    description = "Track expenses, income, and budgets"
    version = "1.0.0"
    priority = 40
    
    keywords = [
        "spent", "spend", "cost", "price", "bought",
        "paid", "expense", "income", "earned", "budget",
        "money", "dollars", "$", "financial", "transaction"
    ]
    
    async def initialize(self):
        """Initialize plugin"""
        self.categories = [
            'food', 'transportation', 'entertainment', 'shopping',
            'utilities', 'rent', 'healthcare', 'income', 'other'
        ]
        self.logger.info(f"{self.name} initialized")
    
    def can_handle(self, message: str, context: Dict[str, Any]) -> bool:
        """Check if message is about finances"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.keywords)
    
    async def handle(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """Handle financial-related messages"""
        message_lower = message.lower()
        
        # Check for reports/queries
        if any(word in message_lower for word in ["how much", "spent", "total", "report", "summary"]):
            return await self._generate_report(message)
        
        # Check for budget commands
        if "budget" in message_lower:
            if any(word in message_lower for word in ["set", "create", "update"]):
                return await self._set_budget(message)
            else:
                return await self._check_budget()
        
        # Check for transaction logging
        if any(word in message_lower for word in ["spent", "paid", "bought", "cost"]):
            return await self._log_transaction(message, 'expense')
        
        if any(word in message_lower for word in ["earned", "received", "income"]):
            return await self._log_transaction(message, 'income')
        
        return None
    
    async def _log_transaction(self, message: str, transaction_type: str) -> str:
        """Log a financial transaction"""
        try:
            # Extract transaction details
            details = await self._extract_transaction_details(message)
            
            if not details.get('amount'):
                return "I couldn't determine the amount. Try: 'I spent $25 on groceries'"
            
            amount = details['amount']
            if transaction_type == 'expense':
                amount = -abs(amount)  # Expenses are negative
            else:
                amount = abs(amount)  # Income is positive
            
            # Store transaction
            with get_db() as db:
                transaction = FinancialTransaction(
                    user_id=self.agent.current_user_id,
                    amount=amount,
                    category=details.get('category', 'other'),
                    description=details.get('description', message),
                    transaction_date=details.get('date', datetime.utcnow()),
                    source='manual'
                )
                db.add(transaction)
                db.commit()
            
            # Format response
            category = details.get('category', 'other')
            emoji = self._get_category_emoji(category)
            
            response = f"[OK] Logged: ${abs(amount):.2f} "
            if transaction_type == 'expense':
                response += f"spent on {category} {emoji}"
            else:
                response += f"earned {emoji}"
            
            # Check budget if expense
            if transaction_type == 'expense':
                budget_status = await self._check_category_budget(category, abs(amount))
                if budget_status:
                    response += f"\n{budget_status}"
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to log transaction: {e}")
            return "I had trouble logging that transaction. Please try again."
    
    async def _extract_transaction_details(self, message: str) -> Dict[str, Any]:
        """Extract transaction details from message"""
        schema = {
            "amount": "number - dollar amount",
            "category": f"string - one of {self.categories}",
            "description": "string - what was purchased/earned",
            "date": "ISO datetime string or null"
        }
        
        details = await self.agent.ai_brain.extract_structured_data(message, schema)
        
        # Parse date if provided
        if details.get('date'):
            try:
                details['date'] = dateparser.parse(details['date'])
            except:
                details['date'] = datetime.utcnow()
        
        return details
    
    async def _generate_report(self, query: str) -> str:
        """Generate financial report"""
        try:
            # Extract time period
            time_range = await self._extract_time_range(query)
            
            with get_db() as db:
                # Get transactions in range
                transactions = db.query(FinancialTransaction).filter(
                    FinancialTransaction.user_id == self.agent.current_user_id,
                    FinancialTransaction.transaction_date >= time_range['start'],
                    FinancialTransaction.transaction_date <= time_range['end']
                ).all()
                
                if not transactions:
                    return f"No transactions found for {self._format_period(time_range)}"
                
                # Calculate totals
                total_expenses = sum(t.amount for t in transactions if t.amount < 0)
                total_income = sum(t.amount for t in transactions if t.amount > 0)
                net = total_income + total_expenses  # expenses are negative
                
                # Category breakdown
                category_totals = {}
                for t in transactions:
                    if t.amount < 0:  # Only expenses
                        category_totals[t.category] = category_totals.get(t.category, 0) + abs(t.amount)
                
                # Format response
                period = self._format_period(time_range)
                response = f"💰 **Financial Summary for {period}:**\n\n"
                response += f"**Income:** ${abs(total_income):.2f}\n"
                response += f"**Expenses:** ${abs(total_expenses):.2f}\n"
                response += f"**Net:** ${net:.2f}\n\n"
                
                if category_totals:
                    response += "**Spending by Category:**\n"
                    for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                        emoji = self._get_category_emoji(category)
                        response += f"{emoji} {category.title()}: ${amount:.2f}\n"
                
                return response
                
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return "I had trouble generating that report."
    
    async def _set_budget(self, message: str) -> str:
        """Set budget limits"""
        # Extract budget amount
        details = await self._extract_transaction_details(message)
        
        if not details.get('amount') or not details.get('category'):
            return "Please specify amount and category. Try: 'Set food budget to $300'"
        
        # Store budget in plugin data
        budgets = await self.load_data('budgets') or {}
        budgets[details['category']] = details['amount']
        await self.store_data('budgets', budgets)
        
        emoji = self._get_category_emoji(details['category'])
        return f"[OK] Set {details['category']} budget to ${details['amount']:.2f} {emoji}"
    
    async def _check_budget(self) -> str:
        """Check budget status"""
        budgets = await self.load_data('budgets') or {}
        
        if not budgets:
            return "You haven't set any budgets yet. Try: 'Set food budget to $300'"
        
        # Get current month spending
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        response = "📊 **Budget Status (This Month):**\n\n"
        
        with get_db() as db:
            for category, budget_amount in budgets.items():
                spent = db.query(func.sum(FinancialTransaction.amount)).filter(
                    FinancialTransaction.user_id == self.agent.current_user_id,
                    FinancialTransaction.category == category,
                    FinancialTransaction.transaction_date >= month_start,
                    FinancialTransaction.amount < 0
                ).scalar() or 0
                
                spent = abs(spent)
                remaining = budget_amount - spent
                percent = (spent / budget_amount * 100) if budget_amount > 0 else 0
                
                emoji = self._get_category_emoji(category)
                status_emoji = "✅" if percent < 80 else "⚠️" if percent < 100 else "🚨"
                
                response += f"{status_emoji} {emoji} **{category.title()}**\n"
                response += f"   Spent: ${spent:.2f} / ${budget_amount:.2f} ({percent:.0f}%)\n"
                response += f"   Remaining: ${remaining:.2f}\n\n"
        
        return response
    
    async def _check_category_budget(self, category: str, amount: float) -> Optional[str]:
        """Check if transaction exceeds budget"""
        budgets = await self.load_data('budgets') or {}
        
        if category not in budgets:
            return None
        
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        with get_db() as db:
            spent = db.query(func.sum(FinancialTransaction.amount)).filter(
                FinancialTransaction.user_id == self.agent.current_user_id,
                FinancialTransaction.category == category,
                FinancialTransaction.transaction_date >= month_start,
                FinancialTransaction.amount < 0
            ).scalar() or 0
        
        spent = abs(spent)
        budget = budgets[category]
        percent = (spent / budget * 100) if budget > 0 else 0
        
        if percent >= 100:
            return f"⚠️ You've exceeded your {category} budget!"
        elif percent >= 80:
            remaining = budget - spent
            return f"💡 Heads up: Only ${remaining:.2f} left in {category} budget"
        
        return None
    
    async def _extract_time_range(self, query: str) -> Dict[str, datetime]:
        """Extract time range from query"""
        query_lower = query.lower()
        now = datetime.now()
        
        if "today" in query_lower:
            start = now.replace(hour=0, minute=0, second=0)
            end = now
        elif "week" in query_lower:
            start = now - timedelta(days=7)
            end = now
        elif "month" in query_lower or "this month" in query_lower:
            start = now.replace(day=1, hour=0, minute=0, second=0)
            end = now
        elif "year" in query_lower:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0)
            end = now
        else:
            # Default to current month
            start = now.replace(day=1, hour=0, minute=0, second=0)
            end = now
        
        return {'start': start, 'end': end}
    
    def _format_period(self, time_range: Dict[str, datetime]) -> str:
        """Format time period for display"""
        start = time_range['start']
        end = time_range['end']
        
        if start.month == end.month and start.year == end.year:
            return start.strftime('%B %Y')
        else:
            return f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}"
    
    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for category"""
        emojis = {
            'food': '🍔',
            'transportation': '🚗',
            'entertainment': '🎬',
            'shopping': '🛍️',
            'utilities': '💡',
            'rent': '🏠',
            'healthcare': '🏥',
            'income': '💵',
            'other': '📦'
        }
        return emojis.get(category, '📦')
    
    def get_commands(self) -> Dict[str, str]:
        """Get available commands"""
        return {
            "I spent $X on [category]": "Log an expense",
            "I earned $X": "Log income",
            "How much did I spend this month": "View spending report",
            "Set [category] budget to $X": "Set budget limit",
            "Check budget": "View budget status"
        }
