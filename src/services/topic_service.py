from http import HTTPStatus
from typing import List

from sqlalchemy.orm import Session

from database.models import Topic
from services.service_result import ServiceResult


class TopicService:
    def __init__(self, db: Session):
        self.db = db

    def get_by(self, **filters):
        return self.db.query(Topic).filter_by(**filters).first()

    def _get_all(self) -> List[Topic]:
        return self.db.query(Topic).all()

    def get_all(self) -> ServiceResult[List[Topic]]:
        try:
            topics: List[Topic] = self._get_all()
            return ServiceResult.success(topics)
        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)

    def get(self, **filters) -> ServiceResult[Topic]:
        try:
            topic: Topic | None = self.get_by(**filters)
            if not topic:
                return ServiceResult.failure("Topic not found", HTTPStatus.NOT_FOUND)
            return ServiceResult.success(topic)
        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)
