from ctypes import c_int
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

import numpy as np
import numpy.typing as npt
from pykinect_azure.k4a import _k4a, _k4atypes

from azure_kinect.k4a.config_device import ColorResolution, DepthMode
from azure_kinect.util import EnumExtend, ResultStatus, ResultWithStatus
from azure_kinect.util.base_wapper import K4AWapper


class CalibrationType(EnumExtend[int], str, Enum):
    UNKNOWN = "Unknown type"
    DEPTH = "Depth camera"
    COLOR = "Color camera"
    GYRO = "Gyroscope"
    ACCEL = "Accelerometer"
    NUM = "Number"

    @classmethod
    def _get_value_map(
        cls: type["CalibrationType"],
    ) -> dict["CalibrationType", int]:
        return {
            CalibrationType.UNKNOWN: _k4a.K4A_CALIBRATION_TYPE_UNKNOWN,
            CalibrationType.DEPTH: _k4a.K4A_CALIBRATION_TYPE_DEPTH,
            CalibrationType.COLOR: _k4a.K4A_CALIBRATION_TYPE_COLOR,
            CalibrationType.GYRO: _k4a.K4A_CALIBRATION_TYPE_GYRO,
            CalibrationType.ACCEL: _k4a.K4A_CALIBRATION_TYPE_ACCEL,
            CalibrationType.NUM: _k4a.K4A_CALIBRATION_TYPE_NUM,
        }


@dataclass(frozen=True)
class IntrinsicParameters:
    __slots__ = ("_raw_params",)

    _raw_params: _k4atypes._param

    @cached_property
    def cx(self) -> float:
        """Principal point in image, x."""
        return self._raw_params.cx

    @cached_property
    def cy(self) -> float:
        """Principal point in image, y."""
        return self._raw_params.cy

    @cached_property
    def fx(self) -> float:
        """Focal length x."""
        return self._raw_params.fx

    @cached_property
    def fy(self) -> float:
        """Focal length y."""
        return self._raw_params.fy

    @cached_property
    def k1(self) -> float:
        """k1 radial distortion coefficient"""
        return self._raw_params.k1

    @cached_property
    def k2(self) -> float:
        """k2 radial distortion coefficient"""
        return self._raw_params.k2

    @cached_property
    def k3(self) -> float:
        """k3 radial distortion coefficient"""
        return self._raw_params.k3

    @cached_property
    def k4(self) -> float:
        """k4 radial distortion coefficient"""
        return self._raw_params.k4

    @cached_property
    def k5(self) -> float:
        """k5 radial distortion coefficient"""
        return self._raw_params.k5

    @cached_property
    def k6(self) -> float:
        """k6 radial distortion coefficient"""
        return self._raw_params.k6

    @cached_property
    def codx(self) -> float:
        """Center of distortion in Z=1 plane, x (only used for Rational6KT)"""
        return self._raw_params.codx

    @cached_property
    def cody(self) -> float:
        """Center of distortion in Z=1 plane, y (only used for Rational6KT)"""
        return self._raw_params.cody

    @cached_property
    def p2(self) -> float:
        """Tangential distortion coefficient 2."""
        return self._raw_params.p2

    @cached_property
    def p1(self) -> float:
        """Tangential distortion coefficient 1."""
        return self._raw_params.p1

    @cached_property
    def metric_radius(self) -> float:
        """Metric radius."""
        return self._raw_params.metric_radius


@dataclass(frozen=True)
class CameraIntrinsicsInfo:
    __slots__ = ("camera_type", "width", "height", "radius", "params")

    camera_type: CalibrationType

    width: int
    height: int
    radius: float

    params: IntrinsicParameters

    @cached_property
    def camera_intrinsics_matrix(self) -> npt.NDArray[np.float32]:
        """Get the intrinsic matrix as a NumPy ndarray."""
        return np.array(
            [
                [self.params.fx, 0, self.params.cx],
                [0, self.params.fy, self.params.cy],
                [0, 0, 1],
            ],
            dtype=np.float32,
        )

    @cached_property
    def distortion_coefficients(self) -> npt.NDArray[np.float32]:
        """Get the distortion coefficients as a NumPy ndarray."""
        return np.array(
            [
                self.params.k1,
                self.params.k2,
                self.params.p1,
                self.params.p2,
                self.params.k3,
                self.params.k4,
                self.params.k5,
                self.params.k6,
            ],
            dtype=np.float32,
        )


