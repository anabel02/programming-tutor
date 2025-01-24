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
    Column('status', Enum('In Progress', 'Submitted', 'Completed', name='exercise_status'), default='Completed'),
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

    # Relación con pistas entregadas
    hints_given = relationship("UserHint", back_populates="user")

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
    difficulty = Column(Enum('Basic', 'Intermediate', 'Advanced', name='difficulty_level'), nullable=False)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with topics
    topic = relationship("Topic", back_populates="exercises")

    # Many-to-many relationship with users
    users = relationship('User', secondary=user_exercise, back_populates='exercises')

    # Relación con pistas
    hints = relationship("ExerciseHint", back_populates="exercise")


class ExerciseHint(Base):
    __tablename__ = 'exercise_hints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer, nullable=False, default=0)  # Hint priority/order
    hint_text = Column(Text, nullable=False)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relación con el ejercicio
    exercise = relationship("Exercise", back_populates="hints")

    # Relación con la tabla de usuarios que han recibido esta pista
    users_received = relationship(
        'UserHint', back_populates='hint', cascade='all, delete-orphan'
    )


class UserHint(Base):
    __tablename__ = 'user_hints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    hint_id = Column(Integer, ForeignKey('exercise_hints.id'), nullable=False)
    given_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relación con el usuario y la pista
    user = relationship("User", back_populates="hints_given")

    # Relación con el modelo ExerciseHint
    hint = relationship("ExerciseHint", back_populates="users_received")
