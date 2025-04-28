from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.trade.bisq_v1.trade_data_validation_exception import (
    TradeDataInvalidAmountException,
    TradeDataInvalidInputException,
    TradeDataInvalidLockTimeException,
    TradeDataInvalidTxException,
    TradeDataMissingTxException,
    TradeDataValidationException,
)

if TYPE_CHECKING:
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bitcoinj.core.transaction import Transaction
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService


# TODO: check after implementing bitcoinj layer
class TradeDataValidation:
    @staticmethod
    def validate_delayed_payout_tx(trade: 'Trade',
                                 delayed_payout_tx: 'Transaction',
                                 btc_wallet_service: 'BtcWalletService',
                                 address_consumer: Optional[Callable[[str], None]] = None) -> None:
        logger = get_ctx_logger(__name__)
        if delayed_payout_tx is None:
            error_msg = "DelayedPayoutTx must not be None"
            logger.error(error_msg)
            raise TradeDataMissingTxException(error_msg)

        # Validate tx structure
        if len(delayed_payout_tx.inputs) != 1:
            error_msg = "Number of delayedPayoutTx inputs must be 1"
            logger.error(error_msg)
            logger.error(str(delayed_payout_tx))
            raise TradeDataInvalidTxException(error_msg)

        # connectedOutput is null and input.getValue() is null at that point as the tx is not committed to the wallet
        # yet. So we cannot check that the input matches but we did the amount check earlier in the trade protocol.
        
        # Validate lock time
        if delayed_payout_tx.lock_time != trade.lock_time:
            error_msg = "delayed_payout_tx.lock_time must match trade.lock_time"
            logger.error(error_msg)
            logger.error(str(delayed_payout_tx))
            raise TradeDataInvalidLockTimeException(error_msg)

        # Validate seq num (0xFFFFFFFE = TransactionInput.NO_SEQUENCE - 1)
        if delayed_payout_tx.inputs[0].nsequence != 0xFFFFFFFE:
            error_msg = "Sequence number must be 0xFFFFFFFE"
            logger.error(error_msg)
            logger.error(str(delayed_payout_tx))
            raise TradeDataInvalidLockTimeException(error_msg)

        if trade.is_using_legacy_burning_man:
            if len(delayed_payout_tx.outputs) != 1:
                error_msg = "Number of delayedPayoutTx outputs must be 1"
                logger.error(error_msg)
                logger.error(str(delayed_payout_tx))
                raise TradeDataInvalidTxException(error_msg)

            # Check amount
            output = delayed_payout_tx.outputs[0]
            offer = trade.get_offer()
            if offer is None:
                raise TradeDataValidationException("Trade offer must not be None")
            
            if trade.get_amount() is None:
                raise TradeDataValidationException("Trade get_amount must not be None")
            ms_output_amount = offer.buyer_security_deposit.add(offer.seller_security_deposit).add(trade.get_amount())

            if output.get_value() != ms_output_amount:
                error_msg = f"Output value of deposit tx and delayed payout tx is not matching. Output: {output} / msOutputAmount: {ms_output_amount}"
                logger.error(error_msg)
                logger.error(str(delayed_payout_tx))
                raise TradeDataInvalidAmountException(error_msg)

            if address_consumer is not None:
                params = btc_wallet_service.params
                delayed_payout_tx_output_address = str(output.get_script_pub_key().get_to_address(params))
                address_consumer(delayed_payout_tx_output_address)

    @staticmethod
    def validate_payout_tx_input(deposit_tx: 'Transaction',
                               delayed_payout_tx: 'Transaction') -> None:
        input_tx = delayed_payout_tx.inputs[0]
        if input_tx is None:
            raise TradeDataInvalidInputException("delayed_payout_tx.inputs[0] must not be None")
        # input.getConnectedOutput() is null as the tx is not committed at that point

        outpoint = input_tx.outpoint
        if str(outpoint.hash) != deposit_tx.get_tx_id() or outpoint.index != 0:
            raise TradeDataInvalidInputException(
                f"Input of delayed payout transaction does not point to output of deposit tx.\n"
                f"Delayed payout tx={delayed_payout_tx}\n"
                f"Deposit tx={deposit_tx}")

    @staticmethod
    def validate_deposit_inputs(trade: 'Trade') -> None:
        # assumption: deposit tx always has 2 inputs, the maker and taker
        if (trade is None or trade.deposit_tx is None or
                len(trade.deposit_tx.inputs) != 2):
            raise TradeDataInvalidTxException("Deposit transaction is None or has unexpected input count")

        deposit_tx = trade.deposit_tx
        tx_id_input0 = str(deposit_tx.inputs[0].outpoint.hash)
        tx_id_input1 = str(deposit_tx.inputs[1].outpoint.hash)
        contract_maker_tx_id = trade.contract.offer_payload.offer_fee_payment_tx_id
        contract_taker_tx_id = trade.contract.taker_fee_tx_id
        
        maker_first_match = (contract_maker_tx_id.lower() == tx_id_input0.lower() and
                           contract_taker_tx_id.lower() == tx_id_input1.lower())
        taker_first_match = (contract_maker_tx_id.lower() == tx_id_input1.lower() and
                           contract_taker_tx_id.lower() == tx_id_input0.lower())

        if not maker_first_match and not taker_first_match:
            err_msg = "Maker/Taker txId in contract does not match deposit tx input"
            logger = get_ctx_logger(__name__)
            logger.error(f"{err_msg}\n"
                        f"Contract Maker tx={contract_maker_tx_id} Contract Taker tx={contract_taker_tx_id}\n"
                        f"Deposit Input0={tx_id_input0} Deposit Input1={tx_id_input1}")
            raise TradeDataInvalidTxException(err_msg)

