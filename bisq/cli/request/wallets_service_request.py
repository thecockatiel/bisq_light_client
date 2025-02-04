from typing import TYPE_CHECKING
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
import grpc_pb2

if TYPE_CHECKING:
    from bisq.cli.grpc_stubs import GrpcStubs


class WalletsServiceRequest:

    def __init__(self, grpc_stubs: "GrpcStubs"):
        self.grpc_stubs = grpc_stubs

    def get_network(self) -> str:
        request = grpc_pb2.GetNetworkRequest()
        response: grpc_pb2.GetNetworkReply = self.grpc_stubs.wallets_service.GetNetwork(
            request
        )
        return response.network

    def get_dao_status(self) -> bool:
        request = grpc_pb2.GetDaoStatusRequest()
        response: grpc_pb2.GetDaoStatusReply = (
            self.grpc_stubs.wallets_service.GetDaoStatus(request)
        )
        return response.is_dao_state_ready_and_in_sync

    def get_all_balances(self) -> grpc_pb2.BalancesInfo:
        return self.get_balances("")

    def get_bsq_balances(self) -> grpc_pb2.BsqBalanceInfo:
        return self.get_balances("BSQ").bsq

    def get_btc_balances(self) -> grpc_pb2.BtcBalanceInfo:
        return self.get_balances("BTC").btc

    def get_balances(self, currency_code: str) -> grpc_pb2.BalancesInfo:
        request = grpc_pb2.GetBalancesRequest(currency_code=currency_code)
        response: grpc_pb2.GetBalancesReply = (
            self.grpc_stubs.wallets_service.GetBalances(request)
        )
        return response.balances

    def get_address_balance(self, address: str) -> grpc_pb2.AddressBalanceInfo:
        request = grpc_pb2.GetAddressBalanceRequest(address=address)
        response: grpc_pb2.GetAddressBalanceReply = (
            self.grpc_stubs.wallets_service.GetAddressBalance(request)
        )
        return response.address_balance_info

    def get_btc_price(self, currency_code: str) -> float:
        request = grpc_pb2.MarketPriceRequest(currency_code=currency_code)
        response: grpc_pb2.MarketPriceReply = (
            self.grpc_stubs.price_service.GetMarketPrice(request)
        )
        return response.price

    def get_funding_addresses(self) -> list[grpc_pb2.AddressBalanceInfo]:
        request = grpc_pb2.GetFundingAddressesRequest()
        response: grpc_pb2.GetFundingAddressesReply = (
            self.grpc_stubs.wallets_service.GetFundingAddresses(request)
        )
        return response.address_balance_info

    def get_unused_bsq_address(self) -> str:
        request = grpc_pb2.GetUnusedBsqAddressRequest()
        response: grpc_pb2.GetUnusedBsqAddressReply = (
            self.grpc_stubs.wallets_service.GetUnusedBsqAddress(request)
        )
        return response.address

    def get_unused_btc_address(self) -> str:
        request = grpc_pb2.GetFundingAddressesRequest()
        response: grpc_pb2.GetFundingAddressesReply = (
            self.grpc_stubs.wallets_service.GetFundingAddresses(request)
        )
        address_balances = response.address_balance_info
        unused_address = next(
            (
                address_info.address
                for address_info in address_balances
                if address_info.is_address_unused
            ),
            None,
        )
        if unused_address is None:
            raise IllegalStateException("No unused BTC address found")
        return unused_address

    def send_bsq(self, address: str, amount: str, tx_fee_rate: str) -> grpc_pb2.TxInfo:
        request = grpc_pb2.SendBsqRequest(
            address=address, amount=amount, tx_fee_rate=tx_fee_rate
        )
        response: grpc_pb2.SendBsqReply = self.grpc_stubs.wallets_service.SendBsq(
            request
        )
        return response.tx_info

    def send_btc(
        self, address: str, amount: str, tx_fee_rate: str, memo: str
    ) -> grpc_pb2.TxInfo:
        request = grpc_pb2.SendBtcRequest(
            address=address, amount=amount, tx_fee_rate=tx_fee_rate, memo=memo
        )
        response: grpc_pb2.SendBtcReply = self.grpc_stubs.wallets_service.SendBtc(
            request
        )
        return response.tx_info

    def verify_bsq_sent_to_address(self, address: str, amount: str) -> bool:
        request = grpc_pb2.VerifyBsqSentToAddressRequest(address=address, amount=amount)
        response: grpc_pb2.VerifyBsqSentToAddressReply = (
            self.grpc_stubs.wallets_service.VerifyBsqSentToAddress(request)
        )
        return response.is_amount_received

    def get_tx_fee_rate(self) -> grpc_pb2.TxFeeRateInfo:
        request = grpc_pb2.GetTxFeeRateRequest()
        response: grpc_pb2.GetTxFeeRateReply = (
            self.grpc_stubs.wallets_service.GetTxFeeRate(request)
        )
        return response.tx_fee_rate_info

    def set_tx_fee_rate(self, tx_fee_rate: int) -> grpc_pb2.TxFeeRateInfo:
        request = grpc_pb2.SetTxFeeRatePreferenceRequest(
            tx_fee_rate_preference=tx_fee_rate
        )
        response: grpc_pb2.SetTxFeeRatePreferenceReply = (
            self.grpc_stubs.wallets_service.SetTxFeeRatePreference(request)
        )
        return response.tx_fee_rate_info

    def unset_tx_fee_rate(self) -> grpc_pb2.TxFeeRateInfo:
        request = grpc_pb2.UnsetTxFeeRatePreferenceRequest()
        response: grpc_pb2.UnsetTxFeeRatePreferenceReply = (
            self.grpc_stubs.wallets_service.UnsetTxFeeRatePreference(request)
        )
        return response.tx_fee_rate_info

    def get_transactions(self) -> list[grpc_pb2.TxInfo]:
        request = grpc_pb2.GetTransactionsRequest()
        response: grpc_pb2.GetTransactionsReply = (
            self.grpc_stubs.wallets_service.GetTransactions(request)
        )
        return response.tx_info

    def get_transaction(self, tx_id: str) -> grpc_pb2.TxInfo:
        request = grpc_pb2.GetTransactionRequest(tx_id=tx_id)
        response: grpc_pb2.GetTransactionReply = (
            self.grpc_stubs.wallets_service.GetTransaction(request)
        )
        return response.tx_info

    def lock_wallet(self) -> grpc_pb2.LockWalletReply:
        request = grpc_pb2.LockWalletRequest()
        response: grpc_pb2.LockWalletReply = self.grpc_stubs.wallets_service.LockWallet(
            request
        )
        return response

    def unlock_wallet(
        self, wallet_password: str, timeout: int
    ) -> grpc_pb2.UnlockWalletReply:
        request = grpc_pb2.UnlockWalletRequest(
            password=wallet_password, timeout=timeout
        )
        response: grpc_pb2.UnlockWalletReply = (
            self.grpc_stubs.wallets_service.UnlockWallet(request)
        )
        return response

    def remove_wallet_password(
        self, wallet_password: str
    ) -> grpc_pb2.RemoveWalletPasswordReply:
        request = grpc_pb2.RemoveWalletPasswordRequest(password=wallet_password)
        response: grpc_pb2.RemoveWalletPasswordReply = (
            self.grpc_stubs.wallets_service.RemoveWalletPassword(request)
        )
        return response

    def set_wallet_password(
        self, wallet_password: str, new_wallet_password: str = None
    ) -> grpc_pb2.SetWalletPasswordReply:
        request = grpc_pb2.SetWalletPasswordRequest(password=wallet_password)
        if new_wallet_password is not None:
            request.new_password = new_wallet_password
        response: grpc_pb2.SetWalletPasswordReply = (
            self.grpc_stubs.wallets_service.SetWalletPassword(request)
        )
        return response
