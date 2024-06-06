from collections import Counter
from itertools import count
from json import dumps
from typing import Iterator, Optional

from pykinect_azure.k4a import _k4a
from simple_singleton import singleton

from azure_kinect.k4a.config_color_control import SceneColorControlConfig
from azure_kinect.k4a.config_device import DEFAULT_CONFIG, DeviceConfig, WiredSyncMode
from azure_kinect.k4a.device_info import SyncJackStatus
from azure_kinect.k4a.device_wrapper import DeviceStatus, K4ADevice
from azure_kinect.k4a_record.config_record import RecordConfig
from azure_kinect.util import Logger

# TODO(batu1579): Use env variable to change this value.
OFFSET = 160
MAX_OFFSET = OFFSET * 9


@singleton(thread_safe=True, allow_subclass=True)
class DeviceManager:
    __slots__ = (
        "_devices",
        "_dom_device_index",
        "_device_config",
        "_record_config",
        "_serial_number_map",
        "_single_deivce_mode",
    )

    _devices: list[K4ADevice]
    _dom_device_index: int
    _device_config: DeviceConfig
    _record_config: Optional[RecordConfig]
    _serial_number_map: dict[str, int]
    _single_deivce_mode: bool

    def __init__(
        self,
        device_config: Optional[DeviceConfig] = None,
        record_config: Optional[RecordConfig] = None,
    ):
        self._devices = []
        self._dom_device_index = -1
        self._device_config = device_config or DEFAULT_CONFIG
        self._record_config = record_config
        self._serial_number_map = {}
        self._single_deivce_mode = False

        self.reload_devices()

    @property
    def device_configuration(self) -> DeviceConfig:
        """The base configuration for all devices."""
        return self._device_config

    @device_configuration.setter
    def device_configuration(self, value: DeviceConfig) -> None:
        if any(device.status == DeviceStatus.STARTED for device in self._devices):
            self.reload_devices()

        self._device_config = value

    @property
    def record_configuration(self) -> Optional[RecordConfig]:
        """The configuration of record.
        This property provides access to the record configuration.
        None may be returned if the record configuration is not set.
        """
        return self._record_config

    @record_configuration.setter
    def record_configuration(self, value: RecordConfig) -> None:
        if any(device.status == DeviceStatus.STARTED for device in self._devices):
            self.reload_devices()

        self._record_config = value

    @property
    def devices_count(self) -> int:
        """The number of Kinect devices installed."""
        return len(self._devices)

    @property
    def dom_device(self) -> K4ADevice:
        """The dom device of the device manager."""
        if self._dom_device_index == -1:
            index = self._get_dom_device_index()

            if index == -1:
                raise RuntimeError("No dom device found!")

            self._dom_device_index = index

        return self._devices[self._dom_device_index]

    @property
    def sub_devices(self) -> Iterator[K4ADevice]:
        """The sub devices of the device manager."""
        if self._single_deivce_mode:
            return

        for index, device in enumerate(self._devices):
            if index != self._dom_device_index:
                yield device

    @property
    def is_all_hardware_version_same(self) -> bool:
        """The hardware versions of all devices are consistent

        Returns:
            bool: True if the versions are consistent, False otherwise.
        """
        if self._single_deivce_mode:
            return True

        return all(
            # TODO(batu1579): Check the hardware version without dom_device.
            device.hardware_version == self.dom_device.hardware_version
            for device in self.sub_devices
        )

    @property
    def is_all_sync_cable_correct(self) -> bool:
        """Check whether all devices are properly synchronized

        Returns:
            bool: True is all devices are properly synchronized, False otherwise.
        """
        if self._single_deivce_mode:
            return True

        devices_jack_status = Counter(
            [device.sync_jack_status for device in self._devices]
        )

        return (
            devices_jack_status.total() in [2, 3]
            and devices_jack_status.get(SyncJackStatus(True, False)) == 1
            and devices_jack_status.get(SyncJackStatus(False, True)) == 1
        )

    @property
    def is_single_device_mode(self) -> bool:
        return self._single_deivce_mode

    @classmethod
    def get_installed_count(cls) -> int:
        """Check the number of connected devices

        Returns:
            int: Returns the number of currently connected devices
        """
        return int(_k4a.k4a_device_get_installed_count())

    def _get_dom_device_index(self) -> int:
        if self._single_deivce_mode:
            return 0

        for index, device in enumerate(self._devices):
            if device.is_dom:
                return index

        return -1

    def get_iterator(
        self,
        *,
        start_with_dom: bool = True,
    ) -> Iterator[K4ADevice]:
        """Iterates over devices in a specific order.

        Args:
            start_with_dom (bool): If True, starts iteration with the dominant
                device. If False, ends iteration with the dominant device.
                Defaults to True

        Yields:
            K4ADevice: The next device in the iteration.
        """
        if start_with_dom:
            yield self.dom_device

        yield from self.sub_devices

        if not start_with_dom:
            yield self.dom_device

    def get_device_by_index(self, index: int) -> K4ADevice | None:
        """Get a device by its index

        Args:
            index (int): device index

        Returns:
            K4ADevice | None: Device object or None if the index is out of range.
        """
        if index < 0 or index >= self.devices_count:
            return None

        return self._devices[index]

    def get_device_by_serial_number(self, serial_number: str) -> K4ADevice | None:
        """Get a device by its serial number

        Args:
            serial_number (str): device serial number

        Returns:
            K4ADevice | None: Device object or None if the index is out of range.
        """
        index = self._serial_number_map.get(serial_number)
        return None if index is None else self._devices[index]

    def _check_hardware_version(self) -> None:
        if not self.is_all_hardware_version_same:
            devices_hardware_version = [
                {
                    "serial_number": device.serial_number,
                    "hardware_version": device.hardware_version,
                }
                for device in self._devices
            ]
            version_str = dumps(devices_hardware_version, indent=4)

            Logger.warning(
                "Devices hardware version are not the same! "
                + "Unexpected errors may occur! "
                + f"Devices hardware version: {version_str}"
            )
            return

        Logger.debug("The hardware version of all devices are consistent")

    def _check_sync_cable(self) -> None:
        if not self.is_all_sync_cable_correct:
            raise RuntimeError("The synchronization cable is incorrectly connected")

        Logger.info("All devices are correctly connected")

    def _set_delay_off_master_usec(self) -> None:
        """Set all sub device delay off master usec

        See:
            https://learn.microsoft.com/zh-cn/azure/kinect-dk/multi-camera-sync?source=recommendations#avoiding-interference-between-multiple-depth-cameras
        """
        if self._single_deivce_mode:
            return

        for device, delay in zip(self.sub_devices, count(OFFSET, OFFSET)):
            device.assign_delay(delay)
            Logger.debug(f"Delay of Device {device.index} is set to {delay} usec")

        Logger.info("Delay has been assigned to all sub devices")

    def set_all_devices_color_control(
        self,
        scene: SceneColorControlConfig,
    ) -> None:
        """Set color controls for all devices to the scene default

        Args:
            scene_config (SceneColorControlConfig): All devices color
                control config for a specified scene.
        """
        Logger.debug(
            f"Setting all device color control config to Scene: {scene.scene_name}"
        )
        _scene_config = scene.device_color_control_configs

        for device in self._devices:
            _device_configs = _scene_config.get(device.serial_number)

            if _device_configs is None:
                Logger.debug(
                    "No configs found in this scene, "
                    + "Skip setting color control for device: "
                    + device.serial_number
                )
                return

            device.set_color_control_of_commands(_device_configs)

    def _start_device(self, device: K4ADevice) -> None:
        """Start the specified device, with record config.

        Args:
            device (K4ADevice): Device to be started.
        """
        config = self._device_config

        if self._single_deivce_mode:
            device_tag = "Single"
            config.wired_sync_mode = WiredSyncMode.STANDALONE
        else:
            if device.is_dom:
                device_tag = "Dom"
                config.wired_sync_mode = WiredSyncMode.MASTER
            else:
                device_tag = "Sub"
                config.wired_sync_mode = WiredSyncMode.SUBORDINATE

        device.set_device_config(config)

        Logger.debug(f"Starting device: {device.serial_number}")

        if self._record_config is None:
            device.start()
            return

        file_suffix = f"index-{device.index}-{device_tag}"
        file_path = self._record_config.get_filepath(suffix=file_suffix)
        file_path = file_path.absolute()

        Logger.debug(f"Recording device: to {file_path}")

        device.start(record_path=file_path)

    def start_all_devices(
        self,
        device_config: Optional[DeviceConfig] = None,
        record_config: Optional[RecordConfig] = None,
        scene_config: Optional[SceneColorControlConfig] = None,
    ) -> None:
        """
        Start all sub devices in order of device index, and finally start
            the master device.

        Args:
            device_config (Optional[DeviceConfig]): The device configuration.
                Defaults to None.
            record_config (Optional[RecordConfiguration]): The record
                configuration. Defaults to None.
            scene_config (Optional[SceneColorControlConfig]): All devices color
                control config for a specified scene. Defaults to None.
        """
        if device_config is not None:
            self._device_config = device_config

        if record_config is not None:
            self._record_config = record_config

        if scene_config is not None:
            # Set color control before starting the device
            # To keep all image in the same config
            self.set_all_devices_color_control(scene_config)

        for device in self.get_iterator(start_with_dom=False):
            self._start_device(device)

        Logger.info("All devices are started")

    def close_all_devices(self) -> None:
        """
        Close all sub devices in order of device index, and finally close
            the master device.
        """
        for device in self.get_iterator(start_with_dom=False):
            Logger.debug(f"Closing device: {device.serial_number}")
            device.close()

        Logger.info("All devices are closed")

    def reopen_all_devices(self) -> None:
        """Reopen all sub devices in order of device index, and finally reopen
        the master device.
        """
        for device in self.get_iterator(start_with_dom=False):
            Logger.debug(f"Being reprepared device: {device.serial_number}")
            device.re_open()

    def reload_devices(self) -> None:
        """Safely reload all devices."""
        self._dom_device_index = -1
        self._serial_number_map = {}

        if self.devices_count > 0:
            self._devices = []

        # Load for new
        devices_count = DeviceManager.get_installed_count()

        if devices_count == 0:
            raise RuntimeError("There is no Kinect device installed!")

        if devices_count == 1:
            self._single_deivce_mode = True
            Logger.info("Single device mode activated")

        if devices_count > 9:
            raise RuntimeError(
                "Supports connecting up to 9 devices, "
                + f"currently {devices_count} devices are connected."
                + f"At least {devices_count - 9} devices need to be removed."
            )

        Logger.info(f"Detected number of connected devices: {devices_count}")

        for index in range(devices_count):
            self._devices.append(device := K4ADevice(index))
            self._serial_number_map.update({device.serial_number: index})

        if not self._single_deivce_mode:
            self._check_hardware_version()
            self._check_sync_cable()
            self._set_delay_off_master_usec()

    def __del__(self) -> None:
        self.close_all_devices()
