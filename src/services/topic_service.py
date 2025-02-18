from sqlalchemy.orm import Session
from database.models import Topic
from database.crud import first_or_default


class TopicService:
    def __init__(self):
        pass

    def get_by(self, session: Session, **filters):
        return first_or_default(session=session, model=Topic, **filters)

    def get_all(self, session):
        return session.query(Topic).all()
