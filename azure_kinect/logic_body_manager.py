from typing import Iterable, Iterator, Literal, overload

from azure_kinect.k4abt.base_body_wapper import RealBodyMarker
from azure_kinect.k4abt.body_3d_wapper import TrackingBody3d
from azure_kinect.k4abt.frame_wapper import TrackingFrame
from azure_kinect.k4abt.logic_body import LogicBody
from azure_kinect.util.id_pool import IdCode


class LogicBodyManager:
    __slots__ = ("_logic_bodies", "_markers_map")

    _logic_bodies: dict[IdCode, LogicBody]  # {logic_body_id: logic_body}
    _markers_map: dict[RealBodyMarker, IdCode]  # {real_body_maker: logic_body_id}

    def __init__(self) -> None:
        self._logic_bodies = {}
        self._markers_map = {}

    @property
    def logic_body_count(self) -> int:
        return len(self._logic_bodies)

    @property
    def real_body_count(self) -> int:
        return len(self._markers_map)

    def get_logic_body(self, id_: IdCode) -> LogicBody | None:
        return self._logic_bodies.get(id_)

    def _remove_real_bodies(self, _markers: Iterable[RealBodyMarker]) -> None:
        for marker in _markers:
            logic_body_id = self._markers_map[marker]
            logic_body = self._logic_bodies[logic_body_id]

            logic_body.remove_real_body(marker)
            self._markers_map.pop(marker)

    def _remove_logic_bodies(self, _ids: Iterable[IdCode]) -> None:
        useless_markers: set[RealBodyMarker] = set()

        for logic_body_id in _ids:
            logic_body = self._logic_bodies[logic_body_id]
            useless_markers.update(logic_body.markers)

            LogicBody.destroy(logic_body)
            self._logic_bodies.pop(logic_body_id)

        # clear mapped markers
        self._markers_map = {
            marker: mapped_id
            for marker, mapped_id in self._markers_map.items()
            if mapped_id not in useless_markers
        }

    def update_logic_bodies(
        self,
        from_frames: Iterable[TrackingFrame],
    ) -> None:
        unused_logic_bodies: set[IdCode] = set(self._logic_bodies.keys())
        all_real_bodies: dict[RealBodyMarker, TrackingBody3d] = {}

        # Get all real bodies
        for frame in from_frames:
            for body in frame.get_3d_body_iterator():
                all_real_bodies[body.marker] = body

        # Remove useless real bodies
        self._remove_real_bodies(
            set(self._markers_map.keys()) - set(all_real_bodies.keys())
        )

        # Update logic bodies
        empty_logic_bodies: set[IdCode] = set()

        for marker, real_body in all_real_bodies.items():
            logic_body_id = self._markers_map.get(marker)

            if logic_body_id is None:
                continue

            logic_body = self._logic_bodies[logic_body_id]

            if logic_body.update_real_body(real_body, add_not_exists=False):
                # Remove from unused set
                unused_logic_bodies.remove(logic_body_id)
                all_real_bodies.pop(marker)
                continue

            # Remove real body and mapping
            logic_body.remove_real_body(real_body.marker)
            self._markers_map.pop(real_body.marker)

            if logic_body.is_empty():
                empty_logic_bodies.add(logic_body_id)

        self._remove_logic_bodies(empty_logic_bodies)

        # Check if the unmatched real body belongs to another logical body
        for logic_body_id, logic_body in self._logic_bodies.items():
            for marker, real_body in all_real_bodies.items():
                if logic_body.is_belong(real_body):
                    # Add if it belongs
                    logic_body.add_real_body(real_body)

                    # Mapping
                    self._markers_map[marker] = logic_body_id

        # Remove useless logic bodies
        self._remove_logic_bodies(unused_logic_bodies)

        # Create logic body for every new real body
        for marker, real_body in all_real_bodies.items():
            new_logic_body = LogicBody.create(real_body)

            # Mapping
            self._logic_bodies[new_logic_body.body_id] = new_logic_body
            self._markers_map[marker] = new_logic_body.body_id

    @overload
    def get_iterator(
        self,
        *,
        to_unreal: Literal[False],
    ) -> Iterator[LogicBody]: ...

    @overload
    def get_iterator(
        self,
        *,
        to_unreal: Literal[True],
    ) -> Iterator[TrackingBody3d]: ...

    def get_iterator(
        self,
        to_unreal: bool = True,
    ) -> Iterator[LogicBody | TrackingBody3d]:
        if to_unreal:
            for logic_body in self._logic_bodies.values():
                yield logic_body.to_3d_body()
        else:
            yield from self._logic_bodies.values()
