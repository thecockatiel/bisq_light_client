from enum import Enum


class MobileModelOS(Enum):
    UNDEFINED = ""
    IOS = "iOS"
    IOS_DEV = "iOSDev"
    ANDROID = "android"

    def __init__(self, magic_string: str):
        self.magic_string = magic_string

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj
