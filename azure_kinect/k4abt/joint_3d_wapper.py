from functools import lru_cache
from typing import ClassVar, NamedTuple, TypeVar

import numpy as np
import numpy.typing as npt
from pykinect_azure.k4a import _k4a
from pykinect_azure.k4abt import _k4abt
from scipy.spatial.transform import Rotation

from azure_kinect.k4abt.base_joint_wapper import BaseTrackingJoint
from azure_kinect.k4abt.joint_enum import JointConfidenceLevel
from azure_kinect.transform import Transform
from azure_kinect.util.types import TransformMatrix

_Point3dT = TypeVar("_Point3dT", bound="Point3d")


class Point3d(NamedTuple):
    x: float
    y: float
    z: float

    @classmethod
    def from_float3(
        cls: type[_Point3dT],
        _coordinates: _k4a.k4a_float3_t,
    ) -> _Point3dT:
        """Creates a Point3d instance from a k4a_float3_t object.

        Args:
            _coordinates (_k4a.k4a_float3_t): The k4a_float3_t object.

        Returns:
            _Point3dT: The created Point3d instance.
        """
        _position = _coordinates.xyz
        return cls(
            x=_position.x,
            y=_position.y,
            z=_position.z,
        )

    @classmethod
    def transform(
        cls: type[_Point3dT],
        original_point: _Point3dT,
        transform: Transform,
    ) -> _Point3dT:
        """Transforms a Point3d using a transformation matrix.

        Args:
            original_point (_Point3dT): The original point to transform.
            transform (Transform): The transformation matrix.

        Returns:
            _Point3dT: The transformed point.
        """
        transformed_position = (
            np.dot(transform.rotation, original_point) + transform.translation
        )
        return cls(*transformed_position)
        # transformed_position = transformation_matrix @ original_point.to_homogeneous()
        # return cls(*transformed_position[:3])

    def to_float3(self) -> _k4a.k4a_float3_t:
        return _k4a.k4a_float3_t(self)

    def to_dict(self) -> dict:
        """Converts the Point3d to a dictionary.

        Returns:
            dict: The dictionary representation of the Point3d.
        """
        # pylint: disable=no-member
        return self._asdict()

    def to_numpy(self) -> npt.NDArray[np.float32]:
        """Converts the Point3d to a NumPy array.

        Returns:
            npt.NDArray[np.float32]: The NumPy array representation of the Point3d.
        """
        return np.array(self, dtype=np.float32)

    def to_homogeneous(self) -> npt.NDArray[np.float32]:
        """Converts the Point3d to a homogeneous coordinate.

        Returns:
            npt.NDArray[np.float32]: The homogeneous coordinate representation of the Point3d.
        """
        return np.array([self.x, self.y, self.z, 1])


_QuaternionT = TypeVar("_QuaternionT", bound="Quaternion")


class Quaternion(NamedTuple):
    w: float
    x: float
    y: float
    z: float

    @classmethod
    def from_quaternion(
        cls: type[_QuaternionT],
        _quaternion: _k4abt.k4a_quaternion_t,
    ) -> _QuaternionT:
        """Creates a Quaternion instance from a k4a_quaternion_t object.

        Args:
            _quaternion (_k4abt.k4a_quaternion_t): The k4a_quaternion_t object.

        Returns:
            _QuaternionT: The created Quaternion instance.
        """
        _orientation = _quaternion.wxyz
        return cls(
            w=_orientation.w,
            x=_orientation.x,
            y=_orientation.y,
            z=_orientation.z,
        )

    @classmethod
    def transform(
        cls: type[_QuaternionT],
        original_quaternion: _QuaternionT,
        rotation_matrix: npt.NDArray[np.float64],
    ) -> _QuaternionT:
        """Transforms a Quaternion using a transformation matrix.

        Args:
            original_quaternion (_QuaternionT): The original quaternion to transform.
            rotation_matrix  (npt.NDArray[np.float64]): The rotation matrix.

        Returns:
            _QuaternionT: The transformed quaternion.

        Note:
            This method is not implemented and will return the original quaternion.
        """
        transformed_quaternion = Rotation.from_matrix(
            rotation_matrix
        ) * Rotation.from_quat(original_quaternion)
        return cls(*transformed_quaternion.as_quat(False))

        # rotation_quaternion = Rotation.from_matrix(rotation_matrix).as_quat(False)

        # transformed_quaternion = Rotation.from_quat(
        #     rotation_quaternion
        # ) * Rotation.from_quat(original_quaternion)

        # return cls(*transformed_quaternion.as_quat(False))

    def to_dict(self) -> dict:
        """Converts the Quaternion to a dictionary.

        Returns:
            dict: The dictionary representation of the Quaternion.
        """
        # pylint: disable=no-member
        return self._asdict()

    def to_numpy(self) -> npt.NDArray[np.float32]:
        """Converts the Quaternion to a NumPy array.

        Returns:
            npt.NDArray[np.float32]: The NumPy array representation of the Quaternion.
        """
        return np.array(self, dtype=np.float32)


