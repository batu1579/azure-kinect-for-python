from copy import deepcopy
from typing import ClassVar, TypeVar

import numpy as np
import numpy.typing as npt

from azure_kinect.k4abt.base_body_wapper import RealBodyMarker
from azure_kinect.k4abt.body_3d_wapper import TrackingBody3d
from azure_kinect.k4abt.joint_3d_wapper import TrackingJoint3d
from azure_kinect.k4abt.joint_enum import JOINT_COUNT, JointConfidenceLevel, JointName
from azure_kinect.util import IdCode, IdPool

_LogicBodyT = TypeVar("_LogicBodyT", bound="LogicBody")


# TODO(batu1579): Load this const from config file or env
DISTANCE_THRESHOLD: float = 0.5
QUATERNION_THRESHOLD: float = 0.01
KEY_JOINT_IDS: tuple[int, ...] = (
    JointName.get_mapped_value(JointName.PELVIS),
    JointName.get_mapped_value(JointName.SPINE_CHEST),
    JointName.get_mapped_value(JointName.SPINE_NAVEL),
    JointName.get_mapped_value(JointName.NECK),
    JointName.get_mapped_value(JointName.CLAVICLE_LEFT),
    JointName.get_mapped_value(JointName.CLAVICLE_RIGHT),
)
MIN_MATCHED_JOINTS: int = int(len(KEY_JOINT_IDS) / 3 * 2)


class LogicBody:
    __slots__ = (
        "_body_id",
        "_real_bodies",
        "_marker_map",
    )

    _body_id: IdCode
    _real_bodies: npt.NDArray[np.float32]
    _marker_map: dict[RealBodyMarker, int]

    _ID_POOL: ClassVar[IdPool] = IdPool("Logic body")

    def __init__(self) -> None:
        self._body_id = LogicBody._ID_POOL.get_id()
        self._real_bodies = np.empty(
            (0, JOINT_COUNT, TrackingJoint3d.JOINT_ARRAY_LENGTH),
            dtype=np.float32,
        )
        self._marker_map = {}

    @property
    def is_destoryed(self) -> bool:
        return self._body_id == LogicBody._ID_POOL.get_invalid_id()

    @property
    def body_id(self) -> IdCode:
        return self._body_id

    @property
    def device_serial_numbers(self) -> tuple[str, ...]:
        return tuple(marker.device_serial_number for marker in self.markers)

    @property
    def real_body_count(self) -> int:
        return len(self._real_bodies)

    @property
    def real_bodies(self) -> npt.NDArray[np.float32]:
        return deepcopy(self._real_bodies)

    @property
    def markers(self) -> tuple[RealBodyMarker, ...]:
        return tuple(self._marker_map.keys())

    @classmethod
    def create(
        cls: type[_LogicBodyT],
        real_body: TrackingBody3d,
    ) -> _LogicBodyT:
        instance = cls()
        instance.add_real_body(real_body)

        return instance

    def destroy(self) -> None:
        LogicBody._ID_POOL.release_id(self._body_id)
        self._body_id = LogicBody._ID_POOL.get_invalid_id()

    def is_empty(self) -> bool:
        return len(self._real_bodies) == 0

    def is_belong(self, real_body: TrackingBody3d) -> bool:
        if self.is_empty():
            return False

        real_body_array = real_body.to_numpy()
        matched_points = 0

        for joint_index in KEY_JOINT_IDS:
            logic_joint_positions = self._real_bodies[:, joint_index, :3]
            real_joint_positions = real_body_array[joint_index, :3]

            logic_joint_quaternion = self._real_bodies[:, joint_index, 3:7]
            real_joint_quaternion = real_body_array[joint_index, 3:7]

            position_distance = np.linalg.norm(
                logic_joint_positions - real_joint_positions,
                axis=1,
            )
            quaternion_diff = np.linalg.norm(
                logic_joint_quaternion - real_joint_quaternion,
                axis=1,
            )

            if np.any(position_distance < DISTANCE_THRESHOLD) and np.any(
                quaternion_diff < QUATERNION_THRESHOLD
            ):
                matched_points += 1

        return matched_points >= MIN_MATCHED_JOINTS

    def _get_joint_by_index(self, joint_index: int) -> TrackingJoint3d:
        if self.is_empty():
            raise ValueError(f"No real body found for joint {joint_index}.")

        joint_data = self._real_bodies[:, joint_index, :]
        weights = np.vectorize(JointConfidenceLevel.to_weight)(
            joint_data[:, 7],
        )

        weighted_positions = np.average(
            joint_data[:, :3],
            axis=0,
            weights=weights,
        )
        weighted_quaternions = np.average(
            joint_data[:, 3:7],
            axis=0,
            weights=weights,
        )
        weighted_quaternions /= np.linalg.norm(weighted_quaternions)

        logic_joint = np.concatenate(
            [
                weighted_positions,
                weighted_quaternions,
                [int(np.mean(weights))],
                [joint_index],
            ]
        )

        return TrackingJoint3d.from_numpy(logic_joint)

    def get_joint_by_name(self, joint_name: JointName) -> TrackingJoint3d:
        joint_index = JointName.get_mapped_value(joint_name)
        return self._get_joint_by_index(joint_index)

    def get_joint_by_index(self, joint_index: int) -> TrackingJoint3d:
        if joint_index < 0 or joint_index >= JOINT_COUNT:
            raise ValueError(f"Joint index out of range: {joint_index}")

        return self._get_joint_by_index(joint_index)

    def get_all_joints(self) -> npt.NDArray[np.object_]:
        joints = np.ndarray((JOINT_COUNT,), dtype=np.object_)

        for joint_index in range(JOINT_COUNT):
            joints[joint_index] = self._get_joint_by_index(joint_index)

        return joints

    def to_3d_body(self) -> TrackingBody3d:
        return TrackingBody3d(
            marker=RealBodyMarker(
                body_id=self._body_id.id_,
                device_serial_number="LOGIC_BODY",
            ),
            joints=self.get_all_joints(),
        )

    def add_real_body(self, real_body: TrackingBody3d) -> None:
        self._real_bodies = np.append(
            self._real_bodies,
            [real_body.to_numpy()],
            axis=0,
        )
        self._marker_map[real_body.marker] = self.real_body_count

    def get_real_body(self, marker: RealBodyMarker) -> TrackingBody3d | None:
        index = self._marker_map.get(marker)

        if index is None:
            return None

        return TrackingBody3d.from_numpy(
            marker=marker,
            joint_array=self._real_bodies[index],
        )

    def update_real_body(
        self,
        real_body: TrackingBody3d,
        *,
        add_not_exists: bool = True,
    ) -> bool:
        if not self.is_belong(real_body):
            return False

        index = self._marker_map.get(real_body.marker)

        if index is not None:
            self._real_bodies[index] = real_body.to_numpy()
            return True

        if add_not_exists:
            self.add_real_body(real_body)
            return True

        return False

    def remove_real_body(self, marker: RealBodyMarker) -> None:
        index = self._marker_map.pop(marker, None)

        if index is None:
            return

        self._real_bodies = np.delete(self._real_bodies, index, axis=0)

        # Update marker map indices
        for key, value in self._marker_map.items():
            if value > index:
                self._marker_map[key] = value - 1

    def __del__(self) -> None:
        self.destroy()
