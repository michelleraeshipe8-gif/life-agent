"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from core.models import Base

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/lifeagent.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv('LOG_LEVEL') == 'DEBUG',
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(SessionLocal)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db():
    """Context manager for database sessions"""
    db = Session()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None):
    """Get existing user or create new one"""
    from core.models import User
    
    with get_db() as db:
        user = db.query(User).filter(User.telegram_id == str(telegram_id)).first()
        
        if not user:
            user = User(
                telegram_id=str(telegram_id),
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Return user data as dict to avoid detached instance issues
        user_data = {
            'id': user.id,
            'telegram_id': user.telegram_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'timezone': user.timezone,
            'preferences': user.preferences
        }
        return user_data
