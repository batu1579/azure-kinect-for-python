from ctypes import c_bool, c_int32, c_size_t, create_string_buffer
from enum import Enum
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Optional, cast

from pykinect_azure.k4a import _k4a

from azure_kinect.k4a import (
    DEFAULT_CONFIG,
    WAIT_INFINITE,
    ColorControlCapabilities,
    ColorControlCommand,
    ColorControlConfig,
    ColorControlConfigsType,
    ColorControlMode,
    ColorResolution,
    DepthMode,
    DeviceConfig,
    HardwareVersion,
    K4ACalibration,
    K4ACapture,
    SyncJackStatus,
    WiredSyncMode,
)
from azure_kinect.k4a.config_color_control import (
    DefaultColorControl,
    DefaultColorControlConfig,
)
from azure_kinect.k4a_record import K4ARecord
from azure_kinect.util import Logger, ResultStatus, ResultWithStatus, WaitResultStatus
from azure_kinect.util.base_wapper import K4AWapper


class DeviceStatus(str, Enum):
    CLOSED = "Closed"
    OPENED = "Opened"
    STARTED = "Started"


# TODO(batu1579): Load this from env
OPEN_DEVICE_RETRY_TIMES = 3


class K4ADevice(K4AWapper[Optional[_k4a.k4a_device_t]]):
    __slots__ = (
        "_index",
        "_status",
        "_default_color_control",
        "_record",
        "_capture",
        "_calibration",
        "_device_config",
        "_delay_off_master_usec",
    )

    _index: int
    _status: DeviceStatus
    _default_color_control: DefaultColorControl

    _record: Optional[K4ARecord]
    _capture: Optional[K4ACapture]
    _calibration: K4ACalibration
    _device_config: DeviceConfig
    _delay_off_master_usec: int

    def __init__(self, index: int = 0) -> None:
        self._index = index
        self._status = DeviceStatus.OPENED
        self._handle = self._get_device_handle()

        original_color_control = self._get_original_color_control()
        assert original_color_control is not None

        self._default_color_control = original_color_control

        self._record = None
        self._capture = None
        self._device_config = DEFAULT_CONFIG
        self._delay_off_master_usec = 0

        self._update_calibration()

    @property
    def index(self) -> int:
        """The index of the device."""
        return self._index

    @property
    def status(self) -> DeviceStatus:
        """The status of the device, including:

        - Off
        - Opened
        - Started

        Returns:
            DeviceStatus: device status
        """
        return self._status

    @property
    def default_color_control(self) -> DefaultColorControl:
        """The default color control configuration, and its capabilities
        of all commands. All commands including:

        - exposure_time_absolute
        - brightness
        - contrast
        - saturation
        - sharpness
        - white_balance
        - backlight_compensation
        - gain
        - powerline_frequency

        Returns:
            DefaultColorControl: default color control configuration
        """
        return self._default_color_control

    @property
    def record(self) -> K4ARecord | None:
        """Get the record of the device."""
        return self._record

    @property
    def calibration(self) -> K4ACalibration:
        """Get the calibration data."""
        return self._calibration

    @property
    def device_config(self) -> DeviceConfig:
        """Get the device configuration."""
        return self._device_config

    @property
    def delay_off_master_usec(self) -> int:
        """The delay off master device usec."""
        return self._delay_off_master_usec

    @cached_property
    def hardware_version(self) -> HardwareVersion:
        """Get the hardware version of the device."""
        _version = _k4a.k4a_hardware_version_t()
        result_status = _k4a.k4a_device_get_version(self._handle, _version)
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Get hardware version failed!")

        return HardwareVersion(
            audio=HardwareVersion.to_version_str(_version.audio),
            depth=HardwareVersion.to_version_str(_version.depth),
            rgb=HardwareVersion.to_version_str(_version.rgb),
            depth_sensor=HardwareVersion.to_version_str(_version.depth_sensor),
        )

    @cached_property
    def serial_number(self) -> str:
        """Get the serial number of the device."""
        serial_number_size = c_size_t()
        _k4a.k4a_device_get_serialnum(self._handle, None, serial_number_size)
        serial_number = create_string_buffer(serial_number_size.value)
        result_status = _k4a.k4a_device_get_serialnum(
            self._handle,
            serial_number,
            serial_number_size,
        )
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Get serial number failed!")

        return cast(bytes, serial_number.value).decode("utf-8")

    @property
    def sync_jack_status(self) -> SyncJackStatus:
        """Get the status of the sync in and out jack on the device.

        Returns:
            A dictionary containing the status of the sync jack, including
            whether the sync in jack is connected and whether the sync out jack
            is connected.
        """
        _in, _out = c_bool(False), c_bool(False)
        result_status = _k4a.k4a_device_get_sync_jack(self._handle, _in, _out)
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Get sync jack status failed!")

        return SyncJackStatus(
            sync_in_jack_connected=_in.value,
            sync_out_jack_connected=_out.value,
        )

    @cached_property
    def is_dom(self) -> bool:
        """Is the device a dom device.

        Returns:
            bool: Return True if the device is a dom device, otherwise False.
        """
        devices_count = int(_k4a.k4a_device_get_installed_count())

        if devices_count == 1:
            return True

        return self.sync_jack_status == SyncJackStatus(False, True)

    def _get_device_handle(self) -> _k4a.k4a_device_t:
        for retry_times in range(OPEN_DEVICE_RETRY_TIMES):
            status, _device_handle = K4ADevice._open(self._index)

            if status == ResultStatus.SUCCEEDED:
                Logger.debug(f"Open device {self._index} succeeded!")
                return _device_handle

            Logger.debug(
                f"Open device {self._index} failed! Retry times: {retry_times}"
            )

        raise RuntimeError(f"Open device {self._index} failed!")

    def _get_calibration_handle(
        self,
    ) -> ResultWithStatus[ResultStatus, _k4a.k4a_calibration_t]:
        """Retrieves calibration data.

        When the configuration is modified, calibration will be updated
        automatically.

        Returns:
            ResultWithStatus[ResultStatus, _k4a.k4a_calibration_t]: The
            calibration data.
        """
        calibration_handle = _k4a.k4a_calibration_t()

        if not self.is_valid():
            return ResultWithStatus(
                status=ResultStatus.FAILED,
                result=calibration_handle,
            )

        result_status = _k4a.k4a_device_get_calibration(
            self._handle,
            DepthMode.get_mapped_value(self.device_config.depth_mode),
            ColorResolution.get_mapped_value(self.device_config.color_resolution),
            calibration_handle,
        )
        result_status = ResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=calibration_handle,
        )

    def _update_calibration(self) -> None:
        if not self.is_valid():
            return

        calibration_handle = self._get_calibration_handle().get_verified_result(
            "Get calibration failed!"
        )
        self._calibration = K4ACalibration(calibration_handle)

    def _get_capture_handle(
        self,
        timeout_in_ms: int = WAIT_INFINITE,
    ) -> ResultWithStatus[WaitResultStatus, _k4a.k4a_capture_t]:
        """Capture image from the device within a specified timeout.

        Args:
            timeout_in_ms (int, optional): The time to wait for a
                capture in milliseconds. Defaults to WAIT_INFINITE,
                which waits indefinitely.

        Returns:
            ResultWithStatus[WaitResultStatus, _k4a.k4a_capture_t]: The capture
                result, including status and the capture handle.
        """
        capture_handle = _k4a.k4a_capture_t()

        if not self.is_valid():
            return ResultWithStatus(
                status=WaitResultStatus.FAILED,
                result=capture_handle,
            )

        result_status = _k4a.k4a_device_get_capture(
            self._handle,
            capture_handle,
            timeout_in_ms,
        )
        result_status = WaitResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=capture_handle,
        )

    def get_capture(
        self,
        timeout_in_ms: int = WAIT_INFINITE,
    ) -> ResultWithStatus[WaitResultStatus, K4ACapture]:
        """Get capture images."""
        status, capture_handle = self._get_capture_handle(timeout_in_ms)

        if self._capture is None:
            self._capture = K4ACapture(
                capture_handle,
                self._calibration,
            )
        else:
            self._capture.update_handle(capture_handle)

        if (
            self._record is not None
            and self._record.is_recording
            and status == WaitResultStatus.SUCCEEDED
        ):
            self._record.write_capture(capture_handle)

        return ResultWithStatus(
            status=status,
            result=self._capture,
        )

    def get_imu_sample(
        self,
        timeout_in_ms: int = WAIT_INFINITE,
    ) -> ResultWithStatus[WaitResultStatus, _k4a.k4a_imu_sample_t]:
        """Retrieve an IMU sample from the device within a specified timeout.

        Args:
            timeout_in_ms (int, optional): The time to wait for an
                IMU sample in milliseconds. Defaults to WAIT_INFINITE,
                which waits indefinitely.

        Returns:
            ResultWithStatus[WaitResultStatus, _k4a.k4a_imu_sample_t]: The IMU
                sample result, including status and the IMU sample data.
        """
        # TODO(batu1579): Write imu wapper
        imu_sample = _k4a.k4a_imu_sample_t()

        if not self.is_valid():
            return ResultWithStatus(
                status=WaitResultStatus.FAILED,
                result=imu_sample,
            )

        result_status = _k4a.k4a_device_get_imu_sample(
            self._handle,
            imu_sample,
            timeout_in_ms,
        )
        result_status = WaitResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=imu_sample,
        )

    def _start_imu(self) -> ResultStatus:
        """Start the IMU sensors on the device.

        Returns:
            ResultStatus: The status of the operation, indicating success or
                failure.
        """
        if not self.is_valid():
            return ResultStatus.FAILED

        result_status = _k4a.k4a_device_start_imu(self._handle)
        return ResultStatus(result_status)

    def _stop_imu(self) -> None:
        """Stop the IMU sensors on the device."""
        if self.is_valid():
            _k4a.k4a_device_stop_imu(self._handle)

    def _start_cameras(self) -> ResultStatus:
        """Start the cameras on the device with the specified configuration.

        Returns:
            ResultStatus: The status of the operation, indicating success or
                failure.
        """
        if not self.is_valid():
            return ResultStatus.FAILED

        # Check the white_balance configuration
        white_balance_config = self.get_color_control(ColorControlCommand.WHITE_BALANCE)
        assert white_balance_config is not None

        if (
            self.device_config.wired_sync_mode != WiredSyncMode.STANDALONE
            and white_balance_config.mode != ColorControlMode.MANUAL
        ):
            Logger.warning(
                "In external synchronization mode, "
                + "you are advised to manually set the white balance. "
                + "Otherwise, it is easy to lose synchronization quickly"
            )
            # TODO(batu1579): maybe to set the white balance automatically?

        # Try to start the cameras
        result_status = _k4a.k4a_device_start_cameras(
            self._handle,
            self._device_config.handle,
        )

        return ResultStatus(result_status)

    def _stop_cameras(self) -> None:
        """Stop the cameras on the device."""
        if self.is_valid():
            _k4a.k4a_device_stop_cameras(self._handle)

    @lru_cache(maxsize=10)
    def get_color_control_capabilities(
        self,
        command: ColorControlCommand,
    ) -> ColorControlCapabilities | None:
        """Get color control capabilities for the specified command.

        Args:
            command (ColorControlCommand): The command to get the capabilities
                for.

        Returns:
            ColorControlCapabilities | None: Capabilities of the specified command.
        """
        if not self.is_valid():
            return None

        _supports_auto = c_bool()
        _min_value, _max_value, _step_value, _default_value = (
            c_int32(),
            c_int32(),
            c_int32(),
            c_int32(),
        )
        _default_mode = _k4a.k4a_color_control_mode_t()
        _command_value = ColorControlCommand.get_mapped_value(command)
        result_status = _k4a.k4a_device_get_color_control_capabilities(
            self._handle,
            _command_value,
            _supports_auto,
            _min_value,
            _max_value,
            _step_value,
            _default_value,
            _default_mode,
        )
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Get color control capabilities failed!")

        return ColorControlCapabilities(
            _supports_auto.value,
            _min_value.value,
            _max_value.value,
            _step_value.value,
            ColorControlMode.get_enum_by_mapped_value(_default_mode.value),
            _default_value.value,
        )

    def get_color_control(
        self,
        command: ColorControlCommand,
    ) -> ColorControlConfig | None:
        """Get the color control configuration for the specified command.

        Args:
            command (ColorControlCommand): The command to get the config for.

        Returns:
            ColorControlConfig | None: The color control configuration for the
                specified command.
        """
        if not self.is_valid():
            return None

        _mode = _k4a.k4a_color_control_mode_t()
        _value = c_int32()
        _command_value = ColorControlCommand.get_mapped_value(command)

        result_status = _k4a.k4a_device_get_color_control(
            self._handle,
            _command_value,
            _mode,
            _value,
        )
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Get color control failed!")

        return ColorControlConfig(
            command,
            _value.value,
            ColorControlMode.get_enum_by_mapped_value(_mode.value),
        )

    def _get_original_color_control(self) -> DefaultColorControl | None:
        """Get color control configuration for all commands before device startup.

        Returns:
            DefaultColorControl | None: The color control configuration before
                device startup.
        """
        if not self.is_valid():
            return None

        result: list[DefaultColorControlConfig] = []

        for command in ColorControlCommand:
            color_control = self.get_color_control(command)
            color_control_capabilities = self.get_color_control_capabilities(
                command,
            )

            assert color_control is not None
            assert color_control_capabilities is not None

            result.append(
                DefaultColorControlConfig(
                    color_control.command,
                    color_control.value,
                    color_control.mode,
                    color_control_capabilities,
                )
            )

        # pylint: disable=no-value-for-parameter
        return DefaultColorControl(*result)

    def set_color_control(
        self,
        config: ColorControlConfig,
    ) -> None:
        """Set the color control configuration for the specified command.

        Args:
            config (ColorControlConfig): The color control configuration
                for the specified command.
        """
        if not self.is_valid():
            Logger.warning("Device is closed! Cannot set color control!")
            return None

        _command_value = ColorControlCommand.get_mapped_value(config.command)
        _mode_value = ColorControlMode.get_mapped_value(config.mode)

        result_status = _k4a.k4a_device_set_color_control(
            self._handle,
            _command_value,
            _mode_value,
            config.value,
        )
        result_status = ResultStatus(result_status)

        if result_status == ResultStatus.FAILED:
            raise RuntimeError("Set color control failed!")

        return None

    def set_color_control_of_commands(
        self,
        color_control_config: ColorControlConfigsType,
    ) -> None:
        """Set multiple color control configuration at once

        Args:
            color_control_config (ColorControlConfigsType): all color control
                configurations to set.
        """
        for config in color_control_config:
            self.set_color_control(config)

    def set_device_config(self, device_config: DeviceConfig) -> None:
        """Setting the device configuration to replace the current one.

        Args:
            device_config (DeviceConfig): new device configuration.
        """
        if device_config == self._device_config:
            return

        self._device_config = device_config
        self._update_calibration()

        if self._status == DeviceStatus.STARTED:
            self.re_open()
            self.start()

    def assign_delay(self, delay_usec: int) -> None:
        """Assigns the delay usec of the current device to the master device.

        Args:
            delay_usec (int): delay in microseconds.
        """
        if delay_usec < 0:
            raise ValueError("delay_usec must be non-negative")

        self._delay_off_master_usec = delay_usec

    def close(self) -> None:
        """Restore the color control configuration before close the device"""
        if self._status == DeviceStatus.CLOSED:
            return

        self._stop_imu()
        self._stop_cameras()
        self.set_color_control_of_commands(self._default_color_control)
        _k4a.k4a_device_close(self._handle)
        self._status = DeviceStatus.CLOSED

        # Clear members
        self._handle = None
        self._record = None
        self._capture = None

        Logger.debug(f"Device {self._index} closed.")

    @staticmethod
    def _open(index: int) -> ResultWithStatus[ResultStatus, _k4a.k4a_device_t]:
        """Open the device with the specified index.

        Args:
            index (int): device index.

        Returns:
            ResultWithStatus[ResultStatus, _k4a.k4a_device_t]: Operation result.
        """
        device_handle = _k4a.k4a_device_t()

        try:
            result_status = _k4a.k4a_device_open(index, device_handle)
            result_status = ResultStatus(result_status)
        except Exception as error:
            Logger.error(f"Open device {index} failed! {error}")
            return ResultWithStatus(
                status=ResultStatus.FAILED,
                result=device_handle,
            )

        return ResultWithStatus(
            status=result_status,
            result=device_handle,
        )

    def re_open(self) -> None:
        """Restart device after device close"""
        if self._status != DeviceStatus.CLOSED:
            self.close()

        self._handle = self._get_device_handle()
        self._status = DeviceStatus.OPENED

    def start(self, record_path: Optional[Path] = None) -> None:
        """Start device with specified configurations.

        Args:
            record_config (Optional[Path], optional): Record file path.
                Defaults to None.
        """
        if not self.is_valid():
            raise RuntimeError(
                "Start device failed! Device handle is invalid!",
            )

        assert self._handle is not None

        if self._status == DeviceStatus.STARTED:
            return

        if self._status == DeviceStatus.CLOSED:
            self.re_open()

        self._device_config = self._device_config
        self._device_config.subordinate_delay_off_master_usec = (
            self._delay_off_master_usec
        )

        if self._start_cameras() == ResultStatus.FAILED:
            raise RuntimeError("Start cameras failed!")

        if self._start_imu() == ResultStatus.FAILED:
            raise RuntimeError("Start imu failed!")

        if record_path is not None:
            self._record = K4ARecord(
                record_path,
                self._handle,
                self._device_config.handle,
            )

        self._status = DeviceStatus.STARTED

        Logger.debug(f"Device {self._index} started.")

    def __wapper_data__(self) -> dict:
        return {
            "__after_class_name__": self._index,
            "serial_number": self.serial_number,
            "status": self._status.name,
        }

    def __del__(self) -> None:
        self.close()
