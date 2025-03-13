from bisq.common.protocol.network.network_payload import NetworkPayload
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.dao.governance.consensus_critical import ConsensusCritical
import pb_pb2 as protobuf
from utils.pb_helper import map_to_stable_extra_data, stable_extra_data_to_map


class BlindVote(PersistablePayload, NetworkPayload, ConsensusCritical):
    """
    Holds encryptedVotes, encryptedMeritList, txId of blindVote tx and stake.
    A encryptedVotes for 1 proposal is 304 bytes
    """

    def __init__(
        self,
        encrypted_votes: bytes,
        tx_id: str,
        stake: int,
        encrypted_merit_list: bytes,
        date: int,
        extra_data_map: dict[str, str],
    ):
        # created from voteWithProposalTxIdList
        self.encrypted_votes = encrypted_votes
        self.tx_id = tx_id
        # Stake is revealed in the BSQ tx anyway as output value so no reason to encrypt it here.
        self.stake = stake
        self.encrypted_merit_list = encrypted_merit_list
        # Publish date of the proposal.
        # We do not use the date at the moment but we prefer to keep it here as it might be
        # used as a relevant protection tool for late publishing attacks.
        # We don't have a clear concept now how to do it but as it will be part of the opReturn data it will impossible
        # to game the publish date. Together with the block time we can use that for some checks. But as said no clear
        # concept yet...
        # As adding that field later would break consensus we prefer to add it now. In the worst case it will stay
        # an unused field.
        self.date = date
        # This hash map allows addition of data in future versions without breaking consensus
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(
            extra_data_map
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self):
        return self.get_builder()

    def get_builder(self):
        builder = protobuf.BlindVote(
            encrypted_votes=self.encrypted_votes,
            tx_id=self.tx_id,
            stake=self.stake,
            encrypted_merit_list=self.encrypted_merit_list,
            date=self.date,
        )
        if self.extra_data_map:
            builder.extra_data.extend(map_to_stable_extra_data(self.extra_data_map))
        return builder

    @staticmethod
    def from_proto(proto: protobuf.BlindVote):
        return BlindVote(
            encrypted_votes=proto.encrypted_votes,
            tx_id=proto.tx_id,
            stake=proto.stake,
            encrypted_merit_list=proto.encrypted_merit_list,
            date=proto.date,
            extra_data_map=stable_extra_data_to_map(proto.extra_data),
        )

    def __str__(self):
        return (
            f"BlindVotePayload{{\n"
            f"     encryptedVotes={bytes_as_hex_string(self.encrypted_votes)},\n"
            f"     txId='{self.tx_id}',\n"
            f"     stake={self.stake},\n"
            f"     encryptedMeritList={bytes_as_hex_string(self.encrypted_merit_list)},\n"
            f"     date={self.date},\n"
            f"     extraDataMap={self.extra_data_map}\n"
            f"}}"
        )

    def __eq__(self, value):
        if not isinstance(value, BlindVote):
            return False
        return (
            self.encrypted_votes == value.encrypted_votes
            and self.tx_id == value.tx_id
            and self.stake == value.stake
            and self.encrypted_merit_list == value.encrypted_merit_list
            and self.date == value.date
            and self.extra_data_map == value.extra_data_map
        )

    def __hash__(self):
        return hash(
            (
                self.encrypted_votes,
                self.tx_id,
                self.stake,
                self.encrypted_merit_list,
                self.date,
                tuple(self.extra_data_map.items()) if self.extra_data_map else None,
            )
        )
