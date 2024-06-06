from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypeVar

from adaptix import Retort, enum_by_name
from pykinect_azure.k4abt import _k4abt, _k4abtTypes
from pykinect_azure.utils import get_k4abt_lite_model_path

from azure_kinect.util import EnumExtend
from azure_kinect.util.serializable_data import ConfigWapper


class SensorOrientation(EnumExtend[int], str, Enum):
    DEFAULT = "Mount the sensor at its default orientation."
    CLOCKWISE90 = "Clockwisely rotate the sensor 90 degree."
    COUNTERCLOCKWISE90 = "Counter-clockwisely rotate the sensor 90 degrees."
    FLIP180 = "Mount the sensor upside-down."

    @classmethod
    def _get_value_map(
        cls: type["SensorOrientation"],
    ) -> dict["SensorOrientation", int]:
        return {
            SensorOrientation.DEFAULT: _k4abtTypes.K4ABT_SENSOR_ORIENTATION_DEFAULT,
            SensorOrientation.CLOCKWISE90: _k4abtTypes.K4ABT_SENSOR_ORIENTATION_CLOCKWISE90,
            SensorOrientation.COUNTERCLOCKWISE90: _k4abtTypes.K4ABT_SENSOR_ORIENTATION_COUNTERCLOCKWISE90,
            SensorOrientation.FLIP180: _k4abtTypes.K4ABT_SENSOR_ORIENTATION_FLIP180,
        }


class ProcessingMode(EnumExtend[int], str, Enum):
    GPU = "SDK will use the most appropriate GPU mode for the operating system to run the tracker."
    CPU = "SDK will use CPU only mode to run the tracker."
    GPU_CUDA = "SDK will use ONNX Cuda EP to run the tracker."
    GPU_TENSORRT = "SDK will use ONNX TensorRT EP to run the tracker."
    GPU_DIRECTML = "SDK will use ONNX DirectML EP to run the tracker (Windows only)"

    @classmethod
    def _get_value_map(cls: type["ProcessingMode"]) -> dict["ProcessingMode", int]:
        return {
            ProcessingMode.GPU: _k4abtTypes.K4ABT_TRACKER_PROCESSING_MODE_GPU,
            ProcessingMode.CPU: _k4abtTypes.K4ABT_TRACKER_PROCESSING_MODE_CPU,
            ProcessingMode.GPU_CUDA: _k4abtTypes.K4ABT_TRACKER_PROCESSING_MODE_GPU_CUDA,
            ProcessingMode.GPU_TENSORRT: _k4abtTypes.K4ABT_TRACKER_PROCESSING_MODE_GPU_TENSORRT,
            ProcessingMode.GPU_DIRECTML: _k4abtTypes.K4ABT_TRACKER_PROCESSING_MODE_GPU_DIRECTML,
        }


class ModelType(EnumExtend[int], str, Enum):
    DEFAULT = "Default body tracking model"
    LITE = "Lite body tracking model"

    @classmethod
    def _get_value_map(cls: type["ModelType"]) -> dict["ModelType", int]:
        return {
            ModelType.DEFAULT: _k4abt.K4ABT_DEFAULT_MODEL,
            ModelType.LITE: _k4abt.K4ABT_LITE_MODEL,
        }


_TrackerConfigT = TypeVar("_TrackerConfigT", bound="TrackerConfig")


@dataclass
class TrackerConfig(ConfigWapper[_k4abt.k4abt_tracker_configuration_t]):
    sensor_orientation: SensorOrientation
    processing_mode: ProcessingMode
    model_type: ModelType
    model_path: Optional[str]
    gpu_device_id: int

    @classmethod
    def get_serialization_settings(cls) -> Retort:
        super_settings = super().get_serialization_settings()
        return super_settings.extend(
            recipe=[
                enum_by_name(SensorOrientation),
                enum_by_name(ProcessingMode),
            ],
        )

    @classmethod
    def create(
        cls: type[_TrackerConfigT],
        sensor_orientation: SensorOrientation = SensorOrientation.DEFAULT,
        processing_mode: ProcessingMode = ProcessingMode.GPU,
        model_type: ModelType = ModelType.DEFAULT,
        model_path: Optional[str] = None,
        gpu_device_id: int = 0,
    ) -> _TrackerConfigT:
        """Creates a new tracker configuration instance."""
        return cls(
            sensor_orientation=sensor_orientation,
            processing_mode=processing_mode,
            model_type=model_type,
            model_path=model_path,
            gpu_device_id=gpu_device_id,
        )

    def _update_handle(self) -> _k4abt.k4abt_tracker_configuration_t:
        _handle = _k4abt.k4abt_tracker_configuration_t()
        _handle.sensor_orientation = SensorOrientation.get_mapped_value(
            self.sensor_orientation,
        )
        _handle.processing_mode = ProcessingMode.get_mapped_value(
            self.processing_mode,
        )
        _handle.gpu_device_id = self.gpu_device_id

        if self.model_path is not None:
            _handle.model_path = self.model_path
        elif self.model_type == ModelType.LITE:
            _handle.model_path = get_k4abt_lite_model_path()

        return _handle


DEFAULT_TRACKER_CONFIG = TrackerConfig.create()
