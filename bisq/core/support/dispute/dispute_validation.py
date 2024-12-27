from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.sig import Sig
from bisq.common.setup.log_setup import get_logger
from bisq.core.support.dispute.disput_validation_exceptions import DisputeValidationAddressException, DisputeValidationNodeAddressException, DisputeValidationReplayException
from bisq.core.support.support_type import SupportType
from bisq.core.util.json_util import JsonUtil 
from typing import TYPE_CHECKING, Optional, List, Callable, Dict, Set

from bisq.core.util.regex_validator_factory import RegexValidatorFactory

if TYPE_CHECKING:
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.common.config.config import Config
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.support.dispute.dispute import Dispute
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bitcoinj.core.network_parameters import NetworkParameters
    from bitcoinj.core.transaction import Transaction

logger = get_logger(__name__)

class DisputeValidation:
    @staticmethod
    def validate_dispute_data(dispute: "Dispute", btc_wallet_service: "BtcWalletService"):
        try:
            contract = dispute.contract
            assert contract.offer_payload.id == dispute.trade_id, "Invalid tradeId"
            assert dispute.contract_as_json == JsonUtil.object_to_json(contract), "Invalid contractAsJson"
            assert dispute.contract_hash == get_sha256_hash(dispute.contract_as_json), "Invalid contractHash"

            deposit_tx = dispute.find_deposit_tx(btc_wallet_service)
            if deposit_tx:
                assert deposit_tx.get_tx_id() == dispute.deposit_tx_id, "Invalid depositTxId"
                assert len(deposit_tx.inputs) >= 2, "DepositTx must have at least 2 inputs"

            try:
                # Only the dispute opener has set the signature
                maker_contract_signature = dispute.maker_contract_signature
                if maker_contract_signature:
                    result = Sig.verify_message(contract.maker_pub_key_ring.signature_pub_key,
                             dispute.contract_as_json,
                             maker_contract_signature)
                    if not result:
                        raise ValueError("Invalid maker contract signature")
                
                taker_contract_signature = dispute.taker_contract_signature
                if taker_contract_signature:
                    result = Sig.verify_message(contract.taker_pub_key_ring.signature_pub_key,
                             dispute.contract_as_json,
                             taker_contract_signature)
                    if not result:
                        raise ValueError("Invalid taker contract signature")

            except CryptoException as e:
                raise ValueError(f"Validation failed for dispute: {e}")
        except Exception as t:
            raise ValueError(f"Validation failed for dispute: {t}")

    @staticmethod
    def validate_trade_and_dispute(dispute: "Dispute", trade: "Trade") -> None:
        try:
            assert dispute.contract == trade.contract, "contract must match contract from trade"

            assert trade.delayed_payout_tx is not None, "trade.delayed_payout_tx must not be None"
            assert dispute.delayed_payout_tx_id is not None, "delayed_payout_tx_id must not be None"
            assert dispute.delayed_payout_tx_id == trade.delayed_payout_tx.get_tx_id(), \
                "delayed_payout_tx_id must match delayed_payout_tx_id from trade"

            assert trade.deposit_tx is not None, "trade.deposit_tx must not be None"
            assert dispute.deposit_tx_id is not None, "deposit_tx_id must not be None"
            assert dispute.deposit_tx_id == trade.deposit_tx.get_tx_id(), \
                "deposit_tx must match deposit_tx from trade"

            assert dispute.deposit_tx_serialized is not None, "deposit_tx_serialized must not be None"
        except Exception as e:
            raise ValueError(f"Validation failed for dispute: {e}")

    @staticmethod
    def validate_sender_node_address(dispute: "Dispute", sender_node_address: "NodeAddress") -> None:
        if (sender_node_address != dispute.contract.buyer_node_address and 
            sender_node_address != dispute.contract.seller_node_address):
            raise DisputeValidationNodeAddressException(dispute, "senderNodeAddress not matching any of the traders node addresses")

    @staticmethod 
    def validate_node_addresses(dispute: "Dispute", config: "Config") -> None:
        if not config.use_localhost_for_p2p:
            DisputeValidation._validate_node_address(dispute, dispute.contract.buyer_node_address)
            DisputeValidation._validate_node_address(dispute, dispute.contract.seller_node_address)

    @staticmethod
    def _validate_node_address(dispute: "Dispute", node_address: "NodeAddress") -> None:
        if not RegexValidatorFactory.onion_address_regex_validator().validate(node_address.get_full_address()).is_valid:
            msg = f"Node address {node_address.get_full_address()} at dispute with trade ID {dispute.get_short_trade_id()} is not a valid address"
            logger.error(msg)
            raise DisputeValidationNodeAddressException(dispute, msg)

    @staticmethod
    def validate_donation_address_matches_any_past_param_values(dispute: "Dispute",
                                                              address_as_string: str,
                                                              dao_facade: "DaoFacade") -> None:
        all_past_param_values = dao_facade.get_all_donation_addresses()
        if address_as_string not in all_past_param_values:
            error_msg = (f"Donation address is not a valid DAO donation address.\n"
                        f"Address used in the dispute: {address_as_string}\n"
                        f"All DAO param donation addresses: {all_past_param_values}")
            logger.error(error_msg)
            raise DisputeValidationAddressException(dispute, error_msg)

    @staticmethod
    def validate_donation_address(dispute: "Dispute",
                                delayed_payout_tx: "Transaction",
                                params: "NetworkParameters") -> None:
        # TODO: fix after implementing transaction
        raise NotImplementedError("validate_donation_address")
        # output = delayed_payout_tx.outputs[0]
        # address = output.script_pub_key.get_to_address(params)
        
        # if address is None:
        #     error_msg = f"Donation address cannot be resolved (not of type P2PK nor P2SH nor P2WH). Output: {output}"
        #     logger.error(error_msg)
        #     logger.error(str(delayed_payout_tx))
        #     raise DisputeValidationAddressException(dispute, error_msg)

        # delayed_payout_tx_output_address = str(address)
        # if delayed_payout_tx_output_address != dispute.donation_address_of_delayed_payout_tx:
        #     raise ValueError(
        #         f"donationAddressOfDelayedPayoutTx from dispute does not match address from delayed payout tx. "
        #         f"delayedPayoutTxOutputAddress={delayed_payout_tx_output_address}; "
        #         f"dispute.getDonationAddressOfDelayedPayoutTx()={dispute.donation_address_of_delayed_payout_tx}")

    @staticmethod
    def test_if_any_dispute_tried_replay(dispute_list: List["Dispute"], 
                                        exception_handler: Callable[["DisputeValidationReplayException"], None]) -> None:
        tuple_maps = DisputeValidation._get_test_replay_hash_maps(dispute_list)
        disputes_per_trade_id, disputes_per_delayed_payout_tx_id, disputes_per_deposit_tx_id = tuple_maps

        for dispute_to_test in dispute_list:
            try:
                DisputeValidation._test_if_dispute_tries_replay(dispute_to_test,
                                                              disputes_per_trade_id,
                                                              disputes_per_delayed_payout_tx_id,
                                                              disputes_per_deposit_tx_id)
            except DisputeValidationReplayException as e:
                exception_handler(e)

    @staticmethod
    def test_if_dispute_tries_replay(dispute: "Dispute", dispute_list: List["Dispute"]) -> None:
        tuple_maps = DisputeValidation._get_test_replay_hash_maps(dispute_list)
        disputes_per_trade_id, disputes_per_delayed_payout_tx_id, disputes_per_deposit_tx_id = tuple_maps

        DisputeValidation._test_if_dispute_tries_replay(dispute,
                                                       disputes_per_trade_id,
                                                       disputes_per_delayed_payout_tx_id,
                                                       disputes_per_deposit_tx_id)

    @staticmethod
    def _get_test_replay_hash_maps(dispute_list: List["Dispute"]) -> tuple[Dict[str, Set[str]], 
                                                                          Dict[str, Set[str]], 
                                                                          Dict[str, Set[str]]]:
        disputes_per_trade_id: Dict[str, Set[str]] = {}
        disputes_per_delayed_payout_tx_id: Dict[str, Set[str]] = {}
        disputes_per_deposit_tx_id: Dict[str, Set[str]] = {}

        for dispute in dispute_list:
            uid = dispute.uid
            trade_id = dispute.trade_id

            if trade_id not in disputes_per_trade_id:
                disputes_per_trade_id[trade_id] = set()
            disputes_per_trade_id[trade_id].add(uid)

            delayed_payout_tx_id = dispute.delayed_payout_tx_id
            if delayed_payout_tx_id is not None:
                if delayed_payout_tx_id not in disputes_per_delayed_payout_tx_id:
                    disputes_per_delayed_payout_tx_id[delayed_payout_tx_id] = set()
                disputes_per_delayed_payout_tx_id[delayed_payout_tx_id].add(uid)

            deposit_tx_id = dispute.deposit_tx_id
            if deposit_tx_id is not None:
                if deposit_tx_id not in disputes_per_deposit_tx_id:
                    disputes_per_deposit_tx_id[deposit_tx_id] = set()
                disputes_per_deposit_tx_id[deposit_tx_id].add(uid)

        return (disputes_per_trade_id, disputes_per_delayed_payout_tx_id, disputes_per_deposit_tx_id)

    @staticmethod
    def _test_if_dispute_tries_replay(dispute_to_test: "Dispute",
                                     disputes_per_trade_id: Dict[str, Set[str]],
                                     disputes_per_delayed_payout_tx_id: Dict[str, Set[str]],
                                     disputes_per_deposit_tx_id: Dict[str, Set[str]]) -> None:
        try:
            trade_id = dispute_to_test.trade_id
            delayed_payout_tx_id = dispute_to_test.delayed_payout_tx_id
            deposit_tx_id = dispute_to_test.deposit_tx_id
            uid = dispute_to_test.uid

            # For pre v1.4.0 we do not get the delayed payout tx sent in mediation cases but in refund agent case we do.
            # So until all users have updated to 1.4.0 we only check in refund agent case. With 1.4.0 we send the
            # delayed payout tx also in mediation cases and that if check can be removed.
            if dispute_to_test.support_type == SupportType.REFUND:
                assert delayed_payout_tx_id is not None, f"Delayed payout transaction ID is None. Trade ID: {trade_id}"

            assert deposit_tx_id is not None, f"deposit_tx_id must not be None. Trade ID: {trade_id}"
            assert uid is not None, f"agents_uid must not be None. Trade ID: {trade_id}"

            disputes_per_trade_id_items = disputes_per_trade_id.get(trade_id)
            assert disputes_per_trade_id_items is not None and len(disputes_per_trade_id_items) <= 2, f"We found more than 2 disputes with the same trade ID. Trade ID: {trade_id}"

            if disputes_per_delayed_payout_tx_id:
                items = disputes_per_delayed_payout_tx_id.get(delayed_payout_tx_id)
                assert items is not None and len(items) <= 2, f"We found more than 2 disputes with the same delayedPayoutTxId. Trade ID: {trade_id}"

            if disputes_per_deposit_tx_id:
                items = disputes_per_deposit_tx_id.get(deposit_tx_id)
                assert items is not None and len(items) <= 2, f"We found more than 2 disputes with the same depositTxId. Trade ID: {trade_id}"
                
        except Exception as e:
            logger.error(f"Error at test_if_dispute_tries_replay: dispute_to_test={dispute_to_test}, "
                        f"disputes_per_trade_id={disputes_per_trade_id}, "
                        f"disputes_per_delayed_payout_tx_id={disputes_per_delayed_payout_tx_id}, "
                        f"disputes_per_deposit_tx_id={disputes_per_deposit_tx_id}")
            raise DisputeValidationReplayException(dispute_to_test, f"{repr(e)} at dispute {str(dispute_to_test)}")



