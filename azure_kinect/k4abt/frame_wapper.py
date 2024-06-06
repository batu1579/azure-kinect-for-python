from functools import cached_property
from typing import TYPE_CHECKING, Iterator, Optional, cast
from weakref import ref

import cv2
import cv2.typing as cvt
import numpy as np
from pykinect_azure.k4abt import _k4abt

from azure_kinect.k4a import (
    CalibrationType,
    K4ACalibration,
    K4ACapture,
    K4AImage,
    K4ATransformation,
)
from azure_kinect.k4a.device_wrapper import K4ADevice
from azure_kinect.k4abt.body_2d_wapper import TrackingBody2d
from azure_kinect.k4abt.body_3d_wapper import TrackingBody3d
from azure_kinect.k4abt.joint_2d_wapper import Point2d, TrackingJoint2d
from azure_kinect.k4abt.joint_3d_wapper import TrackingJoint3d
from azure_kinect.k4abt.joint_enum import JOINT_COUNT
from azure_kinect.util import Logger, ResultStatus
from azure_kinect.util.base_wapper import K4AWapper

if TYPE_CHECKING:
    from azure_kinect.k4abt import K4ABodyTracker


class TrackingFrame(K4AWapper[Optional[_k4abt.k4abt_frame_t]]):
    __slots__ = (
        "_capture",
        "_tracker_ref",
    )

    _tracker_ref: ref["K4ABodyTracker"]
    _capture: Optional[K4ACapture]

    def __init__(
        self,
        frame_handle: _k4abt.k4abt_frame_t,
        tracker_ref: ref["K4ABodyTracker"],
    ) -> None:
        self._handle = None
        self._capture = None
        self._tracker_ref = tracker_ref

        self.update_handle(frame_handle)

    @property
    def from_tracker(self) -> "K4ABodyTracker":
        """Gets the tracker to which the current frame belongs"""
        tracker = self._tracker_ref()

        if tracker is None:
            raise RuntimeError("Tracker is destroyed before frame is released.")

        return tracker

    @property
    def from_device(self) -> K4ADevice:
        return self.from_tracker.bound_device

    @cached_property
    def calibration(self) -> K4ACalibration:
        """The calibration data for the device."""
        return self.from_tracker.calibration

    @cached_property
    def transformation(self) -> K4ATransformation:
        """The transformation object for converting between coordinate spaces."""
        return K4ATransformation(self.calibration)

    @property
    def body_count(self) -> int:
        """The number of bodies detected in the frame."""
        return _k4abt.k4abt_frame_get_num_bodies(self._handle)

    @property
    def device_timestamp_usec(self) -> int:
        """The timestamp of the frame in microseconds."""
        return _k4abt.k4abt_frame_get_device_timestamp_usec(self._handle)

    @property
    def cached_capture(self) -> Optional[K4ACapture]:
        return self._capture

    @staticmethod
    def body_3d_to_2d(
        body_3d: TrackingBody3d,
        calibration: K4ACalibration,
        target_camera: CalibrationType,
    ) -> TrackingBody2d:
        """Converts a 3D tracking body to a 2D tracking body.

        Args:
            body3d (TrackingBody3d): The 3D tracking body.

        Returns:
            TrackingBody2d: The 2D tracking body.
        """
        joints = np.ndarray((JOINT_COUNT,), dtype=np.object_)

        for id_, joint in enumerate(body_3d.joints):
            joint = cast(TrackingJoint3d, joint)

            result, position = calibration.convert_3d_to_2d(
                joint.position.to_float3(),
                source_camera=CalibrationType.DEPTH,
                target_camera=target_camera,
            )

            if result == ResultStatus.FAILED:
                raise ValueError(f"Failed to convert joint {joint} to 2D")

            joints[id_] = TrackingJoint2d(
                joint_id=id_,
                position=Point2d.from_float2(position),
                confidence_level=joint.confidence_level,
            )

        return TrackingBody2d(
            marker=body_3d.marker,
            joints=joints,
        )

    def update_handle(self, new_handle: _k4abt.k4abt_frame_t) -> None:
        """Updates the handle to the tracking frame.

        Args:
            new_handle (_k4abt.k4abt_frame_t): The new handle to the tracking
                frame.
        """
        if self.is_valid():
            _k4abt.k4abt_frame_release(self._handle)

        self._handle = new_handle

    def release_handle(self) -> None:
        """Releases the handle to the tracking frame."""
        if self.is_valid():
            _k4abt.k4abt_frame_release(self._handle)
            self._handle = None

    def _get_3d_body_handle(
        self,
        index: int,
    ) -> _k4abt.k4abt_body_t | None:
        # Get body id
        body_id = _k4abt.k4abt_frame_get_body_id(self._handle, index)

        if body_id == _k4abt.K4ABT_INVALID_BODY_ID:
            Logger.error(f"Invalid body id: {body_id}")
            return None

        # Get body skeleton
        body_skeleton = _k4abt.k4abt_skeleton_t()
        result_status = _k4abt.k4abt_frame_get_body_skeleton(
            self._handle,
            index,
            body_skeleton,
        )

        if ResultStatus(result_status) == ResultStatus.FAILED:
            Logger.error("Failed to get body skeleton")
            return None

        return _k4abt.k4abt_body_t(
            id=body_id,
            skeleton=body_skeleton,
        )

    def get_3d_body(
        self,
        index: int = 0,
        *,
        to_world: bool = True,
    ) -> TrackingBody3d | None:
        """Retrieves a 3D tracking body at a given index.

        Args:
            index (int): The index of the body.
            to_world (bool): Whether to transform the 3D body to world

        Returns:
            TrackingBody3d | None: Returns the body whose index is index,
                or None if not found.
        """
        body_handle = self._get_3d_body_handle(index)

        if body_handle is None:
            return None

        body = TrackingBody3d.from_handle(
            body_handle,
            self.from_device.serial_number,
        )

        if to_world:
            return TrackingBody3d.transform(
                body,
                self.from_tracker.device_transform,
            )

        return body

    def get_2d_body(
        self,
        index: int = 0,
        target_camera: CalibrationType = CalibrationType.DEPTH,
    ) -> TrackingBody2d | None:
        """Retrieves a 2D tracking body at a given index.

        Args:
            index (int): The index of the body.
            target_camera (CalibrationType): The target camera type for the
                2D coordinates.

        Returns:
            TrackingBody2d | None: Returns the body whose index is index,
                or None if not found.
        """
        body_handle = self._get_3d_body_handle(index)

        if body_handle is None:
            return None

        return TrackingBody2d.from_handle_3d(
            body_handle,
            self.from_device.serial_number,
            self.calibration,
            target_camera,
        )

    def get_3d_body_iterator(
        self,
        *,
        to_world: bool = True,
    ) -> Iterator[TrackingBody3d]:
        """Retrieves all 3D tracking bodies in the frame.

        Args:
            to_float3 (bool): Whether to transform the 3D body to world.

        Returns:
            Iterator[TrackingBody3d]: All 3D bodies in this frame.
        """
        for index in range(self.body_count):
            body = self.get_3d_body(index, to_world=to_world)

            if body is not None:
                yield body

    def get_2d_body_iterator(
        self,
        target_camera: CalibrationType = CalibrationType.DEPTH,
    ) -> Iterator[TrackingBody2d]:
        """Retrieves all 2D tracking bodies in the frame.

        Args:
            target_camera (CalibrationType): The target camera type for
                the 2D coordinates.

        Returns:
            Iterator[TrackingBody2d]: All 2D bodies in this frame.
        """
        for index in range(self.body_count):
            body = self.get_2d_body(index, target_camera)

            if body is not None:
                yield body

    def get_capture(self) -> K4ACapture | None:
        """Retrieves the capture associated with the tracking frame.

        Returns:
            K4ACapture | None: The capture if available, otherwise None.
        """
        if not self.is_valid():
            return None

        capture_handle = _k4abt.k4abt_frame_get_capture(self._handle)

        if self._capture is None:
            self._capture = K4ACapture(
                capture_handle,
                self.calibration,
            )
        else:
            self._capture.update_handle(capture_handle)

        return self._capture

    def get_body_index_map(self) -> K4AImage | None:
        """Get the body index map image from the tracking frame.

        Returns:
            K4AImage | None: The body index map image if available,
                otherwise None.
        """
        if not self.is_valid():
            return None

        return K4AImage(_k4abt.k4abt_frame_get_body_index_map(self._handle))

    def get_body_index_map_array(self) -> cvt.MatLike | None:
        """Get the body index map image from the tracking frame."""
        image = self.get_body_index_map()

        if image is None:
            return None

        return image.to_numpy()

    def get_transformed_body_index_map(self) -> K4AImage | None:
        """Get the transformed body index map image from the tracking frame.

        Returns:
            K4AImage | None: The transformed body index map image if available,
                otherwise None.
        """
        capture = self.get_capture()

        if capture is None:
            return None

        depth_image = capture.get_depth_image()
        map_image = self.get_body_index_map()

        if depth_image is None or map_image is None:
            return None

        return self.transformation.depth_to_color_custom(
            depth_image,
            map_image,
        )

    def get_transformed_body_index_map_array(self) -> cvt.MatLike | None:
        """Get the transformed body index map image from the tracking frame."""
        image = self.get_transformed_body_index_map()

        if image is None:
            return None

        return image.to_numpy()

    def _get_segmentation_image_array_from_map(
        self,
        map_image: K4AImage,
    ) -> cvt.MatLike | None:
        """Generates a segmentation image from a body index map.

        Args:
            map_image (K4AImage): The body index map.

        Returns:
            cvt.MatLike | None: The segmentation image if available,
                otherwise None.
        """
        map_image_array = map_image.to_numpy()

        if map_image_array is None:
            return None

        colored_map = np.empty((*map_image_array.shape, 3), dtype=np.uint8)
        for i in range(3):
            colored_map[:, :, i] = cv2.LUT(map_image_array, _k4abt.body_colors[:, i])

        return colored_map

    def get_segmentation_image_array(self) -> cvt.MatLike | None:
        """Retrieves the segmentation image from the tracking frame.

        Returns:
            cvt.MatLike | None: The segmentation image if available,
                otherwise None.
        """
        map_image = self.get_body_index_map()

        if map_image is None:
            return None

        return self._get_segmentation_image_array_from_map(map_image)

    def get_transformed_segmentation_image_array(self) -> cvt.MatLike | None:
        """Retrieves the transformed segmentation image from the tracking frame.

        Returns:
            cvt.MatLike | None: The transformed segmentation image if available,
                otherwise None.
        """
        map_image = self.get_transformed_body_index_map()

        if map_image is None:
            return None

        return self._get_segmentation_image_array_from_map(map_image)

    def __wapper_data__(self) -> dict:
        return {
            "from_device": self.from_device,
            "timestamp_usec": self.device_timestamp_usec,
        }

    def __del__(self) -> None:
        self.release_handle()
