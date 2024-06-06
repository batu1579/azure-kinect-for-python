from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from adaptix import Retort, enum_by_name
from pykinect_azure.k4a import _k4a

from azure_kinect.util import EnumExtend
from azure_kinect.util.serializable_data import ConfigWapper


class DepthMode(EnumExtend[int], str, Enum):
    """Depth camera mode

    See:
        https://learn.microsoft.com/zh-cn/azure/kinect-dk/hardware-specification#depth-camera-supported-operating-modes
    """

    OFF = "Turn Off depth camera"
    NFOV_2X2BINNED = "Narrow Field of View with 2x2 pixel binning"
    NFOV_UNBINNED = "Narrow Field of View without pixel binning"
    WFOV_2X2BINNED = "Wide Field of View with 2x2 pixel binning"
    WFOV_UNBINNED = "Wide Field of View without pixel binning"
    PASSIVE_IR = "Passive Infrared mode"

    @classmethod
    def _get_value_map(cls: type["DepthMode"]) -> dict["DepthMode", int]:
        return {
            DepthMode.OFF: _k4a.K4A_DEPTH_MODE_OFF,
            DepthMode.NFOV_2X2BINNED: _k4a.K4A_DEPTH_MODE_NFOV_2X2BINNED,
            DepthMode.NFOV_UNBINNED: _k4a.K4A_DEPTH_MODE_NFOV_UNBINNED,
            DepthMode.WFOV_2X2BINNED: _k4a.K4A_DEPTH_MODE_WFOV_2X2BINNED,
            DepthMode.WFOV_UNBINNED: _k4a.K4A_DEPTH_MODE_WFOV_UNBINNED,
            DepthMode.PASSIVE_IR: _k4a.K4A_DEPTH_MODE_PASSIVE_IR,
        }


class ColorResolution(EnumExtend[int], str, Enum):
    """Color camera resolution

    See:
        https://learn.microsoft.com/zh-cn/azure/kinect-dk/hardware-specification#color-camera-supported-operating-modes
    """

    OFF = "Turn Off color camera"
    CR_720P = "1280 * 720 (HD)"
    CR_1080P = "1920 * 1080 (FHD)"
    CR_1440P = "2560 * 1440 (2k)"
    CR_1536P = "2048 * 1536"
    CR_2160P = "3840 * 2160 (4k)"
    CR_3072P = "4096 * 3072"

    @classmethod
    def _get_value_map(cls: type["ColorResolution"]) -> dict["ColorResolution", int]:
        return {
            ColorResolution.OFF: _k4a.K4A_COLOR_RESOLUTION_OFF,
            ColorResolution.CR_720P: _k4a.K4A_COLOR_RESOLUTION_720P,
            ColorResolution.CR_1080P: _k4a.K4A_COLOR_RESOLUTION_1080P,
            ColorResolution.CR_1440P: _k4a.K4A_COLOR_RESOLUTION_1440P,
            ColorResolution.CR_1536P: _k4a.K4A_COLOR_RESOLUTION_1536P,
            ColorResolution.CR_2160P: _k4a.K4A_COLOR_RESOLUTION_2160P,
            ColorResolution.CR_3072P: _k4a.K4A_COLOR_RESOLUTION_3072P,
        }


class ImageFormat(EnumExtend[int], str, Enum):
    COLOR_MJPG = "Color image in MJPG format"
    COLOR_NV12 = "Color image in NV12 format"
    COLOR_YUY2 = "Color image in YUY2 format"
    COLOR_BGRA32 = "Color image in BGRA32 format"
    DEPTH16 = "16-bit depth image"
    IR16 = "16-bit infrared (IR) image"
    CUSTOM8 = "8-bit custom image format"
    CUSTOM16 = "16-bit custom image format"
    CUSTOM = "Custom image format"

    @classmethod
    def _get_value_map(cls: type["ImageFormat"]) -> dict["ImageFormat", int]:
        return {
            ImageFormat.COLOR_MJPG: _k4a.K4A_IMAGE_FORMAT_COLOR_MJPG,
            ImageFormat.COLOR_NV12: _k4a.K4A_IMAGE_FORMAT_COLOR_NV12,
            ImageFormat.COLOR_YUY2: _k4a.K4A_IMAGE_FORMAT_COLOR_YUY2,
            ImageFormat.COLOR_BGRA32: _k4a.K4A_IMAGE_FORMAT_COLOR_BGRA32,
            ImageFormat.DEPTH16: _k4a.K4A_IMAGE_FORMAT_DEPTH16,
            ImageFormat.IR16: _k4a.K4A_IMAGE_FORMAT_IR16,
            ImageFormat.CUSTOM8: _k4a.K4A_IMAGE_FORMAT_CUSTOM8,
            ImageFormat.CUSTOM16: _k4a.K4A_IMAGE_FORMAT_CUSTOM16,
            ImageFormat.CUSTOM: _k4a.K4A_IMAGE_FORMAT_CUSTOM,
        }


