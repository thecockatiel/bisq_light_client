from typing import Optional
from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from bisq.core.dao.state.model.immutable_dao_state_model import ImmutableDaoStateModel
import pb_pb2 as protobuf


class Issuance(PersistablePayload, NetworkPayload, ImmutableDaoStateModel):
    """Holds the issuance data (compensation request which was accepted in voting)."""

    def __init__(
        self,
        tx_id: str,
        chain_height: int,
        amount: int,
        pub_key: Optional[str],
        issuance_type: IssuanceType,
    ):
        self._tx_id = tx_id  # comp. request txId
        self._chain_height = chain_height  # of issuance (first block of result phase)
        self._amount = amount

        # sig key as hex of first input in issuance tx used for signing the merits
        # Can be None (payToPubKey tx) but in our case it will never be null. Still keep it nullable to be safe.
        self._pub_key = pub_key
        self._issuance_type = issuance_type

    @property
    def tx_id(self) -> str:
        return self._tx_id

    @property
    def chain_height(self) -> int:
        return self._chain_height

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def pub_key(self) -> Optional[str]:
        return self._pub_key

    @property
    def issuance_type(self) -> IssuanceType:
        return self._issuance_type

    def to_proto_message(self) -> protobuf.Issuance:
        builder = protobuf.Issuance(
            tx_id=self._tx_id,
            chain_height=self._chain_height,
            amount=self._amount,
            issuance_type=self._issuance_type.name,
            pub_key=self._pub_key,
        )
        return builder

    @staticmethod
    def from_proto(proto: protobuf.Issuance) -> "Issuance":
        return Issuance(
            tx_id=proto.tx_id,
            chain_height=proto.chain_height,
            amount=proto.amount,
            pub_key=proto.pub_key if proto.pub_key else None,
            issuance_type=IssuanceType.from_name(proto.issuance_type),
        )

    def __str__(self) -> str:
        return (
            f"Issuance{{\n"
            f"    txId='{self._tx_id}',\n"
            f"    chainHeight={self._chain_height},\n"
            f"    amount={self._amount},\n"
            f"    pubKey='{self._pub_key}',\n"
            f"    issuanceType='{self._issuance_type.name}'\n"
            f"}}"
        )

    def __eq__(self, other):
        if not isinstance(other, Issuance):
            return False
        return (
            self._tx_id == other._tx_id
            and self._chain_height == other._chain_height
            and self._amount == other._amount
            and self._pub_key == other._pub_key
            and self._issuance_type.name == other._issuance_type.name
        )

    def __hash__(self):
        return hash(
            (
                self._tx_id,
                self._chain_height,
                self._amount,
                self._pub_key,
                self._issuance_type,
            )
        )
