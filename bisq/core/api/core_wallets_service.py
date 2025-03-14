from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.api.exception.failed_precondition_exception import (
    FailedPreconditionException,
)
from bisq.core.api.exception.not_available_exception import NotAvailableException
from bisq.core.api.exception.not_found_exception import NotFoundException
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.unsupported_operation_exception import (
    UnsupportedOperationException,
)
from bisq.core.api.model.address_balance_info import AddressBalanceInfo
from bisq.core.api.model.balances_info import BalancesInfo
from bisq.core.api.model.bsq_balance_info import BsqBalanceInfo
from bisq.core.api.model.btc_balance_info import BtcBalanceInfo
from bisq.core.api.model.tx_fee_rate_info import TxFeeRateInfo
from bisq.core.btc.exceptions.address_entry_exception import AddressEntryException
from bisq.core.btc.exceptions.bsq_change_below_dust_exception import (
    BsqChangeBelowDustException,
)
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.btc.exceptions.insufficient_funds_exception import (
    InsufficientFundsException,
)
from bisq.core.btc.exceptions.transaction_verification_exception import (
    TransactionVerificationException,
)
from bisq.core.btc.exceptions.wallet_exception import WalletException
from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback
from bisq.core.util.parsing_utils import ParsingUtils
from bitcoinj.base.coin import Coin
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException
from bitcoinj.core.network_parameters import NetworkParameters
from functools import cache

from utils.aio import FutureCallback

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput
    from bisq.core.api.core_context import CoreContext
    from bisq.core.app.app_startup_state import AppStartupState
    from bisq.core.btc.balances import Balances
    from bisq.core.btc.wallet.bsq_transfer_service import BsqTransferService
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.wallets_manager import WalletsManager
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.user.preferences import Preferences
    from bisq.core.util.coin.bsq_formatter import BsqFormatter
    from bisq.core.util.coin.coin_formatter import CoinFormatter

logger = get_logger(__name__)


