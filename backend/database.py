import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = "postgresql://postgres@localhost/sentiment_db"
engine = create_engine(DATABASE_URL)

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