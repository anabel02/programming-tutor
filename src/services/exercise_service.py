from sqlalchemy.orm import Session
from sqlalchemy import func, case, exists
from database.models import Topic, Student, Exercise, student_exercise
from database.crud import first_or_default


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

    def recommend_exercise(self, session: Session, student: Student, topic: Topic, exercises_count=5) -> Exercise:
        level = self.get_highest_completed_level(session, student.id, topic.id)

        if self._has_completed_sufficient_exercises(session, student.id, topic.id, level, exercises_count):
            index = self.DIFFICULTY_LEVELS.index(level)
            level = self.DIFFICULTY_LEVELS[index + 1] if index < self.DIFFICULTY_LEVELS else 'Advanced'

        if exercise := self.get_first_unattempted_exercise(session, student.id, topic.id, level):
            student.exercises.append(exercise)
            session.commit()
            return exercise

        return None
