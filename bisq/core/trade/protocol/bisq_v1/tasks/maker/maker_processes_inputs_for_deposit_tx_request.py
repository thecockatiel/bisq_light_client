from typing import cast
from bisq.core.exceptions.trade_price_out_of_tolerance_exception import (
    TradePriceOutOfToleranceException,
)
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import (
    InputsForDepositTxRequest,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.coin.coin_util import CoinUtil
from bisq.core.util.validator import Validator
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument, check_not_none, check_state


class MakerProcessesInputsForDepositTxRequest(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            request = cast(InputsForDepositTxRequest, self.process_model.trade_message)
            check_state(
                isinstance(request, InputsForDepositTxRequest),
                f"Expected InputsForDepositTxRequest but got {request.__class__.__name__}",
            )
            Validator.check_trade_id(self.process_model.offer_id, request)

            trading_peer = self.process_model.trade_peer

            # 1.7.0: We do not expect the payment account anymore but in case peer has not updated we still process it.
            if request.taker_payment_account_payload:
                trading_peer.payment_account_payload = (
                    request.taker_payment_account_payload
                )
            if request.hash_of_takers_payment_account_payload:
                trading_peer.hash_of_payment_account_payload = (
                    request.hash_of_takers_payment_account_payload
                )
            if request.takers_payment_method_id:
                trading_peer.payment_method_id = request.takers_payment_method_id

            trading_peer.raw_transaction_inputs = check_not_none(
                request.raw_transaction_inputs
            )
            check_argument(len(request.raw_transaction_inputs) > 0)

            trading_peer.change_output_value = request.change_output_value
            trading_peer.change_output_address = request.change_output_address

            trading_peer.multi_sig_pub_key = check_not_none(
                request.taker_multi_sig_pub_key
            )
            trading_peer.payout_address_string = Validator.non_empty_string_of(
                request.taker_payout_address_string
            )
            trading_peer.pub_key_ring = check_not_none(request.taker_pub_key_ring)

            trading_peer.account_id = Validator.non_empty_string_of(
                request.taker_account_id
            )

            takers_burning_man_selection_height = request.burning_man_selection_height
            check_argument(
                takers_burning_man_selection_height > 0,
                "takers_burning_man_selection_height must not be 0",
            )

            makers_burning_man_selection_height = (
                self.process_model.delayed_payout_tx_receiver_service.get_burning_man_selection_height()
            )
            check_argument(
                takers_burning_man_selection_height
                == makers_burning_man_selection_height,
                "takers_burning_man_selection_height does not match makers_burning_man_selection_height",
            )
            self.process_model.burning_man_selection_height = (
                makers_burning_man_selection_height
            )

            # We set the taker fee only in the processModel yet not in the trade as the tx was only created but not
            # published yet. Once it was published we move it to trade. The takerFeeTx should be sent in a later
            # message but that cannot be changed due backward compatibility issues. It is a left over from the
            # old trade protocol.
            self.process_model.take_offer_fee_tx_id = Validator.non_empty_string_of(
                request.taker_fee_tx_id
            )

            # Taker has to sign offerId (he cannot manipulate that - so we avoid to have a challenge protocol for
            # passing the nonce we want to get signed)
            trading_peer.account_age_witness_nonce = self.trade.get_id().encode("utf-8")
            trading_peer.account_age_witness_signature = (
                request.account_age_witness_signature_of_offer_id
            )
            trading_peer.current_date = request.current_date

            user = check_not_none(self.process_model.user, "User must not be None")

            mediator_node_address = check_not_none(
                request.mediator_node_address,
                "InputsForDepositTxRequest.mediator_node_address must not be None",
            )
            self.trade.mediator_node_address = mediator_node_address
            mediator = check_not_none(
                user.get_accepted_mediator_by_address(mediator_node_address),
                "user.get_accepted_mediator_by_address(mediator_node_address) must not be None",
            )
            self.trade.mediator_pub_key_ring = check_not_none(
                mediator.pub_key_ring, "mediator.pub_key_ring must not be None"
            )

            offer = check_not_none(self.trade.get_offer(), "Offer must not be None")
            try:
                takers_trade_price = request.trade_price
                offer.verify_takers_trade_price(takers_trade_price)
                self.trade.price_as_long = takers_trade_price
            except TradePriceOutOfToleranceException as e:
                self.failed(str(e))
                return
            except Exception as e:
                self.failed(exc=e)
                return

            check_argument(request.trade_amount > 0)
            self.trade.set_amount(Coin.value_of(request.trade_amount))

            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()

        except Exception as e:
            self.failed(exc=e)
