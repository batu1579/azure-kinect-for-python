from ctypes import c_uint32
from enum import Enum
from functools import cached_property
from typing import Optional

from pykinect_azure.k4a import _k4a

from azure_kinect.k4a.calibration_wrapper import (
    CalibrationType,
    CameraIntrinsicsInfo,
    K4ACalibration,
)
from azure_kinect.k4a.config_device import ImageFormat
from azure_kinect.k4a.image_wrapper import K4AImage
from azure_kinect.k4a.point_cloud import PointCloud
from azure_kinect.util import EnumExtend, ResultStatus
from azure_kinect.util.base_wapper import K4AWapper


class TransformInterpolation(EnumExtend[int], str, Enum):
    NEAREST = "nearest"
    LINEAR = "linear"

    @classmethod
    def _get_value_map(
        cls: type["TransformInterpolation"],
    ) -> dict["TransformInterpolation", int]:
        return {
            TransformInterpolation.NEAREST: _k4a.K4A_TRANSFORMATION_INTERPOLATION_TYPE_NEAREST,
            TransformInterpolation.LINEAR: _k4a.K4A_TRANSFORMATION_INTERPOLATION_TYPE_LINEAR,
        }


class K4ATransformation(K4AWapper[Optional[_k4a.k4a_transformation_t]]):
    __slots__ = ("_calibration",)

    _calibration: K4ACalibration

    def __init__(self, calibration: K4ACalibration) -> None:
        self._handle = _k4a.k4a_transformation_create(calibration.handle)
        self._calibration = calibration

    @cached_property
    def color_resolution(self) -> CameraIntrinsicsInfo:
        """Returns the calibration information for the color camera."""
        return self._calibration.get_intrinsics_info(
            CalibrationType.COLOR,
        )

    @cached_property
    def depth_resolution(self) -> CameraIntrinsicsInfo:
        """Returns the calibration information for the depth camera."""
        return self._calibration.get_intrinsics_info(
            CalibrationType.DEPTH,
        )

    def destroy(self) -> None:
        """Destroys the transformation object and releases its resources."""
        if not self.is_valid():
            return

        _k4a.k4a_transformation_destroy(self._handle)
        self._handle = None

    def _get_custom_bytes_per_pixel(self, custom_image: K4AImage) -> int:
        return 1 if custom_image.image_format == ImageFormat.CUSTOM8 else 2

    def depth_to_color(
        self,
        depth_image: K4AImage,
    ) -> K4AImage | None:
        """Transforms a depth image to align with the color camera.

        Args:
            depth_image: The depth image to transform.

        Returns:
            K4AImage | None: The transformed depth image. None is returned
                if any error occurs.
        """
        if not depth_image.is_valid() or depth_image.image_format is None:
            return None

        # TODO(batu1579): convert color image to BGRA32 first

        status, transformed_depth_image = K4AImage.create(
            depth_image.image_format,
            self.color_resolution.width,
            self.color_resolution.height,
            self.color_resolution.width * 2,
        )

        if status == ResultStatus.FAILED:
            return None

        # TODO(batu1579): Modify This function in the library to return a value
        _k4a.k4a_transformation_depth_image_to_color_camera(
            self._handle,
            depth_image.handle,
            transformed_depth_image.handle,
        )
        return transformed_depth_image

    def depth_to_color_custom(
        self,
        depth_image: K4AImage,
        custom_image: K4AImage,
        interpolation: TransformInterpolation = TransformInterpolation.LINEAR,
    ) -> K4AImage | None:
        """Transforms a depth image and a custom image to align with the
        color camera.

        Args:
            depth_image: The depth image to transform.
            custom_image: The custom image to transform.
            interpolation: The interpolation type to use.

        Returns:
            K4AImage | None: The custom type color image. None is returned
                if any error occurs.
        """
        if (
            not depth_image.is_valid()
            or not custom_image.is_valid()
            or custom_image.image_format is None
        ):
            return None

        status, transformed_depth_image = K4AImage.create(
            ImageFormat.DEPTH16,
            self.color_resolution.width,
            self.color_resolution.height,
            self.color_resolution.width * 2,
        )

        if status == ResultStatus.FAILED:
            return None

        bytes_per_pixel = self._get_custom_bytes_per_pixel(custom_image)
        status, transformed_custom_image = K4AImage.create(
            custom_image.image_format,
            self.color_resolution.width,
            self.color_resolution.height,
            self.color_resolution.width * bytes_per_pixel,
        )

        if status == ResultStatus.FAILED:
            return None

        invalid_custom_value = c_uint32()
        result_status = _k4a.k4a_transformation_depth_image_to_color_camera_custom(
            self._handle,
            depth_image.handle,
            custom_image.handle,
            transformed_depth_image.handle,
            transformed_custom_image.handle,
            TransformInterpolation.get_mapped_value(interpolation),
            invalid_custom_value,
        )
        result_status = ResultStatus(result_status)

        return (
            transformed_custom_image
            if result_status == ResultStatus.SUCCEEDED
            else None
        )

    def color_to_depth(
        self,
        depth_image: K4AImage,
        color_image: K4AImage,
    ) -> K4AImage | None:
        """Transforms a color image to align with the depth camera.

        Args:
            depth_image: The depth image used for alignment.
            color_image: The color image to transform.

        Returns:
            K4AImage | None: The converted depth image. None is returned
                if any error occurs.
        """
        if not depth_image.is_valid() or not color_image.is_valid():
            return None

        status, transformed_color_image = K4AImage.create(
            ImageFormat.COLOR_BGRA32,
            self.depth_resolution.width,
            self.depth_resolution.height,
            self.depth_resolution.width * 4,
        )

        if status == ResultStatus.FAILED:
            return None

        result_status = _k4a.k4a_transformation_color_image_to_depth_camera(
            self._handle,
            depth_image.handle,
            color_image.handle,
            transformed_color_image.handle,
        )
        result_status = ResultStatus(result_status)

        return (
            transformed_color_image if result_status == ResultStatus.SUCCEEDED else None
        )

    def depth_to_point_cloud(
        self,
        depth_image: K4AImage,
        targe_camera: CalibrationType = CalibrationType.DEPTH,
    ) -> PointCloud | None:
        """Transforms a depth image into a 3D point cloud.

        Args:
            depth_image: The depth image to transform.
            targe_camera: The type of calibration to use for the
                transformation.

        Returns:
            K4AImage | None: The converted point cloud object. None is returned
                if any error occurs.
        """
        if (
            not depth_image.is_valid()
            or depth_image.width_pixels is None
            or depth_image.height_pixels is None
        ):
            return None

        status, point_cloud = PointCloud.create(
            ImageFormat.CUSTOM,
            depth_image.width_pixels,
            depth_image.height_pixels,
            depth_image.width_pixels * 3 * 2,
        )

        if status == ResultStatus.FAILED:
            return None

        result_status = _k4a.k4a_transformation_depth_image_to_point_cloud(
            self._handle,
            depth_image.handle,
            CalibrationType.get_mapped_value(targe_camera),
            point_cloud.handle,
        )
        result_status = ResultStatus(result_status)

        return point_cloud if result_status == ResultStatus.SUCCEEDED else None

    def __wapper_data__(self) -> dict:
        _color = self.color_resolution
        _depth = self.depth_resolution

        return {
            "color_size": (_color.width, _color.height),
            "depth_size": (_depth.width, _depth.height),
        }

    def __del__(self) -> None:
        self.destroy()
