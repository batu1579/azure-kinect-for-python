from enum import Enum
from typing import Generic, Iterator, TypeVar

_EnumT = TypeVar("_EnumT", bound=Enum)


def get_index_of_enum(enum_class: type[_EnumT], value: _EnumT) -> int:
    """Gets the index when the enumeration value is declared.

    Args:
        value (_EnumT): Enum value.

    Returns:
        int: index of enumeration value.
    """
    assert issubclass(enum_class, Enum)
    assert isinstance(value, enum_class)

    return list(enum_class).index(value)


def get_enum_by_index(enum_class: type[_EnumT], index: int) -> _EnumT:
    """Gets the enumeration instance by its index.

    Args:
        enum_class (type[_EnumT]): The enum class.
        index (int): index of enumeration value.

    Returns:
        _EnumT: Enum instance.
    """
    assert issubclass(enum_class, Enum)

    return list(enum_class)[index]


_T = TypeVar("_T")

_EnumExtendT = TypeVar("_EnumExtendT", bound="EnumExtend")


class EnumExtend(Generic[_T]):
    """
    A generic class that extends the capabilities of the standard Enum class.
    This class allows enum members to be associated with 'real values' of
    a specified type _T. Subclasses must implement the `value_map` class
    property to define the mapping from enum members to their corresponding
    real values.

    This class is intended to be used in combination with the Enum class.

    Usage:
    ::

        class Color(EnumExtend[str], Enum):
            RED = 1
            GREEN = 2
            BLUE = 3

            @classmethod
            def _get_value_map(cls) -> dict["Color", str]:
                return {
                    Color.RED: "red",
                    Color.GREEN: "green",
                    Color.BLUE: "blue",
                }

        # Example
        print(Color.get_mapped_value(Color.RED))  # Outputs "red"

    Note:
        - Subclasses must implement the `value_map` class property.
        - `get_mapped_value` will assert that the mapping is not None.
        Ensure that the mapping is correctly defined for all enum members.
    """

    def __iter__(self) -> Iterator: ...

    @classmethod
    def _get_value_map(cls: type[_EnumExtendT]) -> dict[_EnumExtendT, _T]:
        """Defines a mapping between the enumerated value and the real value.
        Must be implemented by subclasses to return a dictionary mapping enum
        members to their real values. Don't store the dictionary using
        cached_lru or otherwise; it will only be called once.

        Note: Be sure to include each enumeration value.

        Returns:
            dict[_EnumExtendT, _T]: The mappding dictionary.
        """
        raise NotImplementedError("value_map property is not implemented")

    @classmethod
    def get_mapped_value(cls: type[_EnumExtendT], value: _EnumExtendT) -> _T:
        """Gets the real value corresponding to the enumeration value.

        The mapped value declared by the value_map property.

        Args:
            value (_EnumExtendT): Enum value.

        Returns:
            _T: Real value of enumeration value.
        """
        if not hasattr(cls, "_value_map"):
            cls._value_map = cls._get_value_map()

        mapped_value = cls._value_map[value]

        assert mapped_value is not None
        return mapped_value

    @classmethod
    def get_enum_by_mapped_value(
        cls: type[_EnumExtendT], mapped_value: _T
    ) -> _EnumExtendT:
        """Gets the enumeration instance by its mapped value.

        Args:
            mapped_value (_T): Real value of enumeration value.

        Returns:
            Mapped enumeration instance.
        """
        if not hasattr(cls, "_reversed_value_map"):
            cls.reversed_value_map = {_v: _k for _k, _v in cls._get_value_map().items()}

        instance = cls.reversed_value_map[mapped_value]

        if instance is None:
            raise ValueError(
                "Could not find enumeration value"
                + f"for mapped value: {mapped_value}",
            )

        return instance


if __name__ == "__main__":

    class Color(EnumExtend[str], Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

        @classmethod
        def _get_value_map(cls) -> dict["Color", str]:
            return {
                Color.RED: "red",
                Color.GREEN: "green",
                Color.BLUE: "blue",
            }

    print(get_index_of_enum(Color, Color.RED))
    print(Color.get_mapped_value(Color.RED))
