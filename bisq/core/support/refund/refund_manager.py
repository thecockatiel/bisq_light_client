from asyncio import Future
import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING, List

from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from bisq.core.support.dispute.dispute_manager import DisputeManager
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.support.dispute.messages.open_new_dispute_message import (
    OpenNewDisputeMessage,
)
from bisq.core.support.dispute.messages.peer_opened_dispute_message import (
    PeerOpenedDisputeMessage,
)
from bisq.core.support.messages.chat_messsage import ChatMessage
from bisq.core.support.support_type import SupportType
from bisq.core.trade.model.trade_dispute_state import TradeDisputeState
from bisq.core.support.dispute.agent.dispute_agent_lookup_map import (
    DisputeAgentLookupMap,
)
from bisq.core.locale.res import Res
import bisq.common.version as Version
from global_container import GLOBAL_CONTAINER

if TYPE_CHECKING:
    from bitcoinj.core.transaction import Transaction
    from bisq.core.support.dispute.messages.dispute_result_message import (
        DisputeResultMessage,
    )
    from bisq.core.support.dispute.dispute import Dispute
    from bisq.core.support.messages.support_message import SupportMessage
    from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
        DelayedPayoutTxReceiverService,
    )
    from bisq.common.config.config import Config
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService
    from bisq.core.btc.wallets_setup import WalletsSetup
    from bisq.core.dao.dao_facade import DaoFacade
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.offer.open_offer_manager import OpenOfferManager
    from bisq.core.provider.price.price_feed_service import PriceFeedService
    from bisq.core.support.refund.refund_dispute_list_service import (
        RefundDisputeListService,
    )
    from bisq.core.trade.bisq_v1.failed_trades_manager import FailedTradesManager
    from bisq.core.trade.closed_tradable_manager import ClosedTradableManager
    from bisq.core.trade.trade_manager import TradeManager
    from bisq.core.provider.mempool.mempool_service import MempoolService
    from bisq.core.support.refund.refund_dispute_list import RefundDisputeList

logger = get_logger(__name__)


