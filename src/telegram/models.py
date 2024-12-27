from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)  # Telegram User ID
    chat_id = Column(String, unique=True)  # Telegram Chat ID
    language = Column(String, default="en")  # Preferred Language


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    subscribed = Column(Boolean, default=False)  # Subscription Status
    user = relationship("User")
