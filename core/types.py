from enum import Enum


class StrEnum(str, Enum):
    """
    Enum subclass where members are also str instances.
    Defined as per https://docs.python.org/3.7/library/enum.html#others
    """

    @classmethod
    def list(cls):
        return list((i.name, i.value) for i in cls)
