from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple, TypeAlias

from adaptix import Retort, enum_by_name
from pykinect_azure.k4a import _k4a

from azure_kinect.util import EnumExtend
from azure_kinect.util.serializable_data import SerializableData


class ColorControlMode(EnumExtend[int], str, Enum):
    AUTO = "Set the color control value automatically"
    MANUAL = "Set the color control value manually"

    @classmethod
    def _get_value_map(
        cls: type["ColorControlMode"],
    ) -> dict["ColorControlMode", int]:
        return {
            ColorControlMode.AUTO: _k4a.K4A_COLOR_CONTROL_MODE_AUTO,
            ColorControlMode.MANUAL: _k4a.K4A_COLOR_CONTROL_MODE_MANUAL,
        }


class ColorControlCommand(EnumExtend[int], str, Enum):
    EXPOSURE_TIME_ABSOLUTE = "Absolute value of camera exposure time"
    BRIGHTNESS = "Brightness"
    CONTRAST = "Contrast"
    SATURATION = "Saturation"
    SHARPNESS = "Sharpness"
    WHITE_BALANCE = "White balance"
    BACKLIGHT_COMPENSATION = "Backlight compensation"
    GAIN = "Gain"
    POWERLINE_FREQUENCY = "Powerline frequency"

    @classmethod
    def _get_value_map(
        cls: type["ColorControlCommand"],
    ) -> dict["ColorControlCommand", int]:
        return {
            ColorControlCommand.EXPOSURE_TIME_ABSOLUTE: _k4a.K4A_COLOR_CONTROL_EXPOSURE_TIME_ABSOLUTE,
            ColorControlCommand.BRIGHTNESS: _k4a.K4A_COLOR_CONTROL_BRIGHTNESS,
            ColorControlCommand.CONTRAST: _k4a.K4A_COLOR_CONTROL_CONTRAST,
            ColorControlCommand.SATURATION: _k4a.K4A_COLOR_CONTROL_SATURATION,
            ColorControlCommand.SHARPNESS: _k4a.K4A_COLOR_CONTROL_SHARPNESS,
            ColorControlCommand.WHITE_BALANCE: _k4a.K4A_COLOR_CONTROL_WHITEBALANCE,
            ColorControlCommand.BACKLIGHT_COMPENSATION: _k4a.K4A_COLOR_CONTROL_BACKLIGHT_COMPENSATION,
            ColorControlCommand.GAIN: _k4a.K4A_COLOR_CONTROL_GAIN,
            ColorControlCommand.POWERLINE_FREQUENCY: _k4a.K4A_COLOR_CONTROL_POWERLINE_FREQUENCY,
        }


class ColorControlCapabilities(NamedTuple):
    supports_auto: bool
    min_value: int
    max_value: int
    step: int
    default_mode: ColorControlMode
    default_value: int


@dataclass(frozen=True)
class ColorControlConfig:
    __slots__ = ("command", "value", "mode")

    command: ColorControlCommand
    value: int
    mode: ColorControlMode


ColorControlConfigsType: TypeAlias = tuple[ColorControlConfig, ...]


@dataclass(frozen=True)
class DefaultColorControlConfig(ColorControlConfig):
    __slots__ = ("capabilities",)

    capabilities: ColorControlCapabilities


class DefaultColorControl(NamedTuple):
    exposure_time_absolute: DefaultColorControlConfig
    brightness: DefaultColorControlConfig
    contrast: DefaultColorControlConfig
    saturation: DefaultColorControlConfig
    sharpness: DefaultColorControlConfig
    white_balance: DefaultColorControlConfig
    backlight_compensation: DefaultColorControlConfig
    gain: DefaultColorControlConfig
    powerline_frequency: DefaultColorControlConfig


@dataclass(frozen=True)
class SceneColorControlConfig(SerializableData):
    scene_name: str
    device_color_control_configs: dict[str, ColorControlConfigsType]

    @classmethod
    def get_serialization_settings(cls) -> Retort:
        super_settings = super().get_serialization_settings()
        return super_settings.extend(
            recipe=[
                enum_by_name(ColorControlCommand),
                enum_by_name(ColorControlMode),
            ]
        )
