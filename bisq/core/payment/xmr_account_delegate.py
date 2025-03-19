from typing import TYPE_CHECKING

from bisq.common.setup.log_setup import get_logger
from bisq.core.xmr.knaccc.monero.address.exceptions.invalid_wallet_address_exception import (
    InvalidWalletAddressException,
)
from bisq.core.xmr.knaccc.monero.address.wallet_address import WalletAddress
from utils.preconditions import check_argument, check_not_none
from utils.time import get_time_ms


if TYPE_CHECKING:
    from bisq.core.payment.asset_account import AssetAccount
    from bisq.core.payment.payment_account import PaymentAccount

logger = get_logger(__name__)


class XmrAccountDelegate:
    """Delegate for AssetAccount with convenient methods for managing the map entries and creating subAccounts."""

    USE_XMR_SUB_ADDRESSES = "UseXMmrSubAddresses"
    KEY_MAIN_ADDRESS = "XmrMainAddress"
    KEY_PRIVATE_VIEW_KEY = "XmrPrivateViewKey"
    KEY_ACCOUNT_INDEX = "XmrAccountIndex"
    KEY_SUB_ADDRESS_INDEX = "XmrSubAddressIndex"
    KEY_SUB_ADDRESS = "XmrSubAddress"
    KEY_TRADE_ID = "TradeId"

    @staticmethod
    def account_is_using_sub_addresses(payment_account: "PaymentAccount") -> bool:
        return (
            payment_account.extra_data is not None
            and payment_account.extra_data.get(
                XmrAccountDelegate.USE_XMR_SUB_ADDRESSES, "0"
            )
            == "1"
        )

    @staticmethod
    def get_sub_address_index_as_long(payment_account: "PaymentAccount") -> int:
        check_not_none(
            payment_account.extra_data, "paymentAccount.extraData must not be None"
        )
        # We let it throw in case the value is not a number
        try:
            return int(
                payment_account.extra_data.get(XmrAccountDelegate.KEY_SUB_ADDRESS_INDEX)
            )
        except (ValueError, TypeError) as e:
            raise RuntimeError(
                f"Could not parse value {payment_account.extra_data.get(XmrAccountDelegate.KEY_SUB_ADDRESS_INDEX)} to long value."
            ) from e

    def __init__(self, account: "AssetAccount"):
        self.account = account

    def create_and_set_new_sub_address(self):
        account_index = int(self.account_index)
        sub_address_index = int(self.sub_address_index)
        # If both sub_address_index and account_index would be 0 it would be the main address
        # and the wallet_address.get_subaddress_base58 call would return an error.
        check_argument(
            sub_address_index >= 0
            and account_index >= 0
            and (sub_address_index + account_index > 0),
            "account_index and/or sub_address_index are invalid",
        )
        private_view_key = self.private_view_key
        main_address = self.main_address
        if not main_address or not private_view_key:
            return
        try:
            wallet_address = WalletAddress(main_address)
            ts = get_time_ms()
            sub_address = wallet_address.get_subaddress_base58(
                private_view_key, account_index, sub_address_index
            )
            logger.info(
                f"Created new sub_address {sub_address}. Took {get_time_ms() - ts} ms."
            )
            self.sub_address = sub_address
        except InvalidWalletAddressException as e:
            logger.error("WalletAddress.get_subaddress_base58 failed", exc_info=e)
            raise RuntimeError(e)

    def reset(self):
        self._map.pop(XmrAccountDelegate.USE_XMR_SUB_ADDRESSES, None)
        self._map.pop(XmrAccountDelegate.KEY_MAIN_ADDRESS, None)
        self._map.pop(XmrAccountDelegate.KEY_PRIVATE_VIEW_KEY, None)
        self._map.pop(XmrAccountDelegate.KEY_ACCOUNT_INDEX, None)
        self._map.pop(XmrAccountDelegate.KEY_SUB_ADDRESS_INDEX, None)
        self._map.pop(XmrAccountDelegate.KEY_SUB_ADDRESS, None)
        self._map.pop(XmrAccountDelegate.KEY_TRADE_ID, None)

        self.account.address = ""

    @property
    def is_using_sub_addresses(self):
        return XmrAccountDelegate.account_is_using_sub_addresses(self.account)

    @is_using_sub_addresses.setter
    def is_using_sub_addresses(self, value: bool):
        self._map[XmrAccountDelegate.USE_XMR_SUB_ADDRESSES] = "1" if value else "0"

    @property
    def sub_address(self) -> str:
        return self._map.get(XmrAccountDelegate.KEY_SUB_ADDRESS, "")

    @sub_address.setter
    def sub_address(self, sub_address: str):
        self._map[XmrAccountDelegate.KEY_SUB_ADDRESS] = sub_address
        self.account.address = sub_address

    @property
    def sub_account_id(self):
        """Unique ID for subAccount used as key in our global subAccount map."""
        return self.main_address + self.account_index

    @property
    def main_address(self):
        return self._map.get(XmrAccountDelegate.KEY_MAIN_ADDRESS, "")

    @main_address.setter
    def main_address(self, main_address: str):
        self._map[XmrAccountDelegate.KEY_MAIN_ADDRESS] = main_address

    @property
    def private_view_key(self):
        return self._map.get(XmrAccountDelegate.KEY_PRIVATE_VIEW_KEY, "")

    @private_view_key.setter
    def private_view_key(self, private_view_key: str):
        self._map[XmrAccountDelegate.KEY_PRIVATE_VIEW_KEY] = private_view_key

    @property
    def account_index(self):
        return self._map.get(XmrAccountDelegate.KEY_ACCOUNT_INDEX, "")

    @account_index.setter
    def account_index(self, account_index: str):
        self._map[XmrAccountDelegate.KEY_ACCOUNT_INDEX] = account_index

    @property
    def sub_address_index_as_long(self) -> int:
        return XmrAccountDelegate.get_sub_address_index_as_long(self.account)

    @property
    def sub_address_index(self):
        return self._map.get(XmrAccountDelegate.KEY_SUB_ADDRESS_INDEX, "")

    @sub_address_index.setter
    def sub_address_index(self, sub_address_index: str):
        self._map[XmrAccountDelegate.KEY_SUB_ADDRESS_INDEX] = sub_address_index

    @property
    def trade_id(self):
        self._map.get(XmrAccountDelegate.KEY_TRADE_ID, "")

    @trade_id.setter
    def trade_id(self, trade_id: str):
        self._map[XmrAccountDelegate.KEY_TRADE_ID] = trade_id

    @property
    def _map(self):
        return self.account.get_or_create_extra_data()
