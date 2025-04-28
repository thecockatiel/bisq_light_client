from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import logger_context
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
    from bisq.core.user.user_manager import UserManager

class GrpcWalletsService(WalletsServicer):

    def __init__(
        self,
        core_api: "CoreApi",
        exception_handler: "GrpcExceptionHandler",
        user_manager: "UserManager",
    ):
        self._core_api = core_api
        self._exception_handler = exception_handler
        self._user_manager = user_manager

    def GetNetwork(self, request: "GetNetworkRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                return GetNetworkReply(
                    network=self._core_api.get_network_name(user_context)
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetDaoStatus(self, request: "GetDaoStatusRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                return GetDaoStatusReply(
                    is_dao_state_ready_and_in_sync=self._core_api.is_dao_state_ready_and_in_sync(
                        user_context
                    )
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetBalances(self, request: "GetBalancesRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                return GetBalancesReply(
                    balances=self._core_api.get_balances(
                        user_context, request.currency_code
                    ).to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetAddressBalance(
        self, request: "GetAddressBalanceRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                balance_info = self._core_api.get_address_balance_info(
                    user_context, request.address
                )
                return GetAddressBalanceReply(
                    address_balance_info=balance_info.to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetFundingAddresses(
        self, request: "GetFundingAddressesRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                funding_addresses = [
                    addr.to_proto_message()
                    for addr in self._core_api.get_funding_addresses(user_context)
                ]
                return GetFundingAddressesReply(address_balance_info=funding_addresses)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetUnusedBsqAddress(
        self, request: "GetUnusedBsqAddressRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                address = self._core_api.get_unused_bsq_address(
                    user_context,
                )
                return GetUnusedBsqAddressReply(address=address)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def SendBsq(self, request: "SendBsqRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                handler = GrpcWaitableCallbackHandler["Transaction"]()

                class Listener(TxBroadcasterCallback):
                    def on_success(self_, transaction):
                        if transaction is not None:
                            handler.handle_result(transaction)
                        else:
                            handler.handle_error_message("bsq transaction is null")

                    def on_failure(self_, exception):
                        handler.handle_error_message(str(exception))

                self._core_api.send_bsq(
                    user_context,
                    request.address,
                    request.amount,
                    request.tx_fee_rate,
                    Listener(),
                )

                result = handler.wait()
                if handler.has_errored:
                    raise IllegalStateException(handler.error_message)
                user_context.logger.info(
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
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def SendBtc(self, request: "SendBtcRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                handler = GrpcWaitableCallbackHandler["Transaction"]()

                class Listener(TxBroadcasterCallback):
                    def on_success(self_, transaction):
                        if transaction is not None:
                            handler.handle_result(transaction)
                        else:
                            handler.handle_error_message("btc transaction is null")

                    def on_failure(self_, exception):
                        handler.handle_error_message(str(exception))

                self._core_api.send_btc(
                    user_context,
                    request.address,
                    request.amount,
                    request.tx_fee_rate,
                    request.memo,
                    Listener(),
                )

                result = handler.wait()
                if handler.has_errored:
                    raise IllegalStateException(handler.error_message)
                user_context.logger.info(
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
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def VerifyBsqSentToAddress(
        self, request: "VerifyBsqSentToAddressRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                is_amount_received = self._core_api.verify_bsq_sent_to_address(
                    user_context, request.address, request.amount
                )
                return VerifyBsqSentToAddressReply(is_amount_received=is_amount_received)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetTxFeeRate(self, request: "GetTxFeeRateRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                tx_fee_rate_info = self._core_api.get_most_recent_tx_fee_rate_info(
                    user_context,
                )
                return GetTxFeeRateReply(
                    tx_fee_rate_info=tx_fee_rate_info.to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def SetTxFeeRatePreference(
        self, request: "SetTxFeeRatePreferenceRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.set_tx_fee_rate_preference(
                    user_context, request.tx_fee_rate_preference
                )
                tx_fee_rate_info = self._core_api.get_most_recent_tx_fee_rate_info(
                    user_context,
                )
                return SetTxFeeRatePreferenceReply(
                    tx_fee_rate_info=tx_fee_rate_info.to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def UnsetTxFeeRatePreference(
        self, request: "UnsetTxFeeRatePreferenceRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.unset_tx_fee_rate_preference(
                    user_context,
                )
                tx_fee_rate_info = self._core_api.get_most_recent_tx_fee_rate_info(
                    user_context,
                )
                return UnsetTxFeeRatePreferenceReply(
                    tx_fee_rate_info=tx_fee_rate_info.to_proto_message()
                )
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetTransactions(
        self, request: "GetTransactionsRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                transactions = self._core_api.get_transactions(
                    user_context,
                )
                user_context.logger.info(f"Transactions count: {len(transactions)}")
                tx_info_list = [
                    TxInfo.from_transaction(tx).to_proto_message() for tx in transactions
                ]
                return GetTransactionsReply(tx_info=tx_info_list)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def GetTransaction(
        self, request: "GetTransactionRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                transaction = self._core_api.get_transaction(user_context, request.tx_id)
                tx_info = TxInfo.from_transaction(transaction).to_proto_message()
                return GetTransactionReply(tx_info=tx_info)
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def SetWalletPassword(
        self, request: "SetWalletPasswordRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.set_wallet_password(
                    user_context,
                    request.password,
                    request.new_password,
                )
                return SetWalletPasswordReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def RemoveWalletPassword(
        self, request: "RemoveWalletPasswordRequest", context: "ServicerContext"
    ):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.remove_wallet_password(user_context, request.password)
                return RemoveWalletPasswordRequest()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def LockWallet(self, request: "LockWalletRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.lock_wallet(
                    user_context,
                )
                return LockWalletReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)

    def UnlockWallet(self, request: "UnlockWalletRequest", context: "ServicerContext"):
        user_context = self._user_manager.active_context
        try:
            with logger_context(user_context.logger):
                self._core_api.unlock_wallet(
                    user_context, request.password, request.timeout
                )
                return UnlockWalletReply()
        except Exception as e:
            self._exception_handler.handle_exception(user_context.logger, e, context)
