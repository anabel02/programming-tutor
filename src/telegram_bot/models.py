from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Base for all models
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    chat_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