class RefundManager(DisputeManager["RefundDisputeList"]):
    def __init__(
        self,
        p2p_service: "P2PService",
        trade_wallet_service: "TradeWalletService",
        btc_wallet_service: "BtcWalletService",
        wallets_setup: "WalletsSetup",
        trade_manager: "TradeManager",
        closed_tradable_manager: "ClosedTradableManager",
        failed_trades_manager: "FailedTradesManager",
        open_offer_manager: "OpenOfferManager",
        dao_facade: "DaoFacade",
        delayed_payout_tx_receiver_service: "DelayedPayoutTxReceiverService",
        key_ring: "KeyRing",
        refund_dispute_list_service: "RefundDisputeListService",
        config: "Config",
        price_feed_service: "PriceFeedService",
        mempool_service: "MempoolService",
    ):
        super().__init__(
            p2p_service,
            trade_wallet_service,
            btc_wallet_service,
            wallets_setup,
            trade_manager,
            closed_tradable_manager,
            failed_trades_manager,
            open_offer_manager,
            dao_facade,
            key_ring,
            refund_dispute_list_service,
            config,
            price_feed_service,
        )
        self.delayed_payout_tx_receiver_service = delayed_payout_tx_receiver_service
        self.mempool_service = mempool_service

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Implement template methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_support_type(self):
        return SupportType.REFUND

    def on_support_message(self, message: "SupportMessage"):
        if self.can_process_message(message):
            logger.info(
                f"Received {message.__class__.__name__} with tradeId {message.get_trade_id()} and uid {message.uid}"
            )

            if isinstance(message, OpenNewDisputeMessage):
                self.on_open_new_dispute_message(message)
            elif isinstance(message, PeerOpenedDisputeMessage):
                self.on_peer_opened_dispute_message(message)
            elif isinstance(message, ChatMessage):
                self.on_chat_message(message)
            elif isinstance(message, DisputeResultMessage):
                self.on_dispute_result_message(message)
            else:
                logger.warning(
                    f"Unsupported message at dispatch_message. message={message}"
                )

    def get_dispute_state_started_by_peer(self):
        return TradeDisputeState.REFUND_REQUEST_STARTED_BY_PEER

    def get_ack_message_source_type(self):
        return AckMessageSourceType.REFUND_MESSAGE

    def cleanup_disputes(self):
        self.dispute_list_service.cleanup_disputes(
            lambda trade_id: self.trade_manager.close_disputed_trade(
                trade_id, TradeDisputeState.REFUND_REQUEST_CLOSED
            )
        )

    def get_dispute_info(self, dispute: "Dispute") -> str:
        role = Res.get("shared.refundAgent").lower()
        role_context_msg = Res.get(
            "support.initialArbitratorMsg",
            DisputeAgentLookupMap.get_matrix_link_for_agent(
                self.get_agent_node_address(dispute).get_full_address()
            ),
        )
        link = "https://bisq.wiki/Dispute_resolution#Level_3:_Arbitration"
        return Res.get(
            "support.initialInfoRefundAgent", role, role_context_msg, role, link
        )

    def get_dispute_intro_for_peer(self, dispute_info: str) -> str:
        return Res.get("support.peerOpenedDispute", dispute_info, Version.VERSION)

    def get_dispute_intro_for_dispute_creator(self, dispute_info: str) -> str:
        return Res.get("support.youOpenedDispute", dispute_info, Version.VERSION)

    def add_price_info_message(self, dispute: "Dispute", counter: int):
        # At refund agent we do not add the option trade price check as the time for dispute opening is not correct.
        # In case of an option trade the mediator adds to the result summary message automatically the system message
        # with the option trade detection info so the refund agent can see that as well.
        pass

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Message handler
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We get that message at both peers. The dispute object is in context of the trader
    def on_dispute_result_message(self, message: "DisputeResultMessage"):
        dispute_result = message.dispute_result
        trade_id = dispute_result.trade_id
        chat_message = dispute_result.chat_message
        assert chat_message is not None, "chat_message must not be None"

        dispute = self.find_dispute(dispute_result)
        uid = message.uid

        if not dispute:
            logger.warning(
                "We got a dispute result msg but we don't have a matching dispute. "
                "That might happen when we get the disputeResultMessage before the dispute was created. "
                f"We try again after 2 sec. to apply the disputeResultMessage. TradeId = {trade_id}"
            )
            if uid not in self.delay_msg_map:
                # We delay 2 sec. to be sure the comm. msg gets added first
                timer = UserThread.run_after(
                    lambda: self.on_dispute_result_message(message),
                    timedelta(seconds=2),
                )
                self.delay_msg_map[uid] = timer
            else:
                logger.warning(
                    "We got a dispute result msg after we already repeated to apply the message after a delay. "
                    f"That should never happen. TradeId = {trade_id}"
                )
            return

        self.cleanup_retry_map(uid)

        if chat_message not in dispute.chat_messages:
            dispute.add_and_persist_chat_message(chat_message)
        else:
            logger.warning(
                f"We got a dispute mail msg what we have already stored. TradeId = {chat_message.trade_id}"
            )

        dispute.is_closed = True

        if dispute.dispute_result_property.value is not None:
            logger.warning(
                "We got already a dispute result. That should only happen if a dispute needs to be closed "
                f"again because the first close did not succeed. TradeId = {trade_id}"
            )

        dispute.dispute_result_property.value = dispute_result

        trade = self.trade_manager.get_trade_by_id(trade_id)
        if trade:
            if (
                trade.dispute_state == TradeDisputeState.REFUND_REQUESTED
                or trade.dispute_state
                == TradeDisputeState.REFUND_REQUEST_STARTED_BY_PEER
            ):
                trade.dispute_state = TradeDisputeState.REFUND_REQUEST_CLOSED
                self.trade_manager.request_persistence()
        else:
            open_offer = self.open_offer_manager.get_open_offer_by_id(trade_id)
            if open_offer:
                self.open_offer_manager.close_open_offer(open_offer.offer)

        self.send_ack_message(chat_message, dispute.agent_pub_key_ring, True, None)

        # Set state after payout as we call swap_trade_entry_to_available_entry
        if self.trade_manager.get_trade_by_id(trade_id):
            self.trade_manager.close_disputed_trade(
                trade_id, TradeDisputeState.REFUND_REQUEST_CLOSED
            )
        else:
            open_offer = self.open_offer_manager.get_open_offer_by_id(trade_id)
            if open_offer:
                self.open_offer_manager.close_open_offer(open_offer.offer)

        self.maybe_clear_sensitive_data()
        self.request_persistence()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_agent_node_address(self, dispute: "Dispute"):
        return dispute.contract.refund_agent_node_address

    def request_blockchain_transactions(
        self,
        maker_fee_tx_id: str,
        taker_fee_tx_id: str,
        deposit_tx_id: str,
        delayed_payout_tx_id: str,
    ) -> Future[List["Transaction"]]:
        # in regtest mode, simulate a delay & failure obtaining the blockchain transactions
        # since we cannot request them in regtest anyway.  this is useful for checking failure scenarios
        if not GLOBAL_CONTAINER.value.config.base_currency_network.is_mainnet():
            future = Future()
            UserThread.run_after(lambda: future.set_result([]), timedelta(seconds=5))
            return future

        params = self.btc_wallet_service.params
        result_future = Future[List["Transaction"]]()

        # Note: Requests all transaction hex futures all at once, unlike the original code which does it one by one
        maker_fee_tx_hex_future = self.mempool_service.request_tx_as_hex(
            maker_fee_tx_id
        )
        taker_fee_tx_hex_future = self.mempool_service.request_tx_as_hex(
            taker_fee_tx_id
        )
        deposit_tx_hex_future = self.mempool_service.request_tx_as_hex(deposit_tx_id)
        delayed_payout_tx_hex_future = self.mempool_service.request_tx_as_hex(
            delayed_payout_tx_id
        )

        futures = [
            maker_fee_tx_hex_future,
            taker_fee_tx_hex_future,
            deposit_tx_hex_future,
            delayed_payout_tx_hex_future,
        ]

        def handle_hex_futures():
            try:
                txs: list["Transaction"] = []
                # Get hex values in order
                maker_hex = maker_fee_tx_hex_future.result()
                txs.append(Transaction(params, bytes.fromhex(maker_hex)))

                taker_hex = taker_fee_tx_hex_future.result()
                txs.append(Transaction(params, bytes.fromhex(taker_hex)))

                deposit_hex = deposit_tx_hex_future.result()
                txs.append(Transaction(params, bytes.fromhex(deposit_hex)))

                payout_hex = delayed_payout_tx_hex_future.result()
                txs.append(Transaction(params, bytes.fromhex(payout_hex)))

                result_future.set_result(txs)
            except Exception as e:
                result_future.set_exception(e)

        asyncio.gather(*futures).add_done_callback(lambda _: handle_hex_futures())

        return result_future

    def verify_trade_tx_chain(self, txs: List["Transaction"]):
        maker_fee_tx = txs[0]
        taker_fee_tx = txs[1]
        deposit_tx = txs[2]
        delayed_payout_tx = txs[3]

        # The order and number of buyer and seller inputs are not part of the trade protocol consensus.
        # In the current implementation buyer inputs come before seller inputs at depositTx and there is
        # only 1 input per trader, but we do not want to rely on that.
        # So we just check that both fee txs are found in the inputs.
        maker_fee_tx_found = False
        taker_fee_tx_found = False

        for tx_input in deposit_tx.inputs:
            funding_tx_id = str(tx_input.outpoint.hash)
            if not maker_fee_tx_found:
                maker_fee_tx_found = funding_tx_id == maker_fee_tx.get_tx_id()
            if not taker_fee_tx_found:
                taker_fee_tx_found = funding_tx_id == taker_fee_tx.get_tx_id()

        assert maker_fee_tx_found, "makerFeeTx not found at deposit_tx inputs"
        assert taker_fee_tx_found, "takerFeeTx not found at deposit_tx inputs"
        assert len(deposit_tx.inputs) >= 2, "deposit_tx must have at least 2 inputs"
        assert (
            len(delayed_payout_tx.inputs) >= 1
        ), "delayed_payout_tx must have at least 1 inputs"
        delayed_payout_tx_outpoint = delayed_payout_tx.inputs[0].outpoint
        funding_tx_id = str(
            delayed_payout_tx_outpoint.hash
        )
        assert funding_tx_id == deposit_tx.get_tx_id(), "First input at delayed_payout_tx does not connect to deposit_tx"

    def verify_delayed_payout_tx_receivers(
        self, delayed_payout_tx: "Transaction", dispute: "Dispute"
    ):
        deposit_tx = dispute.find_deposit_tx(self.btc_wallet_service)
        if deposit_tx is None:
            raise ValueError("deposit_tx not found at verify_delayed_payout_tx_receivers")
        
        input_amount = deposit_tx.outputs[0].get_value().value
        selection_height = dispute.burning_man_selection_height

        was_bugfix_6699_activated_at_trade_date = (
            dispute.get_trade_date()
            > DelayedPayoutTxReceiverService.BUGFIX_6699_ACTIVATION_DATE
        )
        delayed_payout_tx_receivers = (
            self.delayed_payout_tx_receiver_service.get_receivers(
                selection_height,
                input_amount,
                dispute.trade_tx_fee,
                was_bugfix_6699_activated_at_trade_date,
            )
        )
        logger.info(
            f"Verify delayedPayoutTx using selectionHeight {selection_height} and receivers {delayed_payout_tx_receivers}"
        )
        assert len(delayed_payout_tx.outputs) == len(
            delayed_payout_tx_receivers
        ), "Size of outputs and delayed_payout_tx_receivers must be the same"

        params = self.btc_wallet_service.params
        for i, tx_output in enumerate(delayed_payout_tx.outputs):
            receiver_tuple = delayed_payout_tx_receivers[0]
            assert (
                str(tx_output.get_script_pub_key().get_to_address(params))
                == receiver_tuple[1]
            ), f"output address does not match delayedPayoutTxReceivers address. transactionOutput={tx_output}"
            assert (
                tx_output.get_value().value == receiver_tuple[0]
            ), f"output value does not match delayedPayoutTxReceivers value. transactionOutput={tx_output}"
