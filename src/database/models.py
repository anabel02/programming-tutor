from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship

# Base for all models
Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class User(BaseModel):
    __tablename__ = 'users'

    user_id = Column(String, unique=True, nullable=False)
    chat_id = Column(String, unique=True, nullable=False)

    # Column for inheritance discrimination
    type = Column(String(50), nullable=False)

    # Configuration for inheritance
    __mapper_args__ = {
        'polymorphic_on': type,  # Column for inheritance discrimination
        'polymorphic_identity': 'user',  # Identifier for the base class
    }


class Student(User):
    __tablename__ = 'students'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Many-to-many relationship with exercises suggested
    exercises = relationship("StudentExercise", back_populates="student")

    # Relationship with given hints
    hints_given = relationship("StudentHint", back_populates="student")

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    # Configuration for inheritance
    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }


class Topic(BaseModel):
    __tablename__ = 'topics'

    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Relationship with exercises
    exercises = relationship("Exercise", back_populates="topic")


class Exercise(BaseModel):
    __tablename__ = 'exercises'

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(Enum('Basic', 'Intermediate', 'Advanced', name='difficulty_level'), nullable=False)
    solution = Column(Text, nullable=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)

    # Relationship with topics
    topic = relationship("Topic", back_populates="exercises")

    # Relationship with hints
    hints = relationship("ExerciseHint", back_populates="exercise")


class StudentExercise(BaseModel):
    __tablename__ = 'student_exercise'

    student_id = Column(Integer, ForeignKey('students.id'), primary_key=True)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), primary_key=True)
    status = Column(Enum('In Progress', 'Submitted', 'Completed', name='exercise_status'), default='In Progress')

    student = relationship("Student", back_populates="exercises")


class ExerciseHint(BaseModel):
    __tablename__ = 'exercise_hints'

    order = Column(Integer, nullable=False, default=0)
    hint_text = Column(Text, nullable=False)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), nullable=False)

    # Relationship with exercise
    exercise = relationship("Exercise", back_populates="hints")

    # Relationship with students who have received this hint
    students_received = relationship(
        'StudentHint', back_populates='hint', cascade='all, delete-orphan'
    )


class StudentHint(BaseModel):
    __tablename__ = 'student_hints'

    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    hint_id = Column(Integer, ForeignKey('exercise_hints.id'), nullable=False)

    student = relationship("Student", back_populates="hints_given")
    hint = relationship("ExerciseHint", back_populates="students_received")


class Attempt(BaseModel):
    __tablename__ = 'attempts'
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    exercise_id = Column(Integer, ForeignKey('exercises.id'), nullable=False)
    submitted_code = Column(String, nullable=False)
