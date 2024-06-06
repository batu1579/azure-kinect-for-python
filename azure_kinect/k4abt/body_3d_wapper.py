from typing import ClassVar, TypeVar, cast

import numpy as np
import numpy.typing as npt
from pykinect_azure.k4abt import _k4abt

from azure_kinect.k4abt.base_body_wapper import BaseTrackingBody, RealBodyMarker
from azure_kinect.k4abt.joint_3d_wapper import TrackingJoint3d
from azure_kinect.k4abt.joint_enum import JOINT_COUNT
from azure_kinect.transform import Transform

_TrackingBody3dT = TypeVar("_TrackingBody3dT", bound="TrackingBody3d")


class TrackingBody3d(BaseTrackingBody[TrackingJoint3d]):
    __slots__ = ()

    _FROM_NUMPY_FUNC: ClassVar[np.ufunc] = np.frompyfunc(
        TrackingJoint3d.from_numpy,
        1,
        1,
    )

    @classmethod
    def from_handle(
        cls: type[_TrackingBody3dT],
        body_handle: _k4abt.k4abt_body_t,
        device_serial_number: str,
    ) -> _TrackingBody3dT:
        """Creates a 3D tracking body from a Kinect body handle.

        Args:
            body_handle (_k4abt.k4abt_body_t): The Kinect body handle.
            device_serial_number (str): The name of the device from which
                the body is tracked.

        Returns:
            _TrackingBody3dT: The created 3D tracking body.
        """
        joints = np.ndarray((JOINT_COUNT,), dtype=np.object_)

        for id_, joint in enumerate(body_handle.skeleton.joints):
            joints[id_] = TrackingJoint3d.from_handle_3d(
                joint_id=id_,
                joint_handle=cast(_k4abt.k4abt_joint_t, joint),
            )

        return cls.create(
            body_handle.id,
            device_serial_number,
            joints,
        )

    @classmethod
    def from_numpy(
        cls: type[_TrackingBody3dT],
        marker: RealBodyMarker,
        joint_array: npt.NDArray[np.float32],
    ) -> _TrackingBody3dT:
        """Creates a TrackingBody3d instance from a NumPy array.

        Args:
            marker (RealBodyMarker): The marker associated with the body.
            joint_array (npt.NDArray[np.float32]): A NumPy array containing the joint positions.

        Returns:
            TrackingBody3d: An instance of TrackingBody3d.
        """
        if len(joint_array) != JOINT_COUNT * TrackingJoint3d.JOINT_ARRAY_LENGTH:
            raise ValueError(
                f"Expected {JOINT_COUNT * TrackingJoint3d.JOINT_ARRAY_LENGTH} elements, "
                + f"but got {len(joint_array)}.",
            )

        joints = np.empty(JOINT_COUNT, dtype=np.object_)

        for joint_index in range(JOINT_COUNT):
            start_index = joint_index * 9
            end_index = start_index + 9
            joint_data = joint_array[start_index:end_index]
            joints[joint_index] = TrackingJoint3d.from_numpy(joint_data)

        return cls(marker, joints)

    @classmethod
    def transform(
        cls: type[_TrackingBody3dT],
        original_body: _TrackingBody3dT,
        transform: Transform,
    ) -> _TrackingBody3dT:
        """Transforms a 3D tracking body using a transformation matrix.

        Args:
            original_body (_TrackingBody3dT): The original 3D tracking body
                to transform.
            transform (Transform): The transformation
                matrix to apply.

        Returns:
            _TrackingBody3dT: The transformed 3D tracking body.
        """
        transformed_joints = np.ndarray(
            (JOINT_COUNT,),
            dtype=np.object_,
        )

        for joint_id, joint in enumerate(original_body):
            joint = cast(TrackingJoint3d, joint)
            transformed_joints[joint_id] = TrackingJoint3d.transform(joint, transform)

        return cls(
            marker=original_body.marker,
            joints=transformed_joints,
        )
