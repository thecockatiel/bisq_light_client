from typing import TYPE_CHECKING, cast
from bisq.common.app.dev_env import DevEnv
from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_logger
from bisq.core.api.model.payment_account_form import PaymentAccountForm
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.locale.currency_util import (
    api_supports_crypto_currency,
    find_asset,
    get_crypto_currency,
)
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account_factory import PaymentAccountFactory
from utils.java_compat import java_cmp_str

if TYPE_CHECKING:
    from bisq.core.payment.asset_account import AssetAccount
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.account.witness.account_age_witness_service import (
        AccountAgeWitnessService,
    )
    from bisq.core.api.core_wallets_service import CoreWalletsService
    from bisq.core.user.user import User


logger = get_logger(__name__)

# NOTE: theres a little io in this class, but it's not much to make stuff async. we can reconsider this later.


class CorePaymentAccountsService:

    def __init__(
        self,
        core_wallets_service: "CoreWalletsService",
        account_age_witness_service: "AccountAgeWitnessService",
        user: "User",
        config: "Config",
    ):
        self.core_wallets_service = core_wallets_service
        self.account_age_witness_service = account_age_witness_service
        self.user = user
        self.config = config

    def create_payment_account(self, json_string: str) -> "PaymentAccount":
        payment_account = PaymentAccountForm.to_payment_account(json_string)
        self._verify_payment_account_has_required_fields(payment_account)
        self.user.add_payment_account_if_not_exists(payment_account)
        self.account_age_witness_service.publish_my_account_age_witness(
            payment_account.payment_account_payload
        )
        logger.info(
            f"Saved payment account with id {payment_account.id} and payment method {payment_account.payment_account_payload.payment_method_id}."
        )
        return payment_account

    def get_payment_accounts(self):
        return self.user.payment_accounts

    def get_fiat_payment_methods(self):
        payment_methods = PaymentMethod.get_payment_methods()
        return sorted(
            (method for method in payment_methods if method.is_fiat()),
            key=lambda method: java_cmp_str(method.id),
        )

    def get_payment_account_form_as_string(self, payment_method_id: str) -> str:
        json_form = self.get_payment_account_form(payment_method_id)
        json_str = PaymentAccountForm.to_json_string(json_form)
        json_form.unlink(
            missing_ok=True
        )  # If just asking for a string, delete the form file.
        return json_str

    def get_payment_account_form(self, payment_method_id: str):
        return PaymentAccountForm.get_payment_account_form(payment_method_id)

    def create_crypto_currency_payment_account(
        self, account_name: str, currency_code: str, address: str, trade_instant: bool
    ) -> "PaymentAccount":
        crypto_currency_code = currency_code.upper()
        self._verify_api_does_support_crypto_currency_account(crypto_currency_code)
        self._verify_crypto_currency_address(crypto_currency_code, address)

        crypto_currency_account = None
        if trade_instant:
            # InstantCryptoCurrencyAccount
            crypto_currency_account = cast(
                AssetAccount,
                PaymentAccountFactory.get_payment_account(
                    PaymentMethod.BLOCK_CHAINS_INSTANT
                ),
            )
        else:
            # CryptoCurrencyAccount
            crypto_currency_account = cast(
                AssetAccount,
                PaymentAccountFactory.get_payment_account(PaymentMethod.BLOCK_CHAINS),
            )

        crypto_currency_account.init()
        crypto_currency_account.account_name = account_name
        crypto_currency_account.address = address

        crypto_currency = get_crypto_currency(crypto_currency_code)
        if crypto_currency:
            crypto_currency_account.set_single_trade_currency(crypto_currency)

        self.user.add_payment_account(crypto_currency_account)
        logger.info(
            f"Saved crypto payment account with id {crypto_currency_account.id} and payment method {crypto_currency_account.payment_account_payload.payment_method_id}."
        )
        return crypto_currency_account

    # JAVA TODO Support all alt coin payment methods supported by UI.
    #  The getCryptoCurrencyPaymentMethods method below will be
    #  callable from the CLI when more are supported.

    def get_crypto_currency_payment_methods(self):
        payment_methods = PaymentMethod.get_payment_methods()
        return sorted(
            (method for method in payment_methods if method.is_altcoin()),
            key=lambda method: java_cmp_str(method.id),
        )

    def _verify_crypto_currency_address(self, crypto_currency_code: str, address: str):
        if crypto_currency_code == "BSQ":
            # Validate the BSQ address, but ignore the return value.
            self.core_wallets_service.get_valid_bsq_address(address)
        else:
            asset = self._get_asset(crypto_currency_code)
            if not asset.validate_address(address).is_valid:
                raise IllegalArgumentException(
                    f"{address} is not a valid {crypto_currency_code.lower()} address"
                )

    def _verify_api_does_support_crypto_currency_account(
        self, crypto_currency_code: str
    ):
        if not api_supports_crypto_currency(crypto_currency_code):
            raise IllegalArgumentException(
                f"api does not currently support {crypto_currency_code.lower()} accounts"
            )

    def _get_asset(self, crypto_currency_code: str):
        asset = find_asset(
            crypto_currency_code,
            self.config.base_currency_network,
            DevEnv.is_dao_trading_activated(),
        )
        if asset is None:
            raise IllegalStateException(
                f"crypto currency with code {crypto_currency_code.lower()} not found"
            )
        return asset

    def _verify_payment_account_has_required_fields(
        self, payment_account: "PaymentAccount"
    ):

        if (
            not payment_account.has_multiple_currencies
            and payment_account.get_single_trade_currency() is None
        ):
            raise IllegalArgumentException(
                f"no trade currency defined for {payment_account.payment_method.get_display_string().lower()} payment account"
            )
