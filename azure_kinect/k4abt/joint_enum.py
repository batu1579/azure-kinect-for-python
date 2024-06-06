from enum import Enum

from pykinect_azure.k4abt import _k4abt, _k4abtTypes

from azure_kinect.util import EnumExtend


class JointConfidenceLevel(EnumExtend[int], str, Enum):
    NONE = "The joint is out of range (too far from depth camera)"
    LOW = "The joint is not observed (likely due to occlusion), predicted joint pose."
    MEDIUM = (
        "Medium confidence in joint pose. "
        + "Current SDK will only provide joints up to this confidence level"
    )
    HIGH = "High confidence in joint pose. " + "Placeholder for future SDK"

    @classmethod
    def _get_value_map(
        cls: type["JointConfidenceLevel"],
    ) -> dict["JointConfidenceLevel", int]:
        return {
            JointConfidenceLevel.NONE: _k4abtTypes.K4ABT_JOINT_CONFIDENCE_NONE,
            JointConfidenceLevel.LOW: _k4abtTypes.K4ABT_JOINT_CONFIDENCE_LOW,
            JointConfidenceLevel.MEDIUM: _k4abtTypes.K4ABT_JOINT_CONFIDENCE_MEDIUM,
            JointConfidenceLevel.HIGH: _k4abtTypes.K4ABT_JOINT_CONFIDENCE_HIGH,
        }

    @classmethod
    def to_weight(
        cls: type["JointConfidenceLevel"],
        confidence_level: "JointConfidenceLevel | int",
    ) -> float:
        """Converts the confidence level to a weight value.

        Args:
            confidence_level (JointConfidenceLevel | int): The confidence level.

        Returns:
            float: The weight value.

        Raises:
            TypeError: If the confidence level is not a valid type.
        """
        if isinstance(confidence_level, cls):
            confidence_level = cls.get_mapped_value(confidence_level)
        else:
            raise TypeError(
                f"Invalid type of confidence level: {confidence_level}",
            )

        return confidence_level / JointConfidenceLevel.get_mapped_value(
            JointConfidenceLevel.MEDIUM
        )


CONFIDENCE_LEVEL_COUNT = _k4abtTypes.K4ABT_JOINT_CONFIDENCE_LEVELS_COUNT


