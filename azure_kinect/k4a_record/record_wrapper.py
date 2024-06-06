from pathlib import Path
from typing import Optional

from pykinect_azure.k4a import _k4a
from pykinect_azure.k4arecord import _k4arecord

from azure_kinect.util import Logger, ResultStatus
from azure_kinect.util.base_wapper import K4AWapper


class K4ARecord(K4AWapper[Optional[_k4arecord.k4a_record_t]]):
    __slots__ = (
        "_record_path",
        "_is_recording",
        "_is_header_written",
    )

    _record_path: Path
    _is_recording: bool
    _is_header_written: bool

    def __init__(
        self,
        record_path: Path,
        device_handle: _k4a.k4a_device_t,
        device_config_handle: _k4a.k4a_device_configuration_t,
    ) -> None:
        if record_path.is_file():
            raise FileExistsError(
                f"Record file {record_path} already exists!",
            )

        if not record_path.parent.is_dir():
            raise NotADirectoryError(
                f"Record path {record_path.parent} is not exists!",
            )

        self._handle = None
        self._record_path = record_path
        self._is_recording = False
        self._is_header_written = False

        self._start_recording(device_handle, device_config_handle)

    @property
    def is_recording(self) -> bool:
        """Whether the recorder is currently recording."""
        return self._is_recording

    @property
    def record_path(self) -> Path:
        """The path of the recording file."""
        return self._record_path

    @property
    def is_header_written(self):
        """Whether the header has been written."""
        return self._is_header_written

    def _start_recording(
        self,
        device_handle: _k4a.k4a_device_t,
        device_config_handle: _k4a.k4a_device_configuration_t,
    ) -> None:
        record_handle = _k4arecord.k4a_record_t()
        result_status = _k4arecord.k4a_record_create(
            str(self._record_path.absolute()),
            device_handle,
            device_config_handle,
            record_handle,
        )
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Failed to create recording!")

        self._is_recording = True
        self._handle = record_handle

        Logger.debug("Successfully created recording!")

    def close(self) -> None:
        """Closes the recording and releases any associated resources."""
        if not self.is_valid() or not self._is_recording:
            return

        _k4arecord.k4a_record_close(self._handle)

        self._handle = None
        self._is_recording = False

        Logger.debug("Successfully closed recording!")

    def flush(self) -> ResultStatus:
        """Flushes all pending data to the recording.

        Returns:
            The status of the operation.
        """
        if not self.is_valid() or not self._is_recording:
            return ResultStatus.FAILED

        result_status = _k4arecord.k4a_record_flush(self._handle)
        result_status = ResultStatus(result_status)

        return result_status

    def _write_header(self) -> None:
        """Writes the header information to the recording.

        Raises:
            RuntimeError: If the header could not be written.
        """
        if not self.is_valid() or not self._is_recording:
            return

        result_status = _k4arecord.k4a_record_write_header(self._handle)
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Failed to write header!")

        self._is_header_written = True
        Logger.debug("Successfully wrote header!")

    def write_capture(self, capture_handle) -> ResultStatus:
        """Writes a capture to the recording.

        Args:
            capture_handle: The handle to the capture to write.

        Returns:
            The status of the operation.

        Raises:
            RuntimeError: If unable to write capture when not recording.
        """
        if not self.is_valid() or not self.is_recording:
            raise RuntimeError("Unable to write capture when not recording.")

        if not self._is_header_written:
            self._write_header()

        result_status = _k4arecord.k4a_record_write_capture(
            self._handle,
            capture_handle,
        )
        result_status = ResultStatus(result_status)

        return result_status

    def __wapper_data__(self) -> dict:
        return {
            "is_recording": self.is_recording,
            "is_header_written": self._is_header_written,
            "record_path": self._record_path,
        }

    def __del__(self) -> None:
        self.close()
