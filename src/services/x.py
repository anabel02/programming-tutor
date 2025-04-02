from functools import wraps
from http import HTTPStatus

from database.database import SessionLocal
from services.service_result import ServiceResult


def with_db_session(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with SessionLocal() as session:
                return func(*args, **kwargs, session=session)
        except Exception as e:
            return ServiceResult.failure(f"Error inesperado: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR)

    return wrapper
