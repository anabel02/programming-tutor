from sqlalchemy.orm import Session
from sqlalchemy import func, case, exists
from database.models import Topic, Student, Exercise, student_exercise
from database.crud import first_or_default
from services.service_result import ServiceResult
from database.database import SessionLocal
from http import HTTPStatus


class ExerciseService:
    DIFFICULTY_LEVELS = ['Basic', 'Intermediate', 'Advanced']

    def __init__(self):
        pass

    def get_by(self, session: Session, **filters):
        return first_or_default(session=session, model=Exercise, **filters)

    def get_unattempted_exercises(self, session: Session, student_id: int, topic_id: str, difficulty: str = 'Basic') -> list[Exercise]:
        valid_difficulties = self._get_valid_difficulties(difficulty)
        attempted_exercises_subquery = self._get_attempted_exercises_subquery(session, student_id)

        query = (
            session.query(Exercise)
            .join(Topic)
            .filter(
                Topic.id == topic_id,
                Exercise.difficulty.in_(valid_difficulties),
                ~Exercise.id.in_(attempted_exercises_subquery)
            )
            .order_by(Exercise.id.asc())
        )

        return query.all()

    def get_first_unattempted_exercise(self, session: Session, student_id: int, topic_id: str, difficulty: str = 'Basic') -> Exercise | None:
        valid_difficulties = self._get_valid_difficulties(difficulty)
        attempted_exercises_subquery = self._get_attempted_exercises_subquery(session, student_id)

        return (
            session.query(Exercise)
            .join(Topic)
            .filter(
                Topic.id == topic_id,
                Exercise.difficulty.in_(valid_difficulties),
                ~Exercise.id.in_(attempted_exercises_subquery)
            )
            .order_by(Exercise.id.asc())
            .first()
        )

    def _get_valid_difficulties(self, difficulty: str) -> list[str]:
        if difficulty is None or difficulty not in self.DIFFICULTY_LEVELS:
            return self.DIFFICULTY_LEVELS
        return self.DIFFICULTY_LEVELS[self.DIFFICULTY_LEVELS.index(difficulty):]

    def _get_attempted_exercises_subquery(self, session: Session, student_id: int):
        return (
            session.query(student_exercise.c.exercise_id)
            .filter(student_exercise.c.student_id == student_id)
            .subquery()
        )

    def get_highest_completed_level(self, session: Session, student_id: int, topic_id: int) -> str:
        difficulty_order = self._get_difficulty_order_case()
        highest_level = self._query_highest_level(session, student_id, topic_id, difficulty_order)
        return self._map_level_to_difficulty(highest_level)

    def _get_difficulty_order_case(self):
        return case(
            (Exercise.difficulty == 'Basic', 1),
            (Exercise.difficulty == 'Intermediate', 2),
            (Exercise.difficulty == 'Advanced', 3),
            else_=0
        )

    def _query_highest_level(self, session: Session, student_id: int, topic_id: int, difficulty_order) -> int:
        return (
            session.query(func.max(difficulty_order))
            .join(student_exercise, student_exercise.c.exercise_id == Exercise.id)
            .filter(
                student_exercise.c.student_id == student_id,
                Exercise.topic_id == topic_id,
                student_exercise.c.status != 'In Progress'
            )
            .scalar()
        )

    def _map_level_to_difficulty(self, level: int) -> str:
        level_map = {1: 'Basic', 2: 'Intermediate', 3: 'Advanced'}
        return level_map.get(level, None)

    def _has_completed_sufficient_exercises(self, session: Session, student_id: int, topic_id: int, difficulty: str, exercises_count: int) -> bool:
        return session.query(
            exists().where(
                (Exercise.topic_id == topic_id) &
                (Exercise.difficulty == difficulty) &
                (Exercise.id.in_(self._get_attempted_exercises_subquery(session, student_id)))
            )
        ).scalar()

    def _recommend_exercise(self, session: Session, student: Student, topic: Topic, exercises_count) -> Exercise:
        level = self.get_highest_completed_level(session, student.id, topic.id)

        if self._has_completed_sufficient_exercises(session, student.id, topic.id, level, exercises_count):
            index = self.DIFFICULTY_LEVELS.index(level)
            level = self.DIFFICULTY_LEVELS[index + 1] if index < self.DIFFICULTY_LEVELS else 'Advanced'

        if exercise := self.get_first_unattempted_exercise(session, student.id, topic.id, level):
            student.exercises.append(exercise)
            session.commit()
            session.refresh(exercise)
            return exercise

        return None

    def recommend_exercise(self, user_id: str, topic_name: str) -> ServiceResult[Exercise]:
        try:
            with SessionLocal() as session:
                user: Student | None = session.query(Student).filter_by(user_id=user_id).one_or_none()
                if not user:
                    return ServiceResult.failure("No se encontró al usuario en el sistema.", HTTPStatus.BAD_REQUEST)

                topic: Topic = (
                    session.query(Topic)
                    .filter(Topic.name == topic_name)
                    .one()
                )
                if not topic:
                    return ServiceResult.failure(f"El tema '{topic_name}' no existe. Por favor, elige otro.", HTTPStatus.BAD_REQUEST)

                exercise: Exercise = self._recommend_exercise(session, user, topic, 5)
                if not exercise:
                    return ServiceResult.failure("Exercise not found", HTTPStatus.NOT_FOUND)

                return ServiceResult.success(exercise)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")

    def get_solution(self, user_id: str, exercise_id: str) -> ServiceResult[str]:
        try:
            with SessionLocal() as session:
                exercise: Exercise = self.get_by(session, id=exercise_id)
                if not exercise:
                    return ServiceResult.failure("No encontramos el ejercicio, verifica el número.", HTTPStatus.BAD_REQUEST)
                if not exercise.solution:
                    return ServiceResult.failure("No tenemos solución para este ejercicio.", HTTPStatus.BAD_REQUEST)
                return ServiceResult.success(exercise.solution)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")
