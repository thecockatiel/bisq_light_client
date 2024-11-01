import unittest
from typing import Type, Optional

from bisq.core.common.protocol.proto_util import ProtoUtil

class TestEnumFromProto(unittest.TestCase):
    class MockEnum:
        VALUE_ONE = 1
        UNDEFINED = 0

        @classmethod
        def Value(cls, name: str):
            if hasattr(cls, name):
                return getattr(cls, name)
            else:
                raise ValueError(f"{name} is not a valid enum name")

    def test_valid_enum(self):
        result = ProtoUtil.enum_from_proto(self.MockEnum, "VALUE_ONE")
        self.assertEqual(result, 1)
        self.assertEqual(result, self.MockEnum.VALUE_ONE)

    def test_invalid_enum_with_undefined(self):
        result = ProtoUtil.enum_from_proto(self.MockEnum, "INVALID_NAME")
        self.assertEqual(result, 0)
        self.assertEqual(result, self.MockEnum.UNDEFINED)

    def test_invalid_enum_without_undefined(self):
        class NoUndefinedEnum:
            VALUE_ONE = 1

            @classmethod
            def Value(cls, name: str):
                if hasattr(cls, name):
                    return getattr(cls, name)
                else:
                    raise ValueError(f"{name} is not a valid enum name")

        result = ProtoUtil.enum_from_proto(NoUndefinedEnum, "INVALID_NAME")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()