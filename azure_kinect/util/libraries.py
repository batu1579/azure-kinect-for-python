from collections.abc import Callable
from ctypes import CDLL
from pathlib import Path
from typing import ClassVar, NamedTuple, Optional

from pykinect_azure import pykinect
from pykinect_azure.k4a import _k4a
from pykinect_azure.k4abt import _k4abt
from pykinect_azure.k4arecord import _k4arecord
from typing_extensions import Never

from azure_kinect.util.logger import Logger


class LoadResult(NamedTuple):
    is_success: bool
    message: str


class K4ALibraries:
    _patch_enabled: ClassVar[bool] = False
    _k4a_library_load_result: ClassVar[Optional[LoadResult]] = None
    _k4abt_library_load_result: ClassVar[Optional[LoadResult]] = None
    _k4a_record_library_load_result: ClassVar[Optional[LoadResult]] = None

    _ALL_SUCESS_RESULT: ClassVar[LoadResult] = LoadResult(
        is_success=True,
        message="All libraries are loaded successfully.",
    )

    def __init__(self) -> Never:
        raise RuntimeError("This class should not be instantiated")

    @classmethod
    def is_k4a_library_loaded(cls) -> bool:
        """Checks if the k4a library is loaded.

        Returns:
            bool: True if the k4a library is loaded, False otherwise.
        """
        if cls._k4a_library_load_result is None:
            return False

        return cls._k4a_library_load_result.is_success

    @classmethod
    def is_k4abt_library_loaded(cls) -> bool:
        """Checks if the k4abt library is loaded.

        Returns:
            bool: True if the k4abt library is loaded, False otherwise.
        """
        if cls._k4abt_library_load_result is None:
            return False

        return cls._k4abt_library_load_result.is_success

    @classmethod
    def is_k4a_record_library_loaded(cls) -> bool:
        """Checks if the k4a record library is loaded.

        Returns:
            bool: True if the k4a record library is loaded, False otherwise.
        """
        if cls._k4a_record_library_load_result is None:
            return False

        return cls._k4a_record_library_load_result.is_success

    @classmethod
    def is_all_libraries_loaded(cls) -> bool:
        """Checks if all required libraries are loaded.

        Returns:
            bool: True if all libraries are loaded, False otherwise.
        """
        return (
            cls.is_k4a_library_loaded()
            and cls.is_k4abt_library_loaded()
            and cls.is_k4a_record_library_loaded()
        )

    @classmethod
    def load_k4a_library(
        cls,
        lib_path: Optional[Path] = None,
    ) -> LoadResult:
        """Loads the k4a library.

        Args:
            lib_path (Optional[Path]): The path to the k4a library. If None,
                the default path is used.

        Returns:
            LoadResult: The result of loading the k4a library.
        """
        if cls.is_k4a_library_loaded():
            assert cls._k4a_library_load_result is not None
            return cls._k4a_library_load_result

        def _store_callback(_dll: CDLL) -> None:
            _k4a.k4a_dll = _dll

        if lib_path is None:
            lib_path = Path(pykinect.get_k4a_module_path())

        cls._k4a_library_load_result = cls._initialize_module(
            lib_name="k4a",
            lib_path=lib_path,
            store_callback=_store_callback,
        )

        return cls._k4a_library_load_result

    @classmethod
    def load_k4abt_library(
        cls,
        lib_path: Optional[Path] = None,
    ) -> LoadResult:
        """Loads the k4abt library.

        Args:
            lib_path (Optional[Path]): The path to the k4abt library. If None,
                the default path is used.

        Returns:
            LoadResult: The result of loading the k4abt library.
        """
        if cls.is_k4abt_library_loaded():
            assert cls._k4abt_library_load_result is not None
            return cls._k4abt_library_load_result

        def _store_callback(_dll: CDLL) -> None:
            _k4abt.k4abt_dll = _dll

        if lib_path is None:
            lib_path = Path(pykinect.get_k4abt_module_path())

        cls._k4abt_library_load_result = cls._initialize_module(
            lib_name="k4abt",
            lib_path=lib_path,
            store_callback=_store_callback,
        )

        return cls._k4abt_library_load_result

    @classmethod
    def load_k4a_record_library(
        cls,
        lib_path: Optional[Path] = None,
    ) -> LoadResult:
        """Loads the k4a record library.

        Args:
            lib_path (Optional[Path]): The path to the k4a record library.
                If None, the default path is used.

        Returns:
            LoadResult: The result of loading the k4a record library.
        """
        if cls.is_k4a_record_library_loaded():
            assert cls._k4a_record_library_load_result is not None
            return cls._k4a_record_library_load_result

        def _store_callback(_dll: CDLL) -> None:
            _k4arecord.record_dll = _dll

        if lib_path is None:
            k4a_lib_path = Path(pykinect.get_k4a_module_path())
            lib_path = cls.infer_record_lib_path(k4a_lib_path)

        cls._k4a_record_library_load_result = cls._initialize_module(
            lib_name="k4arecord",
            lib_path=lib_path,
            store_callback=_store_callback,
        )

        return cls._k4a_record_library_load_result

    @classmethod
    def load_all_libraries(
        cls,
        k4a_lib_path: Optional[Path] = None,
        k4abt_lib_path: Optional[Path] = None,
        k4a_record_lib_path: Optional[Path] = None,
        *,
        enable_patch: bool = True,
    ) -> LoadResult:
        """Loads all Kinect Azure libraries and optionally enables patching.

        Args:
            k4a_lib_path (Optional[Path]): The path to the k4a library.
            k4abt_lib_path (Optional[Path]): The path to the k4abt library.
            k4a_record_lib_path (Optional[Path]): The path to the k4a record library.
            enable_patch (bool): Whether to enable patching for the pykinect_azure
                package.

                The patch modifies the behavior of the package when the
                original verification of k4a results fails, from directly exiting the
                program to throwing exceptions. which can be captured and processed
                when necessary, and by writing corresponding code, the robustness of
                the code can be improved to a certain extent.

                This is useful when you need to use the pykinect_azure package
                directly.

        Returns:
            LoadResult: The result of loading all libraries.
        """
        if enable_patch:
            cls.enable_patch()

        if cls.is_all_libraries_loaded():
            return cls._ALL_SUCESS_RESULT

        result = cls.load_k4a_library(k4a_lib_path)
        if not result.is_success:
            return result

        result = cls.load_k4abt_library(k4abt_lib_path)
        if not result.is_success:
            return result

        if k4a_lib_path is not None and k4a_record_lib_path is None:
            k4a_record_lib_path = cls.infer_record_lib_path(k4a_lib_path)

        result = cls.load_k4a_record_library(k4a_record_lib_path)
        if not result.is_success:
            return result

        Logger.info("Initialized all libraries successfully!")

        return cls._ALL_SUCESS_RESULT

    @staticmethod
    def infer_record_lib_path(k4a_lib_path: Path) -> Path:
        """Infers the path to the k4a record library based on the k4a library path.

        Args:
            k4a_lib_path (Path): The path to the k4a library.

        Returns:
            Path: The inferred path to the k4a record library.
        """
        return k4a_lib_path.parent / k4a_lib_path.name.replace(
            "k4a",
            "k4arecord",
        )

    @staticmethod
    def _initialize_module(
        lib_name: str,
        lib_path: Path,
        store_callback: Callable[[CDLL], None],
    ) -> LoadResult:
        """Initializes a specified library module.

        Attempts to load the specified library from the given path. On success,
        it executes a callback function to store the loaded library.

        Args:
            lib_name(str): The name of the library to initialize.
            lib_path(Path): The filesystem path to the library.
            store_callback(Callable[[CDLL], None]): A callback function that
                stores the loaded library.

        Returns:
            LoadResult: A named tuple that contains the result of
                loading the library.
        """
        if not lib_path.is_file():
            return LoadResult(
                False,
                f"Could not find {lib_name} library at {lib_path}",
            )

        try:
            store_callback(CDLL(str(lib_path)))
        except OSError as err:
            return LoadResult(
                False, f"Loading {lib_name} library failed with error: {err}"
            )

        success_msg = f"successfully initialized {lib_name} library"

        Logger.debug(success_msg)
        return LoadResult(True, success_msg)

    @classmethod
    def is_patch_enabled(cls) -> bool:
        """Checks if the patch for the pykinect_azure module is enabled.

        Returns:
            bool: True if the patch is enabled, False otherwise.
        """
        return cls._patch_enabled

    @classmethod
    def enable_patch(cls) -> None:
        """Enables patching for the pykinect_azure module."""
        if cls.is_patch_enabled():
            return

        def _verify_k4a_result(result: _k4a.k4a_result_t, error: str) -> None:
            if result == _k4a.K4A_RESULT_FAILED:
                raise RuntimeError(error)

        _k4a.VERIFY = _verify_k4a_result
        Logger.info("Enable patch for pykinect_azure module")

        cls._patch_enabled = True
