from typing import Iterator, Optional

from simple_singleton import singleton

from azure_kinect.k4a import WAIT_INFINITE, K4ADevice
from azure_kinect.k4abt.config_tracker import TrackerConfig
from azure_kinect.k4abt.frame_wapper import TrackingFrame
from azure_kinect.k4abt.tracker_wapper import K4ABodyTracker
from azure_kinect.registration import SceneRegistration
from azure_kinect.transform import Transform
from azure_kinect.util import IdCode, Logger, ResultStatus, WaitResultStatus


@singleton(thread_safe=True, allow_subclass=True)
class TrackerManager:
    __slots__ = (
        "_trackers",
        "_tracker_id_map",
        "_dom_tracker_index",
    )

    _trackers: list[K4ABodyTracker]
    _tracker_id_map: dict[IdCode, int]  # {tracker_id: tracker_index}
    _dom_tracker_index: int

    def __init__(self) -> None:
        self._trackers = []
        self._tracker_id_map = {}
        self._dom_tracker_index = -1

    @property
    def dom_tracker(self) -> K4ABodyTracker:
        if self._dom_tracker_index == -1:
            Logger.debug("Dom tracker is not set. Try to set it automatically.")
            index = self._get_dom_tracker_index()

            if index == -1:
                raise RuntimeError("No dom tracker found!")

            self._dom_tracker_index = index

        return self._trackers[self._dom_tracker_index]

    @property
    def sub_trackers(self) -> Iterator[K4ABodyTracker]:
        if self.tracker_count == 0:
            return

        for index, tracker in enumerate(self._trackers):
            if index != self._dom_tracker_index:
                yield tracker

    @property
    def tracker_count(self) -> int:
        return len(self._trackers)

    def _get_dom_tracker_index(self) -> int:
        for index, tracker in enumerate(self._trackers):
            if tracker.tracker_id == self.dom_tracker.tracker_id:
                return index

        return -1

    def set_dom_tracker(self, tracker_id: IdCode) -> None:
        index = self._tracker_id_map.get(tracker_id)

        if index is None:
            Logger.warning(f"Failed to find tracker with id: {tracker_id}")
            return

        self._dom_tracker_index = index
        self._trackers[index].set_device_transform(Transform.identity())

    def add_tracker(
        self,
        device: K4ADevice,
        *,
        config: Optional[TrackerConfig] = None,
        auto_dom_tracker: bool = True,
    ) -> IdCode | None:
        status, tracker = K4ABodyTracker.create(device, config=config)

        if status == ResultStatus.FAILED:
            Logger.warning("Failed to create tracker")
            return None

        index = self.tracker_count
        self._trackers.append(tracker)
        self._tracker_id_map.update({tracker.tracker_id: index})

        if auto_dom_tracker and device.is_dom:
            self._dom_tracker_index = index
            Logger.debug(f"Set dom tracker: {self.dom_tracker}")

        Logger.debug(f"Added tracker: {tracker}")
        return tracker.tracker_id

    def get_tracker(self, tracker_id: IdCode) -> K4ABodyTracker | None:
        tracker_index = self._tracker_id_map.get(tracker_id)

        if tracker_index is None:
            Logger.warning(f"Failed to find tracker with id: {tracker_id}")
            return None

        return self._trackers[tracker_index]

    def get_iterator(
        self,
        *,
        start_with_dom: bool = True,
    ) -> Iterator[K4ABodyTracker]:
        if start_with_dom:
            yield self.dom_tracker
            yield from self.sub_trackers
        else:
            yield from self._trackers

    def set_scene_registration(self, scene_config: SceneRegistration) -> None:
        if self.dom_tracker.bound_device.serial_number != scene_config.dom_device:
            Logger.warning(
                "The current dom device is different from the dom device "
                + "in the scene setting. It is recommended to re-register "
                + "the device to ensure the correct transformation matrix "
            )

        for tracker in self._trackers:
            bound_device = tracker.bound_device
            transform = scene_config.device_transforms.get(bound_device.serial_number)

            if transform is None:
                Logger.warning(
                    f"Failed to find transform matrix for device: {bound_device}. "
                    + "It is recommended to re-register the device."
                )
                transform = Transform.identity()

            tracker.set_device_transform(transform)

    def get_scene_registration(self, scene_name: str) -> SceneRegistration:
        dom_device = self.dom_tracker.bound_device
        transforms: dict[str, Transform] = {}

        for tracker in self._trackers:
            bound_device = tracker.bound_device
            transforms[bound_device.serial_number] = tracker.device_transform

        return SceneRegistration(
            scene_name=scene_name,
            dom_device=dom_device.serial_number,
            device_transforms=transforms,
        )

    def shutdown_tracker(self, tracker_id: IdCode) -> None:
        for index, tracker in enumerate(self._trackers):
            if tracker.tracker_id != tracker_id:
                continue

            if index == self._dom_tracker_index:
                self._dom_tracker_index = -1

            self._trackers.pop(index)
            self._tracker_id_map.pop(tracker_id)
            return

        Logger.warning(f"Failed to find tracker with id: {tracker_id}")

    def shutdown_all_trackers(self) -> None:
        self._trackers = []
        self._tracker_id_map = {}
        self._dom_tracker_index = -1

    def enqueue_all_captures(self, timeout_in_ms: int = WAIT_INFINITE) -> None:
        for tracker in self._trackers:
            enqueue_result = tracker.enqueue_capture(timeout_in_ms=timeout_in_ms)

            if enqueue_result == WaitResultStatus.FAILED:
                Logger.warning(
                    f"Failed to enqueue capture from device: {tracker.bound_device}"
                )

    def _pop_frame(
        self,
        tracker: K4ABodyTracker,
        timeout_in_ms: int,
    ) -> TrackingFrame | None:
        frame_status, frame = tracker.pop_result(timeout_in_ms)

        if frame_status == WaitResultStatus.FAILED:
            Logger.warning(f"Failed to pop frame from tracker: {tracker}")

        return frame if frame_status == WaitResultStatus.SUCCEEDED else None

    def pop_frame(
        self,
        tracker_id: IdCode,
        timeout_in_ms: int = WAIT_INFINITE,
    ) -> TrackingFrame | None:
        """Pop a frame from a specific tracker by its id.

        Args:
            tracker_id (IdCode): tracker id.
            timeout_in_ms (int, optional): timeout for pop operation. If it is
                set to 0, it is returned immediately. Defaults to WAIT_INFINITE.

        Returns:
            TrackingFrame | None: Poped frame.
        """
        for tracker in self._trackers:
            if tracker.tracker_id == tracker_id:
                return self._pop_frame(tracker, timeout_in_ms)

        Logger.debug(f"Failed to find tracker with id: {tracker_id}")
        return None

    def pop_all_frames(
        self,
        timeout_in_ms: int = WAIT_INFINITE,
        *,
        start_with_dom: bool = True,
    ) -> Iterator[TrackingFrame]:
        """Pop a frame from a specific tracker by its id.

        Args:
            timeout_in_ms (int, optional): The timeout to each frame. If it is
                set to 0, it is returned immediately. Defaults to WAIT_INFINITE.
            start_with_dom(bool, optional): Start with frame from dom tracker

        Returns:
            TrackingFrame | None: Poped frame.
        """
        if start_with_dom:
            frame = self._pop_frame(self.dom_tracker, timeout_in_ms)

            if frame is not None:
                yield frame

        for tracker in self._trackers:
            if tracker is self.dom_tracker and start_with_dom:
                continue

            frame = self._pop_frame(tracker, timeout_in_ms)

            if frame is not None:
                yield frame

    def __del__(self) -> None:
        self.shutdown_all_trackers()
