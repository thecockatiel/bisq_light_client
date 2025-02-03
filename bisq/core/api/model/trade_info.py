from typing import TYPE_CHECKING, Optional, Union
from bisq.common.payload import Payload
from bisq.core.api.model.bsq_swap_trade_info import BsqSwapTradeInfo
from bisq.core.api.model.contract_info import ContractInfo
from bisq.core.api.model.offer_info import OfferInfo
from bisq.core.api.model.payment_account_payload_info import PaymentAccountPayloadInfo
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.trade.model.bisq_v1.trade import Trade
from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade
from bisq.core.util.price_util import PriceUtil
from bisq.core.util.volume_util import VolumeUtil
import grpc_pb2

if TYPE_CHECKING:
    from bisq.core.trade.model.trade_model import TradeModel


class TradeInfo(Payload):

    # The client cannot see Trade or its fromProto method.  We use the
    # lighter weight TradeInfo proto wrapper instead, containing just enough fields to
    # view and interact with trades.

    def __init__(
        self,
        offer: Optional["OfferInfo"] = None,
        trade_id: Optional[str] = None,
        short_id: Optional[str] = None,
        date: Optional[int] = None,
        role: Optional[str] = None,
        is_currency_for_taker_fee_btc: Optional[bool] = None,
        tx_fee_as_long: Optional[int] = None,
        taker_fee_as_long: Optional[int] = None,
        taker_fee_tx_id: Optional[str] = None,
        deposit_tx_id: Optional[str] = None,
        payout_tx_id: Optional[str] = None,
        trade_amount_as_long: Optional[int] = None,
        trade_price: Optional[str] = None,
        trade_volume: Optional[str] = None,
        trading_peer_node_address: Optional[str] = None,
        state: Optional[str] = None,
        phase: Optional[str] = None,
        trade_period_state: Optional[str] = None,
        is_deposit_published: Optional[bool] = None,
        is_deposit_confirmed: Optional[bool] = None,
        is_payment_started_message_sent: Optional[bool] = None,
        is_payment_received_message_sent: Optional[bool] = None,
        is_payout_published: Optional[bool] = None,
        is_completed: Optional[bool] = None,
        contract_as_json: Optional[str] = None,
        contract: Optional["ContractInfo"] = None,
        auto_conf_tx_id: Optional[str] = None,
        auto_conf_tx_key: Optional[str] = None,
        has_failed: Optional[bool] = None,
        error_message: Optional[str] = None,
        closing_status: Optional[str] = None,
        bsq_swap_trade_info: Optional["BsqSwapTradeInfo"] = None,
    ):
        # Bisq v1 trade protocol fields (some are in common with the BSQ Swap protocol).
        self.offer = offer
        self.trade_id = trade_id
        self.short_id = short_id
        self.date = date
        self.role = role
        self.is_currency_for_taker_fee_btc = is_currency_for_taker_fee_btc
        self.tx_fee_as_long = tx_fee_as_long
        self.taker_fee_as_long = taker_fee_as_long
        self.taker_fee_tx_id = taker_fee_tx_id
        self.deposit_tx_id = deposit_tx_id
        self.payout_tx_id = payout_tx_id
        self.trade_amount_as_long = trade_amount_as_long
        self.trade_price = trade_price
        self.trade_volume = trade_volume
        self.trading_peer_node_address = trading_peer_node_address
        self.state = state
        self.phase = phase
        self.trade_period_state = trade_period_state
        self.is_deposit_published = is_deposit_published
        self.is_deposit_confirmed = is_deposit_confirmed
        self.is_payment_started_message_sent = is_payment_started_message_sent
        self.is_payment_received_message_sent = is_payment_received_message_sent
        self.is_payout_published = is_payout_published
        self.is_completed = is_completed
        self.contract_as_json = contract_as_json
        self.contract = contract
        self.auto_conf_tx_id = auto_conf_tx_id
        self.auto_conf_tx_key = auto_conf_tx_key
        self.has_failed = has_failed
        self.error_message = error_message
        # Optional BSQ swap trade protocol details (post v1).
        self.bsq_swap_trade_info = bsq_swap_trade_info
        self.closing_status = closing_status

    @staticmethod
    def to_new_trade_info(trade: Union["TradeModel"], role: str = None) -> "TradeInfo":
        # Always called by the taker, is_my_offer=False.
        return TradeInfo.to_trade_info(trade, role, False, "Pending", 0)

    @staticmethod
    def _to_offer_info(trade_model: "TradeModel", is_my_offer: bool):
        if is_my_offer:
            return OfferInfo.to_my_inactive_offer_info(trade_model.get_offer())
        else:
            return OfferInfo.to_offer_info(trade_model.get_offer())

    @staticmethod
    def _to_peer_node_address(trade_model: "TradeModel") -> str:
        if trade_model.trading_peer_node_address is not None:
            return trade_model.trading_peer_node_address.get_full_address()
        else:
            return ""

    @staticmethod
    def _to_rounded_volume(trade_model: "TradeModel") -> str:
        volume = trade_model.get_volume()
        if volume is not None:
            return VolumeUtil.format_volume(volume)
        else:
            return ""

    @staticmethod
    def _to_precise_trade_price(trade_model: "TradeModel") -> str:
        price = trade_model.get_price()
        assert price is not None
        return PriceUtil.reformat_market_price(
            price.to_plain_string(), trade_model.get_offer().currency_code
        )

    @staticmethod
    def to_trade_info(
        trade: Union["BsqSwapTrade", "Trade"],
        role: Optional[str],
        is_my_offer: bool,
        closing_status: Optional[str],
        num_confirmations: int = 0,
    ) -> "TradeInfo":
        if isinstance(trade, BsqSwapTrade):
            offer_info = TradeInfo._to_offer_info(trade, is_my_offer)
            # A BSQ Swap miner tx fee is paid in full by the BTC seller (buying BSQ).
            # The BTC buyer's payout = tradeamount minus his share of miner fee.
            is_btc_seller = (
                is_my_offer and trade.get_offer().direction == OfferDirection.SELL
            ) or (not is_my_offer and trade.get_offer().direction == OfferDirection.BUY)
            tx_fee_in_btc = trade.get_tx_fee().value if is_btc_seller else 0
            # A BSQ Swap trade fee is paid in full by the BTC buyer (selling BSQ).
            # The transferred BSQ (payout) is reduced by the peer's trade fee.
            taker_fee_in_bsq = (
                trade.taker_fee_as_long
                if not is_my_offer
                and trade.get_offer().direction == OfferDirection.SELL
                else 0
            )
            return TradeInfo(
                offer=offer_info,
                trade_id=trade.get_id(),
                short_id=trade.get_short_id(),
                date=int(trade.get_date().timestamp() * 1000),
                role=role if role is not None else "",
                is_currency_for_taker_fee_btc=False,  # BSQ Swap fee is always paid in BSQ.
                tx_fee_as_long=tx_fee_in_btc,
                taker_fee_as_long=taker_fee_in_bsq,
                # N/A for bsq-swaps: takerFeeTxId, depositTxId, payoutTxId
                trade_amount_as_long=trade.get_amount_as_long(),
                trade_price=TradeInfo._to_precise_trade_price(trade),
                trade_volume=TradeInfo._to_rounded_volume(trade),
                trading_peer_node_address=TradeInfo._to_peer_node_address(trade),
                state=trade.get_trade_state().name,
                phase=trade.get_trade_phase().name,
                # N/A for bsq-swaps: tradePeriodState, isDepositPublished, isDepositConfirmed
                # N/A for bsq-swaps: isPaymentStartedMessageSent, isPaymentReceivedMessageSent, isPayoutPublished
                # N/A for bsq-swaps: isCompleted, contractAsJson, contract, autoConfTxId, autoConfTxKey
                closing_status=closing_status,
                bsq_swap_trade_info=BsqSwapTradeInfo.from_bsq_swap_trade(
                    trade, is_my_offer, num_confirmations
                ),
            )
        elif isinstance(trade, Trade):
            contract_info = None
            if trade.contract is not None:
                contract = trade.contract
                contract_info = ContractInfo(
                    contract.buyer_payout_address_string,
                    contract.seller_payout_address_string,
                    contract.mediator_node_address.get_full_address(),
                    contract.refund_agent_node_address.get_full_address(),
                    contract.is_buyer_maker_and_seller_taker,
                    contract.maker_account_id,
                    contract.taker_account_id,
                    PaymentAccountPayloadInfo.from_payment_account_payload(
                        contract.maker_payment_account_payload
                    ),
                    PaymentAccountPayloadInfo.from_payment_account_payload(
                        contract.taker_payment_account_payload
                    ),
                    contract.maker_payout_address_string,
                    contract.taker_payout_address_string,
                    contract.lock_time,
                )
            else:
                contract_info = ContractInfo.empty_contract()

            offer_info = TradeInfo._to_offer_info(trade, is_my_offer)

            return TradeInfo(
                offer=offer_info,
                trade_id=trade.get_id(),
                short_id=trade.get_short_id(),
                date=int(trade.get_date().timestamp() * 1000),
                role=role if role is not None else "",
                is_currency_for_taker_fee_btc=trade.is_currency_for_taker_fee_btc,
                tx_fee_as_long=trade.trade_tx_fee_as_long,
                taker_fee_as_long=trade.taker_fee_as_long,
                taker_fee_tx_id=trade.taker_fee_tx_id,
                deposit_tx_id=trade.deposit_tx_id,
                payout_tx_id=trade.payout_tx_id,
                trade_amount_as_long=trade.get_amount_as_long(),
                trade_price=TradeInfo._to_precise_trade_price(trade),
                trade_volume=TradeInfo._to_rounded_volume(trade),
                trading_peer_node_address=TradeInfo._to_peer_node_address(trade),
                state=trade.get_trade_state().name,
                phase=trade.get_trade_phase().name,
                trade_period_state=trade.trade_period_state_property.get().name,
                is_deposit_published=trade.is_deposit_published,
                is_deposit_confirmed=trade.is_deposit_confirmed,
                is_payment_started_message_sent=trade.is_fiat_sent,
                is_payment_received_message_sent=trade.is_fiat_received,
                is_payout_published=trade.is_payout_published,
                is_completed=trade.is_withdrawn,
                contract_as_json=trade.contract_as_json,
                contract=contract_info,
                auto_conf_tx_id=trade.counter_currency_tx_id or "",
                auto_conf_tx_key=trade.counter_currency_extra_data or "",
                has_failed=trade.has_failed,
                error_message=(trade.error_message if trade.has_error_message else ""),
                closing_status=closing_status,
            )
        else:
            raise IllegalStateException(
                f"Unexpected trade type: {trade.__class__.__name__}"
            )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def to_proto_message(self) -> grpc_pb2.TradeInfo:
        proto_builder = grpc_pb2.TradeInfo(
            offer=self.offer.to_proto_message(),
            trade_id=self.trade_id,
            short_id=self.short_id,
            date=self.date,
            role=self.role,
            is_currency_for_taker_fee_btc=self.is_currency_for_taker_fee_btc,
            tx_fee_as_long=self.tx_fee_as_long,
            taker_fee_as_long=self.taker_fee_as_long,
            taker_fee_tx_id=self.taker_fee_tx_id or "",
            deposit_tx_id=self.deposit_tx_id or "",
            payout_tx_id=self.payout_tx_id or "",
            trade_amount_as_long=self.trade_amount_as_long,
            trade_price=self.trade_price or "",
            trade_volume=self.trade_volume or "",
            trading_peer_node_address=self.trading_peer_node_address,
            state=self.state or "",
            phase=self.phase or "",
            trade_period_state=self.trade_period_state or "",
            is_deposit_published=self.is_deposit_published,
            is_deposit_confirmed=self.is_deposit_confirmed,
            is_payment_started_message_sent=self.is_payment_started_message_sent,
            is_payment_received_message_sent=self.is_payment_received_message_sent,
            is_payout_published=self.is_payout_published,
            is_completed=self.is_completed,
            has_failed=self.has_failed,
            error_message=self.error_message or "",
            auto_conf_tx_id=self.auto_conf_tx_id or "",
            auto_conf_tx_key=self.auto_conf_tx_key or "",
            closing_status=self.closing_status,
        )
        if self.bsq_swap_trade_info:
            proto_builder.bsq_swap_trade_info.CopyFrom(
                self.bsq_swap_trade_info.to_proto_message()
            )
        else:
            proto_builder.contract_as_json = self.contract_as_json or ""
            proto_builder.contract.CopyFrom(self.contract.to_proto_message())
        return proto_builder

    @staticmethod
    def from_proto(proto: grpc_pb2.TradeInfo) -> "TradeInfo":
        offer_info = OfferInfo.from_proto(proto.offer)
        contract_info = (
            ContractInfo.from_proto(proto.contract)
            if proto.HasField("contract")
            else None
        )
        bsq_swap_trade_info = (
            BsqSwapTradeInfo.from_proto(proto.bsq_swap_trade_info)
            if proto.HasField("bsq_swap_trade_info")
            else None
        )

        return TradeInfo(
            offer=offer_info,
            trade_id=proto.trade_id,
            short_id=proto.short_id,
            date=proto.date,
            role=proto.role,
            is_currency_for_taker_fee_btc=proto.is_currency_for_taker_fee_btc,
            tx_fee_as_long=proto.tx_fee_as_long,
            taker_fee_as_long=proto.taker_fee_as_long,
            taker_fee_tx_id=proto.taker_fee_tx_id,
            deposit_tx_id=proto.deposit_tx_id,
            payout_tx_id=proto.payout_tx_id,
            trade_amount_as_long=proto.trade_amount_as_long,
            trade_price=proto.trade_price,
            trade_volume=proto.trade_volume,
            trading_peer_node_address=proto.trading_peer_node_address,
            state=proto.state,
            phase=proto.phase,
            trade_period_state=proto.trade_period_state,
            is_deposit_published=proto.is_deposit_published,
            is_deposit_confirmed=proto.is_deposit_confirmed,
            is_payment_started_message_sent=proto.is_payment_started_message_sent,
            is_payment_received_message_sent=proto.is_payment_received_message_sent,
            is_payout_published=proto.is_payout_published,
            is_completed=proto.is_completed,
            contract_as_json=proto.contract_as_json,
            contract=contract_info,
            auto_conf_tx_id=proto.auto_conf_tx_id,
            auto_conf_tx_key=proto.auto_conf_tx_key,
            has_failed=proto.has_failed,
            error_message=proto.error_message,
            closing_status=proto.closing_status,
            bsq_swap_trade_info=bsq_swap_trade_info,
        )

    def __str__(self):
        return (
            f"TradeInfo{{\n"
            f"  trade_id='{self.trade_id}',\n"
            f"  short_id='{self.short_id}',\n"
            f"  date='{self.date}',\n"
            f"  role='{self.role}',\n"
            f"  is_currency_for_taker_fee_btc='{self.is_currency_for_taker_fee_btc}',\n"
            f"  tx_fee_as_long='{self.tx_fee_as_long}',\n"
            f"  taker_fee_as_long='{self.taker_fee_as_long}',\n"
            f"  taker_fee_tx_id='{self.taker_fee_tx_id}',\n"
            f"  deposit_tx_id='{self.deposit_tx_id}',\n"
            f"  payout_tx_id='{self.payout_tx_id}',\n"
            f"  trade_amount_as_long='{self.trade_amount_as_long}',\n"
            f"  trade_price='{self.trade_price}',\n"
            f"  trade_volume='{self.trade_volume}',\n"
            f"  trading_peer_node_address='{self.trading_peer_node_address}',\n"
            f"  state='{self.state}',\n"
            f"  phase='{self.phase}',\n"
            f"  trade_period_state='{self.trade_period_state}',\n"
            f"  is_deposit_published={self.is_deposit_published},\n"
            f"  is_deposit_confirmed={self.is_deposit_confirmed},\n"
            f"  is_payment_started_message_sent={self.is_payment_started_message_sent},\n"
            f"  is_payment_received_message_sent={self.is_payment_received_message_sent},\n"
            f"  is_payout_published={self.is_payout_published},\n"
            f"  is_completed={self.is_completed},\n"
            f"  offer={self.offer},\n"
            f"  contract_as_json={self.contract_as_json},\n"
            f"  contract={self.contract},\n"
            f"  bsq_swap_trade_info={self.bsq_swap_trade_info},\n"
            f"  closing_status={self.closing_status},\n"
            f"  has_failed={self.has_failed},\n"
            f"  error_message={self.error_message},\n"
            f"  auto_conf_tx_id={self.auto_conf_tx_id},\n"
            f"  auto_conf_tx_key={self.auto_conf_tx_key},\n"
            f"}}"
        )
