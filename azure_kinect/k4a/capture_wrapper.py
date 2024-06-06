from typing import Optional, TypeVar

import cv2.typing as cvt
from pykinect_azure.k4a import _k4a

from azure_kinect.k4a.calibration_wrapper import CalibrationType, K4ACalibration
from azure_kinect.k4a.image_wrapper import K4AImage
from azure_kinect.k4a.point_cloud import PointCloud
from azure_kinect.k4a.transformation_wrapper import K4ATransformation
from azure_kinect.util import ResultStatus, ResultWithStatus
from azure_kinect.util.base_wapper import K4AWapper

_CaptureT = TypeVar("_CaptureT", bound="K4ACapture")


class K4ACapture(K4AWapper[Optional[_k4a.k4a_capture_t]]):
    __slots__ = (
        "_calibration",
        "_transformation",
        "_cached_color_image",
        "_cached_depth_image",
        "_cached_ir_image",
    )

    _calibration: K4ACalibration
    _transformation: K4ATransformation

    _cached_color_image: Optional[K4AImage]
    _cached_depth_image: Optional[K4AImage]
    _cached_ir_image: Optional[K4AImage]

    def __init__(
        self,
        capture_handle: _k4a.k4a_capture_t,
        calibration: K4ACalibration,
    ) -> None:
        self._handle = capture_handle
        self._calibration = calibration
        self._transformation = K4ATransformation(calibration)

        self._cached_color_image = None
        self._cached_depth_image = None
        self._cached_ir_image = None

    @property
    def temperature(self) -> float | None:
        """Get the temperature associated with the capture.

        returns the temperature of the device at the time of the capture in
        Celsius. If the temperature is unavailable, the function will return
        None.
        """
        if not self.is_valid():
            return None

        return _k4a.k4a_capture_get_temperature_c(self._handle)

    @property
    def has_color_image(self) -> bool:
        return self.get_color_image() is not None

    @property
    def has_depth_image(self) -> bool:
        return self.get_depth_image() is not None

    @property
    def has_ir_image(self) -> bool:
        return self.get_ir_image() is not None

    @property
    def cached_color_image(self) -> K4AImage | None:
        return self._cached_color_image

    @property
    def cached_depth_image(self) -> K4AImage | None:
        return self._cached_depth_image

    @property
    def cached_ir_image(self) -> K4AImage | None:
        return self._cached_ir_image

    @classmethod
    def create(
        cls: type[_CaptureT],
        calibration: K4ACalibration,
    ) -> ResultWithStatus[ResultStatus, _CaptureT]:
        """Create an empty capture object."""
        capture_handle = _k4a.k4a_capture_t()

        result_status = _k4a.k4a_capture_create(capture_handle)
        result_status = ResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=cls(capture_handle, calibration),
        )

    def release_handle(self) -> None:
        """Release the capture object."""
        if self.is_valid():
            _k4a.k4a_capture_release(self._handle)
            self._handle = None

            # Clear cached images
            if self._cached_color_image is not None:
                self._cached_color_image = None

            if self._cached_depth_image is not None:
                self._cached_depth_image = None

            if self._cached_ir_image is not None:
                self._cached_ir_image = None

    def update_handle(self, new_handle: _k4a.k4a_capture_t) -> None:
        """Update new capture handle.

        The old handle is automatically released and replaced with a new handle,
        if the old handle is not released.
        """
        if self.is_valid():
            self.release_handle()

        self._handle = new_handle

    def get_color_image(self) -> K4AImage | None:
        """Retrieves the color image from the capture.

        Returns:
            K4AImage | None: A K4AImage object representing the color image.
                Will return None if get color image failed.
        """
        if not self.is_valid():
            return None

        if self._cached_color_image is None:
            color_image = K4AImage(_k4a.k4a_capture_get_color_image(self._handle))
            self._cached_color_image = color_image if color_image.is_valid() else None

        return self._cached_color_image

    def get_depth_image(self) -> K4AImage | None:
        """Retrieves the depth image from the capture.

        Returns:
            K4AImage | None: A K4AImage object representing the depth image.
                Will return None if get depth image failed.
        """
        if not self.is_valid():
            return None

        if self._cached_depth_image is None:
            depth_image = K4AImage(_k4a.k4a_capture_get_depth_image(self._handle))
            self._cached_depth_image = depth_image if depth_image.is_valid() else None

        return self._cached_depth_image

    def get_ir_image(self) -> K4AImage | None:
        """Retrieves the infrared (IR) image from the capture.

        Returns:
            K4AImage | None: A K4AImage object representing the ir image.
                Will return None if get ir image failed.
        """
        if not self.is_valid():
            return None

        if self._cached_ir_image is None:
            ir_image = K4AImage(_k4a.k4a_capture_get_ir_image(self._handle))
            self._cached_ir_image = ir_image if ir_image.is_valid() else None

        return self._cached_ir_image

    def get_transformed_depth_image(
        self,
    ) -> K4AImage | None:
        """Transforms the depth image to align with the color camera.

        Returns:
            K4AImage | None: A K4AImage object representing the transformed
                depth image. Will return None if get depth image failed.
        """
        depth_image = self.get_depth_image()

        if depth_image is None:
            return None

        return self._transformation.depth_to_color(depth_image)

    def get_transformed_color_image(
        self,
    ) -> K4AImage | None:
        """Transforms the color image to align with the depth camera.

        Returns:
            K4AImage | None: A K4AImage object representing the transformed
                color image. Will return None if get ir image failed.
        """
        depth_image = self.get_depth_image()
        color_image = self.get_color_image()

        if depth_image is None or color_image is None:
            return None

        return self._transformation.color_to_depth(depth_image, color_image)

    def get_point_cloud(
        self,
        target_camera: CalibrationType = CalibrationType.DEPTH,
    ) -> PointCloud | None:
        """Transforms the depth image into a 3D point cloud.

        Args:
            target_camera: The camera perspective to use for the point cloud.

        Returns:
            PointCloud | None: A PointCloud object representing the 3D point
                cloud. Will return None when get depth image failed.
        """
        depth_image = self.get_depth_image()

        if depth_image is None:
            return None

        return self._transformation.depth_to_point_cloud(
            depth_image,
            target_camera,
        )

    def get_transformed_point_cloud(
        self,
    ) -> PointCloud | None:
        """Transforms the depth image into a 3D point cloud and aligns it with
        the color camera.

        Returns:
            PointCloud | None: A PointCloud object representing the transformed
                3D point cloud. Will return None when get depth image failed.
        """
        transformed_depth_image = self.get_transformed_depth_image()

        if transformed_depth_image is None:
            return None

        return self._transformation.depth_to_point_cloud(
            transformed_depth_image,
            CalibrationType.COLOR,
        )

    def get_color_image_array(self) -> cvt.MatLike | None:
        image = self.get_color_image()

        if image is not None:
            return image.to_numpy()

    def get_depth_image_array(self) -> cvt.MatLike | None:
        image = self.get_depth_image()

        if image is not None:
            return image.to_numpy()

    def get_colored_depth_image_array(
        self,
        *,
        alpha: Optional[float] = None,
    ) -> cvt.MatLike | None:
        image = self.get_depth_image_array()

        if image is not None:
            return K4AImage.color_depth_image(image, alpha)

    def get_ir_image_array(self) -> cvt.MatLike | None:
        image = self.get_ir_image()

        if image is not None:
            return image.to_numpy()

    def get_transformed_color_image_array(self) -> cvt.MatLike | None:
        image = self.get_transformed_color_image()

        if image is not None:
            return image.to_numpy()

    def get_transformed_depth_image_array(self) -> cvt.MatLike | None:
        image = self.get_transformed_depth_image()

        if image is not None:
            return image.to_numpy()

    def get_colored_transformed_depth_image_array(
        self,
        *,
        alpha: Optional[float] = None,
    ) -> cvt.MatLike | None:
        image = self.get_transformed_depth_image_array()

        if image is not None:
            return K4AImage.color_depth_image(image, alpha)

    def get_smooth_depth_image_array(
        self,
        *,
        maximum_hole_size: Optional[int] = None,
    ) -> cvt.MatLike | None:
        image = self.get_depth_image_array()

        if image is not None:
            return K4AImage.smooth_depth_image(image, maximum_hole_size)

    def get_smooth_transformed_depth_image_array(
        self,
        *,
        maximum_hole_size: Optional[int] = None,
    ) -> cvt.MatLike | None:
        image = self.get_transformed_depth_image_array()

        if image is not None:
            return K4AImage.smooth_depth_image(image, maximum_hole_size)

    def __wapper_data__(self) -> dict:
        return {}

    def __del__(self) -> None:
        self.release_handle()
