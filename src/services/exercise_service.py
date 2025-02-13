import random
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from database.models import Topic, Student, Exercise, student_exercise
from database.crud import first_or_default


def get_unattempted_exercises(session, student_id: int, topic_id: str, difficulty: str):
    if difficulty is None:
        difficulty = 'Basic'

    # Definir los niveles de dificultad en orden
    difficulty_levels = ['Basic', 'Intermediate', 'Advanced']

    # Obtener los niveles permitidos
    valid_difficulties = difficulty_levels[difficulty_levels.index(difficulty):]

    # Subquery para obtener los ejercicios ya intentados por el usuario
    attempted_exercises_subquery = (
        session.query(student_exercise.c.exercise_id)
        .filter(student_exercise.c.student_id == student_id)
        .subquery()
    )

    # Query principal para obtener los ejercicios no intentados
    query = (
        session.query(Exercise)
        .join(Topic)
        .filter(
            Topic.id == topic_id,  # Filtrar por el topic
            Exercise.difficulty.in_(valid_difficulties),  # Filtrar por dificultad
            ~Exercise.id.in_(attempted_exercises_subquery)  # Excluir ejercicios ya intentados
        )
    )

    return query.all()


def get_highest_completed_level(session: Session, student_id: int, topic_id: int):
    # Map difficulty levels to a comparable order
    difficulty_order = case(
        (Exercise.difficulty == 'Basic', 1),
        (Exercise.difficulty == 'Intermediate', 2),
        (Exercise.difficulty == 'Advanced', 3),
        else_=0
    )

    # Query for the highest completed level in a topic
    highest_level = (
        session.query(func.max(difficulty_order))
        .join(student_exercise, student_exercise.c.exercise_id == Exercise.id)
        .filter(
            student_exercise.c.student_id == student_id,
            Exercise.topic_id == topic_id,
            student_exercise.c.status == 'Completed'
        )
        .scalar()
    )

    # Map back to difficulty levels
    level_map = {1: 'Basic', 2: 'Intermediate', 3: 'Advanced'}
    return level_map.get(highest_level, None)


class ExerciseService:
    @staticmethod
    def get_by(session: Session, **filters):
        return first_or_default(session=session, model=Exercise, **filters)

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
