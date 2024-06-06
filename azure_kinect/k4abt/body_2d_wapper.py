from typing import TypeVar, cast

import numpy as np
from pykinect_azure.k4abt import _k4abt

from azure_kinect.k4a import CalibrationType, K4ACalibration
from azure_kinect.k4abt.base_body_wapper import BaseTrackingBody
from azure_kinect.k4abt.joint_2d_wapper import TrackingJoint2d
from azure_kinect.k4abt.joint_enum import JOINT_COUNT
from azure_kinect.util import ResultStatus

_TrackingBody2dT = TypeVar("_TrackingBody2dT", bound="TrackingBody2d")


class TrackingBody2d(BaseTrackingBody[TrackingJoint2d]):
    __slots__ = ()

    @classmethod
    def from_handle_2d(
        cls: type[_TrackingBody2dT],
        body_handle: _k4abt.k4abt_body2D_t,
        device_serial_number: str,
    ) -> _TrackingBody2dT:
        joints = np.ndarray((JOINT_COUNT,), dtype=np.object_)

        for id_, joint in enumerate(body_handle.skeleton.joints2D):
            joints[id_] = TrackingJoint2d.from_handle(
                joint_id=id_,
                joint_handle=cast(_k4abt.k4abt_joint2D_t, joint),
            )

        return cls.create(body_handle.id, device_serial_number, joints)

    @classmethod
    def from_handle_3d(
        cls: type[_TrackingBody2dT],
        body_handle: _k4abt.k4abt_body_t,
        device_serial_number: str,
        calibration: K4ACalibration,
        target_camera: CalibrationType,
    ) -> _TrackingBody2dT:
        joints = np.ndarray((JOINT_COUNT,), dtype=np.object_)

        for id_, joint in enumerate(body_handle.skeleton.joints):
            joint = cast(_k4abt.k4abt_joint_t, joint)

            result, position = calibration.convert_3d_to_2d(
                joint.position,
                source_camera=CalibrationType.DEPTH,
                target_camera=target_camera,
            )

            if result == ResultStatus.FAILED:
                raise ValueError(f"Failed to convert joint {joint} to 2D")

            joint_handle = _k4abt.k4abt_joint2D_t()
            joint_handle.position = position
            joint_handle.confidence_level = joint.confidence_level

            joints[id_] = TrackingJoint2d.from_handle(
                joint_id=id_,
                joint_handle=joint_handle,
            )

        return cls.create(body_handle.id, device_serial_number, joints)
