from typing import Protocol, TypeAlias, TypeVar

import numpy as np
import numpy.typing as npt

NumpyT = TypeVar("NumpyT", bound=np.generic)
NumpyT_co = TypeVar("NumpyT_co", bound=np.generic, covariant=True)


class ToDictMixin(Protocol):
    def to_dict(self) -> dict:
        """Convert all necessary data to dictionary"""
        ...


class ToNumpyMixin(Protocol[NumpyT_co]):
    def to_numpy(self) -> npt.NDArray[NumpyT_co]:
        """Convert all necessary data to numpy array"""
        ...


class ToStringMixin(Protocol):
    def __str__(self) -> str:
        """Convert the instance to string"""
        ...


_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_T_contra = TypeVar("_T_contra", contravariant=True)


class NextMixin(Protocol[_T_co]):
    def __next__(self) -> _T_co:
        """Generate the next value"""
        ...


TransformMatrix: TypeAlias = npt.NDArray[np.float64]
Coordinate2d: TypeAlias = tuple[int, int]
Coordinate3d: TypeAlias = tuple[int, int, int]
Size: TypeAlias = tuple[int, int]