_TrackingJoint3dT = TypeVar("_TrackingJoint3dT", bound="TrackingJoint3d")


class TrackingJoint3d(BaseTrackingJoint[Point3d]):
    __slots__ = ("_orientation",)

    _orientation: Quaternion

    JOINT_ARRAY_LENGTH: ClassVar[int] = 9

    def __init__(
        self,
        joint_id: int,
        position: Point3d,
        orientation: Quaternion,
        confidence_level: JointConfidenceLevel,
    ):
        self._joint_id = joint_id
        self._position = position
        self._orientation = orientation
        self._confidence_level = confidence_level

    @property
    def orientation(self) -> Quaternion:
        """The orientation of the joint."""
        return self._orientation

    @classmethod
    def from_handle_3d(
        cls: type[_TrackingJoint3dT],
        joint_id: int,
        joint_handle: _k4abt.k4abt_joint_t,
    ) -> _TrackingJoint3dT:
        """Creates a TrackingJoint3d instance from a Kinect joint handle.

        Args:
            joint_id (int): The unique identifier for the joint.
            joint_handle (_k4abt.k4abt_joint_t): The Kinect joint handle.

        Returns:
            _TrackingJoint3dT: The created TrackingJoint3d instance.
        """
        _position = Point3d.from_float3(joint_handle.position)
        _orientation = Quaternion.from_quaternion(joint_handle.orientation)
        _confidence_level = JointConfidenceLevel.get_enum_by_mapped_value(
            joint_handle.confidence_level,
        )

        return cls(
            joint_id=joint_id,
            position=_position,
            orientation=_orientation,
            confidence_level=_confidence_level,
        )

    @classmethod
    def from_numpy(
        cls: type[_TrackingJoint3dT],
        joint_array: npt.NDArray[np.float32],
    ) -> _TrackingJoint3dT:
        """Creates a TrackingJoint3d instance from a NumPy array.

        Args:
            joint_array (npt.NDArray[np.float32]): The NumPy array representing the joint.

        Returns:
            _TrackingJoint3dT: The created TrackingJoint3d instance.

        Raises:
            ValueError: If the joint_array does not have enough elements.
        """
        if len(joint_array) != TrackingJoint3d.JOINT_ARRAY_LENGTH:
            raise ValueError(
                f"joint_array must have {TrackingJoint3d.JOINT_ARRAY_LENGTH} elements."
            )

        position = Point3d(*joint_array[:3])
        orientation = Quaternion(*joint_array[3:7])
        confidence_level = JointConfidenceLevel.get_enum_by_mapped_value(
            int(joint_array[7])
        )
        joint_id = int(joint_array[8])

        return cls(
            joint_id=joint_id,
            position=position,
            orientation=orientation,
            confidence_level=confidence_level,
        )

    @classmethod
    def transform(
        cls: type[_TrackingJoint3dT],
        original_joint: _TrackingJoint3dT,
        transform: Transform,
    ) -> _TrackingJoint3dT:
        """Transforms a TrackingJoint3d using a transformation matrix.

        Args:
            original_joint (_TrackingJoint3dT): The original joint to transform.
            transform (Transform): The transformation matrix.

        Returns:
            _TrackingJoint3dT: The transformed joint.
        """
        _position = Point3d.transform(original_joint.position, transform)
        _orientation = Quaternion.transform(
            original_joint.orientation,
            transform.rotation,
        )

        return cls(
            joint_id=original_joint.joint_id,
            position=_position,
            orientation=_orientation,
            confidence_level=original_joint.confidence_level,
        )

    @lru_cache(maxsize=1)
    def to_numpy(self) -> npt.NDArray[np.float32]:
        return np.array(
            [
                self._position.x,
                self._position.y,
                self._position.z,
                self._orientation.w,
                self._orientation.x,
                self._orientation.y,
                self._orientation.z,
                JointConfidenceLevel.to_weight(self._confidence_level),
                self._joint_id,
            ]
        )

    @lru_cache(maxsize=1)
    def to_dict(self) -> dict:
        return {
            "joint_id": self._joint_id,
            "joint_name": self.joint_name,
            "position": self.position,
            "orientation": self.orientation,
            "confidence_level": self.confidence_level,
        }

    def __repr_data__(self) -> dict:
        return {
            "__after_class_name__": self.joint_id,
            "joint_name": self.joint_name,
            "position": self.position,
            "orientation": self.orientation,
            "confidence_level": self.confidence_level,
        }
