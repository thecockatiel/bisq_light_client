import json
from typing import Any, Dict

# TODO: check against java implementation
class JsonUtil:
    @staticmethod
    def object_to_json(obj) -> str:
        obj_dict = JsonUtil.recursively_resolve_dict(obj)
        return json.dumps(obj_dict, indent=2, separators=(",", ": "))
    
    @staticmethod
    def recursively_resolve_dict(obj: Dict[str, Any]) -> Dict[str, Any]:
        resolved_dict = {}
        obj_dict = obj if isinstance(obj, dict) else obj.__dict__
        for key, value in obj_dict.items():
            if isinstance(value, dict):
                resolved_dict[key] = JsonUtil.recursively_resolve_dict(value)
            elif hasattr(value, "get_json_dict"):
                resolved_dict[key] = value.get_json_dict()
            else:
                resolved_dict[key] = value
        return resolved_dict
    
    @staticmethod
    def parse_json(input: str):
        return json.loads(input)
