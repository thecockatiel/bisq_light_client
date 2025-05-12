from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Tuple

from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.locale.res import Res
from bisq.core.monetary.price import Price
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.shared.preferences.preferences_const import USE_SYMMETRIC_SECURITY_DEPOSIT
from bisq.core.util.coin.coin_util import CoinUtil
from bitcoinj.base.coin import Coin
from bisq.core.offer.bisq_v1.offer_payload import OfferPayload
from bisq.core.offer.offer import Offer
from bisq.core.payment.payment_account_util import PaymentAccountUtil
from bisq.common.version import Version
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.btc.tx_fee_estimation_service import TxFeeEstimationService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.offer_util import OfferUtil
    from bisq.core.user.user import User
    from bisq.core.provider.price.price_feed_service import PriceFeedService

class CreateOfferService:
    def __init__(self, 
                 offer_util: 'OfferUtil',
                 tx_fee_estimation_service: 'TxFeeEstimationService',
                 price_feed_service: 'PriceFeedService',
                 p2p_service: 'P2PService',
                 pub_key_ring: 'PubKeyRing',
                 user: 'User',
                 btc_wallet_service: 'BtcWalletService'):
        self.logger = get_ctx_logger(__name__)
        self.offer_util = offer_util
        self.tx_fee_estimation_service = tx_fee_estimation_service
        self.price_feed_service = price_feed_service
        self.p2p_service = p2p_service
        self.pub_key_ring = pub_key_ring
        self.user = user
        self.btc_wallet_service = btc_wallet_service

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_and_get_offer(self,
                           offer_id: str,
                           direction: OfferDirection,
                           currency_code: str,
                           amount: Coin,
                           min_amount: Coin,
                           price: Price,
                           tx_fee: Coin,
                           use_market_based_price: bool,
                           market_price_margin: float,
                           buyer_security_deposit: float,
                           payment_account: 'PaymentAccount') -> 'Offer':
        
        self.logger.info(f"create and get offer with offerId={offer_id}, "
                     f"currencyCode={currency_code}, "
                     f"direction={direction}, "
                     f"price={price.value if price else 0}, "
                     f"useMarketBasedPrice={use_market_based_price}, "
                     f"marketPriceMargin={market_price_margin}, "
                     f"amount={amount.value if amount else 0}, "
                     f"minAmount={min_amount.value if min_amount else 0}, "
                     f"buyerSecurityDeposit={buyer_security_deposit}")

        creation_time = get_time_ms()
        maker_address = self.p2p_service.address
        use_market_based_price_value = (use_market_based_price and 
                                      self.is_market_price_available(currency_code) and
                                      not payment_account.has_payment_method_with_id(PaymentMethod.HAL_CASH_ID))

        price_as_long = price.value if price and not use_market_based_price_value else 0
        market_price_margin_param = market_price_margin if use_market_based_price_value else 0.0
        amount_as_long = amount.value if amount else 0
        min_amount_as_long = min_amount.value if min_amount else 0
        it_is_crypto_currency = is_crypto_currency(currency_code)
        base_currency_code = currency_code if it_is_crypto_currency else Res.base_currency_code
        counter_currency_code = Res.base_currency_code if it_is_crypto_currency else currency_code
        
        arbitrator_addresses = self.user.accepted_arbitrator_addresses.copy() if self.user.accepted_arbitrator_addresses else []
        mediator_addresses = self.user.accepted_mediator_addresses.copy() if self.user.accepted_mediator_addresses else []
        
        country_code = PaymentAccountUtil.get_country_code(payment_account)
        accepted_country_codes = PaymentAccountUtil.get_accepted_country_codes(payment_account)
        bank_id = PaymentAccountUtil.get_bank_id(payment_account)
        accepted_banks = PaymentAccountUtil.get_accepted_banks(payment_account)
        
        seller_security_deposit = self.get_seller_security_deposit_as_float(buyer_security_deposit)
        tx_fee_estimation = self.get_estimated_fee_and_tx_vsize(amount, direction, 
                                                              buyer_security_deposit, 
                                                              seller_security_deposit)
        tx_fee_to_use = tx_fee if tx_fee.is_positive() else tx_fee_estimation[0]
        
        maker_fee = self.offer_util.get_maker_fee(amount)
        is_maker_fee_btc = self.offer_util.is_currency_for_maker_fee_btc(amount)
        buyer_security_deposit_coin = self.get_buyer_security_deposit(amount, buyer_security_deposit)
        seller_security_deposit_coin = self.get_seller_security_deposit(amount, seller_security_deposit)
        max_trade_limit = self.offer_util.get_max_trade_limit(payment_account, currency_code, direction)
        max_trade_period = payment_account.get_max_trade_period()

        # reserved for future use cases
        # Use None values if not set
        is_private_offer = False
        use_auto_close = False
        use_reopen_after_auto_close = False
        lower_close_price = 0
        upper_close_price = 0
        hash_of_challenge = None
        extra_data_map = self.offer_util.get_extra_data_map(payment_account, 
                                                           currency_code,
                                                           direction)

        self.offer_util.validate_offer_data(
            buyer_security_deposit,
            payment_account,
            currency_code,
            maker_fee,
            accepted_banks)

        offer_payload = OfferPayload(
            id=offer_id,
            date=creation_time,
            owner_node_address=maker_address,
            pub_key_ring=self.pub_key_ring,
            direction=direction,
            price=price_as_long,
            market_price_margin=market_price_margin_param,
            use_market_based_price=use_market_based_price_value,
            amount=amount_as_long,
            min_amount=min_amount_as_long,
            base_currency_code=base_currency_code,
            counter_currency_code=counter_currency_code,
            arbitrator_node_addresses=arbitrator_addresses,
            mediator_node_addresses=mediator_addresses,
            payment_method_id=payment_account.payment_method.id,
            maker_payment_account_id=payment_account.id,
            offer_fee_payment_tx_id=None,
            country_code=country_code,
            accepted_country_codes=accepted_country_codes,
            bank_id=bank_id,
            accepted_bank_ids=accepted_banks,
            version_nr=Version.VERSION,
            block_height_at_offer_creation=self.btc_wallet_service.last_block_seen_height,
            tx_fee=tx_fee_to_use.value,
            maker_fee=maker_fee.value,
            is_currency_for_maker_fee_btc=is_maker_fee_btc,
            buyer_security_deposit=buyer_security_deposit_coin.value,
            seller_security_deposit=seller_security_deposit_coin.value,
            max_trade_limit=max_trade_limit,
            max_trade_period=max_trade_period,
            use_auto_close=use_auto_close,
            use_re_open_after_auto_close=use_reopen_after_auto_close,
            upper_close_price=upper_close_price,
            lower_close_price=lower_close_price,
            is_private_offer=is_private_offer,
            hash_of_challenge=hash_of_challenge,
            extra_data_map=extra_data_map,
            protocol_version=Version.TRADE_PROTOCOL_VERSION,
        )
        
        offer = Offer(offer_payload)
        offer.price_feed_service = self.price_feed_service
        return offer

    def get_estimated_fee_and_tx_vsize(self, amount: Coin, 
                                      direction: OfferDirection,
                                      buyer_security_deposit: float,
                                      seller_security_deposit: float) -> Tuple[Coin, int]:
        reserved_funds = self.get_reserved_funds_for_offer(direction,
                                                         amount,
                                                         buyer_security_deposit,
                                                         seller_security_deposit)
        return self.tx_fee_estimation_service.get_estimated_fee_and_tx_vsize_for_maker(
            reserved_funds,
            self.offer_util.get_maker_fee(amount))

    def get_reserved_funds_for_offer(self, direction: OfferDirection,
                                   amount: Coin,
                                   buyer_security_deposit: float,
                                   seller_security_deposit: float) -> Coin:
        reserved_funds = self.get_security_deposit(direction,
                                                 amount,
                                                 buyer_security_deposit,
                                                 seller_security_deposit)
        if not self.offer_util.is_buy_offer(direction):
            reserved_funds = reserved_funds.add(amount)
        return reserved_funds

    def get_security_deposit(self, direction: OfferDirection,
                           amount: Coin,
                           buyer_security_deposit: float,
                           seller_security_deposit: float) -> Coin:
        return (self.get_buyer_security_deposit(amount, buyer_security_deposit)
                if self.offer_util.is_buy_offer(direction)
                else self.get_seller_security_deposit(amount, seller_security_deposit))

    def get_seller_security_deposit_as_float(self, buyer_security_deposit: float) -> float:
        return (buyer_security_deposit if USE_SYMMETRIC_SECURITY_DEPOSIT 
                else Restrictions.get_seller_security_deposit_as_percent())

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_market_price_available(self, currency_code: str) -> bool:
        market_price = self.price_feed_service.get_market_price(currency_code)
        return market_price is not None and market_price.is_externally_provided_price

    def get_buyer_security_deposit(self, amount: Coin, buyer_security_deposit: float) -> Coin:
        percent_of_amount = CoinUtil.get_percent_of_amount_as_coin(buyer_security_deposit, amount)
        return self._get_bounded_buyer_security_deposit(percent_of_amount)

    def get_seller_security_deposit(self, amount: Coin, seller_security_deposit: float) -> Coin:
        amount_as_coin = Coin.ZERO() if amount is None else amount
        percent_of_amount = CoinUtil.get_percent_of_amount_as_coin(seller_security_deposit, amount_as_coin)
        return self._get_bounded_seller_security_deposit(percent_of_amount)

    def _get_bounded_buyer_security_deposit(self, value: Coin) -> Coin:
        # We need to ensure that for small amount values we don't get a too low BTC amount. We limit it with using the
        # MinBuyerSecurityDepositAsCoin from Restrictions.
        return Coin.value_of(max(
            Restrictions.get_min_buyer_security_deposit_as_coin().value,
            value.value
        ))

    def _get_bounded_seller_security_deposit(self, value: Coin) -> Coin:
        # We need to ensure that for small amount values we don't get a too low BTC amount. We limit it with using the
        # MinBuyerSecurityDepositAsCoin from Restrictions.
        return Coin.value_of(max(
            Restrictions.get_min_seller_security_deposit_as_coin().value,
            value.value
        ))


