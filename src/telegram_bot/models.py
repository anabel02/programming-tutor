from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime


# Base for all models
Base = declarative_base()

# Join table for the many-to-many relationship between Users and Exercises
user_exercise = Table(
    'user_exercise',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('exercises.id'), primary_key=True),
    # Column('status', Enum('Not Started', 'In Progress', 'Completed', name='exercise_status'), default='Not Started'),
    # Column('attempts', Integer, default=0),
    # Column('last_attempted_at', DateTime, default=datetime.utcnow),
)


# User Model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    chat_id = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Many-to-many relationship with exercises
    exercises = relationship('Exercise', secondary=user_exercise, back_populates='users')

    # Computed property for the full name
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


# Topic Model
class Topic(Base):
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with exercises
    exercises = relationship("Exercise", back_populates="topic")


# Exercise Model
class Exercise(Base):
    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    hints = Column(Text, nullable=True)  # Can store as a comma-separated string or JSON.
    difficulty = Column(Enum('Basic', 'Intermediate', 'Advanced', name='difficulty_level'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with topics
    topic = relationship("Topic", back_populates="exercises")

    # Many-to-many relationship with users
    users = relationship('User', secondary=user_exercise, back_populates='exercises')
