from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.sig import Sig
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.model.bisq_v1.contract import Contract
from bisq.core.trade.model.bisq_v1.seller_as_taker_trade import SellerAsTakerTrade
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.json_util import JsonUtil
from utils.preconditions import check_argument, check_not_none


class TakerVerifyAndSignContract(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            taker_fee_tx_id = check_not_none(self.process_model.take_offer_fee_tx_id)
            maker = self.process_model.trade_peer

            is_buyer_maker_and_seller_taker = isinstance(self.trade, SellerAsTakerTrade)
            buyer_node_address = (
                self.process_model.temp_trading_peer_node_address
                if is_buyer_maker_and_seller_taker
                else self.process_model.my_node_address
            )
            seller_node_address = (
                self.process_model.my_node_address
                if is_buyer_maker_and_seller_taker
                else self.process_model.temp_trading_peer_node_address
            )

            wallet_service = self.process_model.btc_wallet_service
            offer = self.process_model.offer
            offer_id = offer.id
            taker_payout_address_entry = wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.TRADE_PAYOUT
            )
            taker_payout_address_string = (
                taker_payout_address_entry.get_address_string()
            )
            taker_multi_sig_address_entry = wallet_service.get_or_create_address_entry(
                offer_id, AddressEntryContext.MULTI_SIG
            )
            taker_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            check_argument(
                taker_multi_sig_pub_key == taker_multi_sig_address_entry.pub_key,
                f"takerMultiSigPubKey from AddressEntry must match the one from the trade data. trade id = {offer_id}",
            )

            hash_of_makers_payment_account_payload = (
                maker.hash_of_payment_account_payload
            )
            hash_of_takers_payment_account_payload = (
                ProcessModel.hash_of_payment_account_payload(
                    self.process_model.get_payment_account_payload(self.trade)
                )
            )
            makers_payment_method_id = check_not_none(
                maker.payment_method_id, "maker.payment_method_id must not be None"
            )
            takers_payment_method_id = check_not_none(
                self.process_model.get_payment_account_payload(self.trade),
                "process_model.get_payment_account_payload() must not be None",
            ).payment_method_id

            trade_amount = check_not_none(self.trade.get_amount())
            offer_payload = check_not_none(
                offer.offer_payload, "offer.offer_payload must not be None"
            )
            contract = Contract(
                offer_payload=offer_payload,
                trade_amount=trade_amount.value,
                trade_price=self.trade.get_price().value,
                taker_fee_tx_id=taker_fee_tx_id,
                buyer_node_address=buyer_node_address,
                seller_node_address=seller_node_address,
                mediator_node_address=self.trade.mediator_node_address,
                is_buyer_maker_and_seller_taker=is_buyer_maker_and_seller_taker,
                maker_account_id=maker.account_id,
                taker_account_id=self.process_model.account_id,
                maker_payment_account_payload=None,
                taker_payment_account_payload=None,
                maker_pub_key_ring=maker.pub_key_ring,
                taker_pub_key_ring=self.process_model.pub_key_ring,
                maker_payout_address_string=maker.payout_address_string,
                taker_payout_address_string=taker_payout_address_string,
                maker_multi_sig_pub_key=maker.multi_sig_pub_key,
                taker_multi_sig_pub_key=taker_multi_sig_pub_key,
                lock_time=self.trade.lock_time,
                refund_agent_node_address=self.trade.refund_agent_node_address,
                hash_of_makers_payment_account_payload=hash_of_makers_payment_account_payload,
                hash_of_takers_payment_account_payload=hash_of_takers_payment_account_payload,
                maker_payment_method_id=makers_payment_method_id,
                taker_payment_method_id=takers_payment_method_id,
            )
            contract_as_json = JsonUtil.object_to_json(contract)
            # TODO: check contract_as_json is same as in java

            if contract_as_json != self.process_model.trade_peer.contract_as_json:
                contract.print_diff(self.process_model.trade_peer.contract_as_json)
                self.failed("Contracts are not matching")
                return

            signature = Sig.sign_message(
                self.process_model.key_ring.signature_key_pair.private_key,
                contract_as_json,
            )
            self.trade.contract = contract
            self.trade.contract_as_json = contract_as_json

            contract_hash = get_sha256_hash(
                check_not_none(contract_as_json, "contract_as_json must not be None")
            )
            self.trade.contract_hash = contract_hash

            self.trade.taker_contract_signature = signature

            self.process_model.trade_manager.request_persistence()
            try:
                check_not_none(
                    maker.pub_key_ring, "maker.pub_key_ring must not be None"
                )
                Sig.verify_message(
                    maker.pub_key_ring.signature_pub_key,
                    contract_as_json,
                    maker.contract_signature,
                )
                self.complete()
            except Exception as e:
                self.failed(f"Contract signature verification failed. {e}")
        except Exception as e:
            self.failed(exc=e)
