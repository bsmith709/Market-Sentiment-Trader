import sys
import os

# Add backend to path so we can import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import engine
import models

def init_db():
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()