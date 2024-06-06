from dataclasses import dataclass
from datetime import datetime
from itertools import count
from pathlib import Path
from typing import TypeAlias, TypeVar

from adaptix import Retort, name_mapping

from azure_kinect.util import Logger
from azure_kinect.util.serializable_data import SerializableData
from azure_kinect.util.types import NextMixin, ToStringMixin

_RecordConfigT = TypeVar("_RecordConfigT", bound="RecordConfig")
SuffixGenerator: TypeAlias = NextMixin[ToStringMixin]

# TODO(batu1579): Use env variable to change this value.
DEFAULT_RECORD_PATH = Path("./records")
DEFAULT_RECORD_PATH.mkdir(exist_ok=True)


@dataclass(frozen=True)
class RecordConfig(SerializableData):
    record_path: Path
    base_filename: str
    suffix_generator: SuffixGenerator

    @classmethod
    def get_serialization_settings(cls) -> Retort:
        super_settings = super().get_serialization_settings()
        return super_settings.extend(
            recipe=[
                name_mapping(
                    cls,
                    skip=["suffix_generator"],
                    omit_default=True,
                )
            ]
        )

    @classmethod
    def create(
        cls: type[_RecordConfigT],
        record_path: Path,
        base_filename: str,
        suffix_generator: SuffixGenerator,
        *,
        generate_when_not_exists: bool = False,
    ) -> _RecordConfigT:
        """Create a new RecordConfig instance."""
        record_path = cls._check_record_path(
            record_path,
            generate_when_not_exists,
        )

        return cls(
            record_path,
            base_filename,
            suffix_generator,
        )

    @staticmethod
    def _check_record_path(
        record_path: Path,
        generate_when_not_exists: bool,
    ) -> Path:
        """Check if the given record path is valid and exists.
        If the given path is a file, return the parent directory as record path.

        Args:
            record_path (Path): The path to check.
            generate_when_not_exists (bool): Whether to generate the record path
                when it does not exist.

        Raises:

        Returns:
            Path: The path of the given record path.
        """
        if not record_path.exists():
            if not generate_when_not_exists:
                raise FileNotFoundError(
                    f"Record path '{record_path}' does not exist.",
                )

            Logger.debug(
                f"The record path does not exist, creating: {record_path}",
            )
            record_path.mkdir(parents=True, exist_ok=True)

        if record_path.is_file():
            parent_path = record_path.parent

            Logger.warning(
                f"The record path '{record_path}' is a file, "
                + f"will temporarily used the parent directory '{parent_path}'"
            )

            record_path = parent_path

        if list(record_path.iterdir()):
            # The record path is not empty

            # Create a time-dependent folder to store record files
            # to prevent overwriting important files.
            time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            new_folder = Path(record_path) / f"record_{time_str}"
            new_folder.mkdir(parents=True, exist_ok=True)

            Logger.warning(
                f"The record path '{record_path}' is not empty, "
                + f"will temporarily create a new folder '{new_folder}' "
                + "for storing record files."
            )
            record_path = new_folder

        return record_path

    def get_filepath(
        self,
        *,
        suffix: str = "",
        extension: str = "mkv",
    ) -> Path:
        """Generate a file path for saving a record.

        Args:
            suffix (str, optional): A suffix to be added to the base file name
                to prevent file names from being duplicated.
            extension (str, optional): The file extension. Defaults to "mkv".

        Returns:
            Path: The real file path.
        """
        if suffix == "":
            Logger.debug(
                "No suffix was given, will get one from suffix_generator.",
            )
            suffix = str(next(self.suffix_generator))

        return self.record_path / f"{self.base_filename}{suffix}.{extension}"


# TODO(batu1579): Use env variable to change this value.
DEFAULT_RECORD_CONFIG = RecordConfig.create(
    record_path=DEFAULT_RECORD_PATH,
    base_filename="output",
    suffix_generator=count(),
)
