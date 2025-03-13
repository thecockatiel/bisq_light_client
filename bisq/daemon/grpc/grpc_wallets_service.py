from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.api.model.tx_info import TxInfo
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.daemon.grpc.grpc_waitable_callback_handler import GrpcWaitableCallbackHandler
from grpc_pb2_grpc import WalletsServicer
from grpc_pb2 import (
    GetAddressBalanceReply,
    GetAddressBalanceRequest,
    GetBalancesReply,
    GetBalancesRequest,
    GetDaoStatusReply,
    GetDaoStatusRequest,
    GetFundingAddressesReply,
    GetFundingAddressesRequest,
    GetNetworkRequest,
    GetNetworkReply,
    GetTransactionReply,
    GetTransactionRequest,
    GetTransactionsReply,
    GetTransactionsRequest,
    GetTxFeeRateReply,
    GetTxFeeRateRequest,
    GetUnusedBsqAddressReply,
    GetUnusedBsqAddressRequest,
    LockWalletReply,
    LockWalletRequest,
    RemoveWalletPasswordRequest,
    SendBsqReply,
    SendBsqRequest,
    SendBtcReply,
    SendBtcRequest,
    SetTxFeeRatePreferenceReply,
    SetTxFeeRatePreferenceRequest,
    SetWalletPasswordReply,
    SetWalletPasswordRequest,
    UnlockWalletReply,
    UnlockWalletRequest,
    UnsetTxFeeRatePreferenceReply,
    UnsetTxFeeRatePreferenceRequest,
    VerifyBsqSentToAddressReply,
    VerifyBsqSentToAddressRequest,
)

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from grpc import ServicerContext
    from bisq.daemon.grpc.grpc_exception_handler import GrpcExceptionHandler
    from bisq.core.api.core_api import CoreApi

logger = get_logger(__name__)


