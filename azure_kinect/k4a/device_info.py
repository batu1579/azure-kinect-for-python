from typing import NamedTuple

from pykinect_azure.k4a import _k4a


class HardwareVersion(NamedTuple):
    audio: str
    depth: str
    rgb: str
    depth_sensor: str

    @staticmethod
    def to_version_str(version: _k4a.k4a_version_t) -> str:
        """Turn a k4a_version_t struct into a string

        Args:
            version (_k4a.k4a_version_t): k4a_version_t struct

        Returns:
            str: version string
        """
        return f"{version.major}.{version.minor}.{version.iteration}"


class SyncJackStatus(NamedTuple):
    sync_in_jack_connected: bool
    sync_out_jack_connected: bool
