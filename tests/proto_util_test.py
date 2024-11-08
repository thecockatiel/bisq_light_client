from enum import Enum
import unittest
from google.protobuf.internal.enum_type_wrapper import EnumTypeWrapper

from bisq.core.common.protocol.proto_util import ProtoUtil

class TestProtoUtil(unittest.TestCase):
    class MockProtoEnum:
        VALUE_ONE = 1
        UNDEFINED = 0
        
        @classmethod
        def Name(cls, value: int) -> str:
            for k, v in vars(cls).items():
                if v == value:
                    return k
            raise ValueError(f"Invalid enum value: {value}")
            
        @classmethod
        def Value(cls, name: str) -> int:
            if hasattr(cls, name):
                return getattr(cls, name)
            raise ValueError(f"Invalid enum name: {name}")

    class MockEnum(Enum):
        VALUE_ONE = 1
        UNDEFINED = 0

    def test_enum_from_proto(self):
        result = ProtoUtil.enum_from_proto(self.MockEnum, self.MockProtoEnum, 1)
        self.assertEqual(result, self.MockEnum.VALUE_ONE)

    def test_enum_from_proto_undefined(self):
        result = ProtoUtil.enum_from_proto(self.MockEnum, self.MockProtoEnum, 999)  # invalid value
        self.assertEqual(result, self.MockEnum.UNDEFINED)
        
    def test_enum_from_proto_no_proto(self):
        result = ProtoUtil.enum_from_proto(self.MockEnum, 999)
        self.assertEqual(result, self.MockEnum.UNDEFINED)
        
    def test_enum_from_proto_no_proto_valid_value(self):
        result = ProtoUtil.enum_from_proto(self.MockEnum, "VALUE_ONE")
        self.assertEqual(result, self.MockEnum.VALUE_ONE)

    def test_enum_from_proto_no_undefined(self):
        class NoUndefinedEnum(Enum):
            VALUE_ONE = 1

        result = ProtoUtil.enum_from_proto(NoUndefinedEnum, self.MockProtoEnum, 999)
        self.assertIsNone(result)

    def test_proto_enum_from_enum(self):
        result = ProtoUtil.proto_enum_from_enum(self.MockProtoEnum, self.MockEnum.VALUE_ONE)
        self.assertEqual(result, 1)

    def test_proto_enum_from_enum_undefined(self):
        result = ProtoUtil.proto_enum_from_enum(self.MockProtoEnum, None)
        self.assertEqual(result, 0)  # UNDEFINED value

if __name__ == '__main__':
    unittest.main()