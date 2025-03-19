from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.sig import Sig
from bisq.core.trade.protocol.bisq_v1.messages.share_buyer_payment_account_message import (
    ShareBuyerPaymentAccountMessage,
)
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.json_util import JsonUtil
from bisq.core.util.validator import Validator
from utils.preconditions import check_argument


class SellerProcessShareBuyerPaymentAccountMessage(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            message = self.process_model.trade_message
            assert message is not None
            assert isinstance(message, ShareBuyerPaymentAccountMessage)
            Validator.check_trade_id(self.process_model.offer_id, message)

            buyer_payment_account_payload = message.buyer_payment_account_payload

            buyer_payment_hash = ProcessModel.hash_of_payment_account_payload(
                buyer_payment_account_payload
            )
            contract = self.trade.contract
            assert contract is not None
            peers_payment_hash = contract.get_hash_of_peers_payment_account_payload(
                self.process_model.pub_key_ring
            )
            check_argument(
                (buyer_payment_hash == peers_payment_hash),
                "Hash of payment account is invalid",
            )

            self.process_model.trade_peer.payment_account_payload = (
                buyer_payment_account_payload
            )
            contract.set_payment_account_payloads(
                buyer_payment_account_payload,
                self.process_model.get_payment_account_payload(self.trade),
                self.process_model.pub_key_ring,
            )

            # As we have added the payment accounts we need to update the json. We also update the signature
            # thought that has less relevance with the changes of 1.7.0
            contract_json = JsonUtil.object_to_json(contract)
            assert contract_json is not None
            signature = Sig.sign(
                self.process_model.key_ring.signature_key_pair.private_key,
                contract_json.encode("utf-8"),
            )
            self.trade.contract_as_json = contract_json  # TODO: check contract_as_json is same as in java

            if contract.is_buyer_maker_and_seller_taker:
                self.trade.taker_contract_signature = signature
            else:
                self.trade.maker_contract_signature = signature

            contract_hash = get_sha256_hash(contract_json.encode("utf-8"))
            self.trade.contract_hash = contract_hash

            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