class JointName(EnumExtend[int], str, Enum):
    PELVIS = "pelvis"
    SPINE_NAVEL = "spine - navel"
    SPINE_CHEST = "spine - chest"
    NECK = "neck"
    CLAVICLE_LEFT = "left clavicle"
    SHOULDER_LEFT = "left shoulder"
    ELBOW_LEFT = "left elbow"
    WRIST_LEFT = "left wrist"
    HAND_LEFT = "left hand"
    HANDTIP_LEFT = "left handtip"
    THUMB_LEFT = "left thumb"
    CLAVICLE_RIGHT = "right clavicle"
    SHOULDER_RIGHT = "right shoulder"
    ELBOW_RIGHT = "right elbow"
    WRIST_RIGHT = "right wrist"
    HAND_RIGHT = "right hand"
    HANDTIP_RIGHT = "right handtip"
    THUMB_RIGHT = "right thumb"
    HIP_LEFT = "left hip"
    KNEE_LEFT = "left knee"
    ANKLE_LEFT = "left ankle"
    FOOT_LEFT = "left foot"
    HIP_RIGHT = "right hip"
    KNEE_RIGHT = "right knee"
    ANKLE_RIGHT = "right ankle"
    FOOT_RIGHT = "right foot"
    HEAD = "head"
    NOSE = "nose"
    EYE_LEFT = "left eye"
    EAR_LEFT = "left ear"
    EYE_RIGHT = "right eye"
    EAR_RIGHT = "right ear"

    @classmethod
    def _get_value_map(cls: type["JointName"]) -> dict["JointName", int]:
        return {
            JointName.PELVIS: _k4abtTypes.K4ABT_JOINT_PELVIS,
            JointName.SPINE_NAVEL: _k4abtTypes.K4ABT_JOINT_SPINE_NAVEL,
            JointName.SPINE_CHEST: _k4abtTypes.K4ABT_JOINT_SPINE_CHEST,
            JointName.NECK: _k4abtTypes.K4ABT_JOINT_NECK,
            JointName.CLAVICLE_LEFT: _k4abtTypes.K4ABT_JOINT_CLAVICLE_LEFT,
            JointName.SHOULDER_LEFT: _k4abtTypes.K4ABT_JOINT_SHOULDER_LEFT,
            JointName.ELBOW_LEFT: _k4abtTypes.K4ABT_JOINT_ELBOW_LEFT,
            JointName.WRIST_LEFT: _k4abtTypes.K4ABT_JOINT_WRIST_LEFT,
            JointName.HAND_LEFT: _k4abtTypes.K4ABT_JOINT_HAND_LEFT,
            JointName.HANDTIP_LEFT: _k4abtTypes.K4ABT_JOINT_HANDTIP_LEFT,
            JointName.THUMB_LEFT: _k4abtTypes.K4ABT_JOINT_THUMB_LEFT,
            JointName.CLAVICLE_RIGHT: _k4abtTypes.K4ABT_JOINT_CLAVICLE_RIGHT,
            JointName.SHOULDER_RIGHT: _k4abtTypes.K4ABT_JOINT_SHOULDER_RIGHT,
            JointName.ELBOW_RIGHT: _k4abtTypes.K4ABT_JOINT_ELBOW_RIGHT,
            JointName.WRIST_RIGHT: _k4abtTypes.K4ABT_JOINT_WRIST_RIGHT,
            JointName.HAND_RIGHT: _k4abtTypes.K4ABT_JOINT_HAND_RIGHT,
            JointName.HANDTIP_RIGHT: _k4abtTypes.K4ABT_JOINT_HANDTIP_RIGHT,
            JointName.THUMB_RIGHT: _k4abtTypes.K4ABT_JOINT_THUMB_RIGHT,
            JointName.HIP_LEFT: _k4abtTypes.K4ABT_JOINT_HIP_LEFT,
            JointName.KNEE_LEFT: _k4abtTypes.K4ABT_JOINT_KNEE_LEFT,
            JointName.ANKLE_LEFT: _k4abtTypes.K4ABT_JOINT_ANKLE_LEFT,
            JointName.FOOT_LEFT: _k4abtTypes.K4ABT_JOINT_FOOT_LEFT,
            JointName.HIP_RIGHT: _k4abtTypes.K4ABT_JOINT_HIP_RIGHT,
            JointName.KNEE_RIGHT: _k4abtTypes.K4ABT_JOINT_KNEE_RIGHT,
            JointName.ANKLE_RIGHT: _k4abtTypes.K4ABT_JOINT_ANKLE_RIGHT,
            JointName.FOOT_RIGHT: _k4abtTypes.K4ABT_JOINT_FOOT_RIGHT,
            JointName.HEAD: _k4abtTypes.K4ABT_JOINT_HEAD,
            JointName.NOSE: _k4abtTypes.K4ABT_JOINT_NOSE,
            JointName.EYE_LEFT: _k4abtTypes.K4ABT_JOINT_EYE_LEFT,
            JointName.EAR_LEFT: _k4abtTypes.K4ABT_JOINT_EAR_LEFT,
            JointName.EYE_RIGHT: _k4abtTypes.K4ABT_JOINT_EYE_RIGHT,
            JointName.EAR_RIGHT: _k4abtTypes.K4ABT_JOINT_EAR_RIGHT,
        }


JOINT_COUNT = _k4abtTypes.K4ABT_JOINT_COUNT
JOINT_NAME_MAP = tuple(_k4abt.K4ABT_JOINT_NAMES)
SEGMENT_PAIRS = tuple(tuple(i) for i in _k4abt.K4ABT_SEGMENT_PAIRS)


class TrackedJointPresent(EnumExtend[tuple[JointName, ...]], str, Enum):
    BASIC = "Only basic joints will be tracked."
    ADVANCED = "Both basic and advanced joints will be tracked."
    ALL = "All joints of body will be tracked."

    @classmethod
    def _get_value_map(
        cls: type["TrackedJointPresent"],
    ) -> dict["TrackedJointPresent", tuple[JointName, ...]]:
        basic_joints = (
            JointName.PELVIS,
            JointName.NECK,
            JointName.SHOULDER_LEFT,
            JointName.SHOULDER_RIGHT,
            JointName.ELBOW_LEFT,
            JointName.ELBOW_RIGHT,
            JointName.WRIST_LEFT,
            JointName.WRIST_RIGHT,
            JointName.HIP_LEFT,
            JointName.HIP_RIGHT,
            JointName.KNEE_LEFT,
            JointName.KNEE_RIGHT,
            JointName.ANKLE_LEFT,
            JointName.ANKLE_RIGHT,
        )
        advanced_joints = (
            JointName.HEAD,
            JointName.CLAVICLE_LEFT,
            JointName.CLAVICLE_RIGHT,
            JointName.SPINE_CHEST,
            JointName.SPINE_NAVEL,
        )

        return {
            TrackedJointPresent.BASIC: basic_joints,
            TrackedJointPresent.ADVANCED: basic_joints + advanced_joints,
            TrackedJointPresent.ALL: tuple(JointName),
        }
