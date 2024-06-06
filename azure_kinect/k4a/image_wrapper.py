from ctypes import POINTER, c_uint8
from functools import cached_property
from typing import Optional, TypeAlias, TypeVar

import cv2
import cv2.typing as cvt
import numpy as np
import numpy.typing as npt
from pykinect_azure.k4a import _k4a
from typing_extensions import override

from azure_kinect.k4a.config_device import ImageFormat
from azure_kinect.util import ResultStatus, ResultWithStatus
from azure_kinect.util.base_wapper import K4AWapper

_ImageT = TypeVar("_ImageT", bound="K4AImage")
_Buffer: TypeAlias = npt.NDArray[np.uint8]


class K4AImage(K4AWapper[Optional[_k4a.k4a_image_t]]):
    __slots__ = ("_buffer_pointer",)

    _buffer_pointer: Optional[POINTER(c_uint8)]  # type: ignore

    def __init__(
        self,
        image_handle: Optional[_k4a.k4a_image_t] = None,
    ) -> None:
        self._handle = image_handle
        self._buffer_pointer = None

        if self.is_valid():
            self._buffer_pointer = self.get_buffer()

    @cached_property
    def width_pixels(self) -> int | None:
        """Get the width of the image in pixels.

        If the image is invalid, this function will return 0.
        """
        if not self.is_valid():
            return None

        return int(_k4a.k4a_image_get_width_pixels(self._handle))

    @cached_property
    def height_pixels(self) -> int | None:
        """Get the height of the image in pixels.

        If the image is invalid, this function will return 0.
        """
        if not self.is_valid():
            return None

        return int(_k4a.k4a_image_get_height_pixels(self._handle))

    @cached_property
    def stride_bytes(self) -> int | None:
        """Get the stride of the image in bytes

        If the image is invalid, or the image's format does not have a stride,
        the function will return 0.
        """
        if not self.is_valid():
            return None

        return int(_k4a.k4a_image_get_stride_bytes(self._handle))

    @cached_property
    def image_format(self) -> ImageFormat | None:
        """The format of the image.

        If the image is invalid, the function will return ImageFormat.CUSTOM.
        """
        if not self.is_valid():
            return None

        _format = _k4a.k4a_image_get_format(self._handle)
        return ImageFormat.get_enum_by_mapped_value(_format)

    @cached_property
    def device_timestamp_usec(self) -> int:
        """The image's device timestamp in microseconds.

        Returns the device timestamp of the image, as captured by the hardware.
        Timestamps are recorded by the device and represent the mid-point of
        exposure. They may be used for relative comparison, but their absolute
        value has no defined meaning.

        If the image is invalid or if no timestamp was set for the image,
        this function will return 0. It is also possible for 0 to be a valid
        timestamp originating from the beginning of a recording or the start
        of streaming.
        """
        return int(_k4a.k4a_image_get_device_timestamp_usec(self._handle))

    @cached_property
    def system_timestamp_nsec(self) -> int:
        """The image's system timestamp in nanoseconds.

        Returns the system timestamp of the image. Timestamps are recorded by
        the host. They may be used for relative comparision, as they are
        relative to the corresponding system clock. The absolute value is a
        monotonic count from an arbitrary point in the past.

        The system timestamp is captured at the moment host PC finishes
        receiving the image.

        On Linux the system timestamp is read from
        clock_gettime(CLOCK_MONOTONIC), which measures realtime and is not
        impacted by adjustments to the system clock. It starts from an arbitrary
        point in the past. On Windows the system timestamp is read from
        QueryPerformanceCounter(), it also measures realtime and is not impacted
        by adjustments to the system clock. It also starts from an arbitrary
        point in the past.

        If the image is invalid or if no timestamp was set for the image,
        this function will return 0. It is also possible for 0 to be a valid
        timestamp originating from the beginning of a recording or the start
        of streaming.
        """
        return int(_k4a.k4a_image_get_system_timestamp_nsec(self._handle))

    @cached_property
    def exposure_usec(self) -> int:
        """The image's exposure time in microseconds.

        Returns an exposure time in microseconds. This is only supported
        on color image formats.

        If the image is invalid, or no exposure was set on the image,
        the function will return 0. Otherwise, it will return the image
        exposure time in microseconds.
        """
        return int(_k4a.k4a_image_get_exposure_usec(self._handle))

    @cached_property
    def white_balance(self) -> int:
        """The image's white balance.

        This function is only valid for color captures, and not for depth or
        IR captures.

        If image is invalid, or the white balance was not set or not applicable
        to the image, the function will return 0.
        """
        return int(_k4a.k4a_image_get_white_balance(self._handle))

    @cached_property
    def iso_speed(self) -> int:
        """The image's ISO speed.

        This function is only valid for color captures, and not for depth or
        IR captures.

        Returns the ISO speed of the image. 0 indicates the ISO speed was not
        available or an error occurred.
        """
        return int(_k4a.k4a_image_get_iso_speed(self._handle))

    @classmethod
    def create(
        cls: type[_ImageT],
        image_format: ImageFormat,
        width_pixels: int,
        height_pixels: int,
        stride_bytes: int,
    ) -> ResultWithStatus[ResultStatus, _ImageT]:
        """Creates a new K4AImage instance

        This function is used to create images of formats that have consistent
        stride. The function is not suitable for compressed formats that may
        not be represented by the same number of bytes per line.

        For most image formats, the function will allocate an image buffer of
        size height_pixels * stride_bytes. Buffers K4A_IMAGE_FORMAT_COLOR_NV12
        format will allocate an additional height_pixels / 2 set of lines
        (each of stride_bytes). This function cannot be used to allocate
        K4A_IMAGE_FORMAT_COLOR_MJPG buffers.

        To create an image object without the API allocating memory, or to
        represent an image that has a non-deterministic stride, use
        create_from_buffer().

        The k4a_image_t is created with a reference count of 1.

        When finished using the created image, release it with release_handle().

        Args:
            cls (type[_K4AImageT]): _description_
            image_format (ImageFormat): The format of the image that will be
                stored in this image container.
            width_pixels (int): Width in pixels.
            height_pixels (int): Height in pixels.
            stride_bytes (int): 	The number of bytes per horizontal line of
                the image. If set to 0, the stride will be set to the minimum
                size given the format and width_pixels.

        Returns:
            ResultWithStatus[ResultStatus, _K4AImageT]: The created result,
                including status and the new image instance.
        """
        image_handle = _k4a.k4a_image_t()

        result_status = _k4a.k4a_image_create(
            ImageFormat.get_mapped_value(image_format),
            width_pixels,
            height_pixels,
            stride_bytes,
            image_handle,
        )
        result_status = ResultStatus(result_status)

        return ResultWithStatus(
            status=result_status,
            result=cls(image_handle),
        )

    @classmethod
    def empty(cls: type[_ImageT]) -> _ImageT:
        """Creates an empty K4AImage instance"""
        if not hasattr(cls, "_empty_instance"):
            cls._empty_instance = cls(None)

        return cls._empty_instance

    @override
    def is_valid(self) -> bool:
        """Whether the image is valid."""
        return bool(self._handle) or self._buffer_pointer is not None

    def release_handle(self) -> None:
        """Releases the handle of the image"""
        if self.is_valid():
            _k4a.k4a_image_release(self._handle)
            self._handle = None

    def get_buffer_size(self) -> int:
        """Get the image buffer size.

        Returns:
            int: The function will only return 0 if the image is invalid.
        """
        return int(_k4a.k4a_image_get_size(self._handle))

    def get_buffer(self) -> POINTER(c_uint8) | None:  # type: ignore
        """Get the image buffer pointer.

        Returns:
            type[_Pointer[c_uint8]] | None: function only return Null
                if the image is invalid.
        """
        return _k4a.k4a_image_get_buffer(self._handle) if self.is_valid() else None

    def _from_mjpg(self, buffer_array: _Buffer) -> cvt.MatLike:
        return cv2.imdecode(
            np.frombuffer(buffer_array, dtype=np.uint8).copy(),
            flags=-1,
        )

    def _from_nv12(self, buffer_array: _Buffer) -> cvt.MatLike:
        assert self.height_pixels is not None
        assert self.width_pixels is not None

        _image = (
            np.frombuffer(buffer_array, dtype=np.uint8)
            .copy()
            .reshape(int(self.height_pixels * 1.5), self.width_pixels)
        )
        return cv2.cvtColor(_image, cv2.COLOR_YUV2BGR_NV12)

    def _from_yuy2(self, buffer_array: _Buffer) -> cvt.MatLike:
        assert self.height_pixels is not None
        assert self.width_pixels is not None

        _image = (
            np.frombuffer(buffer_array, dtype=np.uint8)
            .copy()
            .reshape(self.height_pixels, self.width_pixels, 2)
        )
        return cv2.cvtColor(_image, cv2.COLOR_YUV2BGR_YUY2)

    def _from_bgra32(self, buffer_array: _Buffer) -> cvt.MatLike:
        assert self.height_pixels is not None
        assert self.width_pixels is not None

        return (
            np.frombuffer(buffer_array, dtype=np.uint8)
            .copy()
            .reshape(self.height_pixels, self.width_pixels, 4)
        )

    def _from_16bit(self, buffer_array: _Buffer) -> cvt.MatLike:
        assert self.height_pixels is not None
        assert self.width_pixels is not None

        # little-endian 16 bits unsigned Depth data
        return (
            np.frombuffer(buffer_array, dtype="<u2")
            .copy()
            .reshape(self.height_pixels, self.width_pixels)
        )

    def _from_custom(self, buffer_array: _Buffer) -> cvt.MatLike:
        return np.frombuffer(buffer_array, dtype="<i2").copy()

    def _from_custom8(self, buffer_array: _Buffer) -> cvt.MatLike:
        assert self.height_pixels is not None
        assert self.width_pixels is not None

        return (
            np.frombuffer(buffer_array, dtype="<u1")
            .copy()
            .reshape(self.height_pixels, self.width_pixels)
        )

    def to_numpy(self) -> cvt.MatLike | None:
        """Convert the image to a numpy array.

        Raises:
            ValueError: Raises if the image format is unknown.

        Returns:
            MatLike | None: If the image is invalid, this function will return
                None, otherwise will return an image.
        """
        if not self.is_valid():
            return None

        assert self.image_format is not None

        # Read the data in the buffer
        buffer_array: _Buffer = np.ctypeslib.as_array(
            self._buffer_pointer,
            shape=(self.get_buffer_size(),),
        )

        # Parse buffer based on image formats
        match self.image_format:
            case ImageFormat.COLOR_MJPG:
                return self._from_mjpg(buffer_array)
            case ImageFormat.COLOR_NV12:
                return self._from_nv12(buffer_array)
            case ImageFormat.COLOR_YUY2:
                return self._from_yuy2(buffer_array)
            case ImageFormat.COLOR_BGRA32:
                return self._from_bgra32(buffer_array)
            case ImageFormat.CUSTOM:
                return self._from_custom(buffer_array)
            case ImageFormat.CUSTOM8:
                return self._from_custom8(buffer_array)
            case ImageFormat.DEPTH16 | ImageFormat.IR16 | ImageFormat.CUSTOM16:
                return self._from_16bit(buffer_array)
            case _:
                raise ValueError(f"Unknown image format: {self.image_format}")

    @staticmethod
    def color_depth_image(
        depth_image_array: cvt.MatLike,
        alpha: Optional[float] = None,
    ) -> cvt.MatLike:
        """Color a depth image.

        Args:
            depth_image_array (cvt.MatLike): The depth image array.
            alpha (float, optional): The transparency of the image. Defaults to 0.05.

        Returns:
            cvt.MatLike: The colored depth image array.
        """
        alpha = alpha or 0.05

        # alpha is fitted by visual comparison with Azure k4aviewer results
        depth_color_image = cv2.convertScaleAbs(
            depth_image_array,
            alpha=alpha,
        )
        return cv2.applyColorMap(depth_color_image, cv2.COLORMAP_JET)

    @staticmethod
    def smooth_depth_image(
        depth_image_array: cvt.MatLike,
        max_hole_size: Optional[int] = None,
    ) -> cvt.MatLike:
        """Smoothes depth image by filling the holes using inpainting method.

        Args:
            depth_image_array(cvt.MatLike): Original depth image
            max_hole_size (int, optional): The maximum hole size to fill.
                Defaults to 10.

        Returns:
            cvt.MatLike: Smoothed depth image

        Remarks:
            Bigger maximum hole size will try to fill bigger holes but requires longer time
        """
        max_hole_size = max_hole_size or 10

        mask = np.zeros(depth_image_array.shape, dtype=np.uint8)
        mask[depth_image_array == 0] = 1

        # Do not include in the mask the holes bigger than the maximum hole size
        kernel = np.ones((max_hole_size, max_hole_size), np.uint8)
        erosion = cv2.erode(mask, kernel, iterations=1)
        # mask = mask - erosion
        mask = np.subtract(mask, erosion)

        return cv2.inpaint(
            depth_image_array.astype(np.uint16),
            mask,
            max_hole_size,
            cv2.INPAINT_NS,
        )

    def __wapper_data__(self) -> dict:
        assert self.image_format is not None

        return {
            "format": self.image_format.name,
            "stride": self.stride_bytes,
            "size": (self.width_pixels, self.height_pixels),
        }

    def __del__(self) -> None:
        self.release_handle()
