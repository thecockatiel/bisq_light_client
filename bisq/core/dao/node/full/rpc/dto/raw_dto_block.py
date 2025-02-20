from typing import Any, Optional
from bisq.core.dao.node.full.rpc.dto.raw_dto_transaction import RawDtoTransaction


class RawDtoBlock:
    def __init__(
        self,
        hash: Optional[str] = None,
        confirmations: Optional[int] = None,
        stripped_size: Optional[int] = None,
        size: Optional[int] = None,
        weight: Optional[int] = None,
        height: Optional[int] = None,
        version: Optional[int] = None,
        version_hex: Optional[str] = None,
        merkle_root: Optional[str] = None,
        tx: Optional[tuple[RawDtoTransaction]] = None,
        time: Optional[int] = None,
        median_time: Optional[int] = None,
        nonce: Optional[int] = None,
        bits: Optional[str] = None,
        difficulty: Optional[float] = None,
        chain_work: Optional[str] = None,
        n_tx: Optional[int] = None,
        previous_block_hash: Optional[str] = None,
        next_block_hash: Optional[str] = None,
    ):
        self.hash = hash
        self.confirmations = confirmations
        self.stripped_size = stripped_size
        self.size = size
        self.weight = weight
        self.height = height
        self.version = version
        self.version_hex = version_hex
        self.merkle_root = merkle_root
        self.tx = tx
        self.time = time
        self.median_time = median_time
        self.nonce = nonce
        self.bits = bits
        self.difficulty = difficulty
        self.chain_work = chain_work
        self.n_tx = n_tx
        self.previous_block_hash = previous_block_hash
        self.next_block_hash = next_block_hash

    def get_json_dict(self) -> dict[str, Any]:
        result = {
            "hash": self.hash,
            "confirmations": self.confirmations,
            "strippedsize": self.stripped_size,
            "size": self.size,
            "weight": self.weight,
            "height": self.height,
            "version": self.version,
            "versionHex": self.version_hex,
            "merkleroot": self.merkle_root,
            "tx": (
                [tx_item.get_json_dict() for tx_item in self.tx]
                if self.tx is not None
                else None
            ),
            "time": self.time,
            "mediantime": self.median_time,
            "nonce": self.nonce,
            "bits": self.bits,
            "difficulty": self.difficulty,
            "chainwork": self.chain_work,
            "nTx": self.n_tx,
            "previousblockhash": self.previous_block_hash,
            "nextblockhash": self.next_block_hash,
        }
        return {k: v for k, v in result.items() if v is not None}

    @staticmethod
    def from_json_dict(json_dict: dict[str, Any]) -> "RawDtoBlock":
        return RawDtoBlock(
            hash=json_dict.get("hash", None),
            confirmations=json_dict.get("confirmations", None),
            stripped_size=json_dict.get("strippedsize", None),
            size=json_dict.get("size", None),
            weight=json_dict.get("weight", None),
            height=json_dict.get("height", None),
            version=json_dict.get("version", None),
            version_hex=json_dict.get("versionHex", None),
            merkle_root=json_dict.get("merkleroot", None),
            tx=(
                tuple(
                    RawDtoTransaction.from_json_dict(item)
                    for item in json_dict.get("tx")
                )
                if json_dict.get("tx", None) is not None
                else None
            ),
            time=json_dict.get("time", None),
            median_time=json_dict.get("mediantime", None),
            nonce=json_dict.get("nonce", None),
            bits=json_dict.get("bits", None),
            difficulty=json_dict.get("difficulty", None),
            chain_work=json_dict.get("chainwork", None),
            n_tx=json_dict.get("nTx", None),
            previous_block_hash=json_dict.get("previousblockhash", None),
            next_block_hash=json_dict.get("nextblockhash", None),
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RawDtoBlock):
            return False
        return (
            self.hash == other.hash
            and self.confirmations == other.confirmations
            and self.stripped_size == other.stripped_size
            and self.size == other.size
            and self.weight == other.weight
            and self.height == other.height
            and self.version == other.version
            and self.version_hex == other.version_hex
            and self.merkle_root == other.merkle_root
            and self.tx == other.tx
            and self.time == other.time
            and self.median_time == other.median_time
            and self.nonce == other.nonce
            and self.bits == other.bits
            and self.difficulty == other.difficulty
            and self.chain_work == other.chain_work
            and self.n_tx == other.n_tx
            and self.previous_block_hash == other.previous_block_hash
            and self.next_block_hash == other.next_block_hash
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.hash,
                self.confirmations,
                self.stripped_size,
                self.size,
                self.weight,
                self.height,
                self.version,
                self.version_hex,
                self.merkle_root,
                self.tx,
                self.time,
                self.median_time,
                self.nonce,
                self.bits,
                self.difficulty,
                self.chain_work,
                self.n_tx,
                self.previous_block_hash,
                self.next_block_hash,
            )
        )

    @staticmethod
    def summarized(hex_str: str) -> "Summarized":
        return Summarized(hex_str)


class Summarized(RawDtoBlock):
    def __init__(self, hex_str: str):
        super().__init__()
        self.hex = hex_str

    def get_json_dict(self) -> Any:
        return self.hex

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Summarized):
            return False
        return super().__eq__() and self.hex == other.hex

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.hex))
