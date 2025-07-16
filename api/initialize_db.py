"""
Initialize the database with the correct schema using SQLAlchemy's create_all() function.
This script will create all tables defined in models.py with the correct integer ID columns.
"""
import os
import sys

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import engine
from models import Base

def initialize_database():
    """
    Initialize the database with tables defined in models.py
    """
    print("Initializing database with integer ID schema...")
    
    try:
        # Create all tables defined in models.py
        Base.metadata.create_all(bind=engine)
        print("Database initialization completed successfully!")
        return True
    except Exception as e:
        print(f"Error during database initialization: {e}")
        return False

if __name__ == "__main__":
    initialize_database()
