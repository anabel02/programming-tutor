from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv
load_dotenv()


def get_database_url() -> str:
    """Get the database URI from environment variables."""
    db_url = os.getenv("DB_URI")
    if not db_url:
        raise ValueError("DB_URI environment variable is not set.")
    return db_url


# Database engine and session setup
engine = create_engine(get_database_url(), echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
