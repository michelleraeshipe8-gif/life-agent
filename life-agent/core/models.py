"""
Database models for Life Agent
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User profile and preferences"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    timezone = Column(String, default='UTC')
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship('Conversation', back_populates='user')
    memories = relationship('Memory', back_populates='user')
    reminders = relationship('Reminder', back_populates='user')


class Conversation(Base):
    """Conversation history"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    context = Column(JSON, default={})
    
    user = relationship('User', back_populates='conversations')


class Memory(Base):
    """Long-term memory storage"""
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    category = Column(String)  # personal, work, health, etc.
    content = Column(Text)
    meta_data = Column(JSON, default={})  # Renamed from metadata to avoid conflict
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    
    user = relationship('User', back_populates='memories')


class Reminder(Base):
    """Reminders and scheduled tasks"""
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(Text)
    reminder_time = Column(DateTime)
    recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String)  # daily, weekly, monthly
    context_trigger = Column(String)  # location, person, etc.
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='reminders')


class FinancialTransaction(Base):
    """Financial transactions"""
    __tablename__ = 'financial_transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    category = Column(String)
    description = Column(Text)
    transaction_date = Column(DateTime)
    source = Column(String)  # manual, bank, receipt
    meta_data = Column(JSON, default={})  # Renamed from metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class Contact(Base):
    """Contacts and relationship tracking"""
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    relationship = Column(String)  # friend, family, colleague
    phone = Column(String)
    email = Column(String)
    birthday = Column(DateTime)
    last_contact = Column(DateTime)
    notes = Column(Text)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    """Tasks and to-dos"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(Text)
    priority = Column(Integer, default=0)
    status = Column(String, default='pending')  # pending, in_progress, completed
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Document storage and references"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    document_type = Column(String)  # receipt, manual, contract, etc.
    file_path = Column(String)
    extracted_text = Column(Text)
    meta_data = Column(JSON, default={})  # Renamed from metadata
    created_at = Column(DateTime, default=datetime.utcnow)


class PluginData(Base):
    """Generic plugin data storage"""
    __tablename__ = 'plugin_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    plugin_name = Column(String)
    data_key = Column(String)
    data_value = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
