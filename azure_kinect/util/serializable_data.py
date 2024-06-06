from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from json import dump, dumps, load, loads
from pathlib import Path
from typing import Any, BinaryIO, Generic, TypeVar

import numpy as np
from adaptix import Retort, dumper, loader, name_mapping

_SerializedDataT = TypeVar("_SerializedDataT", bound="SerializableData")


class SerializableData:
    """This class can be used as a base class for data classes that need to be
    serialized to and deserialized from JSON files. The class offers methods
    to load serializable data from a file or a bytes stream and to save data
    back to a file or a bytes stream. It provides a framework for loading and
    saving data with custom serialization rules.

    Usage:
    ::

        @dataclass
        class ExampleData(SerializableData):
            fiels_a: int
            fiels_b: str

        # Load data from file
        data = ExampleData.load_from_file(Path('data.json'))

        # Save data to file
        data.save_to_file(Path('data.json'))

        stream_file = BytesIO()

        # Load data from bytes
        data = ExampleData.load_from_bytes(stream_file)

        # Save data to bytes
        data.save_to_bytes(stream_file)

        # Save data as json string
        data_json = data.to_json()

        # Load data from json string
        data = ExampleData.load_from_json(data_json)

    Note that the files used to store the data can only be of type json.

    Subclasses can extend the serialization settings by overriding the
    `serialization_settings` method. This allows for customization
    of the serialization process, including handling of specific data types
    like datetime.
    ::

        class ExampleData(SerializableData):
            @classmethod
            def serialization_settings(cls) -> Retort:
                super_settings = super().serialization_settings()
                return super_settings.extend(
                    recipe=[
                        loader(
                            datetime,
                            lambda x: datetime.fromtimestamp(x, tz=timezone.utc)
                        ),
                    ]
                )
    """

    @classmethod
    def get_serialization_settings(cls) -> Retort:
        """Provides serialization settings for the data class.

        Returns:
            Retort: An object containing serialization recipes for converting
            data types like datetime during serialization and deserialization.
        """
        return Retort(
            recipe=[
                loader(
                    datetime,
                    lambda x: datetime.fromtimestamp(x, tz=timezone.utc),
                ),
                dumper(
                    datetime,
                    lambda x: x.timestamp(),
                ),
                loader(
                    np.ndarray,
                    np.array,
                ),
                dumper(
                    np.ndarray,
                    lambda x: x.tolist(),
                ),
            ]
        )

    @classmethod
    def load_from_json(
        cls: type[_SerializedDataT],
        _json: str,
    ) -> _SerializedDataT:
        """Loads a serializable data object from a JSON string.

        Args:
            _json (str): JSON string of data

        Returns:
            _SerializedDataT: An instance of the class with data
        """
        json_obj = loads(_json)
        return cls.get_serialization_settings().load(json_obj, cls)

    @classmethod
    def load_from_file(
        cls: type[_SerializedDataT],
        _path: Path,
    ) -> _SerializedDataT:
        """Loads a serialized object from a file.

        Args:
            _path: Path to the file.

        Returns:
            _SerializedDataT: An instance of the class with data
                loaded from the file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not _path.is_file():
            raise FileNotFoundError(_path)

        with _path.open("r", encoding="utf-8") as _file:
            data = load(_file)

        return cls.get_serialization_settings().load(data, cls)

    @classmethod
    def load_from_bytes(
        cls: type[_SerializedDataT],
        _file: BinaryIO,
    ) -> _SerializedDataT:
        """Load the data from an externally loaded file

        Args:
            _file (BinaryIO): Files from the outside

        Returns:
            _SerializedDataT: An instance of the class with data
                loaded from the file.
        """
        data = load(_file)
        return cls.get_serialization_settings().load(data, cls)

    def to_json(self) -> str:
        """Converts the serialized object to a JSON string.

        Returns:
            str: JSON string of serialized data
        """
        _cls = self.__class__

        data = _cls.get_serialization_settings().dump(self)
        return dumps(data, indent=4)

    def save_to_file(self, _path: Path) -> None:
        """Saves a serialized object to a file.

        Args:
            _path: Path where the data will be saved.
        """
        _cls = self.__class__

        with _path.open("w", encoding="utf-8") as _file:
            data = _cls.get_serialization_settings().dump(self)
            dump(data, _file, indent=4)

    def save_to_bytes(self, _file: BinaryIO) -> None:
        """Saves a serialized object to a stream.

        Args:
            _file: Files from the outside.
        """
        _file.write(self.to_json().encode("utf-8"))


_HandleT_co = TypeVar("_HandleT_co", covariant=True)


@dataclass
class ConfigWapper(SerializableData, Generic[_HandleT_co]):
    @property
    def handle(self) -> _HandleT_co:
        """Handle of the configuration"""
        return self._handle

    @classmethod
    def get_serialization_settings(cls) -> Retort:
        super_settings = super().get_serialization_settings()
        return super_settings.extend(
            recipe=[
                name_mapping(
                    cls,
                    skip=["_handle"],
                    omit_default=True,
                ),
            ],
        )

    @abstractmethod
    def _update_handle(self) -> _HandleT_co: ...

    def __post_init__(self) -> None:
        self._handle = self._update_handle()

    def __setattr__(self, __name: str, __value: Any) -> None:
        if not hasattr(self, "_handle"):
            # For init and post init functions
            super().__setattr__(__name, __value)
            return

        if not hasattr(self, __name):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{__name}'"
            )

        if getattr(self, __name, None) != __value:
            super().__setattr__(__name, __value)
            super().__setattr__("_handle", self._update_handle())


# if __name__ == "__main__":

#     @dataclass
#     class ExampleConfig(ConfigWapper[str]):
#         data: str = "default_data"

#         def _update_handle(self) -> str:
#             return "example_handle"

#     config = ExampleConfig(data="some_data")
#     config.data = "new_data"
#     print(config.to_json())
