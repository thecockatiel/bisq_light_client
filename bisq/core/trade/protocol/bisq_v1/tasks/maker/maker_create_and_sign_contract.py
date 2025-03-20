from bisq.common.config.config import Config
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.sig import Sig
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.model.bisq_v1.buyer_as_maker_trade import BuyerAsMakerTrade
from bisq.core.trade.model.bisq_v1.contract import Contract
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.json_util import JsonUtil
from utils.preconditions import check_argument, check_not_none
from bisq.common.setup.log_setup import get_logger

logger = get_logger(__name__)


class MakerCreateAndSignContract(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            taker_fee_tx_id = check_not_none(self.process_model.take_offer_fee_tx_id)

            taker = self.process_model.trade_peer
            is_buyer_maker_and_seller_taker = isinstance(self.trade, BuyerAsMakerTrade)
            buyer_node_address = (
                self.process_model.my_node_address
                if is_buyer_maker_and_seller_taker
                else self.process_model.temp_trading_peer_node_address
            )
            seller_node_address = (
                self.process_model.temp_trading_peer_node_address
                if is_buyer_maker_and_seller_taker
                else self.process_model.my_node_address
            )
            wallet_service = self.process_model.btc_wallet_service
            offer = self.process_model.offer
            offer_id = offer.id
            maker_address_entry = wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.MULTI_SIG
            )
            maker_multi_sig_pub_key = maker_address_entry.pub_key

            taker_address_entry = wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.TRADE_PAYOUT
            )

            hash_of_makers_payment_account_payload = (
                ProcessModel.hash_of_payment_account_payload(
                    self.process_model.get_payment_account_payload(self.trade)
                )
            )
            hash_of_takers_payment_account_payload = (
                taker.hash_of_payment_account_payload
            )
            makers_payment_method_id = check_not_none(
                self.process_model.get_payment_account_payload(self.trade)
            ).payment_method_id
            takers_payment_method_id = check_not_none(taker.payment_method_id)
            offer_payload = offer.offer_payload

            contract = Contract(
                offer_payload=offer_payload,
                trade_amount=check_not_none(self.trade.get_amount()).value,
                trade_price=self.trade.get_price().get_value(),
                taker_fee_tx_id=taker_fee_tx_id,
                buyer_node_address=buyer_node_address,
                seller_node_address=seller_node_address,
                mediator_node_address=self.trade.mediator_node_address,
                is_buyer_maker_and_seller_taker=is_buyer_maker_and_seller_taker,
                maker_account_id=self.process_model.account_id,
                taker_account_id=check_not_none(taker.account_id),
                maker_payment_account_payload=None,
                taker_payment_account_payload=None,
                maker_pub_key_ring=self.process_model.pub_key_ring,
                taker_pub_key_ring=check_not_none(taker.pub_key_ring),
                maker_payout_address_string=taker_address_entry.get_address_string(),
                taker_payout_address_string=check_not_none(taker.payout_address_string),
                maker_multi_sig_pub_key=maker_multi_sig_pub_key,
                taker_multi_sig_pub_key=check_not_none(taker.multi_sig_pub_key),
                lock_time=self.trade.lock_time,
                refund_agent_node_address=self.trade.refund_agent_node_address,
                hash_of_makers_payment_account_payload=hash_of_makers_payment_account_payload,
                hash_of_takers_payment_account_payload=hash_of_takers_payment_account_payload,
                maker_payment_method_id=makers_payment_method_id,
                taker_payment_method_id=takers_payment_method_id,
            )
            contract_as_json = JsonUtil.object_to_json(
                contract
            )  # TODO: check contract_as_json is same as in java
            signature = Sig.sign_message(
                self.process_model.key_ring.signature_key_pair.private_key,
                contract_as_json,
            )

            self.trade.contract = contract
            self.trade.contract_as_json = contract_as_json
            self.trade.maker_contract_signature = signature

            contract_hash = get_sha256_hash(contract_as_json.encode("utf-8"))
            self.trade.contract_hash = contract_hash

            self.process_model.my_multi_sig_pub_key = maker_multi_sig_pub_key

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
