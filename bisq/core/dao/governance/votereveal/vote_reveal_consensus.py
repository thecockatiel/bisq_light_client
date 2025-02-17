from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.version import Version
from bisq.core.dao.governance.blindvote.blind_vote import BlindVote
from bisq.core.dao.state.model.blockchain.op_return_type import OpReturnType
from io import BytesIO


class VoteRevealConsensus:
    """All consensus critical aspects are handled here."""

    @staticmethod
    def get_hash_of_blind_vote_list(blind_votes: list["BlindVote"]):
        output_stream = bytearray()
        for blind_vote in blind_votes:
            data = blind_vote.serialize_for_hash()
            output_stream.extend(data)
        return get_sha256_ripemd160_hash(bytes(output_stream))

    @staticmethod
    def get_op_return_data(hash_of_blind_vote_list: bytes, secret_key: bytes) -> bytes:
        with BytesIO() as output_stream:
            output_stream.write(bytes([OpReturnType.VOTE_REVEAL.type]))
            output_stream.write(Version.VOTE_REVEAL)
            output_stream.write(hash_of_blind_vote_list)  # hash is 20 bytes
            output_stream.write(secret_key)  # secret_key has 16 bytes
            return output_stream.getvalue()
