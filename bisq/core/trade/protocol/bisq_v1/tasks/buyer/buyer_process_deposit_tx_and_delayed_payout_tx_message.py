from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.sig import Sig
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.messages.delayed_tx_and_delayed_payout_tx_message import (
    DepositTxAndDelayedPayoutTxMessage,
)
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.json_util import JsonUtil
from bisq.core.util.validator import Validator
from utils.preconditions import check_argument


class BuyerProcessDepositTxAndDelayedPayoutTxMessage(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            message = self.process_model.trade_message
            assert message is not None
            assert isinstance(
                message, DepositTxAndDelayedPayoutTxMessage
            ), f"Expected DepositTxAndDelayedPayoutTxMessage but got {message.__class__.__name__}"
            Validator.check_trade_id(self.process_model.offer_id, message)

            # To access tx confidence we need to add that tx into our wallet.
            deposit_tx_bytes = message.deposit_tx
            assert deposit_tx_bytes is not None
            deposit_tx = (
                self.process_model.btc_wallet_service.get_tx_from_serialized_tx(
                    deposit_tx_bytes
                )
            )
            # update with full tx
            wallet = self.process_model.btc_wallet_service.wallet
            committed_deposit_tx = BtcWalletService.maybe_add_self_tx_to_wallet(
                deposit_tx, wallet
            )
            self.trade.apply_deposit_tx(committed_deposit_tx)
            BtcWalletService.print_tx(
                "depositTx received from peer", committed_deposit_tx
            )

            # To access tx confidence we need to add that tx into our wallet.
            delayed_payout_tx_bytes = message.delayed_payout_tx
            assert delayed_payout_tx_bytes is not None
            check_argument(delayed_payout_tx_bytes == self.trade.delayed_payout_tx_bytes, 
                f"mismatch between delayedPayoutTx received from peer and our one. \n"
                f"Expected: {bytes_as_hex_string(self.trade.delayed_payout_tx_bytes)}\n"
                f"Received: {bytes_as_hex_string(delayed_payout_tx_bytes)}"
            )
            self.trade.apply_delayed_payout_tx_bytes(delayed_payout_tx_bytes)

            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            seller_payment_account_payload = message.seller_payment_account_payload
            if seller_payment_account_payload is not None:
                seller_payment_account_payload_hash = (
                    ProcessModel.hash_of_payment_account_payload(
                        seller_payment_account_payload
                    )
                )
                contract = self.trade.contract
                assert contract is not None
                peers_payment_account_payload_hash = (
                    contract.get_hash_of_peers_payment_account_payload(
                        self.process_model.pub_key_ring
                    )
                )
                check_argument(
                    seller_payment_account_payload_hash
                    == peers_payment_account_payload_hash,
                    "Hash of payment account is invalid"
                )

                self.process_model.trade_peer.payment_account_payload = (
                    seller_payment_account_payload
                )
                contract.set_payment_account_payloads(
                    seller_payment_account_payload,
                    self.process_model.get_payment_account_payload(self.trade),
                    self.process_model.pub_key_ring,
                )

                # As we have added the payment accounts we need to update the json. We also update the signature
                # thought that has less relevance with the changes of 1.7.0
                contract_as_json = JsonUtil.object_to_json(contract)
                signature = Sig.sign(
                    self.process_model.key_ring.signature_key_pair.private_key,
                    contract_as_json,
                )
                self.trade.contract_as_json = contract_as_json

                if contract.is_buyer_maker_and_seller_taker:
                    self.trade.maker_contract_signature = signature
                else:
                    self.trade.taker_contract_signature = signature

                assert contract_as_json is not None
                contract_hash = get_sha256_hash(contract_as_json.encode("utf-8"))
                self.trade.contract_hash = contract_hash

            # If we got already the confirmation we don't want to apply an earlier state
            if (
                self.trade.get_trade_state().value
                < TradeState.BUYER_SAW_DEPOSIT_TX_IN_NETWORK.value
            ):
                self.trade.state_property.set(
                    TradeState.BUYER_RECEIVED_DEPOSIT_TX_PUBLISHED_MSG
                )

            self.process_model.btc_wallet_service.swap_trade_entry_to_available_entry(
                self.trade.get_id(), AddressEntryContext.RESERVED_FOR_TRADE
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