class K4ACalibration(K4AWapper[_k4a.k4a_calibration_t]):
    __slots__ = ()

    def __init__(self, calibration_handle: _k4a.k4a_calibration_t):
        self._handle = calibration_handle

    @cached_property
    def depth_mode(self) -> DepthMode:
        """The depth mode of the calibration."""
        return DepthMode.get_enum_by_mapped_value(
            self._handle.depth_mode,
        )

    @cached_property
    def color_resolution(self) -> ColorResolution:
        """The color resolution of the calibration."""
        return ColorResolution.get_enum_by_mapped_value(
            self._handle.color_resolution,
        )

    def _get_camera_calibration(
        self,
        _camera: CalibrationType,
    ) -> _k4a.k4a_calibration_camera_t:
        if _camera == CalibrationType.COLOR:
            _camera_calibration = self._handle.color_camera_calibration
        elif _camera == CalibrationType.DEPTH:
            _camera_calibration = self._handle.depth_camera_calibration
        else:
            raise NotImplementedError(
                f"Can not get calibration of camera type: {_camera}",
            )

        return _camera_calibration

    def get_extrinsics_info(
        self,
        source_camera: CalibrationType,
        target_camera: CalibrationType,
    ) -> _k4a.k4a_calibration_extrinsics_t:
        """Get the extrinsic parameters allow 3D coordinate conversions between
        depth camera, color camera, the IMU's gyroscope and accelerometer.

        Args:
            source_camera (CalibrationType): The source camera type.
            target_camera (CalibrationType): The target camera type.

        Returns:
            _k4a.k4a_calibration_extrinsics_t: Extrinsic transformation
                parameters.
        """
        return self._handle.extrinsics[source_camera][target_camera]

    def get_intrinsics_info(
        self,
        target_camera: CalibrationType,
    ) -> CameraIntrinsicsInfo:
        """Get the intrinsic info of the specified camera.

        Args:
            target_camera (CalibrationType): The type of camera to retrieve
                intrinsics for.

        Returns:
            CameraIntrinsicsInfo: The intrinsic parameters and other properties
                of the specified camera.
        """
        _camera_calibration = self._get_camera_calibration(target_camera)
        _params = IntrinsicParameters(
            _camera_calibration.intrinsics.parameters.param,
        )

        return CameraIntrinsicsInfo(
            camera_type=target_camera,
            width=_camera_calibration.resolution_width,
            height=_camera_calibration.resolution_height,
            radius=_camera_calibration.metric_radius,
            params=_params,
        )

    def convert_3d_to_3d(
        self,
        source_point_3d_mm: _k4a.k4a_float3_t,
        source_camera: CalibrationType,
        target_camera: CalibrationType,
    ) -> ResultWithStatus[ResultStatus, _k4a.k4a_float3_t]:
        """
        Converts a 3D point from one camera coordinate system to another.

        Args:
            source_point_3d_mm: The 3D point in the source camera coordinate system.
            source_camera: The source camera type.
            target_camera: The target camera type.

        Returns:
            A ResultWithStatus object containing the conversion result and status.
        """
        target_point_3d_mm = _k4a.k4a_float3_t()

        result_status = _k4a.k4a_calibration_3d_to_3d(
            self._handle,
            source_point_3d_mm,
            CalibrationType.get_mapped_value(source_camera),
            CalibrationType.get_mapped_value(target_camera),
            target_point_3d_mm,
        )
        result_status = ResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=target_point_3d_mm,
        )

    def convert_3d_to_2d(
        self,
        source_point_3d_mm: _k4a.k4a_float3_t,
        source_camera: CalibrationType,
        target_camera: CalibrationType,
    ) -> ResultWithStatus[ResultStatus, _k4a.k4a_float2_t]:
        """
        Converts a 3D point in a camera coordinate system to a 2D point in another
        camera's image plane.

        Args:
            source_point_3d_mm: The 3D point in the source camera coordinate system.
            source_camera: The source camera type.
            target_camera: The target camera type.

        Returns:
            A ResultWithStatus object containing the conversion result and status.
        """
        target_point_2d = _k4a.k4a_float2_t()
        valid = c_int()

        result_status = _k4a.k4a_calibration_3d_to_2d(
            self._handle,
            source_point_3d_mm,
            CalibrationType.get_mapped_value(source_camera),
            CalibrationType.get_mapped_value(target_camera),
            target_point_2d,
            valid,
        )
        result_status = ResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=target_point_2d,
        )

    def convert_2d_to_3d(
        self,
        source_point_2d: _k4a.k4a_float2_t,
        source_depth_mm: float,
        source_camera: CalibrationType,
        target_camera: CalibrationType,
    ) -> ResultWithStatus[ResultStatus, _k4a.k4a_float3_t]:
        """
        Converts a 2D point in a camera's image plane to a 3D point in another
        camera's coordinate system.

        Args:
            source_point_2d: The 2D point in the source camera's image plane.
            source_depth_mm: The depth of the point in millimeters.
            source_camera: The source camera type.
            target_camera: The target camera type.

        Returns:
            A ResultWithStatus object containing the conversion result and status.
        """
        target_point_3d_mm = _k4a.k4a_float3_t()
        valid = c_int()

        result_status = _k4a.k4a_calibration_2d_to_3d(
            self._handle,
            source_point_2d,
            source_depth_mm,
            CalibrationType.get_mapped_value(source_camera),
            CalibrationType.get_mapped_value(target_camera),
            target_point_3d_mm,
            valid,
        )

        return ResultWithStatus(
            status=result_status,
            result=target_point_3d_mm,
        )

    def convert_2d_to_2d(
        self,
        source_point_2d: _k4a.k4a_float2_t,
        source_depth_mm: float,
        source_camera: CalibrationType,
        target_camera: CalibrationType,
    ) -> ResultWithStatus[ResultStatus, _k4a.k4a_float2_t]:
        """
        Converts a 2D point from one camera's image plane to another camera's
        image plane.

        Args:
            source_point_2d: The 2D point in the source camera's image plane.
            source_depth_mm: The depth of the point in millimeters.
            source_camera: The source camera type.
            target_camera: The target camera type.

        Returns:
            A ResultWithStatus object containing the conversion result and status.
        """
        target_point_2d = _k4a.k4a_float2_t()
        valid = c_int()

        result_status = _k4a.k4a_calibration_2d_to_2d(
            self._handle,
            source_point_2d,
            source_depth_mm,
            CalibrationType.get_mapped_value(source_camera),
            CalibrationType.get_mapped_value(target_camera),
            target_point_2d,
            valid,
        )
        return ResultWithStatus(
            status=result_status,
            result=target_point_2d,
        )

    def convert_color_2d_to_depth_2d(
        self,
        source_point_2d: _k4a.k4a_float2_t,
        depth_image: _k4a.k4a_image_t,
    ) -> ResultWithStatus[ResultStatus, _k4a.k4a_float2_t]:
        """
        Converts a 2D point from the color camera's image plane to the depth
        camera's image plane.

        Args:
            source_point_2d: The 2D point in the color camera's image plane.
            depth_image: The depth image used for conversion.

        Returns:
            A ResultWithStatus object containing the conversion result and status.
        """
        target_point_2d = _k4a.k4a_float2_t()
        valid = c_int()

        result_status = _k4a.k4a_calibration_color_2d_to_depth_2d(
            self._handle,
            source_point_2d,
            depth_image,
            target_point_2d,
            valid,
        )
        return ResultWithStatus(
            status=result_status,
            result=target_point_2d,
        )

    def __wapper_data__(self) -> dict:
        return {
            "depth_mode": self.depth_mode.name,
            "color_resolution": self.color_resolution.name,
        }

    def __del__(self) -> None:
        pass