class TransformationInterpolationType(EnumExtend[int], str, Enum):
    NEAREST = "Nearest neighbor interpolation"
    LINEAR = "Linear interpolation"

    @classmethod
    def _get_value_map(
        cls: type["TransformationInterpolationType"],
    ) -> dict["TransformationInterpolationType", int]:
        return {
            TransformationInterpolationType.NEAREST: _k4a.K4A_TRANSFORMATION_INTERPOLATION_TYPE_NEAREST,
            TransformationInterpolationType.LINEAR: _k4a.K4A_TRANSFORMATION_INTERPOLATION_TYPE_LINEAR,
        }


class FramesPerSecond(EnumExtend[int], str, Enum):
    FPS_5 = "5 frames per second"
    FPS_15 = "15 frames per second"
    FPS_30 = "30 frames per second"

    @classmethod
    def _get_value_map(cls: type["FramesPerSecond"]) -> dict["FramesPerSecond", int]:
        return {
            FramesPerSecond.FPS_5: _k4a.K4A_FRAMES_PER_SECOND_5,
            FramesPerSecond.FPS_15: _k4a.K4A_FRAMES_PER_SECOND_15,
            FramesPerSecond.FPS_30: _k4a.K4A_FRAMES_PER_SECOND_30,
        }


class WiredSyncMode(EnumExtend[int], str, Enum):
    STANDALONE = "Standalone mode"
    MASTER = "Master mode in synchronization chain"
    SUBORDINATE = "Subordinate mode in synchronization chain"

    @classmethod
    def _get_value_map(cls: type["WiredSyncMode"]) -> dict["WiredSyncMode", int]:
        return {
            WiredSyncMode.STANDALONE: _k4a.K4A_WIRED_SYNC_MODE_STANDALONE,
            WiredSyncMode.MASTER: _k4a.K4A_WIRED_SYNC_MODE_MASTER,
            WiredSyncMode.SUBORDINATE: _k4a.K4A_WIRED_SYNC_MODE_SUBORDINATE,
        }


_DeviceConfigT = TypeVar("_DeviceConfigT", bound="DeviceConfig")


@dataclass
class DeviceConfig(ConfigWapper[_k4a.k4a_device_configuration_t]):
    image_format: ImageFormat
    color_resolution: ColorResolution
    depth_mode: DepthMode
    camera_fps: FramesPerSecond
    synchronized_images_only: bool
    disable_streaming_indicator: bool
    depth_delay_off_color_usec: int
    wired_sync_mode: WiredSyncMode
    subordinate_delay_off_master_usec: int

    @classmethod
    def get_serialization_settings(cls) -> Retort:
        super_settings = super().get_serialization_settings()
        return super_settings.extend(
            recipe=[
                enum_by_name(ImageFormat),
                enum_by_name(ColorResolution),
                enum_by_name(DepthMode),
                enum_by_name(FramesPerSecond),
                enum_by_name(WiredSyncMode),
            ],
        )

    @classmethod
    def create(
        cls: type[_DeviceConfigT],
        image_format: ImageFormat = ImageFormat.COLOR_MJPG,
        color_resolution: ColorResolution = ColorResolution.CR_720P,
        depth_mode: DepthMode = DepthMode.NFOV_2X2BINNED,
        camera_fps: FramesPerSecond = FramesPerSecond.FPS_30,
        synchronized_images_only: bool = False,
        disable_streaming_indicator: bool = False,
        depth_delay_off_color_usec: int = 0,
    ) -> _DeviceConfigT:
        """Create a new DeviceConfig instance."""
        return cls(
            image_format=image_format,
            color_resolution=color_resolution,
            depth_mode=depth_mode,
            camera_fps=camera_fps,
            synchronized_images_only=synchronized_images_only,
            disable_streaming_indicator=disable_streaming_indicator,
            depth_delay_off_color_usec=depth_delay_off_color_usec,
            wired_sync_mode=WiredSyncMode.STANDALONE,
            subordinate_delay_off_master_usec=0,
        )

    def _update_handle(self) -> _k4a.k4a_device_configuration_t:
        image_format = ImageFormat.get_mapped_value(self.image_format)
        color_resolution = ColorResolution.get_mapped_value(self.color_resolution)
        depth_mode = DepthMode.get_mapped_value(self.depth_mode)
        camera_fps = FramesPerSecond.get_mapped_value(self.camera_fps)
        wired_sync_mode = WiredSyncMode.get_mapped_value(self.wired_sync_mode)

        return _k4a.k4a_device_configuration_t(
            image_format,
            color_resolution,
            depth_mode,
            camera_fps,
            self.synchronized_images_only,
            self.depth_delay_off_color_usec,
            wired_sync_mode,
            self.subordinate_delay_off_master_usec,
            self.disable_streaming_indicator,
        )


DEFAULT_CONFIG = DeviceConfig.create()
DISABLE_ALL_CONFIG = DeviceConfig.create(
    image_format=ImageFormat.COLOR_MJPG,
    color_resolution=ColorResolution.OFF,
    depth_mode=DepthMode.OFF,
    camera_fps=FramesPerSecond.FPS_30,
    synchronized_images_only=False,
    disable_streaming_indicator=True,
    depth_delay_off_color_usec=0,
)
