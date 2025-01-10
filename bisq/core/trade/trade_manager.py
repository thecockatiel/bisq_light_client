from collections.abc import Callable
from concurrent.futures import Future
from datetime import datetime
from typing import TYPE_CHECKING, Iterator, Optional, Union, cast
from bisq.common.app.dev_env import DevEnv
from bisq.common.clock_watcher_listener import ClockWatcherListener
from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.fault_handler import FaultHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.locale.res import Res
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bisq.core.network.p2p.decrypted_direct_message_listener import (
    DecryptedDirectMessageListener,
)
from bisq.core.network.p2p.decrypted_message_with_pub_key import DecryptedMessageWithPubKey
from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
from bisq.core.offer.availability.offer_availability_model import OfferAvailabilityModel
from bisq.common.setup.log_setup import get_logger
from bisq.core.offer.offer import Offer
from bisq.core.offer.offer_direction import OfferDirection
from bisq.core.offer.offer_state import OfferState
from bisq.core.offer.open_offer_state import OpenOfferState
from bisq.core.payment.payment_account import PaymentAccount
from bisq.core.trade.bisq_v1.trade_result_handler import TradeResultHandler
from bisq.core.trade.bisq_v1.trade_tx_exception import TradeTxException
from bisq.core.trade.model.bisq_v1.buyer_as_maker_trade import BuyerAsMakerTrade
from bisq.core.trade.model.bisq_v1.buyer_as_taker_trade import BuyerAsTakerTrade
from bisq.core.trade.model.bisq_v1.seller_as_maker_trade import SellerAsMakerTrade
from bisq.core.trade.model.bisq_v1.seller_as_taker_trade import SellerAsTakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_buyer_as_taker_trade import BsqSwapBuyerAsTakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_seller_as_taker_trade import BsqSwapSellerAsTakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_trade import BsqSwapTrade
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
from bisq.core.trade.model.trade_period_state import TradePeriodState
from bisq.core.trade.model.trade_state import TradeState
from bisq.core.trade.protocol.bisq_v1.maker_protocol import MakerProtocol
from bisq.core.trade.protocol.bisq_v1.model.process_model import ProcessModel
from bisq.core.trade.protocol.bisq_v1.taker_protocol import TakerProtocol
from bisq.core.trade.protocol.bsq_swap.messages.bsq_swap_request import BsqSwapRequest
from bisq.core.trade.protocol.bsq_swap.model.bsq_swap_protocol_model import BsqSwapProtocolModel
from bisq.core.util.validator import Validator
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_confidence import TransactionConfidence
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from utils.data import SimpleProperty
from bisq.core.trade.model.tradable_list import TradableList
from bisq.core.trade.protocol.trade_protocol import TradeProtocol
from bisq.core.trade.protocol.trade_protocol_factory import TradeProtocolFactory
import uuid
from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import InputsForDepositTxRequest
from bisq.core.trade.model.bsq_swap.bsq_swap_seller_as_maker_trade import BsqSwapSellerAsMakerTrade
from bisq.core.trade.model.bsq_swap.bsq_swap_buyer_as_maker_trade import BsqSwapBuyerAsMakerTrade
from bisq.core.trade.model.bisq_v1.trade import Trade


if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.common.persistence.persistence_manager import PersistenceManager
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.trade.bsq_swap.bsq_swap_trade_manager import BsqSwapTradeManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.user.user import User
    from bisq.common.clock_watcher import ClockWatcher
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.protocol.persistable.core_persistence_proto_resolver import CorePersistenceProtoResolver
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import ArbitratorManager
    from bisq.core.support.dispute.mediation.mediator.mediator_manager import MediatorManager
    from bisq.core.trade.bisq_v1.dump_delayed_payout_tx import DumpDelayedPayoutTx
    from bisq.core.trade.bisq_v1.trade_util import TradeUtil
    from bisq.core.trade.protocol.provider import Provider
    from bisq.core.trade.statistics.referral_id_service import ReferralIdService
    from bisq.core.trade.statistics.trade_statistics_manager import TradeStatisticsManager

logger = get_logger(__name__)

