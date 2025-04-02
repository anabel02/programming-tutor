from http import HTTPStatus
from typing import List

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models import Topic
from services.service_result import ServiceResult


class TopicService:
    def __init__(self):
        pass

    def get_by(self, session: Session, **filters):
        return session.query(Topic).filter_by(**filters).first()

    def _get_all(self, session):
        return session.query(Topic).all()

    def get_all(self) -> ServiceResult[List[Topic]]:
        try:
            with SessionLocal() as session:
                topics: List[Topic] = self._get_all(session)
                return ServiceResult.success(topics)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")

    def get(self, **filters) -> ServiceResult[Topic]:
        try:
            with SessionLocal() as session:
                topic: Topic | None = self.get_by(session, **filters)
                if not topic:
                    return ServiceResult.failure("Topic not found", HTTPStatus.NOT_FOUND)
                return ServiceResult.success(topic)
        except Exception as e:
            return ServiceResult.failure(f"Database error: {str(e)}")
