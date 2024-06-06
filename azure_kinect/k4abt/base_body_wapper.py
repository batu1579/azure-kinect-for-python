from dataclasses import dataclass
from functools import cached_property, lru_cache
from typing import ClassVar, Generic, Iterator, TypeVar, cast

import numpy as np
import numpy.typing as npt

from azure_kinect.k4abt.base_joint_wapper import BaseTrackingJoint
from azure_kinect.k4abt.joint_enum import JointName
from azure_kinect.util import ColorGenerator, RGBAColor
from azure_kinect.util.base_wapper import ReprInfo
from azure_kinect.util.color import BGRType


@dataclass(frozen=True)
class RealBodyMarker(ReprInfo):
    __slots__ = ("body_id", "device_serial_number")

    body_id: int
    device_serial_number: str

    _SEPRATOR: ClassVar[str] = ": "

    def __str__(self) -> str:
        return f"{self.device_serial_number}{RealBodyMarker._SEPRATOR}{self.body_id}"

    def __repr_data__(self) -> dict:
        return {
            "body_id": self.body_id,
            "from_device": self.device_serial_number,
        }


_JointT = TypeVar("_JointT", bound=BaseTrackingJoint)
_BaseTrackingBodyT = TypeVar("_BaseTrackingBodyT", bound="BaseTrackingBody")


class BaseTrackingBody(ReprInfo, Generic[_JointT]):
    __slots__ = (
        "_marker",
        "_joints",
        "_body_color",
    )

    _marker: RealBodyMarker
    _joints: npt.NDArray[np.object_]
    _body_color: RGBAColor

    _TO_NUMPY_FUNC: ClassVar[np.ufunc] = np.frompyfunc(
        lambda joint: cast(_JointT, joint).to_numpy(),
        1,
        1,
    )
    _BODY_COLOR_GENERATOR: ClassVar[Iterator[RGBAColor]] = ColorGenerator(
        step=60,
        saturation=1,
        brightness=0.5,
    )

    def __init__(
        self,
        marker: RealBodyMarker,
        joints: npt.NDArray[np.object_],
    ) -> None:
        # TODO(batu1579): Needs to check the length of joints ?
        self._marker = marker
        self._joints = joints
        self._body_color = BaseTrackingBody.get_body_color(marker)

    @property
    def body_id(self) -> int:
        """The unique identifier for the body."""
        return self._marker.body_id

    @property
    def device_serial_number(self) -> str:
        """The name of the device from which the body is tracked."""
        return self._marker.device_serial_number

    @property
    def marker(self) -> RealBodyMarker:
        """A string that uniquely identifies the body and the device."""
        return self._marker

    @property
    def body_color(self) -> BGRType:
        """The color assigned to the body for visualization."""
        return self._body_color.as_bgr()

    @property
    def joints(self) -> npt.NDArray[np.object_]:
        """The joint positions of the body."""
        return self._joints

    @cached_property
    def joints_array(self) -> npt.NDArray[np.float32]:
        return self.to_numpy()

    @cached_property
    def joints_position(self) -> npt.NDArray[np.float32]:
        return self.joints_array[:, :3]

    @cached_property
    def joints_quaternion(self) -> npt.NDArray[np.float32]:
        return self.joints_array[:, 3:7]

    @cached_property
    def joints_weight(self) -> npt.NDArray[np.float32]:
        return self.joints_array[:, 7]

    @property
    def joints_count(self) -> int:
        return len(self._joints)

    @staticmethod
    @lru_cache
    def get_body_color(_: RealBodyMarker) -> RGBAColor:
        return next(BaseTrackingBody._BODY_COLOR_GENERATOR)

    @classmethod
    def create(
        cls: type[_BaseTrackingBodyT],
        body_id: int,
        device_serial_number: str,
        joints: npt.NDArray[np.object_],
    ) -> _BaseTrackingBodyT:
        marker = RealBodyMarker(
            body_id=body_id,
            device_serial_number=device_serial_number,
        )
        return cls(marker=marker, joints=joints)

    def to_numpy(self) -> npt.NDArray[np.float32]:
        """Converts the body's joint positions to a NumPy array.

        Returns:
            npt.NDArray[np.float32]: A NumPy array containing the joint positions.
        """
        array = BaseTrackingBody._TO_NUMPY_FUNC(self._joints)
        return np.stack(array, axis=0)

    def to_dict(self) -> dict:
        """Converts the body's information to a dictionary.

        Returns:
            dict: A dictionary containing the body's ID and joint information.
        """
        return {
            "body_id": self.body_id,
            "joints": [cast(_JointT, joint).to_dict() for joint in self._joints],
        }

    def get_joint_by_name(self, joint_name: JointName) -> _JointT:
        """Retrieves a specific joint from the body.

        Args:
            joint_name (JointName): The name of the joint to retrieve.

        Returns:
            _JointT: The requested joint.
        """
        _joint_index = JointName.get_mapped_value(joint_name)
        return self._joints[_joint_index]

    def __iter__(self) -> Iterator[_JointT]:
        """Allows iteration over the body's joints."""
        return iter(self._joints)

    def __repr_data__(self) -> dict:
        """Provides data for the representation of the body."""
        return {
            "id": self.body_id,
            "from_device": self.device_serial_number,
        }
