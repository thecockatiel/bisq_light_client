from typing import Any, Optional
from bisq.core.dao.node.full.rpc.dto.raw_dto_input import RawDtoInput
from bisq.core.dao.node.full.rpc.dto.raw_dto_output import RawDtoOutput


class RawDtoTransaction:
    def __init__(
        self,
        in_active_chain: Optional[bool] = None,
        tx_id: Optional[str] = None,
        hash: Optional[str] = None,
        version: Optional[int] = None,
        size: Optional[int] = None,
        vsize: Optional[int] = None,
        weight: Optional[int] = None,
        lock_time: Optional[int] = None,
        vin: Optional[tuple[RawDtoInput]] = None,
        vout: Optional[tuple[RawDtoOutput]] = None,
        block_hash: Optional[str] = None,
        confirmations: Optional[int] = None,
        block_time: Optional[int] = None,
        time: Optional[int] = None,
        hex: Optional[str] = None,
    ):
        self.in_active_chain = in_active_chain
        self.tx_id = tx_id
        self.hash = hash
        self.version = version
        self.size = size
        self.vsize = vsize
        self.weight = weight
        self.lock_time = lock_time
        self.vin = vin
        self.vout = vout
        self.block_hash = block_hash
        self.confirmations = confirmations
        self.block_time = block_time
        self.time = time
        self.hex = hex

    def get_json_dict(self) -> dict[str, Any]:
        result = {
            "in_active_chain": self.in_active_chain,
            "txid": self.tx_id,
            "hash": self.hash,
            "version": self.version,
            "size": self.size,
            "vsize": self.vsize,
            "weight": self.weight,
            "locktime": self.lock_time,
            "vin": (
                [vin_item.get_json_dict() for vin_item in self.vin]
                if self.vin is not None
                else None
            ),
            "vout": (
                [vout_item.get_json_dict() for vout_item in self.vout]
                if self.vout is not None
                else None
            ),
            "blockhash": self.block_hash,
            "confirmations": self.confirmations,
            "blocktime": self.block_time,
            "time": self.time,
            "hex": self.hex,
        }
        # remove null values
        return {k: v for k, v in result.items() if v is not None}

    @staticmethod
    def from_json_dict(json_dict: dict[str, Any]) -> "RawDtoTransaction":
        vin = json_dict.get("vin", None)
        vout = json_dict.get("vout", None)
        return RawDtoTransaction(
            in_active_chain=json_dict.get("in_active_chain", None),
            tx_id=json_dict.get("txid", None),
            hash=json_dict.get("hash", None),
            version=json_dict.get("version", None),
            size=json_dict.get("size", None),
            vsize=json_dict.get("vsize", None),
            weight=json_dict.get("weight", None),
            lock_time=json_dict.get("locktime", None),
            vin=(
                tuple(RawDtoInput.from_json_dict(item) for item in vin)
                if vin is not None
                else None
            ),
            vout=(
                tuple(RawDtoOutput.from_json_dict(item) for item in vout)
                if vout is not None
                else None
            ),
            block_hash=json_dict.get("blockhash", None),
            confirmations=json_dict.get("confirmations", None),
            block_time=json_dict.get("blocktime", None),
            time=json_dict.get("time", None),
            hex=json_dict.get("hex", None),
        )

    def __eq__(self, other):
        if not isinstance(other, RawDtoTransaction):
            return False
        return (
            self.in_active_chain == other.in_active_chain
            and self.tx_id == other.tx_id
            and self.hash == other.hash
            and self.version == other.version
            and self.size == other.size
            and self.vsize == other.vsize
            and self.weight == other.weight
            and self.lock_time == other.lock_time
            and self.vin == other.vin
            and self.vout == other.vout
            and self.block_hash == other.block_hash
            and self.confirmations == other.confirmations
            and self.block_time == other.block_time
            and self.time == other.time
            and self.hex == other.hex
        )

    def __hash__(self):
        return hash(
            (
                self.in_active_chain,
                self.tx_id,
                self.hash,
                self.version,
                self.size,
                self.vsize,
                self.weight,
                self.lock_time,
                self.vin,
                self.vout,
                self.block_hash,
                self.confirmations,
                self.block_time,
                self.time,
                self.hex,
            )
        )

    @staticmethod
    def summarized(hex_str: str) -> "Summarized":
        return Summarized(hex_str)


class Summarized(RawDtoTransaction):
    def __init__(self, hex_str: str):
        super().__init__(hex=hex_str)

    def get_json_dict(self) -> Any:
        return self.hex
