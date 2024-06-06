from dataclasses import dataclass
from functools import lru_cache
from itertools import count
from typing import ClassVar, Iterator, TypeVar
from weakref import ref

from azure_kinect.util.base_wapper import ReprInfo

_IdCodeT = TypeVar("_IdCodeT", bound="IdCode")


@dataclass(frozen=True)
class IdCode(ReprInfo):
    __slots__ = ("id_", "belong_pool_ref")

    id_: int
    belong_pool_ref: ref["IdPool"]

    _SEPRATOR: ClassVar[str] = "-"

    @classmethod
    def create(cls: type[_IdCodeT], id_: int, belong_to: "IdPool") -> _IdCodeT:
        return cls(
            id_=id_,
            belong_pool_ref=ref(belong_to),
        )

    def __str__(self) -> str:
        return f"{self.belong_pool_ref()}{IdCode._SEPRATOR}{self.id_}"

    def __repr_data__(self) -> dict:
        return {
            "__after_class_name__": self.id_,
            "belong": self.belong_pool_ref(),
        }


class IdPool(ReprInfo):
    _pool_id: int
    _pool_name: str
    _pool_size: int
    _used_ids: set[IdCode]
    _unused_ids: set[IdCode]
    _auto_scale: bool

    _POOL_ID_GENERATOR: ClassVar[Iterator[int]] = count()
    _INVALID_SELF_ID: ClassVar[int] = -1

    def __init__(
        self,
        pool_name: str = "untitled id pool",
        pool_size: int = 50,
        auto_scale: bool = True,
    ) -> None:
        self._pool_id = next(IdPool._POOL_ID_GENERATOR)
        self._pool_name = pool_name
        self._pool_size = pool_size
        self._used_ids = set()
        self._unused_ids = {
            IdCode.create(
                id_=self_id,
                belong_to=self,
            )
            for self_id in range(pool_size)
        }
        self._auto_scale = auto_scale

    @property
    def pool_id(self) -> int:
        return self._pool_id

    @property
    def pool_name(self) -> str:
        return self._pool_name

    @property
    def pool_size(self) -> int:
        return self._pool_size

    @property
    def unused_id_count(self) -> int:
        return len(self._unused_ids)

    @property
    def is_run_out(self) -> bool:
        return False if self._auto_scale else (len(self._unused_ids) == 0)

    @property
    def is_auto_scale(self) -> bool:
        return self._auto_scale

    def __iter__(self) -> Iterator[IdCode]:
        return self

    def __next__(self) -> IdCode:
        try:
            return self.get_id()
        except ValueError as err:
            raise StopIteration from err

    def _scale(self, size: int) -> None:
        if size <= 0:
            return

        new_ids = {
            IdCode.create(
                id_=self_id,
                belong_to=self,
            )
            for self_id in range(self._pool_size, size)
        }
        self._unused_ids = self._unused_ids.union(new_ids)
        self._pool_size += size

    def get_id(self) -> IdCode:
        if self.is_run_out:
            if self.is_auto_scale:
                # Double the pool capacity of the id
                self._scale(self._pool_size)
            else:
                raise ValueError("Run out of ids.")

        _id = self._unused_ids.pop()
        self._used_ids.add(_id)

        return _id

    def release_id(self, _id: IdCode) -> None:
        if _id not in self._used_ids:
            raise ValueError(
                f"The released id '{_id}' does not belong to the id pool",
            )

        self._used_ids.remove(_id)
        self._unused_ids.add(_id)

    @lru_cache(maxsize=1)
    def get_invalid_id(self) -> IdCode:
        return IdCode.create(IdPool._INVALID_SELF_ID, self)

    def __str__(self) -> str:
        return f"Id pool {self.pool_name}-{self._pool_id}"

    def __repr_data__(self) -> dict:
        return {
            "__after_class_name__": self._pool_id,
            "name": self._pool_name,
            "size": f"{self.unused_id_count} / {self._pool_size}",
        }