class GrpcWalletsService(WalletsServicer):

    def __init__(self, core_api: "CoreApi", exception_handler: "GrpcExceptionHandler"):
        self.core_api = core_api
        self.exception_handler = exception_handler

    def GetNetwork(self, request: "GetNetworkRequest", context: "ServicerContext"):
        try:
            return GetNetworkReply(network=self.core_api.get_network_name())
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetDaoStatus(self, request: "GetDaoStatusRequest", context: "ServicerContext"):
        try:
            return GetDaoStatusReply(
                is_dao_state_ready_and_in_sync=self.core_api.is_dao_state_ready_and_in_sync
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetBalances(self, request: "GetBalancesRequest", context: "ServicerContext"):
        try:
            return GetBalancesReply(
                balances=self.core_api.get_balances(request.currency_code).to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetAddressBalance(
        self, request: "GetAddressBalanceRequest", context: "ServicerContext"
    ):
        try:
            balance_info = self.core_api.get_address_balance_info(request.address)
            return GetAddressBalanceReply(
                address_balance_info=balance_info.to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetFundingAddresses(
        self, request: "GetFundingAddressesRequest", context: "ServicerContext"
    ):
        try:
            funding_addresses = [
                addr.to_proto_message()
                for addr in self.core_api.get_funding_addresses()
            ]
            return GetFundingAddressesReply(address_balance_info=funding_addresses)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetUnusedBsqAddress(
        self, request: "GetUnusedBsqAddressRequest", context: "ServicerContext"
    ):
        try:
            address = self.core_api.get_unused_bsq_address()
            return GetUnusedBsqAddressReply(address=address)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def SendBsq(self, request: "SendBsqRequest", context: "ServicerContext"):
        try:
            handler = GrpcWaitableCallbackHandler["Transaction"]()

            class Listener(TxBroadcasterCallback):
                def on_success(self, transaction):
                    if transaction is not None:
                        handler.handle_result(transaction)
                    else:
                        handler.handle_error_message("bsq transaction is null")

                def on_failure(self, exception):
                    handler.handle_error_message(str(exception))

            self.core_api.send_bsq(
                request.address, request.amount, request.tx_fee_rate, Listener()
            )

            result = handler.wait()
            if handler.has_errored:
                raise IllegalStateException(handler.error_message)
            logger.info(
                f"Successfully published BSQ tx: "
                f"id {result.get_tx_id()}, "
                f"output sum {result.get_output_sum()} sats, "
                f"fee {result.get_fee()} sats, "
                f"size {result.get_message_size()} bytes"
            )
            return SendBsqReply(
                tx_info=TxInfo.from_transaction(result).to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def SendBtc(self, request: "SendBtcRequest", context: "ServicerContext"):
        try:
            handler = GrpcWaitableCallbackHandler["Transaction"]()

            class Listener(TxBroadcasterCallback):
                def on_success(self, transaction):
                    if transaction is not None:
                        handler.handle_result(transaction)
                    else:
                        handler.handle_error_message("btc transaction is null")

                def on_failure(self, exception):
                    handler.handle_error_message(str(exception))

            self.core_api.send_btc(
                request.address,
                request.amount,
                request.tx_fee_rate,
                request.memo,
                Listener(),
            )

            result = handler.wait()
            if handler.has_errored:
                raise IllegalStateException(handler.error_message)
            logger.info(
                f"Successfully published BTC tx: "
                f"id {result.get_tx_id()}, "
                f"output sum {result.get_output_sum()} sats, "
                f"fee {result.get_fee()} sats, "
                f"size {result.get_message_size()} bytes"
            )
            return SendBtcReply(
                tx_info=TxInfo.from_transaction(result).to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def VerifyBsqSentToAddress(
        self, request: "VerifyBsqSentToAddressRequest", context: "ServicerContext"
    ):
        try:
            is_amount_received = self.core_api.verify_bsq_sent_to_address(
                request.address, request.amount
            )
            return VerifyBsqSentToAddressReply(is_amount_received=is_amount_received)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetTxFeeRate(self, request: "GetTxFeeRateRequest", context: "ServicerContext"):
        try:
            tx_fee_rate_info = self.core_api.get_most_recent_tx_fee_rate_info()
            return GetTxFeeRateReply(
                tx_fee_rate_info=tx_fee_rate_info.to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def SetTxFeeRatePreference(
        self, request: "SetTxFeeRatePreferenceRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.set_tx_fee_rate_preference(request.tx_fee_rate_preference)
            tx_fee_rate_info = self.core_api.get_most_recent_tx_fee_rate_info()
            return SetTxFeeRatePreferenceReply(
                tx_fee_rate_info=tx_fee_rate_info.to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def UnsetTxFeeRatePreference(
        self, request: "UnsetTxFeeRatePreferenceRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.unset_tx_fee_rate_preference()
            tx_fee_rate_info = self.core_api.get_most_recent_tx_fee_rate_info()
            return UnsetTxFeeRatePreferenceReply(
                tx_fee_rate_info=tx_fee_rate_info.to_proto_message()
            )
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetTransactions(
        self, request: "GetTransactionsRequest", context: "ServicerContext"
    ):
        try:
            transactions = self.core_api.get_transactions()
            logger.info(f"Transactions count: {len(transactions)}")
            tx_info_list = [
                TxInfo.from_transaction(tx).to_proto_message() for tx in transactions
            ]
            return GetTransactionsReply(tx_info=tx_info_list)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def GetTransaction(
        self, request: "GetTransactionRequest", context: "ServicerContext"
    ):
        try:
            transaction = self.core_api.get_transaction(request.tx_id)
            tx_info = TxInfo.from_transaction(transaction).to_proto_message()
            return GetTransactionReply(tx_info=tx_info)
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def SetWalletPassword(
        self, request: "SetWalletPasswordRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.set_wallet_password(request.password, request.new_password)
            return SetWalletPasswordReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def RemoveWalletPassword(
        self, request: "RemoveWalletPasswordRequest", context: "ServicerContext"
    ):
        try:
            self.core_api.remove_wallet_password(request.password)
            return RemoveWalletPasswordRequest()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def LockWallet(self, request: "LockWalletRequest", context: "ServicerContext"):
        try:
            self.core_api.lock_wallet()
            return LockWalletReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)

    def UnlockWallet(self, request: "UnlockWalletRequest", context: "ServicerContext"):
        try:
            self.core_api.unlock_wallet(request.password, request.timeout)
            return UnlockWalletReply()
        except Exception as e:
            self.exception_handler.handle_exception(logger, e, context)
