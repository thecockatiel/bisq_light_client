from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING
from bisq.common.taskrunner.task_model import TaskModel
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.monetary.volume import Volume
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.util.coin.coin_util import CoinUtil
from bisq.core.util.volume_util import VolumeUtil
from bitcoinj.base.coin import Coin
from bisq.core.offer.offer_util import OfferUtil
from utils.preconditions import check_argument

if TYPE_CHECKING:
    from bisq.core.account.witness.account_age_witness_service import (
        AccountAgeWitnessService,
    )
    from bisq.core.btc.model.address_entry import AddressEntry
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.offer import Offer
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.provider.price.price_feed_service import PriceFeedService


class TakeOfferModel(TaskModel):
    def __init__(
        self,
        account_age_witness_service: "AccountAgeWitnessService",
        btc_wallet_service: "BtcWalletService",
        fee_service: "FeeService",
        offer_util: "OfferUtil",
        price_feed_service: "PriceFeedService",
    ):
        self.logger = get_ctx_logger(__name__)
        # Immutable
        self.account_age_witness_service = account_age_witness_service
        self.btc_wallet_service = btc_wallet_service
        self.fee_service = fee_service
        self.offer_util = offer_util
        self.price_feed_service = price_feed_service

        # Mutable
        self.address_entry: "AddressEntry" = None
        self.amount: Coin = None
        self.is_currency_for_taker_fee_btc: bool = False
        self.offer: "Offer" = None
        self.payment_account: "PaymentAccount" = None
        self.security_deposit: Coin = None
        self.use_savings_wallet: bool = False

        # Use an average of a typical trade fee tx with 1 input, deposit tx and payout tx.
        self.fee_tx_vsize: int = 192  # (175+233+169)/3
        self.tx_fee_per_vbyte_from_fee_service: Coin = None
        self.tx_fee_from_fee_service: Coin = None
        self.taker_fee: Coin = None
        self.total_to_pay_as_coin: Coin = None
        self.missing_coin: Coin = Coin.ZERO()
        self.total_available_balance: Coin = None
        self.balance: Coin = None
        self.is_btc_wallet_funded: bool = False
        self.volume: Volume = None

    def init_model(
        self,
        offer: "Offer",
        payment_account: "PaymentAccount",
        intended_trade_amount: int,
        use_savings_wallet: bool,
    ):
        self._clear_model()
        self.offer = offer
        self.payment_account = payment_account
        self.address_entry = self.btc_wallet_service.get_or_create_address_entry(
            offer.id, AddressEntryContext.OFFER_FUNDING
        )
        self._validate_model_inputs()

        self.use_savings_wallet = use_savings_wallet
        self.amount = Coin.value_of(
            min(intended_trade_amount, self._get_max_trade_limit())
        )
        self.security_deposit = (
            offer.buyer_security_deposit
            if offer.direction == OfferDirection.SELL
            else offer.seller_security_deposit
        )
        self.is_currency_for_taker_fee_btc = (
            self.offer_util.is_currency_for_taker_fee_btc(self.amount)
        )
        self.taker_fee = self.offer_util.get_taker_fee(
            self.is_currency_for_taker_fee_btc, self.amount
        )

        self._calculate_tx_fees()
        self._calculate_volume()
        self._calculate_total_to_pay()
        offer.reset_state()

        self.price_feed_service.currency_code = offer.currency_code

    def on_complete(self):
        pass

    def _calculate_tx_fees(self):
        # Taker pays 3 times the tx fee (taker fee, deposit, payout) because the mining
        # fee might be different when maker created the offer and reserved his funds.
        # Taker creates at least taker fee and deposit tx at nearly the same moment.
        # Just the payout will be later and still could lead to issues if the required
        # fee changed a lot in the meantime. using RBF and/or multiple batch-signed
        # payout tx with different fees might be an option but RBF is not supported yet
        # in BitcoinJ and batched txs would add more complexity to the trade protocol.

        # A typical trade fee tx has about 175 vbytes (if one input). The trade txs has
        # about 169-263 vbytes. We use 192 as a average value.

        # Fee calculations:
        # Trade fee tx: 175 vbytes (1 input)
        # Deposit tx: 233 vbytes (1 MS output+ OP_RETURN) - 263 vbytes
        #     (1 MS output + OP_RETURN + change in case of smaller trade amount)
        # Payout tx: 169 vbytes
        # Disputed payout tx: 139 vbytes
        self.tx_fee_per_vbyte_from_fee_service = self.fee_service.get_tx_fee_per_vbyte()
        self.tx_fee_from_fee_service = self.offer_util.get_tx_fee_by_vsize(
            self.tx_fee_per_vbyte_from_fee_service, self.fee_tx_vsize
        )
        self.logger.info(
            f"{self.fee_service.__class__.__name__} txFeePerVbyte = {self.tx_fee_per_vbyte_from_fee_service}"
        )

    def _calculate_total_to_pay(self):
        # Taker pays 2 times the tx fee because the mining fee might be different when
        # maker created the offer and reserved his funds, so that would not work well
        # with dynamic fees. The mining fee for the takeOfferFee tx is deducted from
        # the createOfferFee and not visible to the trader.
        fee_and_sec_deposit = self.get_total_tx_fee().add(self.security_deposit)
        if self.is_currency_for_taker_fee_btc:
            fee_and_sec_deposit = fee_and_sec_deposit.add(self.taker_fee)

        self.total_to_pay_as_coin = (
            fee_and_sec_deposit.add(self.amount)
            if self.offer.is_buy_offer
            else fee_and_sec_deposit
        )

        self._update_balance()

    def _calculate_volume(self):
        trade_price = self.offer.get_price()
        assert trade_price is not None
        volume_by_amount = trade_price.get_volume_by_amount(self.amount)

        if self.offer.payment_method.id == PaymentMethod.HAL_CASH_ID:
            volume_by_amount = VolumeUtil.get_adjusted_volume_for_hal_cash(
                volume_by_amount
            )
        elif self.offer.is_fiat_offer:
            volume_by_amount = VolumeUtil.get_rounded_fiat_volume(volume_by_amount)

        self.volume = volume_by_amount

        self._update_balance()

    def _update_balance(self):
        trade_wallet_balance = self.btc_wallet_service.get_balance_for_address(
            self.address_entry.get_address()
        )
        if self.use_savings_wallet:
            saving_wallet_balance = self.btc_wallet_service.get_saving_wallet_balance()
            self.total_available_balance = saving_wallet_balance.add(
                trade_wallet_balance
            )
            if self.total_to_pay_as_coin is not None:
                self.balance = CoinUtil.min_coin(
                    self.total_to_pay_as_coin, self.total_available_balance
                )
        else:
            self.balance = trade_wallet_balance

        self.missing_coin = self.offer_util.get_balance_shortage(
            self.total_to_pay_as_coin, self.balance
        )
        self.is_btc_wallet_funded = self.offer_util.is_balance_sufficient(
            self.total_to_pay_as_coin, self.balance
        )

    def _get_max_trade_limit(self) -> int:
        return self.account_age_witness_service.get_my_trade_limit(
            self.payment_account,
            self.offer.currency_code,
            self.offer.mirrored_direction,
        )

    def get_total_tx_fee(self) -> Coin:
        total_tx_fees = self.tx_fee_from_fee_service.add(
            self._get_tx_fee_for_deposit_tx()
        ).add(self._get_tx_fee_for_payout_tx())
        if self.is_currency_for_taker_fee_btc:
            return total_tx_fees
        else:
            return total_tx_fees.subtract(self.taker_fee)

    def get_funds_needed_for_trade(self) -> Coin:
        # If taking a buy offer, taker needs to reserve the offer.amount too.
        return (
            self.security_deposit.add(self._get_tx_fee_for_deposit_tx())
            .add(self._get_tx_fee_for_payout_tx())
            .add(self.amount if self.offer.is_buy_offer else Coin.ZERO())
        )

    def _get_tx_fee_for_deposit_tx(self) -> Coin:
        # JAVA TODO fix with new trade protocol!
        # Unfortunately we cannot change that to the correct fees as it would break
        # backward compatibility. We still might find a way with offer version or app
        # version checks so lets keep that commented out code as that shows how it
        # should be.
        return self.tx_fee_from_fee_service

    def _get_tx_fee_for_payout_tx(self) -> Coin:
        # JAVA TODO fix with new trade protocol!
        # Unfortunately we cannot change that to the correct fees as it would break
        # backward compatibility. We still might find a way with offer version or app
        # version checks so lets keep that commented out code as that shows how it
        # should be.
        return self.tx_fee_from_fee_service

    def _validate_model_inputs(self):
        assert self.offer is not None, "offer must not be null"
        assert self.offer.amount is not None, "offer amount must not be null"
        check_argument(self.offer.amount.value > 0, "offer amount must not be zero")
        assert self.offer.get_price() is not None, "offer price must not be null"
        assert self.payment_account is not None, "payment account must not be null"
        assert self.address_entry is not None, "address entry must not be null"

    def _clear_model(self):
        self.address_entry = None
        self.amount = None
        self.balance = None
        self.is_btc_wallet_funded = False
        self.is_currency_for_taker_fee_btc = False
        self.missing_coin = Coin.ZERO()
        self.offer = None
        self.payment_account = None
        self.security_deposit = None
        self.taker_fee = None
        self.total_available_balance = None
        self.total_to_pay_as_coin = None
        self.tx_fee_from_fee_service = None
        self.tx_fee_per_vbyte_from_fee_service = None
        self.use_savings_wallet = True
        self.volume = None

    def __str__(self):
        return (
            f"TakeOfferModel{{\n"
            f"  offer.id={self.offer.id if self.offer else 'None'}\n"
            f"  offer.state={self.offer.state if self.offer else 'None'}\n"
            f", paymentAccount.id={self.payment_account.id if self.payment_account else 'None'}\n"
            f", paymentAccount.method.id={self.payment_account.payment_method.id if self.payment_account and self.payment_account.payment_method else 'None'}\n"
            f", useSavingsWallet={self.use_savings_wallet}\n"
            f", addressEntry={self.address_entry}\n"
            f", amount={self.amount}\n"
            f", securityDeposit={self.security_deposit}\n"
            f", feeTxVsize={self.fee_tx_vsize}\n"
            f", txFeePerVbyteFromFeeService={self.tx_fee_per_vbyte_from_fee_service}\n"
            f", txFeeFromFeeService={self.tx_fee_from_fee_service}\n"
            f", takerFee={self.taker_fee}\n"
            f", totalToPayAsCoin={self.total_to_pay_as_coin}\n"
            f", missingCoin={self.missing_coin}\n"
            f", totalAvailableBalance={self.total_available_balance}\n"
            f", balance={self.balance}\n"
            f", volume={self.volume}\n"
            f", fundsNeededForTrade={self.get_funds_needed_for_trade()}\n"
            f", isCurrencyForTakerFeeBtc={self.is_currency_for_taker_fee_btc}\n"
            f", isBtcWalletFunded={self.is_btc_wallet_funded}\n"
            f"}}"
        )
