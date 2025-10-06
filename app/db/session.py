"""Database session configuration."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Get database session dependency.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
