from datetime import datetime, timedelta, timezone
from enum import Enum, IntEnum
import logging
import random
from typing import TYPE_CHECKING, Optional, Union
from bisq.common.crypto.encryption import ECPrivkey, Encryption
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.common.crypto.sig import Sig, dsa
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.common.util.math_utils import MathUtils
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.account.sign.signed_witness import SignedWitness
from bisq.core.account.witness.account_age_witness_utils import AccountAgeWitnessUtils
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.locale.res import Res
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from bisq.core.offer.offer import Offer
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.offer.offer_restrictions import OfferRestrictions
from bisq.core.payment.payload.payment_method import PaymentMethod
from bisq.core.support.dispute.arbitration.trader_data_item import TraderDataItem
from bisq.core.support.dispute.dispute import Dispute
from bisq.core.support.dispute.dispute_result_winner import DisputeResultWinner
from bitcoinj.base.coin import Coin
from utils.concurrency import ThreadSafeDict
from bisq.core.account.witness.account_age_witness import AccountAgeWitness
from utils.time import get_time_ms
from utils.hackyway import create_fake_copy_of_instance

if TYPE_CHECKING:
    from bisq.core.user.preferences import Preferences
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.user.user import User
    from bisq.core.filter.filter_manager import FilterManager
    from utils.clock import Clock
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.persistence.append_only_data_store_service import (
        AppendOnlyDataStoreService,
    )
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.account.sign.signed_witness_service import SignedWitnessService
    from bisq.core.account.witness.account_age_witness_storage_service import AccountAgeWitnessStorageService

logger = get_logger(__name__)


