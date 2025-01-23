import random
from sqlalchemy.orm import Session
from database.models import Topic, User
from database.queries import get_highest_completed_level, get_unattempted_exercises


class ExerciseService:
    @staticmethod
    def get_topic_by_name(session: Session, topic_name: str) -> Topic:
        """Fetch a topic by its name."""
        return session.query(Topic).filter_by(name=topic_name).one_or_none()

    @staticmethod
    def recommend_exercise(session: Session, user: User, topic: Topic):
        """Recommend an exercise based on user's progress."""
        level = get_highest_completed_level(session, user.id, topic.id)
        unattempted_exercises = get_unattempted_exercises(
            session=session, user_id=user.id, topic_id=topic.id, difficulty=level
        )

        if unattempted_exercises:
            exercise = random.choice(unattempted_exercises)
            user.exercises.append(exercise)
            session.commit()
            return exercise

        return None
