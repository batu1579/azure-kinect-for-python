from abc import abstractmethod
from typing import Generic, Protocol, TypeVar, cast

import numpy as np
import numpy.typing as npt

from azure_kinect.k4abt.joint_enum import JOINT_NAME_MAP, JointConfidenceLevel
from azure_kinect.util.base_wapper import ReprInfo
from azure_kinect.util.types import ToDictMixin, ToNumpyMixin

_PointT = TypeVar("_PointT", bound="BasePoint")


class BasePoint(ToNumpyMixin, ToDictMixin, Protocol):
    pass


_TrackingJointT = TypeVar("_TrackingJointT", bound="BaseTrackingJoint")


class BaseTrackingJoint(ReprInfo, Generic[_PointT]):
    __slots__ = ("_joint_id", "_position", "_confidence_level")

    _joint_id: int
    _position: _PointT
    _confidence_level: JointConfidenceLevel

    @property
    def joint_id(self) -> int:
        """The unique identifier for the joint."""
        return self._joint_id

    @property
    def joint_name(self) -> str:
        """The name of the joint."""
        return JOINT_NAME_MAP[self._joint_id]

    @property
    def position(self) -> _PointT:
        """The position of the joint."""
        return self._position

    @property
    def confidence_level(self) -> JointConfidenceLevel:
        """The confidence level of the joint's tracking."""
        return self._confidence_level

    def get_distance(
        self: _TrackingJointT,
        other: _TrackingJointT,
    ) -> float:
        """Calculates the Euclidean distance between this joint and another joint.

        Args:
            other (_TrackingJointT): The other joint to compare with.

        Returns:
            float: The Euclidean distance between the two joints.
        """
        self_position = cast(BasePoint, self._position).to_numpy()
        other_position = cast(BasePoint, other.position).to_numpy()

        return float(np.linalg.norm(self_position - other_position))

    @abstractmethod
    def to_numpy(self) -> npt.NDArray[np.float32]:
        """Converts the joint's position to a NumPy array."""
        ...

    @abstractmethod
    def to_dict(self) -> dict:
        """Converts the joint's information to a dictionary."""
        ...

    @abstractmethod
    def __repr_data__(self) -> dict: ...
