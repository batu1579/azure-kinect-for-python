from functools import lru_cache
from typing import NamedTuple, TypeVar

import numpy as np
import numpy.typing as npt
from pykinect_azure.k4a import _k4a
from pykinect_azure.k4abt import _k4abt

from azure_kinect.k4abt.base_joint_wapper import BaseTrackingJoint
from azure_kinect.k4abt.joint_enum import JointConfidenceLevel
from azure_kinect.util.types import Coordinate2d

_Point2dT = TypeVar("_Point2dT", bound="Point2d")


class Point2d(NamedTuple):
    x: float
    y: float

    @classmethod
    def from_float2(
        cls: type[_Point2dT],
        _coordinates: _k4a.k4a_float2_t,
    ) -> _Point2dT:
        """Creates a Point2d instance from a k4a_float2_t object.

        Args:
            _coordinates (_k4a.k4a_float2_t): The k4a_float2_t object.

        Returns:
            _Point2dT: The created Point2d instance.
        """
        _position = _coordinates.xy
        return cls(
            x=_position.x,
            y=_position.y,
        )

    def to_float2(self) -> _k4a.k4a_float2_t:
        """Converts the Point2d to a k4a_float2_t object."""
        return _k4a.k4a_float2_t(self)

    def to_coordinates(self) -> Coordinate2d:
        """Converts the Point2d to a tuple of integers.

        Returns:
            _Coordinates: The tuple representation of the Point2d.
        """
        return (int(self.x), int(self.y))

    def to_dict(self) -> dict:
        """Converts the Point2d to a dictionary.

        Returns:
            dict: The dictionary representation of the Point2d.
        """
        # pylint: disable=no-member
        return self._asdict()

    def to_numpy(self) -> npt.NDArray[np.float32]:
        """Converts the Point2d to a NumPy array.

        Returns:
            npt.NDArray[np.float32]: The NumPy array representation of the Point2d.
        """
        return np.array(self, dtype=np.float32)


_TrackingJoint2dT = TypeVar("_TrackingJoint2dT", bound="TrackingJoint2d")


class TrackingJoint2d(BaseTrackingJoint[Point2d]):
    __slots__ = ()

    def __init__(
        self,
        joint_id: int,
        position: Point2d,
        confidence_level: JointConfidenceLevel,
    ) -> None:
        self._joint_id = joint_id
        self._position = position
        self._confidence_level = confidence_level

    @classmethod
    def from_handle(
        cls: type[_TrackingJoint2dT],
        joint_id: int,
        joint_handle: _k4abt.k4abt_joint2D_t,
    ) -> _TrackingJoint2dT:
        _position = Point2d.from_float2(joint_handle.position)
        _confidence_level = JointConfidenceLevel.get_enum_by_mapped_value(
            joint_handle.confidence_level
        )

        return cls(
            joint_id=joint_id,
            position=_position,
            confidence_level=_confidence_level,
        )

    @lru_cache(maxsize=1)
    def to_numpy(self) -> npt.NDArray[np.float32]:
        return np.array(
            [
                self._position.x,
                self._position.y,
                JointConfidenceLevel.get_mapped_value(self._confidence_level),
            ],
            dtype=np.float32,
        )

    @lru_cache(maxsize=1)
    def to_dict(self) -> dict:
        return {
            "joint_id": self._joint_id,
            "joint_name": self.joint_name,
            "confidence_level": self.confidence_level,
            "position": self.position,
        }

    def __repr_data__(self) -> dict:
        return {
            "__after_class_name__": self.joint_name,
            "position": self.position,
            "confidence_level": self.confidence_level,
        }
