from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
import psycopg2
from sqlalchemy import Column, Integer, String

DATABASE_URL = "postgresql://postgres:root@localhost:5432/tesis"


# Ensure the database exists
def ensure_database():
    conn = psycopg2.connect("postgresql://postgres:root@localhost:5432/postgres")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'tesis'")
        exists = cur.fetchone()
        if not exists:
            cur.execute("CREATE DATABASE tesis")
    conn.close()


ensure_database()

# Database engine
engine = create_engine(DATABASE_URL, echo=True)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()


# Define User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    chat_id = Column(String, unique=True)
    language = Column(String, default="en")
    first_name = Column(String)
    last_name = Column(String)


# Create tables
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")

# Verify tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Existing tables: {tables}")
