import random
from sqlalchemy.orm import Session
from database.models import Topic, Student, Exercise
from database.queries import get_highest_completed_level, get_unattempted_exercises


class ExerciseService:
    @staticmethod
    def recommend_exercise(session: Session, student: Student, topic: Topic):
        """Recommend an exercise based on user's progress."""
        level = get_highest_completed_level(session, student.id, topic.id)
        unattempted_exercises = get_unattempted_exercises(session, student.id, topic.id, level)

        if unattempted_exercises:
            exercise = random.choice(unattempted_exercises)
            student.exercises.append(exercise)
            session.commit()
            return exercise

        return None

    @staticmethod
    def get_exercise_by_title_and_topic(session, topic_name: str, exercise_title: str):
        return (session
                .query(Exercise).join(Topic)
                .filter(Topic.name == topic_name, Exercise.title == exercise_title)
                .one_or_none())
