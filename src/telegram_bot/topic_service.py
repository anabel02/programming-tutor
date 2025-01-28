from sqlalchemy.orm import Session

from database.models import Topic

from database.crud import first_or_default


class TopicService:
    @staticmethod
    def get_by(session: Session, **filters):
        return first_or_default(session=session, model=Topic, **filters)

    @staticmethod
    def get_all(session):
        return session.query(Topic).all()
