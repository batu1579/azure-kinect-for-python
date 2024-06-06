from enum import Enum
from typing import Generic, TypeVar

from pykinect_azure.k4a import _k4a
from typing_extensions import NamedTuple


class ResultStatus(int, Enum):
    FAILED = _k4a.K4A_RESULT_FAILED
    SUCCEEDED = _k4a.K4A_RESULT_SUCCEEDED


class WaitResultStatus(int, Enum):
    SUCCEEDED = _k4a.K4A_WAIT_RESULT_SUCCEEDED
    FAILED = _k4a.K4A_WAIT_RESULT_FAILED
    TIMEOUT = _k4a.K4A_WAIT_RESULT_TIMEOUT


class BufferResultStatus(int, Enum):
    FAILED = _k4a.K4A_BUFFER_RESULT_FAILED
    SUCCEEDED = _k4a.K4A_BUFFER_RESULT_SUCCEEDED
    TOO_SMALL = _k4a.K4A_BUFFER_RESULT_TOO_SMALL


_ResultT = TypeVar("_ResultT")
_ResultStatusT = TypeVar(
    "_ResultStatusT",
    ResultStatus,
    WaitResultStatus,
    BufferResultStatus,
)


class ResultWithStatus(NamedTuple, Generic[_ResultStatusT, _ResultT]):
    status: _ResultStatusT
    result: _ResultT

    def get_verified_result(
        self,
        _error_info: str = "Get operation result failed.",
    ) -> _ResultT:
        """
        Verifies the status of the operation and returns the result if successful.

        Args:
            _error_info: A custom error message to raise if the operation failed.

        Returns:
            The result of the operation if the status is SUCCEEDED.

        Raises:
            ValueError: If the status of the operation is not SUCCEEDED.
        """
        if self.status == ResultStatus.FAILED:
            raise ValueError(_error_info)

        return self.result

    def get_result_on_succeeded(self) -> _ResultT | None:
        """Returns the result if the status is SUCCEEDED, otherwise None."""
        return self.result if self.status == ResultStatus.SUCCEEDED else None
