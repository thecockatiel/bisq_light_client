from datetime import datetime
from typing import TYPE_CHECKING, cast
from bisq.common.app.dev_env import DevEnv
from bisq.core.monetary.volume import Volume
from bisq.core.payment.payload.assets_account_payload import AssetsAccountPayload
from bisq.core.trade.txproof.asset_tx_proof_model import AssetTxProofModel

if TYPE_CHECKING:
    from bisq.core.user.auto_confirm_settings import AutoConfirmSettings
    from bisq.core.trade.model.bisq_v1.trade import Trade


class XmrTxProofModel(AssetTxProofModel):
    # These are values from a valid tx which are set automatically if DevEnv.isDevMode is enabled
    DEV_ADDRESS = "85q13WDADXE26W6h7cStpPMkn8tWpvWgHbpGWWttFEafGXyjsBTXxxyQms4UErouTY5sdKpYHVjQm6SagiCqytseDkzfgub"
    DEV_TX_KEY = "f3ce66c9d395e5e460c8802b2c3c1fff04e508434f9738ee35558aac4678c906"
    DEV_TX_HASH = "5e665addf6d7c6300670e8a89564ed12b5c1a21c336408e2835668f9a6a0d802"
    DEV_AMOUNT = 8902597360000

    def __init__(
        self,
        service_address: str,
        auto_confirm_settings: "AutoConfirmSettings",
        volume: Volume,
        recipient_address: str,
        tx_hash: str,
        tx_key: str,
        trade_date: datetime,
        trade_id: str,
    ):
        self.service_address = service_address
        self.auto_confirm_settings = auto_confirm_settings

        self.amount = (
            XmrTxProofModel.DEV_AMOUNT
            if DevEnv.is_dev_mode()
            else (volume.value * 10000 if volume else 0)
        )  # XMR satoshis have 12 decimal places vs. bitcoin's 8
        self.recipient_address = (
            XmrTxProofModel.DEV_ADDRESS
            if DevEnv.is_dev_mode()
            else recipient_address
        )
        self.tx_hash = tx_hash
        self.tx_key = tx_key
        self.trade_date = trade_date
        self.trade_id = trade_id

    @staticmethod
    def from_trade(
        trade: "Trade",
        service_address: str,
        auto_confirm_settings: "AutoConfirmSettings",
    ) -> "XmrTxProofModel":
        volume = trade.get_volume()
        assert trade.contract is not None, "trade.contract must not be None"
        sellers_payment_account_payload = trade.contract.seller_payment_account_payload
        assert (
            sellers_payment_account_payload is not None
        ), "trade.contract.sellers_payment_account_payload must not be None"
        # For dev testing we need to add the matching address to the dev tx key and dev view key
        recipient_address = cast(AssetsAccountPayload, sellers_payment_account_payload).address
        tx_hash = trade.counter_currency_tx_id
        tx_key = trade.counter_currency_extra_data
        trade_date = trade.get_date()
        trade_id = trade.get_id()
        return XmrTxProofModel(
            service_address,
            auto_confirm_settings,
            volume,
            recipient_address,
            tx_hash,
            tx_key,
            trade_date,
            trade_id,
        )

    # NumRequiredConfirmations is read just in time. If user changes autoConfirmSettings during requests it will
    # be reflected at next result parsing.
    def get_num_required_confirmations(self):
        return self.auto_confirm_settings.required_confirmations