class AccountAgeWitnessService:
    RELEASE = datetime(2017, 11, 11, tzinfo=timezone.utc)
    SAFE_ACCOUNT_AGE_DATE_MS = int(datetime(2019, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
    #
    THIRTY_DAYS_MS = int(timedelta(days=30).total_seconds() * 1000)
    SIXTY_DAYS_MS = int(timedelta(days=60).total_seconds() * 1000)

    class AccountAge(IntEnum):
        UNVERIFIED = 0
        LESS_ONE_MONTH = 1
        ONE_TO_TWO_MONTHS = 2
        TWO_MONTHS_OR_MORE = 3

    class SignState(Enum):
        UNSIGNED = Res.get("offerbook.timeSinceSigning.notSigned")
        ARBITRATOR = Res.get("offerbook.timeSinceSigning.info.arbitrator")
        PEER_INITIAL = Res.get("offerbook.timeSinceSigning.info.peer")
        PEER_LIMIT_LIFTED = Res.get("offerbook.timeSinceSigning.info.peerLimitLifted")
        PEER_SIGNER = Res.get("offerbook.timeSinceSigning.info.signer")
        BANNED = Res.get("offerbook.timeSinceSigning.info.banned")

        def __init__(self, display_string: str, hash_str="", days_until_limit_lifted=0):
            self.display_string = display_string
            self.hash_str = hash_str
            self.days_until_limit_lifted = days_until_limit_lifted

        def __new__(cls, *args, **kwds):
            value = len(cls.__members__)
            obj = object.__new__(cls)
            obj._value_ = value
            return obj

        def add_hash(self, hash_str: str):
            return create_fake_copy_of_instance(self, {"hash_str": hash_str})

        def set_days_until_limit_lifted(self, days):
            return create_fake_copy_of_instance(self, {"days_until_limit_lifted": days})

        def get_display_string(self):
            if self.hash_str:  # Only showing in DEBUG mode
                return f"{self.display_string} {self.hash_str}"
            return self.display_string.format(self.days_until_limit_lifted)

        def is_limit_lifted(self):
            return self == self.PEER_LIMIT_LIFTED or self == self.PEER_SIGNER or self == self.ARBITRATOR

    def __init__(
        self,
        key_ring: "KeyRing",
        p2p_service: "P2PService",
        user: "User",
        signed_witness_service: "SignedWitnessService",
        # charge_back_risk: ChargeBackRisk, # Unnecessary class
        account_age_witness_storage_service: "AccountAgeWitnessStorageService",
        append_only_data_store_service: "AppendOnlyDataStoreService",
        clock: "Clock",
        preferences: "Preferences",
        filter_manager: "FilterManager",
    ):
        self.key_ring = key_ring
        self.p2p_service = p2p_service
        self.user = user
        self.signed_witness_service = signed_witness_service
        self.account_age_witness_storage_service = account_age_witness_storage_service
        self.clock = clock
        self.preferences = preferences
        self.filter_manager = filter_manager

        self.account_age_witness_map: dict[StorageByteArray, "AccountAgeWitness"] = {}
        
        # The accountAgeWitnessMap is very large (70k items) and access is a bit expensive. We usually only access less
        # than 100 items, those who have offers online. So we use a cache for a fast lookup and only if
        # not found there we use the accountAgeWitnessMap and put then the new item into our cache.
        self.account_age_witness_cache  = ThreadSafeDict[StorageByteArray, "AccountAgeWitness"]()

        self.account_age_witness_utils = AccountAgeWitnessUtils(
            self, signed_witness_service, key_ring
        )

        # We need to add that early (before on_all_services_initialized) as it will be used at startup.
        append_only_data_store_service.add_service(account_age_witness_storage_service)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Lifecycle
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def on_all_services_initialized(self):
        self.p2p_service.get_p2p_data_storage().add_append_only_data_store_listener(
            lambda payload: self.add_to_map(payload) if isinstance(payload, AccountAgeWitness) else None
        )

        # At startup the P2PDataStorage initializes earlier, otherwise we get the listener called
        for entry in self.account_age_witness_storage_service.get_map_of_all_data().values():
            if isinstance(entry, AccountAgeWitness):
                self.add_to_map(entry)

        if self.p2p_service.is_bootstrapped:
            self._on_bootstrapped()
        else:
            outer = self
            class Listener(BootstrapListener):
                def on_data_received(self):
                    outer._on_bootstrapped()
            self.p2p_service.add_p2p_service_listener(Listener())

    def _on_bootstrapped(self):
        self._republish_all_fiat_accounts()
        self.sign_and_publish_same_name_accounts()

    #  At startup we re-publish the witness data of all fiat accounts to ensure we got our data well distributed.
    def _republish_all_fiat_accounts(self):
        if self.user.payment_accounts is not None:
            for account in self.user.payment_accounts:
                if account.payment_method.is_fiat():
                    my_witness = self.get_my_witness(account.payment_account_payload)
                    # We only publish if the date of our witness is inside the date tolerance.
                    # It would be rejected otherwise from the peers.
                    if my_witness.is_date_in_tolerance(self.clock):
                        # We delay with a random interval of 20-60 sec to ensure to be better connected and don't
                        # stress the P2P network with publishing all at once at startup time.
                        delay_in_sec = 20 + random.randint(0, 40)
                        UserThread.run_after(
                            lambda: self.p2p_service.add_persistable_network_payload(my_witness, True),
                            timedelta(seconds=delay_in_sec),
                        )

    def add_to_map(self, account_age_witness: "AccountAgeWitness") -> None:
        storage_bytes = account_age_witness.get_hash_as_byte_array()
        if storage_bytes not in self.account_age_witness_map:
            self.account_age_witness_map[storage_bytes] = account_age_witness

    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Generic
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def publish_my_account_age_witness(self, payment_account_payload: "PaymentAccountPayload") -> None:
        account_age_witness = self.get_my_witness(payment_account_payload)
        storage_bytes = account_age_witness.get_hash_as_byte_array()

        # We use first our fast lookup cache. If its in account_age_witness_cache it is also in account_age_witness_map
        # and we do not publish.
        if storage_bytes in self.account_age_witness_cache:
            return

        if storage_bytes not in self.account_age_witness_map:
            self.p2p_service.add_persistable_network_payload(account_age_witness, False)

    def get_peer_account_age_witness_hash(self, trade: "Trade") -> bytes:
        witness = self.find_trade_peer_witness(trade)
        return witness.get_hash() if witness else None

    def get_account_input_data_with_salt(self, payment_account_payload: "PaymentAccountPayload") -> bytes:
        return payment_account_payload.get_age_witness_input_data() + payment_account_payload.salt

    def get_new_witness(self, payment_account_payload: "PaymentAccountPayload", pub_key_ring: "PubKeyRing") -> "AccountAgeWitness":
        account_input_data_with_salt = self.get_account_input_data_with_salt(payment_account_payload)
        hash_bytes = get_sha256_ripemd160_hash(
            account_input_data_with_salt + pub_key_ring.signature_pub_key_bytes
        )
        return AccountAgeWitness(hash_bytes, get_time_ms())

    def find_witness(self, payment_account_payload: "PaymentAccountPayload", pub_key_ring: "PubKeyRing") -> Optional["AccountAgeWitness"]:
        if payment_account_payload is None or pub_key_ring is None:
            return None

        account_input_data_with_salt = self.get_account_input_data_with_salt(payment_account_payload)
        hash_bytes = get_sha256_ripemd160_hash(
            account_input_data_with_salt + pub_key_ring.signature_pub_key_bytes
        )

        return self.get_witness_by_hash(hash_bytes)

    def find_witness_from_offer(self, offer: "Offer") -> Optional["AccountAgeWitness"]:
        account_age_witness_hash = offer.account_age_witness_hash_as_hex
        return (
            self.get_witness_by_hash_as_hex(account_age_witness_hash) 
            if account_age_witness_hash is not None 
            else None
        )

    def find_trade_peer_witness(self, trade: "Trade") -> Optional["AccountAgeWitness"]:
        trading_peer = trade._process_model.trade_peer
        if (trading_peer is None 
            or trading_peer.payment_account_payload is None 
            or trading_peer.pub_key_ring is None):
            return None
            
        return self.find_witness(
            trading_peer.payment_account_payload,
            trading_peer.pub_key_ring
        )

    def get_witness_by_hash(self, hash_bytes: bytes) -> Optional["AccountAgeWitness"]:
        hash_as_byte_array = StorageByteArray(hash_bytes)

        # First we look up in our fast lookup cache
        if hash_as_byte_array in self.account_age_witness_cache:
            return self.account_age_witness_cache[hash_as_byte_array]

        if hash_as_byte_array in self.account_age_witness_map:
            account_age_witness = self.account_age_witness_map[hash_as_byte_array]
            
            # We add it to our fast lookup cache
            self.account_age_witness_cache[hash_as_byte_array] = account_age_witness
            
            return account_age_witness

        return None

    def get_witness_by_hash_as_hex(self, hash_as_hex: str) -> Optional["AccountAgeWitness"]:
        return self.get_witness_by_hash(bytes.fromhex(hash_as_hex))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Witness age
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_account_age(self, account_age_witness: "AccountAgeWitness", now: datetime = None) -> int:
        if now is None:
            now = datetime.now()
        now_ms = int(now.timestamp() * 1000)
        logger.debug(f"get_account_age now={now_ms}, account_age_witness.date={account_age_witness.date}")
        return now_ms - account_age_witness.date

    # Return -1 if no witness found
    def get_account_age_for_payment_account(
        self, 
        payment_account_payload: "PaymentAccountPayload", 
        pub_key_ring: "PubKeyRing"
    ) -> int:
        witness = self.find_witness(payment_account_payload, pub_key_ring)
        return self.get_account_age(witness) if witness else -1

    def get_account_age_for_offer(self, offer: "Offer") -> int:
        witness = self.find_witness_from_offer(offer)
        return self.get_account_age(witness) if witness else -1

    def get_account_age_for_trade(self, trade: "Trade") -> int:
        witness = self.find_trade_peer_witness(trade)
        return self.get_account_age(witness) if witness else -1

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Signed age
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    # Return -1 if not signed
    def get_witness_sign_age(self, account_age_witness: "AccountAgeWitness", now: datetime = None) -> int:
        if now is None:
            now = datetime.now()
        dates = self.signed_witness_service.get_verified_witness_date_list(account_age_witness)
        if not dates:
            return -1
        return int(now.timestamp() * 1000) - dates[0]

    def get_witness_sign_date(self, account_age_witness: "AccountAgeWitness") -> int:
        dates = self.signed_witness_service.get_verified_witness_date_list(account_age_witness)
        return dates[0] if dates else -1

    def get_witness_sign_age_for_offer(self, offer: "Offer", now: datetime = None) -> int:
        if now is None:
            now = datetime.now()
        witness = self.find_witness_from_offer(offer)
        return self.get_witness_sign_age(witness, now) if witness else -1

    def get_witness_sign_age_for_trade(self, trade: "Trade", now: datetime = None) -> int:
        if now is None:
            now = datetime.now()
        witness = self.find_trade_peer_witness(trade)
        return self.get_witness_sign_age(witness, now) if witness else -1

    def get_peers_account_age_category(self, peers_account_age: int) -> "AccountAge":
        return self._get_account_age_category(peers_account_age)

    def _get_account_age_category(self, account_age: int) -> "AccountAge":
        if account_age < 0:
            return self.AccountAge.UNVERIFIED
        elif account_age < self.THIRTY_DAYS_MS:
            return self.AccountAge.LESS_ONE_MONTH
        elif account_age < self.SIXTY_DAYS_MS:
            return self.AccountAge.ONE_TO_TWO_MONTHS
        else:
            return self.AccountAge.TWO_MONTHS_OR_MORE

    # Get trade limit based on a time schedule
    # Buying of BTC with a payment method that has chargeback risk will use a low trade limit schedule
    # All selling and all other fiat payment methods use the normal trade limit schedule
    # Non fiat always has max limit
    # Account types that can get signed will use time since signing, other methods use time since account age creation
    # when measuring account age
    def get_trade_limit(
        self,
        max_trade_limit: "Coin",
        currency_code: str,
        account_age_witness: "AccountAgeWitness",
        account_age_category: "AccountAge",
        direction: "OfferDirection",
        payment_method: "PaymentMethod"
    ) -> int:
        # If crypto currency or no chargeback risk or selling, return max limit
        if (is_crypto_currency(currency_code) or
            not PaymentMethod.has_chargeback_risk(payment_method, currency_code) or
            direction == OfferDirection.SELL):
            return max_trade_limit.value

        limit = OfferRestrictions.TOLERATED_SMALL_TRADE_AMOUNT.value
        factor = self._signed_buy_factor(account_age_category)
        if factor > 0:
            limit = MathUtils.round_double_to_long(max_trade_limit.value * factor)

        logger.debug(
            f"limit={Coin.value_of(limit).to_friendly_string()}, "
            f"factor={factor}, "
            f"accountAgeWitnessHash={bytes_as_hex_string(account_age_witness.get_hash())}"
        )
        return limit

    def _signed_buy_factor(self, account_age_category: "AccountAge") -> float:
        if account_age_category == self.AccountAge.TWO_MONTHS_OR_MORE:
            return 1.0
        elif account_age_category == self.AccountAge.ONE_TO_TWO_MONTHS:
            return 0.5
        else:  # LESS_ONE_MONTH, UNVERIFIED or other
            return 0.0

    def _normal_factor(self) -> float:
        return 1.0

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Trade limit exceptions
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_immature(self, account_age_witness: "AccountAgeWitness") -> bool:
        return account_age_witness.date > self.SAFE_ACCOUNT_AGE_DATE_MS

    def my_has_trade_limit_exception(self, my_payment_account: "PaymentAccount") -> bool:
        return self.has_trade_limit_exception(
            self.get_my_witness(my_payment_account.payment_account_payload)
        )

    def has_trade_limit_exception(self, account_age_witness: "AccountAgeWitness") -> bool:
        """
        There are no trade limits on accounts that:
        - are mature
        - were signed by an arbitrator
        """
        return (not self.is_immature(account_age_witness) or 
                self.signed_witness_service.is_signed_by_arbitrator(account_age_witness))

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // My witness
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_my_witness(self, payment_account_payload: "PaymentAccountPayload") -> "AccountAgeWitness":
        witness = self.find_witness(payment_account_payload, self.key_ring.pub_key_ring)
        return witness if witness else self.get_new_witness(payment_account_payload, self.key_ring.pub_key_ring)

    def get_my_witness_hash(self, payment_account_payload: "PaymentAccountPayload") -> bytes:
        return self.get_my_witness(payment_account_payload).get_hash()

    def get_my_witness_hash_as_hex(self, payment_account_payload: "PaymentAccountPayload") -> str:
        return self.get_my_witness_hash(payment_account_payload).hex()

    def get_my_account_age(self, payment_account_payload: "PaymentAccountPayload") -> int:
        return self.get_account_age(
            self.get_my_witness(payment_account_payload), 
            datetime.now()
        )

    def get_my_trade_limit(self, payment_account: "PaymentAccount", currency_code: str, direction: "OfferDirection") -> int:
        if payment_account is None:
            return 0

        account_age_witness = self.get_my_witness(payment_account.payment_account_payload)
        # maxTradeLimit is the smaller of the payment method and the user preference setting  (GH proposal #398)
        max_trade_limit = Coin.value_of(min(
            payment_account.payment_method.get_max_trade_limit_as_coin(currency_code).value,
            self.preferences.get_user_defined_trade_limit()
        ))
        
        if self.has_trade_limit_exception(account_age_witness):
            return max_trade_limit.value

        account_sign_age = self.get_witness_sign_age(account_age_witness, datetime.now())
        account_age_category = self._get_account_age_category(account_sign_age)

        return self.get_trade_limit(
            max_trade_limit,
            currency_code,
            account_age_witness,
            account_age_category,
            direction,
            payment_account.payment_method
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Verification
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def verify_account_age_witness(
        self,
        trade: "Trade",
        peers_payment_account_payload: "PaymentAccountPayload",
        peers_current_date: datetime,
        peers_pub_key_ring: "PubKeyRing",
        nonce: bytes,
        signature: bytes,
        error_message_handler: "ErrorMessageHandler"
    ) -> bool:
        # Find witness or create a dummy one if not found
        peers_witness = self.find_witness(peers_payment_account_payload, peers_pub_key_ring)
        # If we don't find a stored witness data we create a new dummy object which makes is easier to reuse the
        # below validation methods. This peersWitness object is not used beside for validation. Some of the
        # validation calls are pointless in the case we create a new Witness ourselves but the verifyPeersTradeLimit
        # need still be called, so we leave also the rest for sake of simplicity.
        if not peers_witness:
            peers_witness = self.get_new_witness(peers_payment_account_payload, peers_pub_key_ring)
            logger.warning("We did not find the peers witness data. That is expected with peers using an older version.")

        # Check if date in witness is not older than the release date of that feature
        if not self.is_date_after_release_date(peers_witness.date, self.RELEASE, error_message_handler):
            return False

        # Check if peer current date is in tolerance range
        if not self.verify_peers_current_date(peers_current_date, error_message_handler):
            return False

        
        peers_account_input_data_with_salt = (
            peers_payment_account_payload.get_age_witness_input_data() + 
            peers_payment_account_payload.salt
        )
        hash_bytes = get_sha256_ripemd160_hash(
            peers_account_input_data_with_salt + 
            peers_pub_key_ring.signature_pub_key_bytes
        )

        # Check if the hash in the witness data matches the hash derived from the data provided by the peer
        peers_witness_hash = peers_witness.get_hash()
        if not self.verify_witness_hash(peers_witness_hash, hash_bytes, error_message_handler):
            return False

        # Check if the peers trade limit is not less than the trade amount
        if not self.verify_peers_trade_limit(
            trade.get_offer(), 
            trade.amount_property.value, 
            peers_witness, 
            peers_current_date,
            error_message_handler
        ):
            logger.error(f"verify_peers_trade_limit failed: peers_payment_account_payload {peers_payment_account_payload}")
            return False

        # Check if the signature is correct
        return self.verify_signature(
            peers_pub_key_ring.signature_pub_key,
            nonce,
            signature,
            error_message_handler
        )

    def verify_peers_trade_amount(
        self,
        offer: "Offer",
        trade_amount: "Coin",
        error_message_handler: "ErrorMessageHandler"
    ) -> bool:
        assert offer is not None, "Offer cannot be None"

        # In case we don't find the witness we check if the trade amount is above the
        # TOLERATED_SMALL_TRADE_AMOUNT (0.01 BTC) and only in that case return false.
        witness = self.find_witness_from_offer(offer)
        if witness:
            return self.verify_peers_trade_limit(
                offer,
                trade_amount,
                witness,
                datetime.now(),
                error_message_handler
            )
        return self._is_tolerated_small_amount(trade_amount)

    def _is_tolerated_small_amount(self, trade_amount: "Coin") -> bool:
        return trade_amount.value <= OfferRestrictions.TOLERATED_SMALL_TRADE_AMOUNT.value

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // (JAVA): Package scope verification subroutines
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_date_after_release_date(
        self,
        witness_date_as_long: int, 
        age_witness_release_date: datetime,
        error_message_handler: "ErrorMessageHandler"
    ) -> bool:
        # Release date minus 1 day as tolerance for not synced clocks
        release_date_with_tolerance = age_witness_release_date - timedelta(days=1)
        witness_date = datetime.fromtimestamp(witness_date_as_long / 1000, tz=timezone.utc)
        result = witness_date > release_date_with_tolerance
        
        if not result:
            msg = (
                f"Witness date is set earlier than release date of ageWitness feature. "
                f"ageWitnessReleaseDate={age_witness_release_date}, witnessDate={witness_date}"
            )
            logger.warning(msg)
            error_message_handler(msg)
            
        return result

    def verify_peers_current_date(
        self,
        peers_current_date: datetime,
        error_message_handler: "ErrorMessageHandler"
    ) -> bool:
        # Convert milliseconds difference to absolute days
        time_diff = peers_current_date - datetime.now()
        result = time_diff <= timedelta(days=1)
        
        if not result:
            msg = (
                f"Peers current date is further than 1 day off to our current date. "
                f"PeersCurrentDate={peers_current_date}; myCurrentDate={datetime.now()}"
            )
            logger.warning(msg)
            error_message_handler(msg)
            
        return result

    def verify_witness_hash(
        self,
        witness_hash: bytes,
        hash_bytes: bytes,
        error_message_handler: "ErrorMessageHandler"
    ) -> bool:
        result = witness_hash == hash_bytes
        if not result:
            msg = (
                f"witnessHash is not matching peers hash. "
                f"witnessHash={bytes_as_hex_string(witness_hash)}, hash={bytes_as_hex_string(hash_bytes)}"
            )
            logger.warning(msg)
            error_message_handler(msg)
        return result

    def verify_peers_trade_limit(
        self,
        offer: "Offer",
        trade_amount: "Coin",
        peers_witness: "AccountAgeWitness",
        peers_current_date: datetime,
        error_message_handler: "ErrorMessageHandler"
    ) -> bool:
        assert offer is not None, "Offer cannot be None"
            
        currency_code = offer.currency_code
        default_max_trade_limit = offer.payment_method.get_max_trade_limit_as_coin(currency_code)
        peers_current_trade_limit = default_max_trade_limit.value
        
        if not self.has_trade_limit_exception(peers_witness):
            account_sign_age = self.get_witness_sign_age(peers_witness, peers_current_date)
            account_age_category = self.get_peers_account_age_category(account_sign_age)
            direction = (offer.mirrored_direction 
                       if offer.is_my_offer(self.key_ring) 
                       else offer.direction)
            peers_current_trade_limit = self.get_trade_limit(
                default_max_trade_limit,
                currency_code,
                peers_witness,
                account_age_category,
                direction,
                offer.payment_method
            )

        # Makers current trade limit cannot be smaller than that in the offer
        result = trade_amount.value <= peers_current_trade_limit
        if not result:
            msg = (
                f"The peers trade limit is less than the traded amount.\n"
                f"tradeAmount={trade_amount.to_friendly_string()}\n"
                f"Peers trade limit={Coin.value_of(peers_current_trade_limit).to_friendly_string()}\n"
                f"Offer ID={offer.short_id}\n"
                f"PaymentMethod={offer.payment_method.id}\n"
                f"CurrencyCode={offer.currency_code}"
            )
            logger.warning(msg)
            error_message_handler(msg)
            
        return result

    def verify_signature(
        self,
        peers_public_key: "dsa.DSAPublicKey",
        nonce: bytes,
        signature: bytes,
        error_message_handler: "ErrorMessageHandler"
    ) -> bool:
        try:
            result = Sig.verify(peers_public_key, nonce, signature)
        except Exception as e:
            logger.warning(e)
            result = False

        if not result:
            msg = (
                f"Signature of nonce is not correct. "
                f"peersPublicKey={peers_public_key}, "
                f"nonce(hex)={bytes_as_hex_string(nonce)}, "
                f"signature={bytes_as_hex_string(signature)}"
            )
            logger.warning(msg)
            error_message_handler(msg)

        return result

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Witness signing
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def arbitrator_sign_account_age_witness(
        self,
        trade_amount: "Coin",
        account_age_witness: "AccountAgeWitness",
        key: "ECPrivkey",
        peers_pub_key: "dsa.DSAPublicKey"
    ) -> None:
        self.signed_witness_service.sign_and_publish_account_age_witness(
            account_age_witness=account_age_witness, 
            ec_key=key,
            trade_amount=trade_amount, 
            peers_pub_key=peers_pub_key
        )

    def arbitrator_sign_orphan_witness(
        self,
        account_age_witness: "AccountAgeWitness",
        ec_key: "ECPrivkey",
        time: int
    ) -> str:
        # JAVA TODO Is not found signedWitness considered an error case?
        #   Previous code version was throwing an exception in case no signedWitness was found...

        # signAndPublishAccountAgeWitness returns an empty string in success case and error otherwise
        signed_witness_set = self.signed_witness_service.get_signed_witness_set(account_age_witness)
        for signed_witness in signed_witness_set:
            witness_owner_pub_key = signed_witness.witness_owner_pub_key
            return self.signed_witness_service.sign_and_publish_account_age_witness(
                account_age_witness=account_age_witness,
                ec_key=ec_key,
                peers_pub_key=witness_owner_pub_key,
                time=time
            )
        return "No signedWitness found"

    def arbitrator_sign_orphan_pub_key(
        self,
        key: "ECPrivkey",
        peers_pub_key: bytes,
        child_sign_time: int
    ) -> str:
        return self.signed_witness_service.sign_trader_pub_key(
            key,
            peers_pub_key,
            child_sign_time
        )

    def arbitrator_sign_account_age_witness(
        self,
        account_age_witness: "AccountAgeWitness",
        ec_key: "ECPrivkey",
        traders_pub_key: bytes,
        time: int
    ) -> None:
        self.signed_witness_service.sign_and_publish_account_age_witness(
            account_age_witness=account_age_witness,
            ec_key=ec_key,
            peers_pub_key=traders_pub_key,
            time=time
        )

    def trader_sign_and_publish_peers_account_age_witness(self, trade: "Trade") -> Optional["SignedWitness"]:
        try:
            peers_witness = self.find_trade_peer_witness(trade)
            trade_amount = trade.amount_property.value
            
            assert trade._process_model.trade_peer.pub_key_ring is not None, "Peer must have a keyring"
                
            peers_pub_key = trade._process_model.trade_peer.pub_key_ring.signature_pub_key
            
            assert peers_witness is not None, f"Not able to find peers witness, unable to sign for trade {trade}"
            assert trade_amount is not None, "Trade amount must not be None"
            assert peers_pub_key is not None, "Peers pub key must not be None"

            return self.signed_witness_service.sign_and_publish_account_age_witness(
                account_age_witness=peers_witness,
                trade_amount=trade_amount,
                peers_pub_key=peers_pub_key,
            )
            
        except Exception as e:
            logger.warning(f"Trader failed to sign witness, exception {e}")
            
        return None

    def publish_own_signed_witness(self, signed_witness: "SignedWitness") -> bool:
        return self.signed_witness_service.publish_own_signed_witness(signed_witness)

    # Arbitrator signing
    def get_trader_payment_accounts(
        self,
        safe_date: int,
        payment_method: "PaymentMethod",
        disputes: list["Dispute"]
    ) -> list["TraderDataItem"]:
        filtered_disputes = [
            dispute for dispute in disputes
            if (dispute.contract.payment_method_id == payment_method.id
                and self.is_not_filtered(dispute)
                and self.has_chargeback_risk(dispute)
                and self.is_buyer_winner(dispute))
        ]
        
        trader_data_items: list["TraderDataItem"] = []
        for dispute in filtered_disputes:
            items = self.get_trader_data(dispute)
            if items:
                trader_data_items.extend(items)
        
        # First we create a set to make it unique, then create a list from it
        return list({
            item for item in trader_data_items
                if (item is not None
                    and not self.signed_witness_service.is_signed_account_age_witness(item.account_age_witness)
                    and item.account_age_witness.date < safe_date)
        })
        
    def is_not_filtered(self, dispute: "Dispute") -> bool:
        contract = dispute.contract
        is_filtered = (
            self.filter_manager.is_node_address_banned(contract.buyer_node_address) or
            self.filter_manager.is_node_address_banned(contract.seller_node_address) or
            self.filter_manager.is_currency_banned(contract.offer_payload.currency_code) or
            self.filter_manager.is_payment_method_banned(
                PaymentMethod.get_payment_method(contract.payment_method_id)) or
            self.filter_manager.are_peers_payment_account_data_banned(contract.buyer_payment_account_payload) or
            self.filter_manager.are_peers_payment_account_data_banned(
                contract.seller_payment_account_payload) or
            self.filter_manager.is_witness_signer_pub_key_banned(
                contract.buyer_pub_key_ring.signature_pub_key_bytes.hex()) or
            self.filter_manager.is_witness_signer_pub_key_banned(
                contract.seller_pub_key_ring.signature_pub_key_bytes.hex())
        )
        return not is_filtered

    def has_chargeback_risk(self, dispute: "Dispute") -> bool:
        return PaymentMethod.has_chargeback_risk(
            dispute.contract.payment_method_id,
            dispute.contract.offer_payload.currency_code
        )

    def is_buyer_winner(self, dispute: "Dispute") -> bool:
        if not dispute.is_closed or not dispute.dispute_result_property.value:
            return False
        return dispute.dispute_result_property.value.winner == DisputeResultWinner.BUYER

    def get_trader_data(self, dispute: "Dispute") -> list["TraderDataItem"]:
        trade_amount = dispute.contract.get_trade_amount()
        
        buyer_pub_key_ring = dispute.contract.buyer_pub_key_ring
        seller_pub_key_ring = dispute.contract.seller_pub_key_ring
        
        buyer_payment_account_payload = dispute.contract.buyer_payment_account_payload
        seller_payment_account_payload = dispute.contract.seller_payment_account_payload
        
        buyer_data = None
        seller_data = None
        
        buyer_witness = self.find_witness(buyer_payment_account_payload, buyer_pub_key_ring)
        if buyer_witness:
            buyer_data = TraderDataItem(
                buyer_payment_account_payload,
                buyer_witness,
                trade_amount,
                buyer_pub_key_ring.signature_pub_key
            )
            
        seller_witness = self.find_witness(seller_payment_account_payload, seller_pub_key_ring)
        if seller_witness:
            seller_data = TraderDataItem(
                seller_payment_account_payload,
                seller_witness,
                trade_amount,
                seller_pub_key_ring.signature_pub_key
            )
            
        return [buyer_data, seller_data]

    def has_signed_witness(self, offer: "Offer") -> bool:
        witness = self.find_witness_from_offer(offer)
        return self.signed_witness_service.is_signed_account_age_witness(witness) if witness else False

    def peer_has_signed_witness(self, trade: "Trade") -> bool:
        witness = self.find_trade_peer_witness(trade)
        return self.signed_witness_service.is_signed_account_age_witness(witness) if witness else False

    def account_is_signer(self, account_age_witness: "AccountAgeWitness") -> bool:
        return self.signed_witness_service.is_signer_account_age_witness(account_age_witness)

    def trade_amount_is_sufficient(self, trade_amount: "Coin") -> bool:
        return self.signed_witness_service.is_sufficient_trade_amount_for_signing(trade_amount)

    def get_sign_state(self, offer_or_trade_or_witness: Union["Offer", "Trade", "AccountAgeWitness"]) -> "SignState":
        if isinstance(offer_or_trade_or_witness, Offer):
            witness = self.find_witness_from_offer(offer_or_trade_or_witness)
            return self._get_sign_state(witness) if witness else self.SignState.UNSIGNED
        elif isinstance(offer_or_trade_or_witness, Trade):
            witness = self.find_trade_peer_witness(offer_or_trade_or_witness)
            return self._get_sign_state(witness) if witness else self.SignState.UNSIGNED
        else: 
            # AccountAgeWitness
            return self._get_sign_state(offer_or_trade_or_witness)

    def _get_sign_state(self, account_age_witness: "AccountAgeWitness") -> "SignState":
        assert isinstance(account_age_witness, AccountAgeWitness), f"expected AccountAgeWitness but got {type(account_age_witness)}"
        # Add hash to sign state info when running in debug mode
        hash_str = ""
        if logger.isEnabledFor(logging.DEBUG):
            hash_str = (
                f"{bytes_as_hex_string(account_age_witness.get_hash())}\n" +
                self.signed_witness_service.owner_pub_key_as_string(account_age_witness)
            )

        if self.signed_witness_service.is_filtered_witness(account_age_witness):
            return self.SignState.BANNED.add_hash(hash_str)

        if self.signed_witness_service.is_signed_by_arbitrator(account_age_witness):
            return self.SignState.ARBITRATOR.add_hash(hash_str)

        account_sign_age = self.get_witness_sign_age(account_age_witness, datetime.now())
        account_age_category = self._get_account_age_category(account_sign_age)

        if account_age_category in (self.AccountAge.TWO_MONTHS_OR_MORE, self.AccountAge.ONE_TO_TWO_MONTHS):
            return self.SignState.PEER_SIGNER.add_hash(hash_str)
        elif account_age_category == self.AccountAge.LESS_ONE_MONTH:
            days_until_limit_lifted = 30 - (account_sign_age // (24 * 60 * 60 * 1000))  # Convert ms to days
            return (self.SignState.PEER_INITIAL.add_hash(hash_str)
                .set_days_until_limit_lifted(days_until_limit_lifted))
        else:
            # UNVERIFIED or default
            return self.SignState.UNSIGNED.add_hash(hash_str)

    def get_orphan_signed_witnesses(self) -> set["AccountAgeWitness"]:
        root_signed_witness_set = self.signed_witness_service.get_root_signed_witness_set(False)
        orphan_witnesses = set["AccountAgeWitness"]()
        
        for signed_witness in root_signed_witness_set:
            witness = self.get_witness_by_hash(signed_witness.account_age_witness_hash)
            if witness is not None:
                orphan_witnesses.add(witness)
                
        return orphan_witnesses

    def sign_and_publish_same_name_accounts(self) -> None:
        if not self.user.payment_accounts:
            return

        # Collect accounts that have ownerId to sign unsigned accounts with the same ownderId
        signer_accounts = {
            account for account in self.user.payment_accounts
            if (account.owner_id is not None and 
                self.account_is_signer(self.get_my_witness(account.payment_account_payload)))
        }
        unsigned_accounts = {
            account for account in self.user.payment_accounts
            if (account.owner_id is not None and
                not self.signed_witness_service.is_signed_account_age_witness(
                        self.get_my_witness(account.payment_account_payload)
                    )
                )
        }

        # For each signer, sign matching unsigned accounts
        for signer in signer_accounts:
            for unsigned in unsigned_accounts:
                if signer.owner_id == unsigned.owner_id:
                    try:
                        self.signed_witness_service.self_sign_and_publish_account_age_witness(
                            self.get_my_witness(unsigned.payment_account_payload)
                        )
                    except Exception as e:
                        logger.warning(f"Self signing failed, exception {e}")

    def get_unsigned_signer_pub_keys(self) -> set["SignedWitness"]:
        return self.signed_witness_service.get_unsigned_signer_pub_keys()

    def is_sign_witness_trade(self, trade: "Trade") -> bool:
        try:
            assert trade is not None, "trade must not be None"
            assert trade.get_offer() is not None, "offer must not be None"
            contract = trade.contract
            assert contract is not None, "contract must not be None"
                
            seller_payment_account_payload = contract.seller_payment_account_payload
            assert seller_payment_account_payload is not None, "seller_payment_account_payload must not be None"
                
            my_witness = self.get_my_witness(seller_payment_account_payload)
            self.account_age_witness_utils.witness_debug_log(trade, my_witness)
            
            return (self.account_is_signer(my_witness) and
                    not self.peer_has_signed_witness(trade) and
                    self.trade_amount_is_sufficient(trade.amount_property.value))
                    
        except Exception as e:
            logger.exception(e, exc_info=e)
            return False

    def get_sign_info_from_account(self, payment_account: "PaymentAccount") -> str:
        pub_key = self.key_ring.signature_key_pair.public_key
        witness = self.get_my_witness(payment_account.payment_account_payload)
        return f"{bytes_as_hex_string(witness.get_hash())}, {bytes_as_hex_string(Encryption.get_public_key_bytes(pub_key))}"

    def get_sign_info_from_string(self, sign_info: str) -> Optional[tuple["AccountAgeWitness", bytes]]:
        parts = sign_info.split(',')
        if len(parts) != 2:
            return None
            
        try:
            account_age_witness_hash = bytes.fromhex(parts[0])
            pub_key_hash = bytes.fromhex(parts[1])
            
            account_age_witness = self.get_witness_by_hash(account_age_witness_hash)
            if account_age_witness:
                return (account_age_witness, pub_key_hash)
        except Exception:
            pass
            
        return None

    def is_filtered_witness(self, account_age_witness: "AccountAgeWitness") -> bool:
        return self.signed_witness_service.is_filtered_witness(account_age_witness)
    