# TODO: implement wallet functionaility first and then visit back this file
class CoreWalletsService:

    def __init__(
        self,
        app_startup_state: "AppStartupState",
        core_context: "CoreContext",
        balances: "Balances",
        wallets_manager: "WalletsManager",
        bsq_wallet_service: "BsqWalletService",
        bsq_transfer_service: "BsqTransferService",
        bsq_formatter: "BsqFormatter",
        btc_wallet_service: "BtcWalletService",
        btc_formatter: "CoinFormatter",
        fee_service: "FeeService",
        dao_facade: "DaoFacade",
        preferences: "Preferences",
    ):
        self.app_startup_state = app_startup_state
        self.core_context = core_context
        self.balances = balances
        self.wallets_manager = wallets_manager
        self.bsq_wallet_service = bsq_wallet_service
        self.bsq_transfer_service = bsq_transfer_service
        self.bsq_formatter = bsq_formatter
        self.btc_wallet_service = btc_wallet_service
        self.btc_formatter = btc_formatter
        self.fee_service = fee_service
        self.dao_facade = dao_facade
        self.preferences = preferences

        self.lock_timer: Optional[Timer] = None
        self.temp_password: Optional[str] = None

    def get_key(self) -> str:
        self.verify_encrypted_wallet_is_unlocked()
        return self.temp_password

    def get_network_parameters(self) -> "NetworkParameters":
        return self.btc_wallet_service.params

    def get_network_name(self) -> str:
        network_parameters = self.get_network_parameters()
        payment_protocol_id = network_parameters.get_payment_protocol_id()
        if payment_protocol_id == NetworkParameters.PAYMENT_PROTOCOL_ID_TESTNET:
            return "testnet3"
        elif payment_protocol_id == NetworkParameters.PAYMENT_PROTOCOL_ID_REGTEST:
            return "regtest"
        else:
            return "mainnet"

    @property
    def is_dao_state_ready_and_in_sync(self) -> bool:
        return self.dao_facade.is_dao_state_ready_and_in_sync

    def get_balances(self, currency_code: str) -> BalancesInfo:
        self._verify_wallet_currency_code_is_valid(currency_code)
        self.verify_wallets_are_available()
        self.verify_encrypted_wallet_is_unlocked()

        if self.balances.available_balance is None:
            raise NotAvailableException("balance is not yet available")

        currency_code = currency_code.strip().upper()
        if currency_code == "BSQ":
            return BalancesInfo(self._get_bsq_balances(), BtcBalanceInfo.EMPTY)
        elif currency_code == "BTC":
            return BalancesInfo(BsqBalanceInfo.EMPTY, self._get_btc_balances())
        else:
            return BalancesInfo(self._get_bsq_balances(), self._get_btc_balances())

    def get_address_balance(self, address_string: str) -> int:
        address = self._get_address_entry(address_string).get_address()
        return self.btc_wallet_service.get_balance_for_address(address).value

    def get_address_balance_info(self, address_string: str) -> "AddressBalanceInfo":
        satoshi_balance = self.get_address_balance(address_string)
        num_confirmations = self.get_num_confirmations_for_most_recent_transaction(
            address_string
        )
        address = self._get_address_entry(address_string).get_address()
        return AddressBalanceInfo(
            address_string,
            satoshi_balance,
            num_confirmations,
            self.btc_wallet_service.is_address_unused(address),
        )

    def get_funding_addresses(self) -> list["AddressBalanceInfo"]:
        self.verify_wallets_are_available()
        self.verify_encrypted_wallet_is_unlocked()

        # Create a new unused funding address if none exists
        unused_address_exists = any(
            self.btc_wallet_service.is_address_unused(a.get_address())
            for a in self.btc_wallet_service.get_available_address_entries()
        )
        if not unused_address_exists:
            self.btc_wallet_service.get_fresh_address_entry()

        address_strings = [
            entry.get_address_string()
            for entry in self.btc_wallet_service.get_available_address_entries()
        ]

        # get_address_balance is memoized, because we'll map it over addresses twice.
        memoized_balance = cache(self.get_address_balance)

        # Check if any address has zero balance
        no_address_has_zero_balance = all(
            memoized_balance(addr_str) != 0 for addr_str in address_strings
        )

        if no_address_has_zero_balance:
            new_zero_balance_address = self.btc_wallet_service.get_fresh_address_entry()
            address_strings.append(new_zero_balance_address.get_address_string())

        return [
            AddressBalanceInfo(
                address,
                memoized_balance(address),
                self.get_num_confirmations_for_most_recent_transaction(address),
                self.btc_wallet_service.is_address_unused(
                    self._get_address_entry(address).get_address()
                ),
            )
            for address in address_strings
        ]

    def get_unused_bsq_address(self) -> str:
        return self.bsq_wallet_service.get_unused_bsq_address_as_string()

    def send_bsq(
        self,
        address_str: str,
        amount: str,
        tx_fee_rate: str,
        callback: TxBroadcasterCallback,
    ) -> None:
        self.verify_wallets_are_available()
        self.verify_encrypted_wallet_is_unlocked()

        try:
            address = self.get_valid_bsq_address(address_str)
            receiver_amount = self._get_valid_transfer_amount(
                amount, self.bsq_formatter
            )
            tx_fee_per_vbyte = (
                self._get_tx_fee_rate_from_param_or_preference_or_fee_service(
                    tx_fee_rate
                )
            )
            model = self.bsq_transfer_service.get_bsq_transfer_model(
                address, receiver_amount, tx_fee_per_vbyte
            )
            logger.info(
                f"Sending {amount} BSQ to {address} with tx fee rate {tx_fee_per_vbyte.value} sats/byte",
            )
            self.bsq_transfer_service.send_funds(model, callback)
        except InsufficientMoneyException as ex:
            logger.error(str(ex))
            raise NotAvailableException(
                "cannot send bsq due to insufficient funds",
                ex,
            )
        except (
            ValueError,
            BsqChangeBelowDustException,
            TransactionVerificationException,
            WalletException,
        ) as ex:
            logger.error(str(ex))
            raise IllegalStateException(ex)

    def send_btc(
        self,
        address: str,
        amount: str,
        tx_fee_rate: str,
        memo: str,
        callback: FutureCallback["Transaction"],
    ) -> None:
        self.verify_wallets_are_available()
        self.verify_encrypted_wallet_is_unlocked()

        try:
            from_addresses = {
                entry.get_address_string()
                for entry in self.btc_wallet_service.get_address_entries_for_available_balance_stream()
            }
            receiver_amount = self._get_valid_transfer_amount(
                amount, self.btc_formatter
            )
            tx_fee_per_vbyte = (
                self._get_tx_fee_rate_from_param_or_preference_or_fee_service(
                    tx_fee_rate
                )
            )

            # JAVA TODO Support feeExcluded (or included), default is fee included.
            #  See WithdrawalView # onWithdraw (and refactor).
            fee_estimation_transaction = self.btc_wallet_service.get_fee_estimation_transaction_for_multiple_addresses(
                from_addresses, address, receiver_amount, tx_fee_per_vbyte
            )
            if fee_estimation_transaction is None:
                raise IllegalStateException("could not estimate the transaction fee")

            dust = self.btc_wallet_service.get_dust(fee_estimation_transaction)
            fee = fee_estimation_transaction.get_fee().add(dust)
            if dust.is_positive():
                fee = fee_estimation_transaction.get_fee().add(dust)
                logger.info(
                    f"Dust txo ({dust.value} sats) was detected, the dust amount has been added to the fee "
                    f"(was {fee_estimation_transaction.get_fee()}, now {fee.value})"
                )

            logger.info(
                f"Sending {amount} BTC to {address} with tx fee of {fee.value} sats "
                f"(fee rate {tx_fee_per_vbyte.value} sats/byte)"
            )
            self.btc_wallet_service.send_funds_for_multiple_addresses(
                from_addresses,
                address,
                receiver_amount,
                fee,
                None,
                self.temp_password,
                memo if memo else None,
                callback,
            )
        except AddressEntryException as ex:
            logger.error(str(ex))
            raise IllegalStateException(
                "cannot send btc from any addresses in wallet", ex
            )
        except (InsufficientFundsException, InsufficientMoneyException) as ex:
            logger.error(str(ex))
            raise NotAvailableException("cannot send btc due to insufficient funds", ex)

    def verify_bsq_sent_to_address(self, address: str, amount: str) -> bool:
        receiver_address = self.get_valid_bsq_address(address)
        network_parameters = self.get_network_parameters()
        coin_value = ParsingUtils.parse_to_coin(amount, self.bsq_formatter)

        def is_match(tx_out: "TransactionOutput"):
            return (
                tx_out.get_script_pub_key().get_to_address(network_parameters)
                == receiver_address
                and tx_out.get_value().value == coin_value.value
            )

        spendable_bsq_tx_outputs = (
            self.bsq_wallet_service.get_spendable_bsq_transaction_outputs()
        )

        logger.info(
            f"Searching {len(spendable_bsq_tx_outputs)} spendable tx outputs for matching address {address} and value {coin_value.to_plain_string()}"
        )

        num_matches = 0
        for tx_out in spendable_bsq_tx_outputs:
            if is_match(tx_out):
                logger.info(
                    f"\t\tTx {tx_out.parent.get_tx_id()} output has matching address {address} and value {tx_out.get_value().to_plain_string()}"
                )
                num_matches += 1

        if num_matches > 1:
            logger.warning(
                f"{num_matches} tx outputs matched address {address} and value {coin_value.to_plain_string()}, "
                f"could be a false positive BSQ payment verification result."
            )

        return num_matches > 0

    def set_tx_fee_rate_preference(self, tx_fee_rate: int) -> None:
        min_fee_per_vbyte = self.fee_service.min_fee_per_vbyte
        if tx_fee_rate < min_fee_per_vbyte:
            raise IllegalArgumentException(
                f"tx fee rate preference must be >= {min_fee_per_vbyte} sats/byte"
            )

        self.preferences.set_use_custom_withdrawal_tx_fee(True)
        sats_per_byte = Coin.value_of(tx_fee_rate)
        self.preferences.set_withdrawal_tx_fee_in_vbytes(sats_per_byte.value)

    def unset_tx_fee_rate_preference(self) -> None:
        self.preferences.set_use_custom_withdrawal_tx_fee(False)

    def get_most_recent_tx_fee_rate_info(self) -> "TxFeeRateInfo":
        return TxFeeRateInfo(
            self.preferences.get_use_custom_withdrawal_tx_fee(),
            self.preferences.get_withdrawal_tx_fee_in_vbytes(),
            self.fee_service.min_fee_per_vbyte,
            self.fee_service.get_tx_fee_per_vbyte().value,
            self.fee_service.last_request,
        )

    def get_transactions(self) -> set["Transaction"]:
        return self.btc_wallet_service.get_transactions(False)

    def get_transaction(self, tx_id: str) -> "Transaction":
        return self._get_transaction_with_id(tx_id)

    def get_transaction_confirmations(self, tx_id: str) -> int:
        return (
            self._get_transaction_with_id(tx_id).get_confidence().depth
        )

    def get_num_confirmations_for_most_recent_transaction(
        self, address_string: str
    ) -> int:
        address = self._get_address_entry(address_string).get_address()
        confidence = self.btc_wallet_service.get_confidence_for_address(address)
        return 0 if confidence is None else confidence.depth

    def set_wallet_password(self, password: str, new_password: str = None) -> None:
        self.verify_wallets_are_available()

        raise IllegalStateException(
            "core_wallets_service.set_wallet_password is not implemented yet"
        )

    def lock_wallet(self) -> None:
        raise IllegalStateException(
            "core_wallets_service.lock_wallet is not implemented yet"
        )

    def unlock_wallet(self, password: str, timeout: int) -> None:
        raise IllegalStateException(
            "core_wallets_service.unlock_wallet is not implemented yet"
        )

    def remove_wallet_password(self, password: str) -> None:
        raise IllegalStateException(
            "core_wallets_service.remove_wallet_password is not implemented yet"
        )

    def verify_wallets_are_available(self) -> None:
        """Throws a RuntimeError if wallets are not available (encrypted or not)."""
        self.verify_wallet_is_synced()

        # JAVA TODO This check may be redundant, but the AppStartupState is new and unused
        # prior to commit 838595cb03886c3980c40df9cfe5f19e9f8a0e39. I would prefer
        # to leave this check in place until certain AppStartupState will always work
        # as expected.
        if not self.wallets_manager.are_wallets_available():
            raise NotAvailableException("wallet is not yet available")

    def verify_wallet_is_available_and_encrypted(self) -> None:
        """Throws a RuntimeError if wallets are not available or not encrypted."""
        self.verify_wallet_is_synced()

        if not self.wallets_manager.are_wallets_available():
            raise NotAvailableException("wallet is not yet available")

        if not self.wallets_manager.are_wallets_encrypted():
            raise FailedPreconditionException("wallet is not encrypted with a password")

    def verify_encrypted_wallet_is_unlocked(self) -> None:
        """Throws a RuntimeError if wallets are encrypted and locked."""
        if self.wallets_manager.are_wallets_encrypted() and self.temp_password is None:
            raise FailedPreconditionException("wallet is locked")

    def verify_wallet_is_synced(self) -> None:
        """Throws a RuntimeError if wallets is not synced yet."""
        if not self.app_startup_state.wallet_synced.get():
            raise NotAvailableException("wallet not synced yet")

    def verify_application_is_fully_initialized(self) -> None:
        """Throws a RuntimeError if application is not fully initialized."""
        if not self.app_startup_state.application_fully_initialized.get():
            raise NotAvailableException("server is not fully initialized")

    def get_valid_bsq_address(self, address: str):
        """Returns an Address for the string, or raises RuntimeError if invalid."""
        try:
            return self.bsq_formatter.get_address_from_bsq_address(address)
        except Exception as e:
            logger.error("", exc_info=e)
            raise IllegalArgumentException(f"{address} is not a valid bsq address")

    def _verify_wallet_currency_code_is_valid(self, currency_code: str) -> None:
        """Throws a RuntimeError if wallet currency code is not BSQ or BTC."""
        if not currency_code or not currency_code.strip():
            return

        if currency_code.upper() not in ["BSQ", "BTC"]:
            raise UnsupportedOperationException(
                f"wallet does not support {currency_code}"
            )

    def _maybe_set_wallets_manager_key(self) -> None:
        """
        Unlike the UI, a daemon cannot capture the user's wallet encryption password
        during startup. This method will set the wallet service's aesKey if necessary.
        """
        if self.temp_password is None:
            raise IllegalStateException(
                "cannot use None key, unlockwallet timeout may have expired"
            )

        if (
            self.btc_wallet_service.password is None
            or self.bsq_wallet_service.password is None
        ):
            password = self.temp_password
            self.wallets_manager.set_password(password)
            self.wallets_manager.maybe_add_segwit_keychains(password)

    def _get_bsq_balances(self) -> "BsqBalanceInfo":
        self.verify_wallets_are_available()
        self.verify_encrypted_wallet_is_unlocked()

        available_balance = self.bsq_wallet_service.available_balance
        unverified_balance = self.bsq_wallet_service.unverified_balance
        unconfirmed_change_balance = self.bsq_wallet_service.unconfirmed_change_balance
        locked_for_voting_balance = self.bsq_wallet_service.locked_for_voting_balance
        lockup_bonds_balance = self.bsq_wallet_service.lockup_bonds_balance
        unlocking_bonds_balance = self.bsq_wallet_service.unlocking_bonds_balance

        return BsqBalanceInfo(
            available_balance.value,
            unverified_balance.value,
            unconfirmed_change_balance.value,
            locked_for_voting_balance.value,
            lockup_bonds_balance.value,
            unlocking_bonds_balance.value,
        )

    def _get_btc_balances(self) -> "BtcBalanceInfo":
        self.verify_wallets_are_available()
        self.verify_encrypted_wallet_is_unlocked()

        available_balance = self.balances.available_balance
        if available_balance is None:
            raise NotAvailableException("balance is not yet available")

        reserved_balance = self.balances.reserved_balance
        if reserved_balance is None:
            raise NotAvailableException("reserved balance is not yet available")

        locked_balance = self.balances.locked_balance
        if locked_balance is None:
            raise NotAvailableException("locked balance is not yet available")

        return BtcBalanceInfo(
            available_balance.value,
            reserved_balance.value,
            available_balance.add(reserved_balance).value,
            locked_balance.value,
        )

    def _get_valid_transfer_amount(
        self, amount: str, coin_formatter: "CoinFormatter"
    ) -> "Coin":
        """Returns a Coin for the transfer amount string, or raises if invalid."""
        amount_as_coin = ParsingUtils.parse_to_coin(amount, coin_formatter)
        if amount_as_coin.is_less_than(Restrictions.get_min_non_dust_output()):
            raise IllegalArgumentException(f"{amount} is an invalid transfer amount")
        return amount_as_coin

    def _get_tx_fee_rate_from_param_or_preference_or_fee_service(
        self, tx_fee_rate: str
    ) -> "Coin":
        # A non txFeeRate String value overrides the fee service and custom fee.
        if not tx_fee_rate:
            return self.btc_wallet_service.get_tx_fee_for_withdrawal_per_vbyte()
        return Coin.value_of(int(tx_fee_rate))

    def _get_key_crypter_scrypt(self):
        raise IllegalStateException("wallet encrypter is not available")

    def _get_address_entry(self, address_string: str):
        address_entry = next(
            (
                entry
                for entry in self.btc_wallet_service.get_address_entry_list_as_immutable_list()
                if address_string == entry.get_address_string()
            ),
            None,
        )

        if address_entry is None:
            raise NotFoundException(f"address {address_string} not found in wallet")

        return address_entry

    def _get_transaction_with_id(self, tx_id: str) -> "Transaction":
        if len(tx_id) != 64:
            raise IllegalArgumentException(f"{tx_id} is not a transaction id")

        try:
            tx = self.btc_wallet_service.get_transaction(tx_id)
            if tx is None:
                raise NotFoundException(f"tx with id {tx_id} not found")
            return tx
        except IllegalArgumentException as ex:
            logger.error(str(ex))
            raise IllegalStateException(
                f"could not get transaction with id {tx_id}\ncause: {str(ex).lower()}"
            )
