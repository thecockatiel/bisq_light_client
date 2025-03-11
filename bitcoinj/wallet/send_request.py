from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from bitcoinj.base.coin import Coin
from bitcoinj.util.exchange_rate import ExchangeRate
from bitcoinj.wallet.missing_sigs_mode import MissingSigsMode


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.wallet.coin_selector import CoinSelector
    from bitcoinj.core.address import Address


@dataclass
class SendRequest:
    tx: "Transaction" = field(default=None)
    empty_wallet: bool = field(default=False)
    change_address: "Address" = field(default=None)
    fee: "Coin" = field(default=None)
    fee_per_kb: "Coin" = field(default=None)
    ensure_min_required_fee: bool  = field(default=False)
    sign_inputs: bool = field(default=True)
    password: str = field(default=None)
    coin_selector: "CoinSelector" = field(default=None)
    shuffle_outputs: bool = field(default=True)
    missing_sigs_mode: "MissingSigsMode" = field(default=MissingSigsMode.THROW)
    exchange_rate: "ExchangeRate" = field(default=None)
    memo: "str" = field(default=None)
    recipients_pay_fees: bool = field(default=False)
    completed: bool = field(default=False)

    @staticmethod
    def for_tx(tx: "Transaction"):
        return SendRequest(tx=tx)

