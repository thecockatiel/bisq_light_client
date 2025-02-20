from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from bisq.core.dao.node.full.rpc.dto.dto_pub_key_script import DtoPubKeyScript


class RawDtoOutput:
    def __init__(
        self,
        value: Optional[float] = None,
        n: Optional[int] = None,
        scriptPubKey: Optional["DtoPubKeyScript"] = None,
    ):
        self.value = value
        self.n = n
        self.script_pub_key = scriptPubKey

    def get_json_dict(self) -> dict[str, Any]:
        result = {
            "value": self.value,
            "n": self.n,
            "scriptPubKey": (
                self.script_pub_key.get_json_dict() if self.script_pub_key else None
            ),
        }
        # remove null values
        return {k: v for k, v in result.items() if v is not None}

    @staticmethod
    def from_json_dict(json_dict: dict[str, Any]) -> "RawDtoOutput":
        script_pub_key = json_dict.get("scriptPubKey", None)
        if script_pub_key is not None:
            from bisq.core.dao.node.full.rpc.dto.dto_pub_key_script import (
                DtoPubKeyScript,
            )

            script_pub_key = DtoPubKeyScript.from_json_dict(script_pub_key)
        return RawDtoOutput(
            value=json_dict.get("value", None),
            n=json_dict.get("n", None),
            scriptPubKey=script_pub_key,
        )

    def __eq__(self, other):
        if not isinstance(other, RawDtoOutput):
            return False
        return (
            self.value == other.value
            and self.n == other.n
            and self.script_pub_key == other.script_pub_key
        )

    def __hash__(self):
        return hash((self.value, self.n, self.script_pub_key))
