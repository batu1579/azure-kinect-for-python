from abc import abstractmethod
from typing import Generic, TypeVar


class ReprInfo:
    @abstractmethod
    def __repr_data__(self) -> dict:
        """Information to carry when converting to a repr string

        The default format is:

        <ClassName: data_name=data>

        Or you can customize the repr string format by adding the following
        fields, to the returned dictionary:

        - `__before_class_name__`: String before class name, default by `""`.
        - `__after_class_name__`: String after class name, default by `""`.
        - `__class_info_seprator__`: Separator between the class info and the
            datas, default by `": "`.
        - `__data_seprator__`: Separator between the datas, default by `", "`.
        - `__key_value_seprator__`: Separator between the key and the value,
            default by `"="`.

        Returns:
            dict: Information dictionary
        """
        ...

    def __repr__(self) -> str:
        data_dict = self.__repr_data__()
        before_class = data_dict.pop("__before_class_name__", "")
        after_class = data_dict.pop("__after_class_name__", "")
        class_info_seprator = data_dict.pop("__class_info_seprator__", ": ")
        data_seprator = data_dict.pop("__data_seprator__", ", ")
        key_value_seprator = data_dict.pop("__key_value_seprator__", "=")

        if before_class != "":
            before_class = f"{before_class} "

        if after_class != "":
            after_class = f" {after_class}"

        class_info = f"{before_class}{self.__class__.__name__}{after_class}"

        if len(data_dict) == 0:
            data_str = f"object at {hex(id(self))}"
        else:
            data_str = str(data_seprator).join(
                [
                    f"{data_name}{key_value_seprator}{value}"
                    for data_name, value in data_dict.items()
                ]
            )

        return f"<{class_info}{class_info_seprator}{data_str}>"


_HandleT_co = TypeVar("_HandleT_co", covariant=True)


class K4AWapper(ReprInfo, Generic[_HandleT_co]):
    __slots__ = ("_handle",)

    _handle: _HandleT_co

    @property
    def handle(self) -> _HandleT_co:
        """Get the handle of the wapper"""
        return self._handle

    def is_valid(self) -> bool:
        """Check whether the wapper handle is valid."""
        return bool(self._handle)

    def __repr_data__(self) -> dict:
        return self.__wapper_data__() if self.is_valid() else {"is_valid": False}

    @abstractmethod
    def __wapper_data__(self) -> dict:
        """Important data of the wapper instance.
        Will only be called if the is_valid method is true.

        Special elements are same as `ReprInfo.__repr_data__()`:

        - `__before_class_name__`: String before class name, default by `""`.
        - `__after_class_name__`: String after class name, default by `""`.
        - `__class_info_seprator__`: Separator between the class info and the
            datas, default by `": "`.
        - `__data_seprator__`: Separator between the datas, default by `", "`.
        - `__key_value_seprator__`: Separator between the key and the value,
            default by `"="`.

        Returns:
            dict: Information dictionary
        """
        ...

    @abstractmethod
    def __del__(self) -> None:
        """Called when the wapper is deleted."""
        ...


if __name__ == "__main__":

    class Test(ReprInfo):
        def __repr_data__(self) -> dict:
            return {}

    print(Test())
