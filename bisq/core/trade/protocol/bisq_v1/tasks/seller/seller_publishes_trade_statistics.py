from bisq.common.capability import Capability
from bisq.common.setup.log_setup import get_logger
from bisq.core.network.p2p.network.tor_network_node import TorNetworkNode
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.trade.statistics.trade_statistics_3 import TradeStatistics3

logger = get_logger(__name__)


class SellerPublishesTradeStatistics(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()

            assert self.trade.deposit_tx is not None

            capabilities = self.process_model.p2p_service.find_peers_capabilities(
                self.trade.trading_peer_node_address
            )
            if Capability.TRADE_STATISTICS_3 in capabilities:
                # Our peer has updated, so as we are the seller we will publish the trade statistics.
                # The peer as buyer does not publish anymore with v.1.4.0 (where Capability.TRADE_STATISTICS_3 was added)
                referral_id = (
                    self.process_model.referral_id_service.get_optional_referral_id()
                )
                is_tor_network_node = isinstance(
                    self.process_model.p2p_service.network_node, TorNetworkNode
                )
                trade_statistics = TradeStatistics3.from_trade(
                    self.trade, referral_id, is_tor_network_node
                )
                if trade_statistics.is_valid():
                    logger.info("Publishing trade statistics")
                    self.process_model.p2p_service.add_persistable_network_payload(
                        trade_statistics, True
                    )
                else:
                    logger.warning(
                        f"Trade statistics are invalid. We do not publish. {trade_statistics}"
                    )
                self.complete()
            else:
                logger.info(
                    "Our peer does not have updated yet, so they will publish the trade statistics. "
                    "To avoid duplicates we do not publish from our side."
                )
                self.complete()

        except Exception as e:
            self.failed(exc=e)