# TODO: check again after dependencies implemented
class TradeManager(PersistedDataHost, DecryptedDirectMessageListener):
    def __init__(self, user: 'User',
                 key_ring: 'KeyRing',
                 btc_wallet_service: 'BtcWalletService',
                 bsq_wallet_service: 'BsqWalletService',
                 open_offer_manager: 'OpenOfferManager',
                 closed_tradable_manager: 'ClosedTradableManager',
                 bsq_swap_trade_manager: 'BsqSwapTradeManager',
                 failed_trades_manager: 'FailedTradesManager',
                 p2p_service: 'P2PService',
                 price_feed_service: 'PriceFeedService',
                 trade_statistics_manager: 'TradeStatisticsManager',
                 trade_util: 'TradeUtil',
                 arbitrator_manager: 'ArbitratorManager',
                 mediator_manager: 'MediatorManager',
                 provider: 'Provider',
                 clock_watcher: 'ClockWatcher',
                 persistence_manager: 'PersistenceManager[TradableList[Trade]]',
                 referral_id_service: 'ReferralIdService',
                 core_persistence_proto_resolver: 'CorePersistenceProtoResolver',
                 dump_delayed_payout_tx: 'DumpDelayedPayoutTx',
                 allow_faulty_delayed_txs: bool):
        
        self.user = user
        self.key_ring = key_ring
        self.btc_wallet_service = btc_wallet_service
        self.bsq_wallet_service = bsq_wallet_service
        self.open_offer_manager = open_offer_manager
        self.closed_tradable_manager = closed_tradable_manager
        self.bsq_swap_trade_manager = bsq_swap_trade_manager
        self.failed_trades_manager = failed_trades_manager
        self.p2p_service = p2p_service
        self.price_feed_service = price_feed_service
        self.trade_statistics_manager = trade_statistics_manager
        self.trade_util = trade_util
        self.arbitrator_manager = arbitrator_manager
        self.mediator_manager = mediator_manager
        self.provider = provider
        self.clock_watcher = clock_watcher

        # We use uid for that map not the trade ID
        self.trade_protocol_by_trade_uid: dict[str, 'TradeProtocol'] = {}
        
        # We maintain a map with trade (offer) ID to reset a pending trade protocol for the same offer.
        # Pending trade protocol could happen in edge cases when an early error did not cause a removal of the
        # offer and the same peer takes the offer later again. Usually it is prevented for the taker to take again after a
        # failure but that is only based on failed trades state and it can be that either the taker deletes the failed trades
        # file or it was not persisted. Such rare cases could lead to a pending protocol and when taker takes again the
        # offer the message listener from the old pending protocol gets invoked and processes the messages based on
        # potentially outdated model data (e.g. old inputs).
        self.pending_trade_protocol_by_trade_id: dict[str, 'TradeProtocol'] = {}

        self.persistence_manager = persistence_manager
        self.tradable_list: TradableList["Trade"]  = TradableList()
        self.persisted_trades_initialized = SimpleProperty(False)
        self.take_offer_request_error_message_handler: Optional['ErrorMessageHandler'] = None
        self.num_pending_trades = SimpleProperty(0)
        self.referral_id_service = referral_id_service
        self.core_persistence_proto_resolver = core_persistence_proto_resolver
        self.dump_delayed_payout_tx = dump_delayed_payout_tx
        self.allow_faulty_delayed_txs = allow_faulty_delayed_txs

        self.persistence_manager.initialize(self.tradable_list, PersistenceManagerSource.PRIVATE, "PendingTrades")

        self.p2p_service.add_decrypted_direct_message_listener(self)

        self.failed_trades_manager.unfail_trade_callback = self.un_fail_trade


    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PersistedDataHost
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def read_persisted(self, complete_handler: Callable[[], None]):
        def on_persisted(persisted: TradableList["Trade"]):
            self.tradable_list.set_all(persisted.list)
    
            for trade in self.tradable_list:
                if trade.get_offer() is not None:
                    trade.get_offer().price_feed_service = self.price_feed_service
            
            self.dump_delayed_payout_tx.maybe_dump_delayed_payout_txs(
                self.tradable_list, 
                "delayed_payout_txs_pending"
            )
            complete_handler()

        self.persistence_manager.read_persisted(
            on_persisted,
            complete_handler
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DecryptedDirectMessageListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_direct_message(self, message: 'DecryptedMessageWithPubKey', peer: 'NodeAddress'):
        network_envelope = message.network_envelope
        if isinstance(network_envelope, InputsForDepositTxRequest):
            self.handle_take_offer_request(peer, network_envelope)
        elif isinstance(network_envelope, BsqSwapRequest):
            self.handle_bsq_swap_request(peer, network_envelope)

    # The maker received a TakeOfferRequest
    def handle_take_offer_request(self, peer: 'NodeAddress', inputs_for_deposit_tx_request: 'InputsForDepositTxRequest'):
        logger.info(f"Received inputsForDepositTxRequest from {peer} with tradeId "
                   f"{inputs_for_deposit_tx_request.trade_id} and uid {inputs_for_deposit_tx_request.uid}")

        try:
            Validator.non_empty_string_of(inputs_for_deposit_tx_request.trade_id)
        except:
            logger.warning(f"Invalid inputsForDepositTxRequest {inputs_for_deposit_tx_request}")
            return

        open_offer = self.open_offer_manager.get_open_offer_by_id(inputs_for_deposit_tx_request.trade_id)
        if not open_offer:
            return

        if open_offer.state != OpenOfferState.AVAILABLE:
            return

        offer = open_offer.get_offer()
        self.open_offer_manager.reserve_open_offer(open_offer)

        if offer.is_buy_offer:
            trade = BuyerAsMakerTrade(
                offer=offer,
                trade_tx_fee=Coin.value_of(inputs_for_deposit_tx_request.tx_fee),
                taker_fee=Coin.value_of(inputs_for_deposit_tx_request.taker_fee),
                is_currency_for_taker_fee_btc=inputs_for_deposit_tx_request.is_currency_for_taker_fee_btc,
                arbitrator_node_address=open_offer.arbitrator_node_address,
                mediator_node_address=open_offer.mediator_node_address,
                refund_agent_node_address=open_offer.refund_agent_node_address,
                btc_wallet_service=self.btc_wallet_service,
                process_model=self.get_new_process_model(offer),
                uid=str(uuid.uuid4())
            )
        else:
            trade = SellerAsMakerTrade(
                offer=offer,
                trade_tx_fee=Coin.value_of(inputs_for_deposit_tx_request.tx_fee),
                taker_fee=Coin.value_of(inputs_for_deposit_tx_request.taker_fee),
                is_currency_for_taker_fee_btc=inputs_for_deposit_tx_request.is_currency_for_taker_fee_btc,
                arbitrator_node_address=open_offer.arbitrator_node_address,
                mediator_node_address=open_offer.mediator_node_address,
                refund_agent_node_address=open_offer.refund_agent_node_address,
                btc_wallet_service=self.btc_wallet_service,
                process_model=self.get_new_process_model(offer),
                uid=str(uuid.uuid4())
            )

        trade_protocol = self.create_trade_protocol(trade)
        self.init_trade_and_protocol(trade, trade_protocol)

        cast(MakerProtocol, trade_protocol).handle_take_offer_request(inputs_for_deposit_tx_request, peer, 
            lambda error_message: self.take_offer_request_error_message_handler(error_message) if self.take_offer_request_error_message_handler else None
            )

        self.request_persistence()

    def handle_bsq_swap_request(self, peer: 'NodeAddress', request: 'BsqSwapRequest'):
        # TODO
        return
        # if not BsqSwapTakeOfferRequestVerification.is_valid(
        #         self.open_offer_manager, 
        #         self.provider.fee_service, 
        #         self.key_ring, 
        #         peer, 
        #         request):
        #     return

        # open_offer_optional = self.open_offer_manager.get_open_offer_by_id(request.trade_id)
        # assert open_offer_optional is not None
        # open_offer = open_offer_optional
        # offer = open_offer.get_offer()
        # self.open_offer_manager.reserve_open_offer(open_offer)

        # amount = Coin.value_of(request.trade_amount)
        # bsq_swap_protocol_model = BsqSwapProtocolModel(self.key_ring.pub_key_ring)
        
        # if isinstance(request, BuyersBsqSwapRequest):
        #     assert not offer.is_buy_offer(), "offer is expected to be a sell offer at handle_bsq_swap_request"
        #     bsq_swap_trade = BsqSwapSellerAsMakerTrade(
        #         offer=offer,
        #         amount=amount,
        #         trade_date=request.trade_date,
        #         sender_node_address=request.sender_node_address,
        #         tx_fee_per_vbyte=request.tx_fee_per_vbyte,
        #         maker_fee=request.maker_fee,
        #         taker_fee=request.taker_fee,
        #         bsq_swap_protocol_model=bsq_swap_protocol_model)
        # else:
        #     assert isinstance(request, SellersBsqSwapRequest)
        #     assert offer.is_buy_offer(), "offer is expected to be a buy offer at handle_bsq_swap_request"
        #     bsq_swap_trade = BsqSwapBuyerAsMakerTrade(
        #         offer=offer,
        #         amount=amount,
        #         trade_date=request.trade_date,
        #         sender_node_address=request.sender_node_address,
        #         tx_fee_per_vbyte=request.tx_fee_per_vbyte,
        #         maker_fee=request.maker_fee,
        #         taker_fee=request.taker_fee,
        #         bsq_swap_protocol_model=bsq_swap_protocol_model)

        # trade_protocol = self.create_trade_protocol(bsq_swap_trade)
        # self.init_trade_and_protocol(bsq_swap_trade, trade_protocol)

        # trade_protocol.handle_take_offer_request(
        #     request,
        #     peer,
        #     lambda error_message: self.take_offer_request_error_message_handler(
        #         f"{error_message}{self.get_resource('notification.bsqSwap.errorHelp')}"
        #     ) if self.take_offer_request_error_message_handler else None
        # )

        # self.request_persistence()

    def on_all_services_initialized(self):
        if self.p2p_service.is_bootstrapped:
            self.init_persisted_trades()
        else:
            class Listener(BootstrapListener):
                def on_data_received(self_):
                    self.init_persisted_trades()
            
            self.p2p_service.add_p2p_service_listener(Listener())

        self.get_observable_list().add_listener(lambda x: self.on_trades_changed())
        self.on_trades_changed()

        for address_entry in self.btc_wallet_service.get_address_entries_for_available_balance_stream():
            if address_entry.offer_id:
                logger.warning(f"Swapping pending OFFER_FUNDING entries at startup. offerId={address_entry.offer_id}")
                self.btc_wallet_service.swap_trade_entry_to_available_entry(
                    address_entry.offer_id, 
                    AddressEntryContext.OFFER_FUNDING
                )

    def get_trade_protocol(self, trade: "TradeModel") -> 'TradeProtocol':
        uid = trade.uid
        if uid in self.trade_protocol_by_trade_uid:
            return self.trade_protocol_by_trade_uid[uid]
        else:
            trade_protocol = TradeProtocolFactory.get_new_trade_protocol(trade)
            prev = self.trade_protocol_by_trade_uid.get(uid, None)
            self.trade_protocol_by_trade_uid[uid] = trade_protocol
            if prev is not None:
                logger.error(f"We had already an entry with uid {trade.uid}")
            

            pending = self.pending_trade_protocol_by_trade_id.get(trade.get_id(), None)
            self.pending_trade_protocol_by_trade_id[trade.get_id()] = trade_protocol
            if pending is not None:
                pending.reset()

            return trade_protocol

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Init pending trade
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def init_persisted_trades(self):
        to_remove = set["Trade"]()
        for trade_model in self.tradable_list:
            valid = self.init_persisted_trade(trade_model)
            if not valid:
                to_remove.add(trade_model)
        
        for trade in to_remove:
            self.tradable_list.remove(trade)
        
        if to_remove:
            self.request_persistence()

        self.persisted_trades_initialized.set(True)

        # We do not include failed trades as they should not be counted anyway in the trade statistics
        all_trades = set(self.closed_tradable_manager.get_closed_trades())
        all_trades.update(self.bsq_swap_trade_manager.get_bsq_swap_trades())
        all_trades.update(self.tradable_list.list)
        
        referral_id = self.referral_id_service.get_optional_referral_id()
        is_tor_network_node = isinstance(self.p2p_service.network_node, TorNetworkNode)
        self.trade_statistics_manager.maybe_republish_trade_statistics(
            all_trades, 
            referral_id, 
            is_tor_network_node
        )

    def init_persisted_trade(self, trade_model: Union['TradeModel', 'Trade', 'BsqSwapTrade']) -> bool:
        if isinstance(trade_model, BsqSwapTrade) and not trade_model.is_completed():
            # We do not keep pending or failed BsqSwap trades in our list and
            # do not process them at restart.
            # We remove the trade from the list after iterations in init_persisted_trades
            return False
            
        self.init_trade_and_protocol(trade_model, self.get_trade_protocol(trade_model))

        if hasattr(trade_model, 'update_deposit_tx_from_wallet'):
            trade_model.update_deposit_tx_from_wallet()
            
        self.request_persistence()
        return True
    
    def init_trade_and_protocol(self, trade_model: 'TradeModel', trade_protocol: 'TradeProtocol'):
        trade_protocol.initialize(self.provider, self, trade_model.get_offer())
        trade_model.initialize(self.provider)
        self.request_persistence()

    def request_persistence(self):
        self.persistence_manager.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Take offer
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def check_offer_availability(self, offer: 'Offer',
                               is_taker_api_user: bool,
                               result_handler: 'ResultHandler',
                               error_message_handler: 'ErrorMessageHandler'):
        if (self.btc_wallet_service.is_unconfirmed_transactions_limit_hit() or
                self.bsq_wallet_service.is_unconfirmed_transactions_limit_hit()):
            error_message = "Unconfirmed transactions limit reached"
            error_message_handler(error_message)
            logger.warning(error_message)
            return

        offer.check_offer_availability(
            self.get_offer_availability_model(offer, is_taker_api_user),
            result_handler,
            error_message_handler
        )

    # First we check if offer is still available then we create the trade with the protocol
    def on_take_offer(self, amount: 'Coin',
                     tx_fee: 'Coin',
                     taker_fee: 'Coin',
                     is_currency_for_taker_fee_btc: bool,
                     trade_price: int,
                     funds_needed_for_trade: 'Coin',
                     offer: 'Offer',
                     payment_account_id: str,
                     use_savings_wallet: bool,
                     is_taker_api_user: bool,
                     trade_result_handler: 'TradeResultHandler[Trade]',
                     error_message_handler: 'ErrorMessageHandler'):
        
        assert not self.was_offer_already_used_in_trade(offer.id)

        model = self.get_offer_availability_model(offer, is_taker_api_user)
        
        def on_available():
            if offer.state == OfferState.AVAILABLE:
                if offer.is_buy_offer:
                    trade = SellerAsTakerTrade(
                        offer=offer,
                        amount=amount,
                        trade_tx_fee=tx_fee,
                        taker_fee=taker_fee,
                        is_currency_for_taker_fee_btc=is_currency_for_taker_fee_btc,
                        price_as_long=trade_price,
                        trading_peer_node_address=model.peer_node_address,
                        arbitrator_node_address=model.selected_arbitrator,
                        mediator_node_address=model.selected_mediator,
                        refund_agent_node_address=model.selected_refund_agent,
                        btc_wallet_service=self.btc_wallet_service,
                        process_model=self.get_new_process_model(offer),
                        uid=str(uuid.uuid4())
                    )
                else:
                    trade = BuyerAsTakerTrade(
                        offer=offer,
                        amount=amount,
                        trade_tx_fee=tx_fee,
                        taker_fee=taker_fee,
                        is_currency_for_taker_fee_btc=is_currency_for_taker_fee_btc,
                        price_as_long=trade_price,
                        trading_peer_node_address=model.peer_node_address,
                        arbitrator_node_address=model.selected_arbitrator,
                        mediator_node_address=model.selected_mediator,
                        refund_agent_node_address=model.selected_refund_agent,
                        btc_wallet_service=self.btc_wallet_service,
                        process_model=self.get_new_process_model(offer),
                        uid=str(uuid.uuid4())
                    )
                
                trade.process_model.use_savings_wallet = use_savings_wallet
                trade.process_model.funds_needed_for_trade_as_long = funds_needed_for_trade.value
                trade.taker_payment_account_id = payment_account_id

                trade_protocol = self.create_trade_protocol(trade)
                
                self.init_trade_and_protocol(trade, trade_protocol)

                cast(TakerProtocol, trade_protocol).on_take_offer()
                trade_result_handler(trade)
                self.request_persistence()

        offer.check_offer_availability(model, on_available, error_message_handler)
        self.request_persistence()

    def on_take_bsq_swap_offer(self, 
                              offer: 'Offer',
                              amount: 'Coin',
                              tx_fee_per_vbyte: int,
                              maker_fee: int,
                              taker_fee: int,
                              is_taker_api_user: bool,
                              trade_result_handler: 'TradeResultHandler[BsqSwapTrade]',
                              error_message_handler: 'ErrorMessageHandler'):
        
        assert not self.was_offer_already_used_in_trade(offer.id)

        model = self.get_offer_availability_model(offer, is_taker_api_user)

        def on_available():
            if offer.state == OfferState.AVAILABLE:
                peer_node_address = model.peer_node_address
                bsq_swap_protocol_model = BsqSwapProtocolModel(self.key_ring.pub_key_ring)

                if offer.is_buy_offer:
                    bsq_swap_trade = BsqSwapSellerAsTakerTrade(
                        offer=offer,
                        amount=amount,
                        peer_node_address=peer_node_address,
                        tx_fee_per_vbyte=tx_fee_per_vbyte,
                        maker_fee=maker_fee,
                        taker_fee=taker_fee,
                        bsq_swap_protocol_model=bsq_swap_protocol_model
                    )
                else:
                    bsq_swap_trade = BsqSwapBuyerAsTakerTrade(
                        offer=offer,
                        amount=amount,
                        peer_node_address=peer_node_address,
                        tx_fee_per_vbyte=tx_fee_per_vbyte,
                        maker_fee=maker_fee,
                        taker_fee=taker_fee,
                        bsq_swap_protocol_model=bsq_swap_protocol_model
                    )

                trade_protocol = self.create_trade_protocol(bsq_swap_trade)
                
                self.init_trade_and_protocol(bsq_swap_trade, trade_protocol)

                cast(TakerProtocol, trade_protocol).on_take_offer()
                trade_result_handler(bsq_swap_trade)
                self.request_persistence()

        offer.check_offer_availability(model, on_available, error_message_handler)
        self.request_persistence()

    def create_trade_protocol(self, trade_model: 'TradeModel') -> 'TradeProtocol':
        trade_protocol = TradeProtocolFactory.get_new_trade_protocol(trade_model)
        prev = self.trade_protocol_by_trade_uid.get(trade_model.uid, None)
        self.trade_protocol_by_trade_uid[trade_model.uid] = trade_protocol
        if prev is not None:
            logger.error(f"We had already an entry with uid {trade_model.uid}")

        if isinstance(trade_model, Trade):
            self.tradable_list.append(trade_model)

        pending = self.pending_trade_protocol_by_trade_id.get(trade_model.get_id(), None)
        self.pending_trade_protocol_by_trade_id[trade_model.get_id()] = trade_protocol
        if pending is not None:
            pending.reset()

        # For BsqTrades we only store the trade at completion

        return trade_protocol

    def get_new_process_model(self, offer: 'Offer') -> 'ProcessModel':
        assert offer is not None, "Offer must not be None"
        return ProcessModel(
            offer.id,
            self.provider.user.account_id,
            self.provider.key_ring.pub_key_ring
        )

    def get_offer_availability_model(self, offer: 'Offer', is_taker_api_user: bool) -> 'OfferAvailabilityModel':
        return OfferAvailabilityModel(
            offer=offer,
            pub_key_ring=self.key_ring.pub_key_ring,
            p2p_service=self.p2p_service,
            user=self.user,
            mediator_manager=self.mediator_manager,
            trade_statistics_manager=self.trade_statistics_manager,
            delayed_payout_tx_receiver_service=self.provider.delayed_payout_tx_receiver_service,
            is_taker_api_user=is_taker_api_user
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Complete trade
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_withdraw_request(self, to_address: str,
                          amount: 'Coin',
                          fee: 'Coin',
                          aes_key: bytes,
                          trade: 'Trade',
                          memo: Optional[str],
                          result_handler: 'ResultHandler',
                          fault_handler: 'FaultHandler'):
        
        from_address = self.btc_wallet_service.get_or_create_address_entry(
            trade.get_id(),
            AddressEntryContext.TRADE_PAYOUT
        ).get_address_string()
            
        def on_done(f: Future['Transaction']):
            try:
                transaction = f.result()
                if transaction:
                    logger.debug(f"onWithdraw onSuccess tx ID: {transaction.get_tx_id()}")
                    self.on_trade_completed(trade)
                    trade.state_property.value = TradeState.WITHDRAW_COMPLETED
                    self.get_trade_protocol(trade).on_withdraw_completed()
                    self.request_persistence()
                    result_handler()
            except Exception as e:
                logger.error(e, exc_info=e)
                fault_handler("An exception occurred at request_withdraw (on_failure).", e)

        try:
            self.btc_wallet_service.send_funds(
                from_address=from_address,
                to_address=to_address,
                receiver_amount=amount,
                fee=fee,
                aes_key=aes_key,
                context=AddressEntryContext.TRADE_PAYOUT,
                memo=memo,
                callback=on_done
            )
        except Exception as e:
            logger.error(e, exc_info=e)
            fault_handler("An exception occurred at request_withdraw.", e)

    # If trade was completed (closed without fault but might be closed by a dispute) we move it to the closed trades
    def on_trade_completed(self, trade: 'Trade'):
        self.remove_trade(trade)
        self.closed_tradable_manager.add(trade)

        # JAVA TODO The address entry should have been removed already. Check and if its the case remove that.
        self.btc_wallet_service.reset_address_entries_for_pending_trade(trade.get_id())
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Dispute
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def close_disputed_trade(self, trade_id: str, dispute_state: 'TradeDisputeState'):
        trade = self.get_trade_by_id(trade_id)
        if trade:
            trade.dispute_state = dispute_state
            assert trade.contract is not None, "Trade contract must not be null"
            
            if trade.contract.is_my_role_buyer(self.key_ring.pub_key_ring):
                trade.state_property.value = TradeState.BUYER_RECEIVED_PAYOUT_TX_PUBLISHED_MSG  # buyer to trade step 4
            else:
                trade.state_property.value = TradeState.SELLER_SAW_ARRIVED_PAYOUT_TX_PUBLISHED_MSG  # seller to trade step 4
            
            self.btc_wallet_service.swap_trade_entry_to_available_entry(
                trade_id,
                AddressEntryContext.TRADE_PAYOUT
            )
            self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Trade period state
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def apply_trade_period_state(self):
        self.update_trade_period_state()
        
        class Listener(ClockWatcherListener):
            def on_second_tick(self_):
                if DevEnv.is_dev_mode():
                    self.update_trade_period_state()
                    
            def on_minute_tick(self_):
                self.update_trade_period_state()
            
        self.clock_watcher.add_listener(Listener())
        
    def update_trade_period_state(self):
        for trade in self.get_observable_list():
            if not trade.is_payout_published:
                max_trade_period_date = trade.get_max_trade_period_date()
                half_trade_period_date = trade.get_half_trade_period_date()
                
                if DevEnv.is_dev_mode():
                    confidence = self.btc_wallet_service.get_confidence_for_tx_id(trade.deposit_tx_id)
                    if (confidence is not None and 
                            confidence.get_depth_in_blocks() > 4):
                        trade.trade_period_state_property.value = TradePeriodState.TRADE_PERIOD_OVER
                        
                if max_trade_period_date and half_trade_period_date:
                    now = datetime.now()
                    if now > max_trade_period_date:
                        trade.trade_period_state_property.value = TradePeriodState.TRADE_PERIOD_OVER
                        self.request_persistence()
                    elif now > half_trade_period_date:
                        trade.trade_period_state_property.value = TradePeriodState.SECOND_HALF
                        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Failed trade handling
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # If trade is in already in critical state (if taker role: taker fee; both roles: after deposit published)
    # we move the trade to failed_trades_manager
    def on_move_invalid_trade_to_failed_trades(self, trade: 'Trade'):
        self.remove_trade(trade)
        self.failed_trades_manager.add(trade)

    def add_trade_to_pending_trades(self, trade: 'Trade'):
        if not trade.is_initialized:
            self.init_persisted_trade(trade)
        self.add_trade(trade)

    def get_trades_stream_with_funds_locked_in(self) -> Iterator['Trade']:
        return (trade for trade in self.get_observable_list() if trade.is_funds_locked_in)

    def get_set_of_failed_or_closed_trade_ids_from_locked_in_funds(self) -> set[str]:

        trade_tx_exception = None
        trades_id_set = set[str]()

        # Get failed trades from current trades
        trades_id_set.update(
            trade.get_id() for trade in self.get_trades_stream_with_funds_locked_in() 
            if trade.has_failed
        )

        # Get failed trades from failed trades manager
        for trade in self.failed_trades_manager.get_trades_stream_with_funds_locked_in():
            if trade.get_deposit_tx() is not None:
                logger.warning(f"We found a failed trade with locked up funds. That should never happen. trade ID={trade.get_id()}")
                trades_id_set.add(trade.get_id())

        # Get failed trades from closed trades
        for trade in self.closed_tradable_manager.get_trades_stream_with_funds_locked_in():
            deposit_tx = trade.get_deposit_tx()
            if deposit_tx is not None:
                confidence = self.btc_wallet_service.get_confidence_for_tx_id(deposit_tx.get_tx_id())
                if confidence is not None and confidence.confidence_type != TransactionConfidenceType.BUILDING:
                    trade_tx_exception = TradeTxException(Res.get("error.closedTradeWithUnconfirmedDepositTx", trade.get_short_id()))
                else:
                    logger.warning(f"We found a closed trade with locked up funds. That should never happen. trade ID={trade.get_id()}")
            else:
                trade_tx_exception = TradeTxException(Res.get("error.closedTradeWithNoDepositTx", trade.get_short_id()))
            trades_id_set.add(trade.get_id())

        if trade_tx_exception is not None:
            raise trade_tx_exception

        return trades_id_set

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BsqSwapTradeManager delegates
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_bsq_swap_trade_completed(self, bsq_swap_trade: 'BsqSwapTrade'):
        self.bsq_swap_trade_manager.on_trade_completed(bsq_swap_trade)

    def find_bsq_swap_trade_by_id(self, trade_id: str) -> Optional['BsqSwapTrade']:
        return self.bsq_swap_trade_manager.find_bsq_swap_trade_by_id(trade_id)
    
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Getters, Utils
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_observable_list(self):
        return self.tradable_list.get_observable_list()

    def persisted_trades_initialized_property(self):
        return self.persisted_trades_initialized

    def is_my_offer(self, offer: 'Offer') -> bool:
        return offer.is_my_offer(self.key_ring)

    def was_offer_already_used_in_trade(self, offer_id: str) -> bool:
        def combined_stream():
            yield from self.get_pending_and_bsq_swap_trades()
            yield from self.failed_trades_manager.get_observable_list()
            yield from self.closed_tradable_manager.get_observable_list()
            
        return any(t.get_offer().id == offer_id for t in combined_stream())

    def is_buyer(self, offer: 'Offer') -> bool:
        # If I am the maker, we use the OfferDirection, otherwise the mirrored direction
        if self.is_my_offer(offer):
            return offer.is_buy_offer
        else:
            return offer.direction == OfferDirection.SELL

    def get_trade_model_by_id(self, trade_id: str) -> Optional['TradeModel']:
        return next((trade_model for trade_model in self.get_pending_and_bsq_swap_trades()
                    if trade_model.get_id() == trade_id), None)

    def get_trade_by_id(self, trade_id: str) -> Optional['Trade']:
        trade_model = self.get_trade_model_by_id(trade_id)
        if trade_model and isinstance(trade_model, Trade):
            return trade_model
        return None

    def get_trades(self) -> tuple['Trade']:
        return tuple(self.get_observable_list())

    def remove_trade(self, trade: 'Trade'):
        if self.tradable_list.remove(trade):
            self.request_persistence()

    def add_trade(self, trade: 'Trade'):
        if self.tradable_list.append(trade):
            self.request_persistence()

    def get_pending_and_bsq_swap_trades(self):
        yield from self.tradable_list
        yield from self.bsq_swap_trade_manager.get_observable_list()

    # JAVA TODO Remove once tradableList is refactored to a final field
    #  (part of the persistence refactor PR)
    def on_trades_changed(self):
        self.num_pending_trades.set(len(self.get_observable_list()))

    # If trade still has funds locked up it might come back from failed trades
    # Aborts unfailing if the address entries needed are not available
    def un_fail_trade(self, trade: 'Trade') -> bool:
        if not self.recover_addresses(trade):
            logger.warning("Failed to recover address during unFail trade")
            return False

        self.init_persisted_trade(trade)

        self.tradable_list.append(trade)
        return True


    # The trade is added to pending trades if the associated address entries are AVAILABLE and
    # the relevant entries are changed, otherwise it's not added and no address entries are changed
    def recover_addresses(self, trade: 'Trade') -> bool:
        # Find addresses associated with this trade
        entries = self.trade_util.get_available_addresses(trade)
        if entries is None:
            return False

        self.btc_wallet_service.recover_address_entry(
            trade.get_id(), 
            entries[0],
            AddressEntryContext.MULTI_SIG
        )
        self.btc_wallet_service.recover_address_entry(
            trade.get_id(), 
            entries[1],
            AddressEntryContext.TRADE_PAYOUT
        )
        return True

    def clone_account(self, payment_account: 'PaymentAccount') -> 'PaymentAccount':
        proto_message = payment_account.to_proto_message()
        cloned = PaymentAccount.from_proto(proto_message, self.core_persistence_proto_resolver)
        assert cloned is not None
        return cloned

