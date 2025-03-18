from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.coin.coin_util import CoinUtil
from utils.preconditions import check_argument


class CheckRestrictions(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            amount = self.trade.get_amount()

            buyer_security_deposit = self.trade.get_offer().buyer_security_deposit
            min_buyer_security_deposit = (
                Restrictions.get_min_buyer_security_deposit_as_coin()
            )
            check_argument(
                buyer_security_deposit.value >= min_buyer_security_deposit.value,
                "Buyer security deposit is less than the min. buyer security deposit (as coin)",
            )

            min_buyer_security_deposit_as_percent = (
                Restrictions.get_min_buyer_security_deposit_as_percent()
            )
            min_buyer_security_deposit_from_percentage = (
                CoinUtil.get_percent_of_amount_as_coin(
                    min_buyer_security_deposit_as_percent,
                    amount,
                )
            )
            check_argument(
                buyer_security_deposit.value
                >= min_buyer_security_deposit_from_percentage.value,
                "Buyer security deposit is less than the min. buyer security deposit (as percentage)",
            )

            seller_security_deposit = self.trade.get_offer().seller_security_deposit
            min_seller_security_deposit = (
                Restrictions.get_min_seller_security_deposit_as_coin()
            )
            check_argument(
                seller_security_deposit.value >= min_seller_security_deposit.value,
                "Seller security deposit is less than the min. seller security deposit (as coin)",
            )

            min_seller_security_deposit_as_percent = (
                Restrictions.get_min_seller_security_deposit_as_percent()
            )
            min_seller_security_deposit_from_percentage = (
                CoinUtil.get_percent_of_amount_as_coin(
                    min_seller_security_deposit_as_percent, amount
                )
            )
            check_argument(
                seller_security_deposit.value
                >= min_seller_security_deposit_from_percentage.value,
                "Seller security deposit is less than the min. seller security deposit (as percentage)",
            )

            self.complete()
        except Exception as e:
            self.failed(exc=e)
