from http import HTTPStatus

from sqlalchemy.exc import SQLAlchemyError

from database.database import SessionLocal
from database.models import Exercise, Student, Attempt
from services.service_result import ServiceResult


class SubmissionService:
    def __init__(self):
        pass

    def submit_code(self, user_id: str, exercise_id: int, code: str) -> ServiceResult[None]:
        try:
            with SessionLocal() as session:
                exercise = session.query(Exercise).filter(Exercise.id == exercise_id).one_or_none()
                if exercise is None:
                    return ServiceResult.failure(f"El ejercicio con número {exercise_id} no existe.",
                                                 HTTPStatus.NOT_FOUND)

                student = session.query(Student).filter_by(user_id=user_id).one_or_none()
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

                session.add(new_attempt)
                session.commit()

                return ServiceResult.success(None)

        except SQLAlchemyError as e:
            return ServiceResult.failure(f"Error de base de datos: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)

        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)
