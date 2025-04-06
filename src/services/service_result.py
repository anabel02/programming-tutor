from http import HTTPStatus
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class ServiceResult(Generic[T]):
    def __init__(
            self,
            item: Optional[T] = None,
            message: Optional[str] = None,
            status_code: HTTPStatus = HTTPStatus.OK
    ):
        if item is not None and not (200 <= status_code < 300):
            raise ValueError("Success results should have a 2xx status code.")

        self.item = item
        self.message = message
        self.status_code = status_code

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @classmethod
    def success(cls, item: T, status_code: HTTPStatus = HTTPStatus.OK):
        return cls(item=item, status_code=status_code)

    @classmethod
    def failure(cls, message: str, status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR):
        return cls(message=message, status_code=status_code)
