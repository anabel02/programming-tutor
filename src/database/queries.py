from database.models import Topic, Exercise, user_exercise
from sqlalchemy import func, case
from sqlalchemy.orm import Session


def get_unattempted_exercises(session, user_id: int, topic_id: str, difficulty: str):
    if difficulty is None:
        difficulty = 'Basic'

    # Definir los niveles de dificultad en orden
    difficulty_levels = ['Basic', 'Intermediate', 'Advanced']

    # Obtener los niveles permitidos
    valid_difficulties = difficulty_levels[difficulty_levels.index(difficulty):]

    # Subquery para obtener los ejercicios ya intentados por el usuario
    attempted_exercises_subquery = (
        session.query(user_exercise.c.exercise_id)
        .filter(user_exercise.c.user_id == user_id)
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


def get_highest_completed_level(session: Session, user_id: int, topic_id: int):
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
        .join(user_exercise, user_exercise.c.exercise_id == Exercise.id)
        .filter(
            user_exercise.c.user_id == user_id,
            Exercise.topic_id == topic_id,
            user_exercise.c.status == 'Completed'
        )
        .scalar()
    )

    # Map back to difficulty levels
    level_map = {1: 'Basic', 2: 'Intermediate', 3: 'Advanced'}
    return level_map.get(highest_level, None)
