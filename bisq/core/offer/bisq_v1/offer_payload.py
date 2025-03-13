from dataclasses import dataclass, field
import json
from typing import Optional

from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.pub_key_ring import PubKeyRing
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.offer.offer_payload_base import OfferPayloadBase
import pb_pb2 as protobuf
from utils.data import raise_required
from utils.pb_helper import map_to_stable_extra_data, stable_extra_data_to_map
from utils.preconditions import check_argument



# OfferPayload has about 1.4 kb. We should look into options to make it smaller but will be hard to do it in a
# backward compatible way. Maybe a candidate when segwit activation is done as hardfork?
@dataclass
class OfferPayload(OfferPayloadBase):
    # Keys for extra map
    # Only set for fiat offers
    ACCOUNT_AGE_WITNESS_HASH = "accountAgeWitnessHash"
    REFERRAL_ID = "referralId"
    # Only used in payment method F2F
    F2F_CITY = "f2fCity"
    F2F_EXTRA_INFO = "f2fExtraInfo"
    CASH_BY_MAIL_EXTRA_INFO = "cashByMailExtraInfo"

    # Comma separated list of ordinal of a bisq.common.app.Capability. E.g. ordinal of
    # Capability.SIGNED_ACCOUNT_AGE_WITNESS is 11 and Capability.MEDIATION is 12 so if we want to signal that maker
    # of the offer supports both capabilities we add "11, 12" to capabilities.
    CAPABILITIES = "capabilities"
    # If maker is seller and has xmrAutoConf enabled it is set to "1" otherwise it is not set
    XMR_AUTO_CONF = "xmrAutoConf"
    XMR_AUTO_CONF_ENABLED_VALUE = "1"

    ##############################################################################################
    ## Instance fields
    ##############################################################################################

    # Distance form market price if percentage based price is used (usePercentageBasedPrice = true), otherwise 0.
    # E.g. 0.1 -> 10%. Can be negative as well. Depending on direction the marketPriceMargin is above or below the market price.
    # Positive values is always the usual case where you want a better price as the market.
    # E.g. Buy offer with market price 400.- leads to a 360.- price.
    # Sell offer with market price 400.- leads to a 440.- price.
    market_price_margin: float = field(default_factory=raise_required)
    # We use 2 type of prices: fixed price or price based on distance from market price
    use_market_based_price: bool = field(default_factory=raise_required)

    # Not used anymore, but we cannot set it Nullable or remove it to not break backward compatibility (diff. hash)
    arbitrator_node_addresses: list[NodeAddress] = field(default_factory=raise_required)
    # Not used anymore, but we cannot set it Nullable or remove it to not break backward compatibility (diff. hash)
    mediator_node_addresses: list[NodeAddress] = field(default_factory=raise_required)

    # Mutable property. Has to be set before offer is saved in P2P network as it changes the payload hash!
    offer_fee_payment_tx_id: Optional[str] = field(default=None)
    country_code: Optional[str] = field(default=None)
    accepted_country_codes: Optional[list[str]] = field(default=None)
    bank_id: Optional[str] = field(default=None)
    accepted_bank_ids: Optional[list[str]] = field(default=None)
    block_height_at_offer_creation: int = field(default_factory=raise_required)
    tx_fee: int = field(default_factory=raise_required)
    maker_fee: int = field(default_factory=raise_required)
    is_currency_for_maker_fee_btc: bool = field(default_factory=raise_required)
    buyer_security_deposit: int = field(default_factory=raise_required)
    seller_security_deposit: int = field(default_factory=raise_required)
    max_trade_limit: int = field(default_factory=raise_required)
    max_trade_period: int = field(default_factory=raise_required)

    # reserved for future use cases
    # Close offer when certain price is reached
    use_auto_close: bool = field(default_factory=raise_required)
    # If useReOpenAfterAutoClose=true we re-open a new offer with the remaining funds if the trade amount
    # was less than the offer's max. trade amount.
    use_re_open_after_auto_close: bool = field(default_factory=raise_required)
    # Used when useAutoClose is set for canceling the offer when lowerClosePrice is triggered
    lower_close_price: int = field(default_factory=raise_required)
    # Used when useAutoClose is set for canceling the offer when upperClosePrice is triggered
    upper_close_price: int = field(default_factory=raise_required)
    # Reserved for possible future use to support private trades where the taker needs to have an accessKey
    is_private_offer: bool = field(default_factory=raise_required)
    hash_of_challenge: Optional[str] = field(default=None)

    def getHash(self) -> bytes:
        if self.hash is None and self.offer_fee_payment_tx_id is not None:
            # A proto message can be created only after the offerFeePaymentTxId is
            # set to a non-null value;  now is the time to cache the payload hash.
            self.hash = get_sha256_hash(self.serialize_for_hash())
        return self.hash

    def to_proto_message(self) -> protobuf.StoragePayload:
        offer_payload = protobuf.OfferPayload(
            id=self.id,
            date=self.date,
            owner_node_address=self.owner_node_address.to_proto_message(),
            pub_key_ring=self.pub_key_ring.to_proto_message(),
            direction=OfferDirection.to_proto_message(self.direction),
            price=self.price,
            market_price_margin=self.market_price_margin,
            use_market_based_price=self.use_market_based_price,
            amount=self.amount,
            min_amount=self.min_amount,
            base_currency_code=self.base_currency_code,
            counter_currency_code=self.counter_currency_code,
            arbitrator_node_addresses=[
                node.to_proto_message() for node in self.arbitrator_node_addresses
            ],
            mediator_node_addresses=[
                node.to_proto_message() for node in self.mediator_node_addresses
            ],
            payment_method_id=self.payment_method_id,
            maker_payment_account_id=self.maker_payment_account_id,
            version_nr=self.version_nr,
            block_height_at_offer_creation=self.block_height_at_offer_creation,
            tx_fee=self.tx_fee,
            maker_fee=self.maker_fee,
            is_currency_for_maker_fee_btc=self.is_currency_for_maker_fee_btc,
            buyer_security_deposit=self.buyer_security_deposit,
            seller_security_deposit=self.seller_security_deposit,
            max_trade_limit=self.max_trade_limit,
            max_trade_period=self.max_trade_period,
            use_auto_close=self.use_auto_close,
            use_re_open_after_auto_close=self.use_re_open_after_auto_close,
            lower_close_price=self.lower_close_price,
            upper_close_price=self.upper_close_price,
            is_private_offer=self.is_private_offer,
            protocol_version=self.protocol_version,
        )
        assert (
            self.offer_fee_payment_tx_id is not None
        ), "OfferPayload is in invalid state: offerFeePaymentTxID is not set when adding to P2P network."
        offer_payload.offer_fee_payment_tx_id = self.offer_fee_payment_tx_id

        if self.country_code:
            offer_payload.country_code = self.country_code
        if self.bank_id:
            offer_payload.bank_id = self.bank_id
        if self.accepted_bank_ids:
            offer_payload.accepted_bank_ids.extend(self.accepted_bank_ids)
        if self.accepted_country_codes:
            offer_payload.accepted_country_codes.extend(self.accepted_country_codes)
        if self.hash_of_challenge:
            offer_payload.hash_of_challenge = self.hash_of_challenge
        if self.extra_data_map:
            offer_payload.extra_data.extend(map_to_stable_extra_data(self.extra_data_map))

        return protobuf.StoragePayload(offer_payload=offer_payload)

    @staticmethod
    def from_proto(proto: protobuf.OfferPayload) -> "OfferPayload":
        check_argument(
            proto.offer_fee_payment_tx_id,
            "OfferFeePaymentTxId must be set in PB.OfferPayload"
        )

        return OfferPayload(
            id=proto.id,
            date=proto.date,
            owner_node_address=NodeAddress.from_proto(proto.owner_node_address),
            pub_key_ring=PubKeyRing.from_proto(proto.pub_key_ring),
            direction=OfferDirection.from_proto(proto.direction),
            price=proto.price,
            market_price_margin=proto.market_price_margin,
            use_market_based_price=proto.use_market_based_price,
            amount=proto.amount,
            min_amount=proto.min_amount,
            base_currency_code=proto.base_currency_code,
            counter_currency_code=proto.counter_currency_code,
            arbitrator_node_addresses=[
                NodeAddress.from_proto(node) for node in proto.arbitrator_node_addresses
            ],
            mediator_node_addresses=[
                NodeAddress.from_proto(node) for node in proto.mediator_node_addresses
            ],
            payment_method_id=proto.payment_method_id,
            maker_payment_account_id=proto.maker_payment_account_id,
            offer_fee_payment_tx_id=proto.offer_fee_payment_tx_id,
            country_code=ProtoUtil.string_or_none_from_proto(proto.country_code),
            accepted_country_codes=(
                list(proto.accepted_country_codes)
                if proto.accepted_country_codes
                else None
            ),
            bank_id=ProtoUtil.string_or_none_from_proto(proto.bank_id),
            accepted_bank_ids=(
                list(proto.accepted_bank_ids) if proto.accepted_bank_ids else None
            ),
            version_nr=proto.version_nr,
            block_height_at_offer_creation=proto.block_height_at_offer_creation,
            tx_fee=proto.tx_fee,
            maker_fee=proto.maker_fee,
            is_currency_for_maker_fee_btc=proto.is_currency_for_maker_fee_btc,
            buyer_security_deposit=proto.buyer_security_deposit,
            seller_security_deposit=proto.seller_security_deposit,
            max_trade_limit=proto.max_trade_limit,
            max_trade_period=proto.max_trade_period,
            use_auto_close=proto.use_auto_close,
            use_re_open_after_auto_close=proto.use_re_open_after_auto_close,
            lower_close_price=proto.lower_close_price,
            upper_close_price=proto.upper_close_price,
            is_private_offer=proto.is_private_offer,
            hash_of_challenge=ProtoUtil.string_or_none_from_proto(
                proto.hash_of_challenge
            ),
            extra_data_map=stable_extra_data_to_map(proto.extra_data),
            protocol_version=proto.protocol_version,
        )

    def __str__(self) -> str:
        return (
            f"OfferPayload{{"
            f"\r\n     marketPriceMargin={self.market_price_margin},"
            f"\r\n     useMarketBasedPrice={self.use_market_based_price},"
            f"\r\n     arbitratorNodeAddresses={self.arbitrator_node_addresses},"
            f"\r\n     mediatorNodeAddresses={self.mediator_node_addresses},"
            f"\r\n     offerFeePaymentTxId='{self.offer_fee_payment_tx_id}',"
            f"\r\n     countryCode='{self.country_code}',"
            f"\r\n     acceptedCountryCodes={self.accepted_country_codes},"
            f"\r\n     bankId='{self.bank_id}',"
            f"\r\n     acceptedBankIds={self.accepted_bank_ids},"
            f"\r\n     blockHeightAtOfferCreation={self.block_height_at_offer_creation},"
            f"\r\n     txFee={self.tx_fee},"
            f"\r\n     makerFee={self.maker_fee},"
            f"\r\n     isCurrencyForMakerFeeBtc={self.is_currency_for_maker_fee_btc},"
            f"\r\n     buyerSecurityDeposit={self.buyer_security_deposit},"
            f"\r\n     sellerSecurityDeposit={self.seller_security_deposit},"
            f"\r\n     maxTradeLimit={self.max_trade_limit},"
            f"\r\n     maxTradePeriod={self.max_trade_period},"
            f"\r\n     useAutoClose={self.use_auto_close},"
            f"\r\n     useReOpenAfterAutoClose={self.use_re_open_after_auto_close},"
            f"\r\n     lowerClosePrice={self.lower_close_price},"
            f"\r\n     upperClosePrice={self.upper_close_price},"
            f"\r\n     isPrivateOffer={self.is_private_offer},"
            f"\r\n     hashOfChallenge='{self.hash_of_challenge}'"
            f"\r\n}} " + super().__str__()
        )

    # For backward compatibility we need to ensure same order for json fields as with 1.7.5. and earlier versions.
    # The json is used for the hash in the contract and change of order would cause a different hash and
    # therefore a failure during trade.
    def get_json_dict(self):
        """
        returns a dictionary representation of the OfferPayload, ready to be serialized to JSON
        """
        data = {
            "id": self.id,
            "date": self.date,
            "ownerNodeAddress": self.owner_node_address,
            "direction": self.direction,
            "price": self.price,
            "marketPriceMargin": self.market_price_margin,
            "useMarketBasedPrice": self.use_market_based_price,
            "amount": self.amount,
            "minAmount": self.min_amount,
            "baseCurrencyCode": self.base_currency_code,
            "counterCurrencyCode": self.counter_currency_code,
            "arbitratorNodeAddresses": self.arbitrator_node_addresses,
            "mediatorNodeAddresses": self.mediator_node_addresses,
            "paymentMethodId": self.payment_method_id,
            "makerPaymentAccountId": self.maker_payment_account_id,
            "offerFeePaymentTxId": self.offer_fee_payment_tx_id,
            "versionNr": self.version_nr,
            "blockHeightAtOfferCreation": self.block_height_at_offer_creation,
            "txFee": self.tx_fee,
            "makerFee": self.maker_fee,
            "isCurrencyForMakerFeeBtc": self.is_currency_for_maker_fee_btc,
            "buyerSecurityDeposit": self.buyer_security_deposit,
            "sellerSecurityDeposit": self.seller_security_deposit,
            "maxTradeLimit": self.max_trade_limit,
            "maxTradePeriod": self.max_trade_period,
            "useAutoClose": self.use_auto_close,
            "useReOpenAfterAutoClose": self.use_re_open_after_auto_close,
            "lowerClosePrice": self.lower_close_price,
            "upperClosePrice": self.upper_close_price,
            "isPrivateOffer": self.is_private_offer,
            "extraDataMap": self.extra_data_map,
            "protocolVersion": self.protocol_version,
        }
        return data

    def __hash__(self):
        return hash(self.get_hash())
