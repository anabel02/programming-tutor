from typing import Generic, TypeVar, Optional
from http import HTTPStatus

T = TypeVar("T")


class ServiceResult(Generic[T]):
    def __init__(
        self,
        is_success: bool,
        item: Optional[T] = None,
        error_message: Optional[str] = None,
        error_code: Optional[HTTPStatus] = None
    ):
        self.is_success = is_success
        self.item = item
        self.error_message = error_message
        self.error_code = error_code

    @classmethod
    def success(cls, item: T):
        return cls(is_success=True, item=item)

    @classmethod
    def failure(cls, error_message: str, error_code: Optional[HTTPStatus] = HTTPStatus.INTERNAL_SERVER_ERROR):
        return cls(is_success=False, error_message=error_message, error_code=error_code)
