from typing import TYPE_CHECKING
from bisq.common.config.config import Config 
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.exceptions.illegal_state_exception import IllegalStateException 
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_response import (
    InputsForDepositTxResponse,
)
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator
from utils.preconditions import check_argument, check_not_none
 
if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.common.taskrunner.task_runner import TaskRunner

class TakerProcessesInputsForDepositTxResponse(TradeTask):
        
    def __init__(self, task_handler: "TaskRunner[Trade]", trade: "Trade"):
        super().__init__(task_handler, trade)
        self.logger = get_ctx_logger(__name__)

    def run(self):
        try:
            self.run_intercept_hook()

            response = self.process_model.trade_message
            if not isinstance(response, InputsForDepositTxResponse):
                IllegalStateException(
                    f"Expected InputsForDepositTxResponse at TakerProcessesInputsForDepositTxResponse but got {response.__class__.__name__}"
                )
            Validator.check_trade_id(self.process_model.offer_id, response)
            check_not_none(
                response,
                "response should be available at TakerProcessesInputsForDepositTxResponse",
            )

            trading_peer = self.process_model.trade_peer

            # 1.7.0: We do not expect the payment account anymore but in case peer has not updated we still process it.
            if response.maker_payment_account_payload is not None:
                trading_peer.payment_account_payload = (
                    response.maker_payment_account_payload
                )
            if response.hash_of_makers_payment_account_payload is not None:
                trading_peer.hash_of_payment_account_payload = (
                    response.hash_of_makers_payment_account_payload
                )
            if response.makers_payment_method_id is not None:
                trading_peer.payment_method_id = response.makers_payment_method_id

            trading_peer.account_id = Validator.non_empty_string_of(
                response.maker_account_id
            )
            trading_peer.multi_sig_pub_key = check_not_none(
                response.maker_multi_sig_pub_key
            )
            trading_peer.contract_as_json = Validator.non_empty_string_of(
                response.maker_contract_as_json
            )
            trading_peer.contract_signature = Validator.non_empty_string_of(
                response.maker_contract_signature
            )
            trading_peer.payout_address_string = Validator.non_empty_string_of(
                response.maker_payout_address_string
            )
            trading_peer.raw_transaction_inputs = check_not_none(
                response.maker_inputs,
                "maker_inputs should be available at TakerProcessesInputsForDepositTxResponse",
            )
            prepared_deposit_tx = check_not_none(
                response.prepared_deposit_tx,
                "prepared_deposit_tx should be available at TakerProcessesInputsForDepositTxResponse",
            )
            self.process_model.prepared_deposit_tx = prepared_deposit_tx
            lock_time = response.lock_time
            if Config.BASE_CURRENCY_NETWORK_VALUE.is_mainnet():
                my_lock_time = (
                    self.process_model.btc_wallet_service.get_best_chain_height()
                    + Restrictions.get_lock_time(
                        self.process_model.offer.payment_method.is_blockchain()
                    )
                )
                # We allow a tolerance of 3 blocks as BestChainHeight might be a bit different on maker and taker in case a new
                # block was just found
                check_argument(
                    abs(lock_time - my_lock_time) <= 3,
                    f"Lock time of maker is more than 3 blocks different to the lockTime I calculated. Makers lockTime= {lock_time}, myLockTime= {my_lock_time}",
                )
            self.trade.lock_time = lock_time
            delay = (
                self.process_model.btc_wallet_service.get_best_chain_height()
                - lock_time
            )
            self.logger.info(f"lock_time={lock_time}, delay={delay}")

            # Maker has to sign prepared_deposit_tx. He cannot manipulate the prepared_deposit_tx - so we avoid to have a
            # challenge protocol for passing the nonce we want to get signed.
            trading_peer.account_age_witness_nonce = (
                self.process_model.prepared_deposit_tx
            )
            trading_peer.account_age_witness_signature = check_not_none(
                response.account_age_witness_signature_of_prepared_deposit_tx
            )

            trading_peer.current_date = response.current_date

            check_argument(
                len(response.maker_inputs) > 0, "Maker inputs must not be empty"
            )

            # Update to the latest peer address of our peer if the message is correct
            self.trade.trading_peer_node_address = (
                self.process_model.temp_trading_peer_node_address
            )

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
