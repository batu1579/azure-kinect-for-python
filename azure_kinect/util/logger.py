import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from sys import stdout
from textwrap import dedent
from typing import (
    Callable,
    ClassVar,
    Optional,
    Protocol,
    TextIO,
    TypeAlias,
    TypedDict,
    TypeVar,
)

from simple_singleton import singleton
from typing_extensions import Never

from azure_kinect.util.check_dependency import check_dependency
from azure_kinect.util.enum_utils import EnumExtend
from azure_kinect.util.types import ToStringMixin


class LogLevel(EnumExtend[str], str, Enum):
    DEBUG = "Debug"
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    CRITICAL = "Critical"

    @classmethod
    def _get_value_map(cls: type["LogLevel"]) -> dict["LogLevel", str]:
        # Ensure each value matches the key names in LogLevelDict
        return {
            LogLevel.DEBUG: "debug",
            LogLevel.INFO: "info",
            LogLevel.WARNING: "warning",
            LogLevel.ERROR: "error",
            LogLevel.CRITICAL: "critical",
        }


_LogLevelType: TypeAlias = int | str


class LogLevelDict(TypedDict):
    debug: _LogLevelType
    info: _LogLevelType
    warning: _LogLevelType
    error: _LogLevelType
    critical: _LogLevelType


_StreamType: TypeAlias = TextIO


class LogFunc(Protocol):
    def __call__(self, *message: ToStringMixin, separator: str = ", ") -> None: ...


_LogSolutionBaseT = TypeVar("_LogSolutionBaseT", bound="LogSolutionBase")


class LogSolutionBase(Protocol):
    _level_dict: ClassVar[LogLevelDict]

    def __init__(self) -> Never:
        raise RuntimeError("This class should not be instantiated")

    @classmethod
    def init_solution(
        cls: type[_LogSolutionBaseT],
        lowest_level: LogLevel,
        stream_to: Optional[_StreamType] = None,
    ) -> type[_LogSolutionBaseT]:
        """Initialize the log solution."""
        ...

    @staticmethod
    def debug(*message: ToStringMixin, separator: str = ", ") -> None: ...

    @staticmethod
    def info(*message: ToStringMixin, separator: str = ", ") -> None: ...

    @staticmethod
    def warning(*message: ToStringMixin, separator: str = ", ") -> None: ...

    @staticmethod
    def error(*message: ToStringMixin, separator: str = ", ") -> None: ...

    @staticmethod
    def critical(*message: ToStringMixin, separator: str = ", ") -> None: ...


def log_solution(cls: type[LogSolutionBase]) -> type[LogSolutionBase]:
    """Decorator for the log solution."""
    return dataclass(frozen=True, init=False)(cls)


# Log solutions
# TODO(batu1579): Skip directly when don't need to log


@log_solution
class _PrintSolution(LogSolutionBase):
    _level_dict: ClassVar[LogLevelDict] = {
        "debug": 0,
        "info": 1,
        "warning": 2,
        "error": 3,
        "critical": 4,
    }

    _stream_to: ClassVar[Optional[_StreamType]] = None
    _lowest_level: ClassVar[LogLevel] = LogLevel.DEBUG

    def __init__(self) -> Never:
        raise RuntimeError("This class should not be instantiated")

    @classmethod
    def init_solution(
        cls,
        lowest_level: LogLevel,
        stream_to: Optional[_StreamType] = None,
    ) -> type["_PrintSolution"]:
        cls._stream_to = stream_to
        cls._lowest_level = lowest_level

        # log functions
        cls.debug = staticmethod(cls._log_adapter(LogLevel.DEBUG))
        cls.info = staticmethod(cls._log_adapter(LogLevel.INFO))
        cls.warning = staticmethod(cls._log_adapter(LogLevel.WARNING))
        cls.error = staticmethod(cls._log_adapter(LogLevel.ERROR))
        cls.critical = staticmethod(cls._log_adapter(LogLevel.CRITICAL))

        return cls

    @classmethod
    def _need_record(cls, current_level: LogLevel) -> bool:
        lowest_level_key = LogLevel.get_mapped_value(cls._lowest_level)
        current_level_key = LogLevel.get_mapped_value(current_level)
        lowest_level_value = cls._level_dict[lowest_level_key]
        current_level_value = cls._level_dict[current_level_key]

        return lowest_level_value <= current_level_value

    @staticmethod
    def _empty_log_func(
        *message: ToStringMixin,
        separator: str = ", ",  # pylint: disable=unused-argument
    ) -> None:
        return

    @classmethod
    def _log_adapter(cls, current_level: LogLevel) -> LogFunc:
        current_level_name = LogLevel.get_mapped_value(current_level).upper()

        def func(*message: ToStringMixin, separator: str = ", ") -> None:
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            join_msg = separator.join(map(str, message))
            print(
                f"{time_str} | {current_level_name: <8} | {join_msg}",
                file=cls._stream_to,
            )

        return func if cls._need_record(current_level) else cls._empty_log_func


