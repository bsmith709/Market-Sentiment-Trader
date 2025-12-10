from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# PRIORITY: Look for the env var 'DATABASE_URL' first.
# If not found, default to localhost (for when you run scripts on your Mac).
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost/sentiment_db"
)

# Fix for Heroku/Render URLs that start with "postgres://" (SQLAlchemy needs "postgresql://")
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create the SessionLocal class used to query DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base (All your models will inherit from this)
Base = declarative_base()

# Dependency (This is used in every API endpoint to get a connection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()