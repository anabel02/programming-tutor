from http import HTTPStatus

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import Exercise, StudentHint, Student, ExerciseHint
from services.service_result import ServiceResult


class HintService:
    def __init__(self, db: Session):
        self.db = db

    def give_hint(self, user_id: str, exercise_id: str) -> ServiceResult[ExerciseHint]:
        try:
            exercise: Exercise | None = self.db.query(Exercise).filter(Exercise.id == exercise_id).one_or_none()

            if exercise is None:
                return ServiceResult.failure("El ejercicio no existe.", HTTPStatus.NOT_FOUND)

            student: Student | None = self.db.query(Student).filter_by(user_id=user_id).one_or_none()

            if student is None:
                return ServiceResult.failure("El usuario no existe.", HTTPStatus.NOT_FOUND)

            if not any(ex.id == exercise_id for ex in student.exercises):
                return ServiceResult.failure("Parece que no te he recomendado ese ejercicio.",
                                             HTTPStatus.BAD_REQUEST)

            hints = sorted(exercise.hints, key=lambda hint: hint.order)

            if not hints:
                return ServiceResult.failure("No hay pistas disponibles para este ejercicio.",
                                             HTTPStatus.BAD_REQUEST)

            # Filtrar pistas que ya se entregaron al usuario
            given_hints_ids = {
                uh.hint_id
                for uh in self.db.query(StudentHint).filter_by(student_id=student.id).all()
            }

            available_hints = [hint for hint in hints if hint.id not in given_hints_ids]

            if not available_hints:
                return ServiceResult.failure("Ya se te han dado todas las pistas disponibles para este ejercicio.",
                                             HTTPStatus.BAD_REQUEST)

            hint_to_give = available_hints[0]

            user_hint = StudentHint(student_id=student.id, hint_id=hint_to_give.id)
            self.db.add(user_hint)
            self.db.commit()

            return ServiceResult.success(hint_to_give)
        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}")