@log_solution
class _LoggingSolution(LogSolutionBase):
    _level_dict: ClassVar[LogLevelDict] = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARN,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self) -> Never:
        raise RuntimeError("This class should not be instantiated")

    @classmethod
    def init_solution(
        cls,
        lowest_level: LogLevel,
        stream_to: Optional[_StreamType] = None,
    ) -> type["_LoggingSolution"]:
        lowest_level_key = LogLevel.get_mapped_value(lowest_level)

        logging.basicConfig(
            stream=stream_to,
            level=cls._level_dict[lowest_level_key],
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # log functions
        cls.debug = staticmethod(cls._log_adapter(logging.debug))
        cls.info = staticmethod(cls._log_adapter(logging.info))
        cls.warning = staticmethod(cls._log_adapter(logging.warning))
        cls.error = staticmethod(cls._log_adapter(logging.error))
        cls.critical = staticmethod(cls._log_adapter(logging.critical))

        return cls

    @classmethod
    def _log_adapter(cls, base_func: Callable[[str], None]) -> LogFunc:
        def func(*message: ToStringMixin, separator: str = ", ") -> None:
            join_msg = separator.join(map(str, message))
            base_func(join_msg)

        return func


if _IS_LOGURU_INSTALLED := check_dependency("loguru"):
    from loguru import logger as loguru_logger


@log_solution
class _Loguru(_LoggingSolution):
    _level_dict: ClassVar[LogLevelDict] = {
        "debug": "DEBUG",
        "info": "INFO",
        "warning": "WARNING",
        "error": "ERROR",
        "critical": "CRITICAL",
    }

    @classmethod
    def init_solution(
        cls,
        lowest_level: LogLevel,
        stream_to: Optional[_StreamType] = None,
    ) -> type[LogSolutionBase]:
        if not _IS_LOGURU_INSTALLED:
            return _LoggingSolution.init_solution(
                lowest_level,
                stream_to,
            )

        assert loguru_logger

        lowest_level_key = LogLevel.get_mapped_value(lowest_level)

        loguru_logger.remove()
        loguru_logger.add(
            stream_to or stdout,
            level=cls._level_dict[lowest_level_key],
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green>"
            + " | <level>{level: <8}</level>"
            + " | <level>{message}</level>",
        )

        cls.debug = staticmethod(cls._log_adapter(loguru_logger.debug))
        cls.info = staticmethod(cls._log_adapter(loguru_logger.info))
        cls.warning = staticmethod(cls._log_adapter(loguru_logger.warning))
        cls.error = staticmethod(cls._log_adapter(loguru_logger.error))
        cls.critical = staticmethod(cls._log_adapter(loguru_logger.critical))

        return cls

    @classmethod
    def _log_adapter(cls, base_func: Callable[[str], None]) -> LogFunc:
        def func(*message: ToStringMixin, separator: str = ", ") -> None:
            join_msg = separator.join(map(str, message))
            base_func(join_msg)

        return func


class LogSolution(EnumExtend[type[LogSolutionBase]], str, Enum):
    PRINT = "Print"
    LOGURU = "Loguru"
    LOGGING = "Logging"

    @classmethod
    def _get_value_map(
        cls: type["LogSolution"],
    ) -> dict["LogSolution", type[LogSolutionBase]]:
        return {
            LogSolution.PRINT: _PrintSolution,
            LogSolution.LOGURU: _Loguru,
            LogSolution.LOGGING: _LoggingSolution,
        }


@singleton(thread_safe=True)
class Logger:
    _is_initialized: bool = False
    _current_solution: LogSolution = LogSolution.PRINT

    def __init__(self) -> Never:
        raise RuntimeError("This class should not be instantiated")

    @classmethod
    def is_initialized(cls) -> bool:
        """Whether the logger is initialized."""
        return cls._is_initialized

    @classmethod
    def get_current_solution(cls) -> LogSolution:
        """Return the current log solution"""
        return cls._current_solution

    @classmethod
    def __init_logger__(cls, _selected_solution: type[LogSolutionBase]) -> None:
        cls.debug = staticmethod(_selected_solution.debug)
        cls.info = staticmethod(_selected_solution.info)
        cls.warning = staticmethod(_selected_solution.warning)
        cls.error = staticmethod(_selected_solution.error)
        cls.critical = staticmethod(_selected_solution.critical)

    @classmethod
    def init(
        cls,
        solution: LogSolution,
        lowest_level: Optional[LogLevel] = None,
        stream_to: Optional[_StreamType] = None,
    ) -> None:
        """
        Initializes the Logger with a specific logging solution.

        This method sets up the logger based on the specified logging solution.
        It should be called before using the logger. If the logger is already
        initialized, this method does nothing.

        Args:
            solution (LogSolution): The logging solution enum to use.
            lowest_level (Optional[LogLevel]): The lowest log level to capture.
            stream_to (Optional[_StreamT]): The stream to which logs should be written.
        """
        if cls._is_initialized:
            return

        if solution == LogSolution.LOGURU and not _IS_LOGURU_INSTALLED:
            Logger.warning(
                dedent(
                    f"""\
                    The loguru dependency library is not installed,
                    please install with pip using the following command:

                    >> pip install loguru

                    or install with poetry by the following command:

                    >> poetry add loguru

                    Currently using the default solution ({cls._current_solution})
                    """
                )
            )
            return

        lowest_level = lowest_level or LogLevel.DEBUG
        solution_class = LogSolution.get_mapped_value(solution)
        solution_class.init_solution(
            lowest_level=lowest_level,
            stream_to=stream_to,
        )

        cls.__init_logger__(solution_class)
        cls._is_initialized = True

    @classmethod
    def init_by_default_solution(cls) -> None:
        """
        Initializes the Logger with a default logging solution.

        This method is primarily used to set up the logger with a default logging
        solution automatically when the Logger class is imported. This ensures that
        the Logger is ready to use immediately, even before explicitly calling the
        'init' method.

        This is invoked at the end of this class definition to set up a default
        solution, making Logger ready to use immediately after import.

        Important:
            Do not call this method manually; use the 'init' method instead for
            custom initialization.
        """
        default_solution = _Loguru if _IS_LOGURU_INSTALLED else _PrintSolution
        default_solution.init_solution(
            lowest_level=LogLevel.DEBUG,
        )

        cls.__init_logger__(default_solution)


Logger.init_by_default_solution()
