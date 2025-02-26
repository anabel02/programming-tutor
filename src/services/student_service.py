from sqlalchemy.orm import Session
from database.models import Student
from database.crud import first_or_default
from services.service_result import ServiceResult
from database.database import SessionLocal
from http import HTTPStatus


class StudentService:
    def __init__(self):
        pass

    def create_user(self, user_id: str, chat_id: str, first_name: str, last_name: str) -> ServiceResult[Student]:
        try:
            with SessionLocal() as session:
                if self.user_exists(session, user_id):
                    return ServiceResult.failure("Already exists", HTTPStatus.BAD_REQUEST)
                user = Student(user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name)
                session.add(user)
                session.commit()
                session.refresh(user)
                return ServiceResult.success(user)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")

    def get_user(self, user_id: str) -> ServiceResult[Student]:
        try:
            with SessionLocal() as session:
                user = self.first_or_default(session=session, user_id=user_id)
                if user:
                    return ServiceResult.success(user)
                return ServiceResult.failure("User not found", HTTPStatus.NOT_FOUND)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")

    def first_or_default(self, session: Session, **filters):
        return first_or_default(session=session, model=Student, **filters)

    def user_exists(self, session: Session, student_id: int) -> bool:
        return self.first_or_default(session, user_id=student_id) is not None
