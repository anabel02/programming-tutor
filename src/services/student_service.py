from sqlalchemy.orm import Session
from database.models import Student
from database.crud import first_or_default


class StudentService:
    def __init__(self):
        pass

    def get_or_create_user(self, session: Session, user_id: str, chat_id: int, first_name: str, last_name: str) -> Student:
        user = session.query(Student).filter_by(user_id=user_id).one_or_none()
        if not user:
            user = Student(user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name)
            session.add(user)
            session.commit()
        return user

    def create_user(self, session: Session, user_id: str, chat_id: int, first_name: str, last_name: str) -> Student:
        user = Student(user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name)
        session.add(user)
        session.commit()
        return user

    def first_or_default(self, session: Session, **filters):
        return first_or_default(session=session, model=Student, **filters)
