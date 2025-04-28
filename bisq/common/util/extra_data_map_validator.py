from typing import Optional
 
from utils.preconditions import check_argument

class ExtraDataMapValidator:
    """
    Validator for extraDataMap fields used in network payloads.
    Ensures that we don't get the network attacked by huge data inserted there.
    """
    # ExtraDataMap is only used for exceptional cases to not break backward compatibility.
    # We don't expect many entries there.
    MAX_SIZE = 10
    MAX_KEY_LENGTH = 100
    MAX_VALUE_LENGTH = 100000  # 100 kb

    @staticmethod
    def get_validated_extra_data_map(extra_data_map: Optional[dict[str, str]] = None) -> Optional[dict[str, str]]:
        return ExtraDataMapValidator.get_validated_extra_data_map_with_limits(extra_data_map, ExtraDataMapValidator.MAX_SIZE, ExtraDataMapValidator.MAX_KEY_LENGTH, ExtraDataMapValidator.MAX_VALUE_LENGTH)

    @staticmethod
    def get_validated_extra_data_map_with_limits(extra_data_map: Optional[dict[str, str]], max_size: int, max_key_length: int, max_value_length: int) -> Optional[dict[str, str]]:
        if extra_data_map is None:
            return None

        try:
            check_argument(len(extra_data_map) <= max_size, f"Size of map must not exceed {max_size}")
            for key, value in extra_data_map.items():
                check_argument(len(key) <= max_key_length, f"Length of key must not exceed {max_key_length}")
                check_argument(len(value) <= max_value_length, f"Length of value must not exceed {max_value_length}")
            return extra_data_map
        except Exception as e:
            return {}

    @staticmethod
    def validate(extra_data_map: Optional[dict[str, str]] = None):
        ExtraDataMapValidator.validate_with_limits(extra_data_map, ExtraDataMapValidator.MAX_SIZE, ExtraDataMapValidator.MAX_KEY_LENGTH, ExtraDataMapValidator.MAX_VALUE_LENGTH)

    @staticmethod
    def validate_with_limits(extra_data_map: Optional[dict[str, str]], max_size: int, max_key_length: int, max_value_length: int):
        if extra_data_map is None:
            return

        check_argument(len(extra_data_map) <= max_size, f"Size of map must not exceed {max_size}")
        for key, value in extra_data_map.items():
            check_argument(len(key) <= max_key_length, f"Length of key must not exceed {max_key_length}")
            check_argument(len(value) <= max_value_length, f"Length of value must not exceed {max_value_length}")