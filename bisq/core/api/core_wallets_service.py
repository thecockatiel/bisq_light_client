from collections import defaultdict
from typing import TYPE_CHECKING, Optional
from bisq.common.timer import Timer
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
from bisq.core.user.user_context import UserContext
from bisq.core.util.parsing_utils import ParsingUtils
from bitcoinj.base.coin import Coin
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException
from bitcoinj.core.network_parameters import NetworkParameters
from functools import cache

from utils.aio import FutureCallback

if TYPE_CHECKING:
    from bisq.core.user.user_manager import UserManager
    from bitcoinj.core.transaction_confidence import TransactionConfidence
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.transaction_output import TransactionOutput
    from bisq.core.api.core_context import CoreContext
    from bisq.core.util.coin.coin_formatter import CoinFormatter


# TODO: implement wallet functionaility first and then visit back this file
class CoreWalletsService:

    def __init__(
        self,
        core_context: "CoreContext",
        user_manager: "UserManager",
    ):
        self._user_manager = user_manager
        self.core_context = core_context
        self.lock_timer: Optional[Timer] = None
        self.user_temp_passwords = defaultdict[str, Optional[str]](lambda: None)

    def get_key(self, user_context: "UserContext") -> str:
        self.verify_encrypted_wallet_is_unlocked(user_context)
        return self.user_temp_passwords[user_context.user_id]

    def get_network_parameters(
        self, user_context: "UserContext"
    ) -> "NetworkParameters":
        return user_context.global_container.btc_wallet_service.params

    def get_network_name(self, user_context: "UserContext") -> str:
        network_parameters = self.get_network_parameters(user_context)
        payment_protocol_id = network_parameters.get_payment_protocol_id()
        if payment_protocol_id == NetworkParameters.PAYMENT_PROTOCOL_ID_TESTNET:
            return "testnet3"
        elif payment_protocol_id == NetworkParameters.PAYMENT_PROTOCOL_ID_REGTEST:
            return "regtest"
        else:
            return "mainnet"

    def is_dao_state_ready_and_in_sync(self, user_context: "UserContext") -> bool:
        return user_context.global_container.dao_facade.is_dao_state_ready_and_in_sync

    def get_balances(
        self, user_context: "UserContext", currency_code: str
    ) -> BalancesInfo:
        self._verify_wallet_currency_code_is_valid(currency_code)
        self.verify_wallets_are_available(user_context)
        self.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        if c.balances.available_balance is None:
            raise NotAvailableException("balance is not yet available")

        currency_code = currency_code.strip().upper()
        if currency_code == "BSQ":
            return BalancesInfo(
                self._get_bsq_balances(user_context), BtcBalanceInfo.EMPTY
            )
        elif currency_code == "BTC":
            return BalancesInfo(
                BsqBalanceInfo.EMPTY, self._get_btc_balances(user_context)
            )
        else:
            return BalancesInfo(
                self._get_bsq_balances(user_context),
                self._get_btc_balances(user_context),
            )

    def get_address_balance(
        self, user_context: "UserContext", address_string: str
    ) -> int:
        address = self._get_address_entry(user_context, address_string).get_address()
        return user_context.global_container.btc_wallet_service.get_balance_for_address(
            address
        ).value

    def get_address_balance_info(
        self, user_context: "UserContext", address_string: str
    ) -> "AddressBalanceInfo":
        satoshi_balance = self.get_address_balance(user_context, address_string)
        num_confirmations = self.get_num_confirmations_for_most_recent_transaction(
            user_context, address_string
        )
        address = self._get_address_entry(user_context, address_string).get_address()
        return AddressBalanceInfo(
            address_string,
            satoshi_balance,
            num_confirmations,
            user_context.global_container.btc_wallet_service.is_address_unused(address),
        )

    def get_funding_addresses(
        self, user_context: "UserContext"
    ) -> list["AddressBalanceInfo"]:
        self.verify_wallets_are_available(user_context)
        self.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        # Create a new unused funding address if none exists
        unused_address_exists = any(
            c.btc_wallet_service.is_address_unused(a.get_address())
            for a in c.btc_wallet_service.get_available_address_entries()
        )
        if not unused_address_exists:
            c.btc_wallet_service.get_fresh_address_entry()

        address_strings = [
            entry.get_address_string()
            for entry in c.btc_wallet_service.get_available_address_entries()
        ]

        # get_address_balance is memoized, because we'll map it over addresses twice.
        memoized_balance = cache(self.get_address_balance)

        # Check if any address has zero balance
        no_address_has_zero_balance = all(
            memoized_balance(user_context, addr_str) != 0
            for addr_str in address_strings
        )

        if no_address_has_zero_balance:
            new_zero_balance_address = c.btc_wallet_service.get_fresh_address_entry()
            address_strings.append(new_zero_balance_address.get_address_string())

        return [
            AddressBalanceInfo(
                address,
                memoized_balance(user_context, address),
                self.get_num_confirmations_for_most_recent_transaction(
                    user_context, address
                ),
                c.btc_wallet_service.is_address_unused(
                    self._get_address_entry(user_context, address).get_address()
                ),
            )
            for address in address_strings
        ]

    def get_unused_bsq_address(self, user_context: "UserContext") -> str:
        return (
            user_context.global_container.bsq_wallet_service.get_unused_bsq_address_as_string()
        )

    def send_bsq(
        self,
        user_context: "UserContext",
        address_str: str,
        amount: str,
        tx_fee_rate: str,
        callback: TxBroadcasterCallback,
    ) -> None:
        self.verify_wallets_are_available(user_context)
        self.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        try:
            address = self.get_valid_bsq_address(user_context, address_str)
            receiver_amount = self._get_valid_transfer_amount(amount, c.bsq_formatter)
            tx_fee_per_vbyte = (
                self._get_tx_fee_rate_from_param_or_preference_or_fee_service(
                    user_context, tx_fee_rate
                )
            )
            model = c.bsq_transfer_service.get_bsq_transfer_model(
                address, receiver_amount, tx_fee_per_vbyte
            )
            user_context.logger.info(
                f"Sending {amount} BSQ to {address} with tx fee rate {tx_fee_per_vbyte.value} sats/byte",
            )
            c.bsq_transfer_service.send_funds(model, callback)
        except InsufficientMoneyException as ex:
            user_context.logger.error(str(ex))
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
            user_context.logger.error(str(ex))
            raise IllegalStateException(ex)

    def send_btc(
        self,
        user_context: "UserContext",
        address: str,
        amount: str,
        tx_fee_rate: str,
        memo: str,
        callback: FutureCallback["Transaction"],
    ) -> None:
        self.verify_wallets_are_available(user_context)
        self.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        try:
            from_addresses = {
                entry.get_address_string()
                for entry in c.btc_wallet_service.get_address_entries_for_available_balance_stream()
            }
            receiver_amount = self._get_valid_transfer_amount(amount, c.btc_formatter)
            tx_fee_per_vbyte = (
                self._get_tx_fee_rate_from_param_or_preference_or_fee_service(
                    user_context, tx_fee_rate
                )
            )

            # JAVA TODO Support feeExcluded (or included), default is fee included.
            #  See WithdrawalView # onWithdraw (and refactor).
            fee_estimation_transaction = c.btc_wallet_service.get_fee_estimation_transaction_for_multiple_addresses(
                from_addresses, address, receiver_amount, tx_fee_per_vbyte
            )
            if fee_estimation_transaction is None:
                raise IllegalStateException("could not estimate the transaction fee")

            dust = c.btc_wallet_service.get_dust(fee_estimation_transaction)
            fee = fee_estimation_transaction.get_fee().add(dust)
            if dust.is_positive():
                fee = fee_estimation_transaction.get_fee().add(dust)
                user_context.logger.info(
                    f"Dust txo ({dust.value} sats) was detected, the dust amount has been added to the fee "
                    f"(was {fee_estimation_transaction.get_fee()}, now {fee.value})"
                )

            user_context.logger.info(
                f"Sending {amount} BTC to {address} with tx fee of {fee.value} sats "
                f"(fee rate {tx_fee_per_vbyte.value} sats/byte)"
            )
            c.btc_wallet_service.send_funds_for_multiple_addresses(
                from_addresses,
                address,
                receiver_amount,
                fee,
                None,
                self.user_temp_passwords[user_context.user_id],
                memo if memo else None,
                callback,
            )
        except AddressEntryException as ex:
            user_context.logger.error(str(ex))
            raise IllegalStateException(
                "cannot send btc from any addresses in wallet", ex
            )
        except (InsufficientFundsException, InsufficientMoneyException) as ex:
            user_context.logger.error(str(ex))
            raise NotAvailableException("cannot send btc due to insufficient funds", ex)

    def verify_bsq_sent_to_address(
        self, user_context: "UserContext", address: str, amount: str
    ) -> bool:
        c = user_context.global_container
        receiver_address = self.get_valid_bsq_address(user_context, address)
        network_parameters = self.get_network_parameters(user_context)
        coin_value = ParsingUtils.parse_to_coin(amount, c.bsq_formatter)

        def is_match(tx_out: "TransactionOutput"):
            return (
                tx_out.get_script_pub_key().get_to_address(network_parameters)
                == receiver_address
                and tx_out.get_value().value == coin_value.value
            )

        spendable_bsq_tx_outputs = (
            c.bsq_wallet_service.get_spendable_bsq_transaction_outputs()
        )

        user_context.logger.info(
            f"Searching {len(spendable_bsq_tx_outputs)} spendable tx outputs for matching address {address} and value {coin_value.to_plain_string()}"
        )

        num_matches = 0
        for tx_out in spendable_bsq_tx_outputs:
            if is_match(tx_out):
                user_context.logger.info(
                    f"\t\tTx {tx_out.parent.get_tx_id()} output has matching address {address} and value {tx_out.get_value().to_plain_string()}"
                )
                num_matches += 1

        if num_matches > 1:
            user_context.logger.warning(
                f"{num_matches} tx outputs matched address {address} and value {coin_value.to_plain_string()}, "
                f"could be a false positive BSQ payment verification result."
            )

        return num_matches > 0

    def set_tx_fee_rate_preference(
        self, user_context: "UserContext", tx_fee_rate: int
    ) -> None:
        c = user_context.global_container
        min_fee_per_vbyte = c.fee_service.min_fee_per_vbyte
        if tx_fee_rate < min_fee_per_vbyte:
            raise IllegalArgumentException(
                f"tx fee rate preference must be >= {min_fee_per_vbyte} sats/byte"
            )

        c.preferences.set_use_custom_withdrawal_tx_fee(True)
        sats_per_byte = Coin.value_of(tx_fee_rate)
        c.preferences.set_withdrawal_tx_fee_in_vbytes(sats_per_byte.value)

    def unset_tx_fee_rate_preference(self, user_context: "UserContext") -> None:
        user_context.global_container.preferences.set_use_custom_withdrawal_tx_fee(
            False
        )

    def get_most_recent_tx_fee_rate_info(
        self, user_context: "UserContext"
    ) -> "TxFeeRateInfo":
        c = user_context.global_container
        return TxFeeRateInfo(
            c.preferences.get_use_custom_withdrawal_tx_fee(),
            c.preferences.get_withdrawal_tx_fee_in_vbytes(),
            c.fee_service.min_fee_per_vbyte,
            c.fee_service.get_tx_fee_per_vbyte().value,
            c.fee_service.last_request,
        )

    def get_transactions(
        self,
        user_context: "UserContext",
    ) -> set["Transaction"]:
        return user_context.global_container.btc_wallet_service.get_transactions(False)

    def get_transaction(self, user_context: "UserContext", tx_id: str) -> "Transaction":
        return self._get_transaction_with_id(user_context, tx_id)

    def get_transaction_confirmations(
        self, user_context: "UserContext", tx_id: str
    ) -> int:
        return self._get_transaction_confidence(user_context, tx_id).depth

    def get_num_confirmations_for_most_recent_transaction(
        self, user_context: "UserContext", address_string: str
    ) -> int:
        address = self._get_address_entry(user_context, address_string).get_address()
        confidence = (
            user_context.global_container.btc_wallet_service.get_confidence_for_address(
                address
            )
        )
        return 0 if confidence is None else confidence.confirmations

    def set_wallet_password(
        self, user_context: "UserContext", password: str, new_password: str = None
    ) -> None:
        self.verify_wallets_are_available(user_context)

        raise IllegalStateException(
            "core_wallets_service.set_wallet_password is not implemented yet"
        )

    def lock_wallet(self, user_context: "UserContext") -> None:
        raise IllegalStateException(
            "core_wallets_service.lock_wallet is not implemented yet"
        )

    def unlock_wallet(
        self, user_context: "UserContext", password: str, timeout: int
    ) -> None:
        raise IllegalStateException(
            "core_wallets_service.unlock_wallet is not implemented yet"
        )

    def remove_wallet_password(
        self, user_context: "UserContext", password: str
    ) -> None:
        raise IllegalStateException(
            "core_wallets_service.remove_wallet_password is not implemented yet"
        )

    def verify_wallets_are_available(self, user_context: "UserContext") -> None:
        """Throws a RuntimeError if wallets are not available (encrypted or not)."""
        self.verify_wallet_is_synced(user_context)
        c = user_context.global_container

        # JAVA TODO This check may be redundant, but the AppStartupState is new and unused
        # prior to commit 838595cb03886c3980c40df9cfe5f19e9f8a0e39. I would prefer
        # to leave this check in place until certain AppStartupState will always work
        # as expected.
        if not c.wallets_manager.are_wallets_available():
            raise NotAvailableException("wallet is not yet available")

    def verify_wallet_is_available_and_encrypted(
        self, user_context: "UserContext"
    ) -> None:
        """Throws a RuntimeError if wallets are not available or not encrypted."""
        self.verify_wallet_is_synced(user_context)
        c = user_context.global_container

        if not c.wallets_manager.are_wallets_available():
            raise NotAvailableException("wallet is not yet available")

        if not c.wallets_manager.are_wallets_encrypted():
            raise FailedPreconditionException("wallet is not encrypted with a password")

    def verify_encrypted_wallet_is_unlocked(self, user_context: "UserContext") -> None:
        """Throws a RuntimeError if wallets are encrypted and locked."""
        c = user_context.global_container
        if (
            c.wallets_manager.are_wallets_encrypted()
            and self.user_temp_passwords[user_context.user_id] is None
        ):
            raise FailedPreconditionException("wallet is locked")

    def verify_wallet_is_synced(self, user_context: "UserContext") -> None:
        """Throws a RuntimeError if wallets is not synced yet."""
        c = user_context.global_container
        if not c.app_startup_state.wallet_synced.get():
            raise NotAvailableException("wallet not synced yet")

    def verify_application_is_fully_initialized(
        self, user_context: "UserContext"
    ) -> None:
        """Throws a RuntimeError if application is not fully initialized."""
        c = user_context.global_container
        if not c.app_startup_state.application_fully_initialized.get():
            raise NotAvailableException("server is not fully initialized")

    def get_valid_bsq_address(self, user_context: "UserContext", address: str):
        """Returns an Address for the string, or raises RuntimeError if invalid."""
        try:
            return user_context.global_container.bsq_formatter.get_address_from_bsq_address(
                address
            )
        except Exception as e:
            user_context.logger.error("", exc_info=e)
            raise IllegalArgumentException(f"{address} is not a valid bsq address")

    def _verify_wallet_currency_code_is_valid(self, currency_code: str) -> None:
        """Throws a RuntimeError if wallet currency code is not BSQ or BTC."""
        if not currency_code or not currency_code.strip():
            return

        if currency_code.upper() not in ["BSQ", "BTC"]:
            raise UnsupportedOperationException(
                f"wallet does not support {currency_code}"
            )

    def _maybe_set_wallets_manager_key(self, user_context: "UserContext") -> None:
        """
        Unlike the UI, a daemon cannot capture the user's wallet encryption password
        during startup. This method will set the wallet service's aesKey if necessary.
        """
        if self.user_temp_passwords[user_context.user_id] is None:
            raise IllegalStateException(
                "cannot use None key, unlockwallet timeout may have expired"
            )
        c = user_context.global_container

        if (
            c.btc_wallet_service.password is None
            or c.bsq_wallet_service.password is None
        ):
            password = self.user_temp_passwords[user_context.user_id]
            c.wallets_manager.set_password(password)
            c.wallets_manager.maybe_add_segwit_keychains(password)

    def _get_bsq_balances(self, user_context: "UserContext") -> "BsqBalanceInfo":
        self.verify_wallets_are_available(user_context)
        self.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        available_balance = c.bsq_wallet_service.available_balance
        unverified_balance = c.bsq_wallet_service.unverified_balance
        unconfirmed_change_balance = c.bsq_wallet_service.unconfirmed_change_balance
        locked_for_voting_balance = c.bsq_wallet_service.locked_for_voting_balance
        lockup_bonds_balance = c.bsq_wallet_service.lockup_bonds_balance
        unlocking_bonds_balance = c.bsq_wallet_service.unlocking_bonds_balance

        return BsqBalanceInfo(
            available_balance.value,
            unverified_balance.value,
            unconfirmed_change_balance.value,
            locked_for_voting_balance.value,
            lockup_bonds_balance.value,
            unlocking_bonds_balance.value,
        )

    def _get_btc_balances(self, user_context: "UserContext") -> "BtcBalanceInfo":
        self.verify_wallets_are_available(user_context)
        self.verify_encrypted_wallet_is_unlocked(user_context)
        c = user_context.global_container

        available_balance = c.balances.available_balance
        if available_balance is None:
            raise NotAvailableException("balance is not yet available")

        reserved_balance = c.balances.reserved_balance
        if reserved_balance is None:
            raise NotAvailableException("reserved balance is not yet available")

        locked_balance = c.balances.locked_balance
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
        self, user_context: "UserContext", tx_fee_rate: str
    ) -> "Coin":
        # A non txFeeRate String value overrides the fee service and custom fee.
        if not tx_fee_rate:
            return (
                user_context.global_container.btc_wallet_service.get_tx_fee_for_withdrawal_per_vbyte()
            )
        return Coin.value_of(int(tx_fee_rate))

    def _get_key_crypter_scrypt(self):
        raise IllegalStateException("wallet encrypter is not available")

    def _get_address_entry(self, user_context: "UserContext", address_string: str):
        address_entry = next(
            (
                entry
                for entry in user_context.global_container.btc_wallet_service.get_address_entry_list_as_immutable_list()
                if address_string == entry.get_address_string()
            ),
            None,
        )

        if address_entry is None:
            raise NotFoundException(f"address {address_string} not found in wallet")

        return address_entry

    def _get_transaction_with_id(
        self, user_context: "UserContext", tx_id: str
    ) -> "Transaction":
        if len(tx_id) != 64:
            raise IllegalArgumentException(f"{tx_id} is not a transaction id")

        try:
            tx = user_context.global_container.btc_wallet_service.get_transaction(tx_id)
            if tx is None:
                raise NotFoundException(f"tx with id {tx_id} not found")
            return tx
        except IllegalArgumentException as ex:
            user_context.logger.error(str(ex))
            raise IllegalStateException(
                f"could not get transaction with id {tx_id}\ncause: {str(ex).lower()}"
            )

    def _get_transaction_confidence(
        self, user_context: "UserContext", tx_id: str
    ) -> "TransactionConfidence":
        if len(tx_id) != 64:
            raise IllegalArgumentException(f"{tx_id} is not a transaction id")

        self._get_transaction_with_id(user_context, tx_id)  # raises if not found
        try:
            confidence = user_context.global_container.btc_wallet_service.get_confidence_for_tx_id(
                tx_id
            )
            if confidence is None:
                raise IllegalStateException(f"wallet not initialized yet")
            return confidence
        except IllegalArgumentException as ex:
            user_context.logger.error(str(ex))
            raise IllegalStateException(
                f"could not get confidence for txid {tx_id}\ncause: {str(ex).lower()}"
            )
