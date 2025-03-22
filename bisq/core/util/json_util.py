from enum import Enum
import json
from typing import Any
from ctypes import c_int8

# TODO: check against java implementation
class JsonUtil:
    @staticmethod
    def object_to_json(obj) -> str:
        obj_dict = JsonUtil.recursively_resolve_dict(obj)
        return json.dumps(obj_dict, indent=2, separators=(",", ": "))
    
    @staticmethod
    def recursively_resolve_dict(obj: dict[str, Any]) -> Any:
        if obj is None:
            return obj
        resolved_dict = {}
        if isinstance(obj, dict):
            obj_dict = obj 
        elif hasattr(obj, "get_json_dict"):
            obj_dict = obj.get_json_dict()
            if not isinstance(obj_dict, dict):
                return obj_dict
        else:
            obj_dict = obj.__dict__
        for key, value in obj_dict.items():
            if isinstance(value, dict):
                resolved_dict[key] = JsonUtil.recursively_resolve_dict(value)
            elif hasattr(value, "get_json_dict"):
                resolved_dict[key] = JsonUtil.recursively_resolve_dict(value.get_json_dict())
            elif isinstance(value, Enum):
                resolved_dict[key] = value.name
            elif isinstance(value, (list, tuple)):
                resolved_dict[key] = [
                    JsonUtil.recursively_resolve_dict(item) for item in value
                ]
            elif isinstance(value, (bytes, bytearray)):
                resolved_dict[key] = [
                    c_int8(b).value for b in value
                ]
            else:
                resolved_dict[key] = value
        # filter out null values, as does Gson by default
        resolved_dict = {k: v for k, v in resolved_dict.items() if v is not None}
        return resolved_dict
    
    @staticmethod
    def parse_json(input: str):
        return json.loads(input)
