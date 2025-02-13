from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Base for all models
Base = declarative_base()

# Join table for the many-to-many relationship between Students and Exercises
student_exercise = Table(
    'student_exercise',
    Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('exercises.id'), primary_key=True),
    Column('status', Enum('In Progress', 'Submitted', 'Completed', name='exercise_status'), default='In Progress'),
)


# User Model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, unique=True, index=True, nullable=False)
    user_id = Column(String, unique=True, nullable=False)
    chat_id = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Column for inheritance discrimination
    type = Column(String(50), nullable=False)

    # Configuration for inheritance
    __mapper_args__ = {
        'polymorphic_on': type,  # Column for inheritance discrimination
        'polymorphic_identity': 'user',  # Identifier for the base class
    }


# Student Model
class Student(User):
    __tablename__ = 'students'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Many-to-many relationship with exercises suggested
    exercises = relationship('Exercise', secondary=student_exercise)

    # Relationship with given hints
    hints_given = relationship("StudentHint", back_populates="student")

    # Computed property for the full name
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    # Configuration for inheritance
    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }


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
    solution = Column(Text, nullable=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship with topics
    topic = relationship("Topic", back_populates="exercises")

    # Relationship with hints
    hints = relationship("ExerciseHint", back_populates="exercise")


class ExerciseHint(Base):
    __tablename__ = 'exercise_hints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer, nullable=False, default=0)
    hint_text = Column(Text, nullable=False)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship with exercise
    exercise = relationship("Exercise", back_populates="hints")

    # Relationship with students who have received this hint
    students_received = relationship(
        'StudentHint', back_populates='hint', cascade='all, delete-orphan'
    )


class StudentHint(Base):
    __tablename__ = 'student_hints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    hint_id = Column(Integer, ForeignKey('exercise_hints.id'), nullable=False)
    given_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student = relationship("Student", back_populates="hints_given")
    hint = relationship("ExerciseHint", back_populates="students_received")
