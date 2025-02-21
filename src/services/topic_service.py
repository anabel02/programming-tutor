from sqlalchemy.orm import Session
from database.models import Topic
from database.crud import first_or_default
from services.service_result import ServiceResult
from database.database import SessionLocal
from typing import List
from http import HTTPStatus


class TopicService:
    def __init__(self):
        pass

    def get_by(self, session: Session, **filters):
        return first_or_default(session=session, model=Topic, **filters)

    def _get_all(self, session):
        return session.query(Topic).all()

    def get_all(self) -> ServiceResult[List[Topic]]:
        try:
            with SessionLocal() as session:
                topics: List[Topic] = self._get_all(session)
                return ServiceResult.success(topics)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")

    def get(self, **filters) -> ServiceResult[List[Topic]]:
        try:
            with SessionLocal() as session:
                topic: Topic = self.get_by(session, **filters)
                if not topic:
                    return ServiceResult.failure("Topic not found", HTTPStatus.NOT_FOUND)
                return ServiceResult.success(topic)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")
