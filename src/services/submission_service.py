from http import HTTPStatus

from sqlalchemy.orm import Session

from database.models import Exercise, Student, Attempt
from services.service_result import ServiceResult


class SubmissionService:
    def __init__(self, db: Session):
        self.db = db

    def submit_code(self, user_id: str, exercise_id: int, code: str) -> ServiceResult[None]:
        try:
            exercise: Exercise | None = self.db.query(Exercise).filter(Exercise.id == exercise_id).one_or_none()
            if exercise is None:
                return ServiceResult.failure(f"El ejercicio con número {exercise_id} no existe.",
                                             HTTPStatus.NOT_FOUND)

            student: Student | None = self.db.query(Student).filter_by(user_id=user_id).one_or_none()
            if student is None:
                return ServiceResult.failure("El estudiante no está registrado.", HTTPStatus.BAD_REQUEST)

            if not any(ex.id == exercise_id for ex in student.exercises):
                return ServiceResult.failure("Parece que no te he recomendado ese ejercicio.",
                                             HTTPStatus.BAD_REQUEST)

            new_attempt = Attempt(
                student_id=student.id,
                exercise_id=exercise_id,
                submitted_code=code,
            )

            self.db.add(new_attempt)
            self.db.commit()

            return ServiceResult.success(None)
        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)
