from typing import ClassVar, Optional, TypeVar
from weakref import ref

from pykinect_azure.k4abt import _k4abt

from azure_kinect.k4a import WAIT_INFINITE, K4ACalibration, K4ACapture, K4ADevice
from azure_kinect.k4abt.config_tracker import DEFAULT_TRACKER_CONFIG, TrackerConfig
from azure_kinect.k4abt.frame_wapper import TrackingFrame
from azure_kinect.transform import Transform
from azure_kinect.util import (
    IdCode,
    IdPool,
    Logger,
    ResultStatus,
    ResultWithStatus,
    WaitResultStatus,
)
from azure_kinect.util.base_wapper import K4AWapper

_TrackerT = TypeVar("_TrackerT", bound="K4ABodyTracker")


class K4ABodyTracker(K4AWapper[Optional[_k4abt.k4abt_tracker_t]]):
    __slots__ = (
        "_tracker_id",
        "_tracker_config",
        "_smoothing_factor",
        "_frame",
        "_bound_device_ref",
        "_transform_matrix",
    )

    _tracker_id: IdCode
    _tracker_config: TrackerConfig
    _smoothing_factor: float

    _frame: Optional[TrackingFrame]
    _bound_device_ref: ref[K4ADevice]
    _device_transform: Transform

    _ID_POOL: ClassVar[IdPool] = IdPool("Body Tracker")

    def __init__(
        self,
        handle: _k4abt.k4abt_tracker_t,
        tracker_config: TrackerConfig,
        bound_device_ref: ref[K4ADevice],
    ) -> None:
        self._handle = handle
        self._tracker_id = next(self._ID_POOL)
        self._tracker_config = tracker_config
        self._smoothing_factor = _k4abt.K4ABT_DEFAULT_TRACKER_SMOOTHING_FACTOR

        self._frame = None
        self._bound_device_ref = bound_device_ref
        self._device_transform = Transform.identity()

    @property
    def tracker_id(self) -> IdCode:
        """The unique identifier for the body tracker."""
        return self._tracker_id

    @property
    def bound_device(self) -> K4ADevice:
        """The device that the body tracker is bound to."""
        device = self._bound_device_ref()

        if device is None:
            raise RuntimeError("The device being tracked has been destroyed. ")

        return device

    @property
    def calibration(self) -> K4ACalibration:
        """The calibration data for the device."""
        return self.bound_device.calibration

    @property
    def tracker_config(self) -> TrackerConfig:
        """The configuration for the body tracker."""
        return self._tracker_config

    @property
    def smoothing_factor(self) -> float:
        """The smoothing factor for temporal smoothing."""
        return self._smoothing_factor

    @property
    def device_transform(self) -> Transform:
        """The transform between current bound device and dom device."""
        return self._device_transform

    @property
    def cached_frame(self) -> TrackingFrame | None:
        return self._frame

    def destroy(self) -> None:
        """Destroy the body tracker."""
        if self.is_valid():
            K4ABodyTracker._ID_POOL.release_id(self.tracker_id)
            _k4abt.k4abt_tracker_destroy(self._handle)
            self._handle = None

    def shutdown(self) -> None:
        """Shutdown the body tracker."""
        _k4abt.k4abt_tracker_shutdown(self._handle)

    @classmethod
    def create(
        cls: type[_TrackerT],
        device: K4ADevice,
        *,
        config: Optional[TrackerConfig] = None,
    ) -> ResultWithStatus[ResultStatus, _TrackerT]:
        """Creates a new instance of the K4ABodyTracker class.

        Args:
            device (K4ADevice): The device to track.

        Returns:
            ResultWithStatus[ResultStatus, _TrackerT]: The result containing the body tracker.
        """
        config = config or DEFAULT_TRACKER_CONFIG
        tracker_handle = _k4abt.k4abt_tracker_t()

        result_status = _k4abt.k4abt_tracker_create(
            device.calibration.handle,
            config.handle,
            tracker_handle,
        )
        result_status = ResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=cls(
                tracker_handle,
                config,
                ref(device),
            ),
        )

    def _enqueue_capture(
        self,
        capture: K4ACapture,
        timeout_in_ms: int,
    ) -> WaitResultStatus:
        result_status = _k4abt.k4abt_tracker_enqueue_capture(
            self._handle,
            capture.handle,
            timeout_in_ms,
        )

        return WaitResultStatus(result_status)

    def enqueue_capture(
        self,
        capture: Optional[K4ACapture] = None,
        timeout_in_ms: int = WAIT_INFINITE,
    ) -> WaitResultStatus:
        """Enqueues a capture for body tracking.

        Args:
            capture (K4ACapture, optional): The capture to enqueue. Defaults
                to get from the bound device.
            timeout_in_ms (int): The timeout in milliseconds.

        Returns:
            WaitResultStatus: The result status of the operation.
        """
        if capture is None:
            status, capture = self.bound_device.get_capture(timeout_in_ms)

            if status == WaitResultStatus.FAILED:
                Logger.error(f"Failed to get capture from device: {self.bound_device}!")
                return status

            if status == WaitResultStatus.TIMEOUT or not capture.has_depth_image:
                return WaitResultStatus.TIMEOUT

        return self._enqueue_capture(capture, timeout_in_ms)

    def _get_frame_handle(
        self,
        timeout_in_ms: int = WAIT_INFINITE,
    ) -> ResultWithStatus[WaitResultStatus, _k4abt.k4abt_frame_t]:
        """Retrieves the handle to the tracking frame.

        Args:
            timeout_in_ms (int, optional): The timeout in milliseconds.

        Returns:
            ResultWithStatus[WaitResultStatus, _k4abt.k4abt_frame_t]:
                The result containing the frame handle.
        """
        frame_handle = _k4abt.k4abt_frame_t()

        if not self.is_valid():
            return ResultWithStatus(
                status=WaitResultStatus.FAILED,
                result=frame_handle,
            )

        result_status = _k4abt.k4abt_tracker_pop_result(
            self._handle,
            frame_handle,
            timeout_in_ms,
        )
        result_status = WaitResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=frame_handle,
        )

    def pop_result(
        self,
        timeout_in_ms: int = WAIT_INFINITE,
    ) -> ResultWithStatus[WaitResultStatus, TrackingFrame]:
        """Pops the tracking frame result.

        Args:
            timeout_in_ms (int): The timeout in milliseconds.

        Returns:
            ResultWithStatus[WaitResultStatus, TrackingFrame]: The result
                containing the tracking frame.
        """
        status, frame_handle = self._get_frame_handle(timeout_in_ms)

        if self._frame is None:
            self._frame = TrackingFrame(
                frame_handle,
                ref(self),
            )
        else:
            self._frame.update_handle(frame_handle)

        return ResultWithStatus(
            status=status,
            result=self._frame,
        )

    def set_device_transform(self, transform: Transform) -> None:
        """Sets the transform between current bound device and dom device.

        Args:
            transform (Transform): The device transform.
        """
        self._device_transform = transform

    def set_temporal_smoothing(self, smoothing_factor: float) -> None:
        """Sets the temporal smoothing factor for the body tracker.

        Args:
            smoothing_factor (float): The smoothing factor.
        """
        if smoothing_factor < 0 or smoothing_factor > 1:
            Logger.warning(
                "Temporal smoothing factor should be in range [0, 1]. "
                + f"Recived: {smoothing_factor}"
            )
            return

        self._smoothing_factor = smoothing_factor
        _k4abt.k4abt_tracker_set_temporal_smoothing(
            self._handle,
            smoothing_factor,
        )

    def __wapper_data__(self) -> dict:
        return {
            "__after_class_name__": self._tracker_id,
            "tracking_device": self.bound_device.serial_number,
        }

    def __del__(self) -> None:
        self.shutdown()
        self.destroy()
