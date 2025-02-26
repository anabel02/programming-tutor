from database.models import Exercise, Student, Attempt
from services.service_result import ServiceResult
from database.database import SessionLocal
from http import HTTPStatus


class SubmissionService:
    def __init__(self):
        pass

    def submit_code(self, user_id: str, exercise_id: str, code: str) -> ServiceResult[None]:
        try:
            with SessionLocal() as session:
                exercise: Exercise = (
                    session.query(Exercise)
                    .filter(Exercise.id == exercise_id)
                    .one()
                )
                if exercise is None:
                    return ServiceResult.failure(f"El ejercicio con número {exercise_id} no existe.", HTTPStatus.BAD_REQUEST)

                student: Student | None = session.query(Student).filter_by(user_id=user_id).one_or_none()
                if student is None:
                    return ServiceResult.failure("El estudiante no está registrado.", HTTPStatus.BAD_REQUEST)

                if exercise.id not in {ex.id for ex in student.exercises}:
                    return ServiceResult.failure("Parece que no te he recomendado ese ejercicio.", HTTPStatus.BAD_REQUEST)

                new_attempt = Attempt(
                    student_id=student.id,
                    exercise_id=exercise_id,
                    submitted_code=code,
                )

                session.add(new_attempt)
                session.commit()

                return ServiceResult.success(None)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")
