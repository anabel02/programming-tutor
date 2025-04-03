from http import HTTPStatus

from sqlalchemy.orm import Session

from database.models import Student
from services.service_result import ServiceResult


class StudentService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_id: str, chat_id: str, first_name: str, last_name: str) -> ServiceResult[Student]:
        try:
            if self.user_exists(user_id):
                return ServiceResult.failure("Already exists", HTTPStatus.BAD_REQUEST)
            user = Student(user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return ServiceResult.success(user)
        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}")

    def get_user(self, user_id: str) -> ServiceResult[Student]:
        try:

            user = self.first_or_default(user_id=user_id)
            if user:
                return ServiceResult.success(user)
            return ServiceResult.failure("User not found", HTTPStatus.NOT_FOUND)
        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}")

    def first_or_default(self, **filters):
        return self.db.query(Student).filter_by(**filters).first()

    def user_exists(self, student_id: str) -> bool:
        return self.first_or_default(user_id=student_id) is not None
