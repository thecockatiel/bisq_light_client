from typing import TYPE_CHECKING
from bisq.common.crypto.encryption import Encryption
from bisq.common.setup.log_setup import get_logger
from bisq.core.dao.governance.voteresult.vote_result_exception import (
    VoteResultException,
)
from bisq.core.dao.state.model.governance.issuance_type import IssuanceType
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.dao.state.model.governance.merit_list import MeritList
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService

logger = get_logger(__name__)


class MeritConsensus:
    # Value with 144 blocks a day and 365 days would be 52560. We take a close round number instead.
    BLOCKS_PER_YEAR = 50_000

    @staticmethod
    def decrypt_merit_list(
        encrypted_merit_list: bytes, secret_key: bytes
    ) -> "MeritList":
        try:
            decrypted = Encryption.decrypt(encrypted_merit_list, secret_key)
            return MeritList.get_merit_list_from_bytes(decrypted)
        except Exception as e:
            raise VoteResultException.DecryptionException(e)

    @staticmethod
    def get_merit_stake(
        blind_vote_tx_id: str,
        merit_list: MeritList,
        dao_state_service: "DaoStateService",
    ) -> int:
        # We need to take the chain height when the blindVoteTx got published so we get the same merit for the vote even at
        # later blocks (merit decreases with each block).
        tx = dao_state_service.get_tx(blind_vote_tx_id)
        blind_vote_tx_height = tx.block_height if tx else 0
        if blind_vote_tx_height == 0:
            logger.error(
                f"Error at get_merit_stake: blindVoteTx not found in daoStateService. blindVoteTxId={blind_vote_tx_id}"
            )
            return 0

        # We only use past issuance. In case we would calculate the merit after the vote result phase we have the
        # issuance from the same cycle but we must not add that to the merit.
        total_merit_stake = 0
        for merit in merit_list.list:
            if (
                MeritConsensus._is_signature_valid(
                    merit.signature, merit.issuance.pub_key, blind_vote_tx_id
                )
                and merit.issuance.chain_height <= blind_vote_tx_height
            ):
                try:
                    issuance = merit.issuance
                    check_argument(
                        issuance.issuance_type == IssuanceType.COMPENSATION,
                        "issuance must be of type COMPENSATION",
                    )
                    total_merit_stake += MeritConsensus.get_weighted_merit_amount(
                        issuance.amount,
                        issuance.chain_height,
                        blind_vote_tx_height,
                        MeritConsensus.BLOCKS_PER_YEAR,
                    )
                except Exception as e:
                    logger.error(
                        f"Error at get_merit_stake: error={str(e)}, merit={merit}"
                    )
        return total_merit_stake

    @staticmethod
    def _is_signature_valid(
        signature_from_merit: bytes, pub_key_as_hex: str, blind_vote_tx_id: str
    ) -> bool:
        # We verify if signature of hash of blindVoteTxId is correct. EC key from first input for blind vote tx is
        # used for signature.
        if pub_key_as_hex is None:
            logger.error("Error at is_signature_valid: pub_key_as_hex is None")
            return False

        try:
            pub_key = Encryption.get_ec_public_key_from_bytes(
                bytes.fromhex(pub_key_as_hex)
            )
            result = pub_key.ecdsa_verify(
                signature_from_merit, bytes.fromhex(blind_vote_tx_id)
            )
        except Exception as e:
            logger.error(f"Signature verification of issuance failed: {str(e)}")
            return False

        if not result:
            logger.error(
                f"Signature verification of issuance failed: blindVoteTxId={blind_vote_tx_id}, pubKeyAsHex={pub_key_as_hex}"
            )
        return result

    @staticmethod
    def get_weighted_merit_amount(
        amount: int, issuance_height: int, block_height: int, blocks_per_year: int
    ) -> int:
        if issuance_height > block_height:
            raise ValueError(
                f"issuance_height must not be larger than block_height. issuance_height={issuance_height}; block_height={block_height}"
            )
        if block_height < 0:
            raise ValueError(
                f"block_height must not be negative. block_height={block_height}"
            )
        if amount < 0:
            raise ValueError(f"amount must not be negative. amount={amount}")
        if blocks_per_year < 0:
            raise ValueError(
                f"blocks_per_year must not be negative. blocks_per_year={blocks_per_year}"
            )
        if issuance_height < 0:
            raise ValueError(
                f"issuance_height must not be negative. issuance_height={issuance_height}"
            )

        # We use a linear function to apply a factor for the issuance amount of 1 if the issuance was recent and 0
        # if the issuance was 2 years old or older.
        # To avoid rounding issues with float values we multiply initially with a large number and divide at the end
        # by that number again. As we multiply the amount in satoshis we get a reasonably good precision even the long
        # division is not using rounding. Sticking with int values makes that operation safer against consensus
        # failures caused by rounding differences with float.

        max_age = (
            2 * blocks_per_year
        )  # max_age=100 000 (MeritConsensus.BLOCKS_PER_YEAR is 50_000)
        age = min(max_age, block_height - issuance_height)
        inverse_age = max_age - age

        # We want a resolution of 1 block so we use the inverse_age and divide by max_age afterwards to get the
        # weighted amount.
        # We need to multiply first before we divide!
        weighted_amount = (amount * inverse_age) // max_age

        logger.debug(
            f"get_weighted_merit_amount: age={age}, inverse_age={inverse_age}, weighted_amount={weighted_amount}, amount={amount}"
        )
        return weighted_amount

    @staticmethod
    def get_currently_available_merit(
        merit_list: "MeritList", current_chain_height: int
    ) -> int:
        # We need to take the chain height when the blindVoteTx got published so we get the same merit for the vote even at
        # later blocks (merit decreases with each block).
        # We add 1 block to currentChainHeight so that the displayed merit would match the merit in case we get the
        # blind vote tx into the next block.
        height = current_chain_height + 1
        total_merit = 0

        for merit in merit_list.list:
            try:
                issuance = merit.issuance
                check_argument(
                    issuance.issuance_type == IssuanceType.COMPENSATION,
                    "issuance must be of type COMPENSATION",
                )
                issuance_height = issuance.chain_height
                check_argument(
                    issuance_height <= height,
                    "issuance_height must not be larger than current_chain_height",
                )
                total_merit += MeritConsensus.get_weighted_merit_amount(
                    issuance.amount,
                    issuance_height,
                    height,
                    MeritConsensus.BLOCKS_PER_YEAR,
                )
            except Exception as e:
                logger.error(f"Error at get_currently_available_merit: {str(e)}")

        return total_merit
