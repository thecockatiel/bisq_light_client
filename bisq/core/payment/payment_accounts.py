from collections.abc import Callable
import logging
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from bisq.common.setup.log_setup import get_logger

if TYPE_CHECKING:
    from bisq.core.offer.offer import Offer
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.account.witness.account_age_witness_service import (
        AccountAgeWitnessService,
    )


logger = get_logger(__name__)


class PaymentAccounts:
    def __init__(
        self,
        accounts: set["PaymentAccount"],
        account_age_witness_service: "AccountAgeWitnessService",
        validator: "Callable[[Offer, PaymentAccount], bool]" = None,
    ) -> None:
        if validator is None:
            from bisq.core.payment.payment_account_util import PaymentAccountUtil

            validator = PaymentAccountUtil.is_payment_account_valid_for_offer
        self.accounts = accounts
        self.account_age_witness_service = account_age_witness_service
        self.validator = validator

    def get_oldest_payment_account_for_offer(
        self, offer: "Offer"
    ) -> Optional["PaymentAccount"]:
        sorted_valid_accounts = self._sort_valid_accounts(offer)
        self._log_accounts(sorted_valid_accounts)
        return self._first_or_null(sorted_valid_accounts)

    def _sort_valid_accounts(self, offer: "Offer") -> list["PaymentAccount"]:
        valid_accounts = [
            account for account in self.accounts if self.validator(offer, account)
        ]
        # TODO: check if sort result is indeed equal to java code
        return sorted(valid_accounts, key=self._compare_by_trade_limit, reverse=True)

    def _first_or_null(
        self, accounts: list["PaymentAccount"]
    ) -> Optional["PaymentAccount"]:
        return accounts[0] if accounts else None

    def _log_accounts(self, accounts: list["PaymentAccount"]) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            message = ["Valid accounts:"]
            for account in accounts:
                account_name = account.account_name
                witness_hex = (
                    self.account_age_witness_service.get_my_witness_hash_as_hex(
                        account.payment_account_payload
                    )
                )
                message.append(f"name = {account_name}; witness hex = {witness_hex};")

            logger.debug("\n".join(message))

    # Accounts ranked by trade limit
    def _compare_by_trade_limit(self, account: "PaymentAccount") -> int:
        # Mature accounts count as infinite sign age
        has_limit_exception = (
            self.account_age_witness_service.my_has_trade_limit_exception(account)
        )

        if has_limit_exception:
            return (1, 0)  # Will sort at the end

        witness = self.account_age_witness_service.get_my_witness(
            account.payment_account_payload
        )
        sign_age = self.account_age_witness_service.get_witness_sign_age(
            witness, datetime.now()
        )
        return (0, sign_age)
