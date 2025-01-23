from sqlalchemy.orm import Session
from database.models import Topic
from database.crud import first_or_default


class TopicService:
    @staticmethod
    def first_or_default(session: Session, **filters):
        return first_or_default(session=session, model=Topic, **filters)
