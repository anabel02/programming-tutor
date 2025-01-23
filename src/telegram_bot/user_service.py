from sqlalchemy.orm import Session
from database.models import User
from database.crud import first_or_default


class UserService:
    @staticmethod
    def get_or_create_user(session: Session, user_id: str, chat_id: int, first_name: str, last_name: str) -> User:
        """Get or create a user in the database."""
        user = session.query(User).filter_by(user_id=user_id).one_or_none()
        if not user:
            user = User(user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name)
            session.add(user)
            session.commit()
        return user

    @staticmethod
    def first_or_default(session: Session, **filters):
        return first_or_default(session=session, model=User, **filters)
