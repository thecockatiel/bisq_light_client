from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from bisq.core.dao.node.full.rpc.dto.dto_signature_script import DtoSignatureScript


class RawDtoInput:
    def __init__(
        self,
        tx_id: Optional[str] = None,
        vout: Optional[int] = None,
        coinbase: Optional[str] = None,
        scriptSig: Optional["DtoSignatureScript"] = None,
        tx_in_witness: Optional[tuple[str]] = None,
        sequence: Optional[int] = None,
    ):
        self.tx_id = tx_id
        self.vout = vout
        self.coinbase = coinbase
        self.script_sig = scriptSig
        self.tx_in_witness = tx_in_witness
        self.sequence = sequence

    def get_json_dict(self) -> dict[str, Any]:
        result = {
            "txid": self.tx_id,
            "vout": self.vout,
            "coinbase": self.coinbase,
            "scriptSig": self.script_sig.get_json_dict() if self.script_sig else None,
            "txinwitness": self.tx_in_witness,
            "sequence": self.sequence,
        }
        # remove null values
        return {k: v for k, v in result.items() if v is not None}

    @staticmethod
    def from_json_dict(json_dict: dict[str, Any]) -> "RawDtoInput":
        script_sig = json_dict.get("scriptSig", None)
        if script_sig is not None:
            from bisq.core.dao.node.full.rpc.dto.dto_signature_script import (
                DtoSignatureScript,
            )

            script_sig = DtoSignatureScript.from_json_dict(script_sig)

        tx_in_witness = json_dict.get("txinwitness", None)
        if tx_in_witness is not None:
            tx_in_witness = tuple(tx_in_witness)

        return RawDtoInput(
            tx_id=json_dict.get("txid", None),
            vout=json_dict.get("vout", None),
            coinbase=json_dict.get("coinbase", None),
            scriptSig=script_sig,
            tx_in_witness=tx_in_witness,
            sequence=json_dict.get("sequence", None),
        )

    def __eq__(self, other):
        if not isinstance(other, RawDtoInput):
            return False
        return (
            self.tx_id == other.tx_id
            and self.vout == other.vout
            and self.coinbase == other.coinbase
            and self.script_sig == other.script_sig
            and self.tx_in_witness == other.tx_in_witness
            and self.sequence == other.sequence
        )

    def __hash__(self):
        return hash(
            (
                self.tx_id,
                self.vout,
                self.coinbase,
                self.script_sig,
                self.tx_in_witness,
                self.sequence,
            )
        )
