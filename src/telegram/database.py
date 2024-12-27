from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
DATABASE_URL = "postgresql://postgres:root@localhost:5432/tesis"
# Database engine
engine = create_engine(DATABASE_URL, echo=True)
# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base for models
Base = declarative_base()
