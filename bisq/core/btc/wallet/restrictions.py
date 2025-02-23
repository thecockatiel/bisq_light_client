from datetime import datetime, timezone
from bisq.common.config.config import Config
from bitcoinj.base.coin import Coin


class Restrictions:
    MIN_SECURITY_DEPOSIT_CHANGE_ACTIVATION_DATE = datetime(
        2025, 2, 17, tzinfo=timezone.utc
    )

    MIN_TRADE_AMOUNT: "Coin" = None
    MIN_BUYER_SECURITY_DEPOSIT: "Coin" = None
    # For the seller we use a fixed one as there is no way the seller can cancel the trade
    # To make it editable would just increase complexity.
    MIN_SELLER_SECURITY_DEPOSIT: "Coin" = None
    # At mediation we require a min. payout to the losing party to keep incentive for the trader to accept the
    # mediated payout. For Refund agent cases we do not have that restriction.
    MIN_REFUND_AT_MEDIATED_DISPUTE: "Coin" = None

    min_non_dust_output: "Coin" = None

    @staticmethod
    def get_min_non_dust_output():
        if Restrictions.min_non_dust_output is None:
            Restrictions.min_non_dust_output = (
                Config.BASE_CURRENCY_NETWORK_VALUE.parameters.get_min_non_dust_output()
            )
        return Restrictions.min_non_dust_output

    @staticmethod
    def is_above_dust(amount: "Coin"):
        return amount >= Restrictions.get_min_non_dust_output()

    @staticmethod
    def is_dust(amount: "Coin"):
        return not Restrictions.is_above_dust(amount)

    @staticmethod
    def get_min_trade_amount():
        if Restrictions.MIN_TRADE_AMOUNT is None:
            Restrictions.MIN_TRADE_AMOUNT = Coin.value_of(
                10000
            )  # 0.7 USD @ 7000 USD/BTC
        return Restrictions.MIN_TRADE_AMOUNT

    @staticmethod
    def get_default_buyer_security_deposit_as_percent():
        return 0.15  # 15% of trade amount

    @staticmethod
    def get_min_buyer_security_deposit_as_percent():
        return 0.15  # 15% of trade amount

    @staticmethod
    def get_max_buyer_security_deposit_as_percent():
        return 0.5  # 50% of trade amount. For a 1 BTC trade it is about 3500 USD @ 7000 USD/BTC

    # We use MIN_BUYER_SECURITY_DEPOSIT as well as lower bound in case of small trade amounts.
    # So 0.0005 BTC is the min. buyer security deposit even with amount of 0.0001 BTC and 0.05% percentage value.
    @staticmethod
    def get_min_buyer_security_deposit_as_coin():
        now = datetime.now(timezone.utc)
        if now > Restrictions.MIN_SECURITY_DEPOSIT_CHANGE_ACTIVATION_DATE:
            if (
                Restrictions.MIN_BUYER_SECURITY_DEPOSIT is None
                or Restrictions.MIN_BUYER_SECURITY_DEPOSIT == Coin.parse_coin("0.001")
            ):
                Restrictions.MIN_BUYER_SECURITY_DEPOSIT = Coin.parse_coin(
                    "0.0003"
                )  # 0.0003 BTC is 27 USD @ 90000 USD/BTC
        else:
            if Restrictions.MIN_BUYER_SECURITY_DEPOSIT is None:
                Restrictions.MIN_BUYER_SECURITY_DEPOSIT = Coin.parse_coin(
                    "0.001"
                )  # 0.001 BTC is 60 USD @ 60000 USD/BTC
        return Restrictions.MIN_BUYER_SECURITY_DEPOSIT

    @staticmethod
    def get_seller_security_deposit_as_percent():
        return 0.15  # 15% of trade amount

    @staticmethod
    def get_min_seller_security_deposit_as_percent():
        return 0.15  # 15% of trade amount

    @staticmethod
    def get_min_seller_security_deposit_as_coin():
        now = datetime.now(timezone.utc)
        if now > Restrictions.MIN_SECURITY_DEPOSIT_CHANGE_ACTIVATION_DATE:
            if (
                Restrictions.MIN_SELLER_SECURITY_DEPOSIT is None
                or Restrictions.MIN_SELLER_SECURITY_DEPOSIT == Coin.parse_coin("0.001")
            ):
                Restrictions.MIN_SELLER_SECURITY_DEPOSIT = Coin.parse_coin(
                    "0.0003"
                )  # 0.0003 BTC is 27 USD @ 90000 USD/BTC
        else:
            if Restrictions.MIN_SELLER_SECURITY_DEPOSIT is None:
                Restrictions.MIN_SELLER_SECURITY_DEPOSIT = Coin.parse_coin(
                    "0.001"
                )  # 0.001 BTC is 60 USD @ 60000 USD/BTC
        return Restrictions.MIN_SELLER_SECURITY_DEPOSIT

    # This value must be lower than MIN_BUYER_SECURITY_DEPOSIT and SELLER_SECURITY_DEPOSIT
    @staticmethod
    def get_min_refund_at_mediated_dispute(trade_amount: "Coin"):
        if Restrictions.MIN_REFUND_AT_MEDIATED_DISPUTE is None:
            Restrictions.MIN_REFUND_AT_MEDIATED_DISPUTE = Coin.parse_coin(
                "0.0005"
            )  # 0.0005 BTC is 30 USD @ 60000 USD/BTC
        five_percent_of_trade_amount = trade_amount.divide(20)
        if five_percent_of_trade_amount.is_less_than(
            Restrictions.MIN_REFUND_AT_MEDIATED_DISPUTE
        ):
            return Restrictions.MIN_REFUND_AT_MEDIATED_DISPUTE
        return five_percent_of_trade_amount

    @staticmethod
    def get_lock_time(is_asset):
        # 10 days for altcoins, 20 days for other payment methods
        return 144 * 10 if is_asset else 144 * 20
