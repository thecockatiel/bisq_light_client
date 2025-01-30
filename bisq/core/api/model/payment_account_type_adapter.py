from collections.abc import Callable
import importlib
import json
import re
from typing import Any, Generic, Type, TypeVar, Union
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.locale.country_util import find_country_by_code
from bisq.core.locale.currency_util import (
    get_currency_by_country_code,
    get_trade_currencies_in_list,
    get_trade_currency,
)
from bisq.core.locale.res import Res
from bisq.core.payment.country_based_payment_account import CountryBasedPaymentAccount
from bisq.core.payment.money_gram_account import MoneyGramAccount
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.util.json_util import JsonUtil
from utils.formatting import to_camel_case, to_snake_case
from utils.gson_helpers import TypeAdapter
from bisq.core.payment.payment_account import PaymentAccount

from utils.reflection_utils import FieldType, get_settable_fields


_T = TypeVar("T", bound=PaymentAccount)

logger = get_logger(__name__)


class PaymentAccountTypeAdapter(Generic[_T], TypeAdapter[_T]):
    JSON_COMMENTS = [
        "Do not manually edit the paymentMethodId field.",
        "Edit the salt field only if you are recreating a payment"
        + " account on a new installation and wish to preserve the account age.",
    ]

    def __init__(
        self, payment_account_type: Type[_T], excluded_fields: list[str] = None
    ):
        self.payment_account_type = payment_account_type
        self.payment_account_payload_type = self._get_payment_account_payload_type()
        self.excluded_fields = excluded_fields or []
        self.account_fields = dict[str, FieldType]()
        self.account_payload_fields = dict[str, FieldType]()
        self.unique_settable_fields = set()
        self.init_account_settable_fields()

    def init_account_settable_fields(
        self,
    ) -> dict[
        str, Callable[[Union[PaymentAccount, PaymentAccountPayload], str, Any], None]
    ]:
        self.account_fields = {
            f[0]: f[1]
            for f in get_settable_fields(self.payment_account_type)
            if f[0] not in self.excluded_fields
        }
        self.account_payload_fields = {
            f[0]: f[1]
            for f in get_settable_fields(self.payment_account_payload_type)
            if f[0] not in self.excluded_fields
        }
        self.unique_settable_fields = sorted(
            list(
                set(self.account_fields.keys()).union(
                    set(self.account_payload_fields.keys())
                )
            )
        )

    def write(self, account: PaymentAccount):
        # We write a blank payment acct form for a payment method id.
        # We're not serializing a real payment account instance here.
        json_data = {}

        # All json forms start with immutable _COMMENTS_ and paymentMethodId fields.
        self._write_comments(json_data, account)

        json_data["paymentMethodId"] = account.payment_method.id

        # Write the editable, PaymentAccount subclass specific fields.
        self._write_inner_mutable_fields(json_data, account)

        # The last field in all json forms is the empty, editable salt field.
        json_data["salt"] = ""

        return JsonUtil.object_to_json(json_data)

    def _write_comments(self, json_data: dict, account: PaymentAccount):
        json_data["_COMMENTS_"] = PaymentAccountTypeAdapter.JSON_COMMENTS
        if account.has_payment_method_with_id(PaymentMethod.SWIFT_ID):
            # Add extra comments for more complex swift account form.
            wrapped_swift_comments = Res.get_wrapped_as_list(
                "payment.swift.info.account", 110
            )
            json_data["_COMMENTS_"].extend(wrapped_swift_comments)

    def _write_inner_mutable_fields(self, json_data: dict, account: PaymentAccount):
        if account.has_multiple_currencies:
            self._write_trade_currencies_field(json_data, account)
            self._write_selected_trade_currency_field(json_data, account)

        for field in self.unique_settable_fields:
            # Write out a json element if field is settable
            logger.debug(f"Append form with settable field: {field}")
            if field == "country":
                json_data[to_camel_case(field)] = "your two letter country code"
            else:
                json_data[to_camel_case(field)] = f"your {field.lower()}"

    # In some cases (TransferwiseAccount), we need to include a 'tradeCurrencies'
    # field in the json form, though the 'tradeCurrencies' field has no setter method in
    # the PaymentAccount class hierarchy.  At of time of this change, TransferwiseAccount
    # is the only known exception to the rule.
    def _write_trade_currencies_field(self, json_data: dict, account: PaymentAccount):
        field_name = "tradeCurrencies"
        logger.debug(f"Append form with non-settable field: {field_name}")
        json_data[field_name] = (
            "comma delimited currency code list, e.g., gbp,eur,jpy,usd"
        )

    # PaymentAccounts that support multiple 'tradeCurrencies' need to define a
    # 'selectedTradeCurrency' field (not simply defaulting to first in list).
    # Write this field to the form.
    def _write_selected_trade_currency_field(
        self, json_data: dict, account: PaymentAccount
    ):
        field_name = "selectedTradeCurrency"
        logger.debug(f"Append form with settable field: {field_name}")
        json_data[field_name] = "primary trading currency code, e.g., eur"

    def read(self, json_str: str) -> PaymentAccount:
        account = self._init_new_payment_account()

        json_data = json.loads(json_str)
        if not isinstance(json_data, dict):
            raise IllegalStateException(
                f"cannot de-serialize json to a '{account.__class__.__name__}' "
                f"because the json data is not a dictionary."
            )
        for current_field_name, value in json_data.items():

            # The tradeCurrencies field is common to all payment account types,
            # but has no setter.
            if self._did_read_trade_currencies_field(
                json_data, account, current_field_name
            ):
                continue

            # The selectedTradeCurrency field is common to all payment account types,
            # but is @Nullable, and may not need to be explicitly defined by user.
            if self._did_read_selected_trade_currency_field(
                json_data, account, current_field_name
            ):
                continue

            # Some fields are common to all payment account types.
            if self._did_read_common_field(json_data, account, current_field_name):
                continue

            # If the account is a subclass of CountryBasedPaymentAccount, set the
            # account's Country, and use the Country to derive and set the account's
            # FiatCurrency.
            if self._did_read_country_field(json_data, account, current_field_name):
                continue

            self._invoke_setter_method(account, current_field_name, json_data)

        return account

    def _invoke_setter_method(
        self, account: PaymentAccount, field: str, json_data: dict[str, Any]
    ) -> None:
        try:
            # NOTE: we normalize field name to handle forms that are camel case as well
            orig_field = field
            field = to_snake_case(field)
            # The setter might be on the PaymentAccount instance, or its
            # PaymentAccountPayload instance.
            value = self._get_string_or_none(
                json_data, orig_field
            )  # we want to pass orig_field name to help prevent conversion issues, if there's any.
            if field in self.account_fields:
                if self.account_fields[field] == FieldType.DATA:
                    setattr(account, field, value)
                elif self.account_fields[field] == FieldType.PROPERTY:
                    getattr(type(account), field).fset(account, value)
            elif field in self.account_payload_fields:
                if self.account_payload_fields[field] == FieldType.DATA:
                    setattr(account.payment_account_payload, field, value)
                elif self.account_payload_fields[field] == FieldType.PROPERTY:
                    getattr(type(account.payment_account_payload), field).fset(
                        account.payment_account_payload, value
                    )
            else:
                raise IllegalStateException(
                    f"programmer error: cannot de-serialize json to a '{account.__class__.__name__}' "
                    f"because there is no {field} field."
                )
        except Exception as e:
            raise IllegalStateException(
                f"programmer error: cannot set the {field} field on {account.__class__.__name__}. reason: {e}"
            )

    def _get_int_or_none(self, json_data: dict[str, Any], field: str) -> int:
        if field in json_data and json_data[field] is not None:
            return int(json_data[field])
        camel_cased = to_camel_case(field)
        if camel_cased in json_data and json_data[camel_cased] is not None:
            return int(json_data[camel_cased])
        return None

    def _get_string_or_none(self, json_data: dict[str, Any], field: str) -> str:
        if field in json_data and json_data[field] is not None:
            return str(json_data[field])
        camel_cased = to_camel_case(field)
        if camel_cased in json_data and json_data[camel_cased] is not None:
            return str(json_data[camel_cased])
        return None

    @staticmethod
    def _is_comma_delimited_currency_list(s: str) -> bool:
        return s is not None and "," in s

    @classmethod
    def _comma_delimited_codes_to_list(cls, s: str) -> list[str]:
        if cls._is_comma_delimited_currency_list(s):
            return [a.strip().upper() for a in s.split(",")]
        elif s:
            return [s.strip().upper()]
        else:
            return []

    def _did_read_trade_currencies_field(
        self, json_data: dict, account: PaymentAccount, field_name: str
    ) -> bool:
        if field_name not in ["tradeCurrencies", "trade_currencies"]:
            return False

        # The PaymentAccount.tradeCurrencies field is a special case
        field_value = self._get_string_or_none(json_data, field_name)
        currency_codes = self._comma_delimited_codes_to_list(field_value)
        trade_currencies = self._get_reconciled_trade_currencies(
            currency_codes, account
        )

        if trade_currencies:
            for trade_currency in trade_currencies:
                account.add_currency(trade_currency)
        else:
            # Do a check in a calling
            # class to make sure the tradeCurrencies field is populated in the
            # PaymentAccount object, if it is required for the payment account method.
            logger.warning(
                f"No trade currencies were found in the {account.payment_method.get_display_string()} account form."
            )
        return True

    def _get_reconciled_trade_currencies(
        self, currency_codes: list[str], account: PaymentAccount
    ) -> list:
        return get_trade_currencies_in_list(
            currency_codes, account.get_supported_currencies()
        )

    def _did_read_selected_trade_currency_field(
        self, json_data: dict, account: PaymentAccount, field_name: str
    ) -> bool:
        if field_name not in ["selectedTradeCurrency", "selected_trade_currency"]:
            return False

        field_value = self._get_string_or_none(json_data, field_name)
        if field_value:
            trade_currency = get_trade_currency(field_value.upper())
            if trade_currency:
                account.selected_trade_currency = trade_currency
            else:
                logger.error(f"{field_value} is not a valid trade currency code.")
        return True

    def _did_read_common_field(
        self, json_data: dict, account: PaymentAccount, field_name: str
    ) -> bool:
        if field_name in ["_COMMENTS_", "paymentMethodId", "payment_method_id"]:
            # Skip over comments and paymentMethodId field, which
            # are already set on the PaymentAccount instance.
            return True
        elif field_name in ["accountName", "account_name"]:
            # Set the account name using the value read from json.
            account.account_name = self._get_string_or_none(json_data, field_name)
            return True
        elif field_name == "salt":
            # Set the account salt using the value read from json.
            salt_as_hex = self._get_string_or_none(json_data, field_name)
            if salt_as_hex and salt_as_hex.strip():
                account.salt = bytes.fromhex(salt_as_hex)
            return True
        else:
            return False

    def _did_read_country_field(
        self, json_data: dict, account: PaymentAccount, field_name: str
    ) -> bool:
        if field_name not in ["country"]:
            return False

        country_code = self._get_string_or_none(json_data, field_name)
        country = find_country_by_code(country_code)
        if country:
            if isinstance(account, CountryBasedPaymentAccount):
                account.country = country
                fiat_currency = get_currency_by_country_code(country_code)
                account.set_single_trade_currency(fiat_currency)
            elif isinstance(account, MoneyGramAccount):
                account.country = country
            else:
                err_msg = (
                    f"cannot set the country on a {self.payment_account_type.__name__}"
                )
                logger.error(f"{err_msg.capitalize()}.")
                raise IllegalStateException(f"programmer error: {err_msg}")
            return True
        else:
            raise ValueError(f"'{country_code}' is an invalid country code.")

    def _get_payment_account_payload_type(self) -> type:
        try:
            # strip end of PaymentAccountPayload.__module__ to get the package name
            pkg = re.sub(r"\.[^.]+$", "", PaymentAccountPayload.__module__)
            class_name = f"{self.payment_account_type.__name__}Payload"
            payload_pkg = f"{pkg}.{to_snake_case(class_name)}"
            return getattr(importlib.import_module(payload_pkg), class_name)
        except Exception as e:
            errMsg = (
                f"cannot get the payload class for {self.payment_account_type.__name__}"
            )
            logger.error(f"{errMsg.capitalize()}.", exc_info=e)
            raise IllegalStateException(f"programmer error: {errMsg}")

    def _init_new_payment_account(self) -> PaymentAccount:
        try:
            payment_account: PaymentAccount = self.payment_account_type()
            payment_account.init()
            return payment_account
        except Exception as ex:
            errMsg = f"cannot instantiate a new {self.payment_account_type.__name__}"
            logger.error(f"{errMsg.capitalize()}.", exc_info=ex)
            raise IllegalStateException(f"programmer error: {errMsg}")
