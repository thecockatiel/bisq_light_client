from pathlib import Path
from typing import Union
from bisq.common.setup.log_setup import get_logger
from bisq.core.api.model.payment_account_type_adapter import PaymentAccountTypeAdapter
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.payment.payment_account_factory import PaymentAccountFactory
from bisq.core.util.json_util import JsonUtil
import tempfile

logger = get_logger(__name__)


class PaymentAccountForm:
    """
    An instance of this class can write new payment account forms (editable json files), and de-serialize edited json files into PaymentAccount instances.

    Example use case: (1) ask for a blank Hal Cash account form, (2) edit it, (3) derive a bisq. core. payment. HalCashAccount instance from the edited json file.


    (1) Ask for a hal cash account form: Pass a PaymentMethod. HAL_CASH_ID to getPaymentAccountForm(String) to get the json Hal Cash payment account form:
    ```
      {
        "_COMMENTS_": [
          "Do not manually edit the paymentMethodId field.",
          "Edit the salt field only if you are recreating a payment account on a new installation and wish to preserve the account age."
        ],
        "paymentMethodId": "HAL_CASH",
        "accountName": "Your accountname",
        "mobileNr": "Your mobilenr"
        "salt": ""
      }
    ```

    (2) Save the Hal Cash payment account form to disk, and edit it:
    ```
      {
        "_COMMENTS_": [
          "Do not manually edit the paymentMethodId field.",
          "Edit the salt field only if you are recreating a payment account on a new installation and wish to preserve the account age."
        ],
        "paymentMethodId": "HAL_CASH",
        "accountName": "Hal Cash Acct",
        "mobileNr": "798 123 456"
        "salt": ""
      }
    ```

    (3) De-serialize the edited json account form: Pass the edited json file to toPaymentAccount(File), or a json string to toPaymentAccount(String) and get a bisq. core. payment. HalCashAccount instance.
      ```
      PaymentAccount(
      paymentMethod=PaymentMethod(id=HAL_CASH,
                                  maxTradePeriod=86400000,
                                  maxTradeLimit=50000000),
      id=e33c9d94-1a1a-43fd-aa11-fcaacbb46100,
      creationDate=Mon Nov 16 12:26:43 BRST 2020,
      paymentAccountPayload=HalCashAccountPayload(mobileNr=798 123 456),
      accountName=Hal Cash Acct,
      tradeCurrencies=[FiatCurrency(currency=EUR)],
      selectedTradeCurrency=FiatCurrency(currency=EUR)
      )
      ```
    """

    # A list of PaymentAccount fields to exclude from json forms.
    excluded_fields = [
        "log",
        "id",
        "acceptedCountryCodes",
        "extraData",
        # "countryCode",
        "creationDate",
        "excludeFromJsonDataMap",
        "maxTradePeriod",
        "paymentAccountPayload",
        "paymentMethod",
        "paymentMethodId",  # Will be included, but handled differently.
        "persistedAccountName",  # Automatically set in PaymentAccount.onPersistChanges().
        "selectedTradeCurrency",  # May be included, but handled differently.
        "tradeCurrencies",  # May be included, but handled differently.
        "HOLDER_NAME",
        "SALT",  # Will be included, but handled differently.
        # for our python implementation we need to exclude snake cases of them as well
        "accepted_country_codes",
        "extra_data",
        # "country_code",
        "creation_date",
        "exclude_from_json_data_map",
        "max_trade_period",
        "payment_account_payload",
        "payment_method",
        "payment_method_id",
        "persisted_account_name",
        "selected_trade_currency",
        "trade_currencies",
    ]

    @staticmethod
    def get_payment_account_form(payment_method_id: str) -> Path:
        """Returns path to a blank payment account form (json) for the given payment_method_id."""
        payment_method = PaymentMethod.get_payment_method(payment_method_id)
        file_path = None
        try:
            acc = PaymentAccountFactory.get_payment_account(payment_method)
            clazz = acc.__class__
            json_string = PaymentAccountTypeAdapter(clazz, PaymentAccountForm.excluded_fields).write(acc)
            with tempfile.NamedTemporaryFile(
                mode="w",
                prefix=f"{payment_method_id.lower()}_form_",
                suffix=".json",
                encoding="utf-8",
                delete=False,
                delete_on_close=False,
            ) as file:
                file.write(json_string)
                file_path = Path(file.name)
            
            if file_path is None:
                raise IllegalStateException(f"cannot create json file for a {payment_method_id} payment method")
        except Exception as ex:
            err_msg = f"cannot create a payment account form for a {payment_method_id} payment method. reason: {ex}"
            logger.error(f"{err_msg.capitalize()}.", exc_info=ex)
            raise IllegalStateException(err_msg)
        return Path(file_path)

    @staticmethod
    def to_payment_account(json_string: str):
        clazz = PaymentAccountForm.get_payment_account_class_from_json(json_string)
        return PaymentAccountTypeAdapter(clazz, PaymentAccountForm.excluded_fields).read(json_string)

    @staticmethod
    def to_json_string(json_file: Union[str, Path]) -> str:
        try:
            with open(json_file, 'r') as file:
                return file.read()
        except Exception as ex:
            err_msg = f"cannot read json string from file '{json_file}'"
            logger.error(f"{err_msg.capitalize()}.", exc_info=ex)
            raise IllegalStateException(err_msg)

    @staticmethod
    def get_payment_account_class_from_json(json_str: str):
        json_map = JsonUtil.parse_json(json_str)
        assert isinstance(json_map, dict), "json string must be a json object"
        payment_method_id = json_map.get("paymentMethodId", None)
        if not payment_method_id:
            raise ValueError(
                f"Cannot find a paymentMethodId in json string: {json_str}"
            )
        return PaymentAccountForm.get_payment_account_class(payment_method_id)

    @staticmethod
    def get_payment_account_class(payment_method_id: str):
        payment_method = PaymentMethod.get_payment_method(payment_method_id)
        return PaymentAccountFactory.get_payment_account(payment_method).__class__
