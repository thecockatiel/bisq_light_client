from typing import TYPE_CHECKING

from bisq.core.btc.wallet.wallets_manager import WalletsManager
from bisq.core.dao.dao_facade import DaoFacade
from bisq.core.offer.open_offer_manager import OpenOfferManager
from bisq.core.trade.statistics.trade_statistics_manager import TradeStatisticsManager

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.dao.burningman.delayed_payout_tx_receiver_service import (
        DelayedPayoutTxReceiverService,
    )
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.provider.fee.fee_service import FeeService
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import (
        ArbitratorManager,
    )
    from bisq.core.support.dispute.mediation.mediator.mediator_manager import (
        MediatorManager,
    )
    from bisq.core.support.refund.refundagent.refund_agent_manager import (
        RefundAgentManager,
    )
    from bisq.core.user.user import User
    from bisq.core.account.witness.account_age_witness_service import (
        AccountAgeWitnessService,
    )
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService
    from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService
    from bisq.core.trade.statistics.referral_id_service import ReferralIdService
    from bisq.core.dao.burningman.btc_fee_receiver_service import BtcFeeReceiverService


class Provider:
    def __init__(
        self,
        open_offer_manager: "OpenOfferManager",
        p2p_service: "P2PService",
        btc_wallet_service: "BtcWalletService",
        bsq_wallet_service: "BsqWalletService",
        trade_wallet_service: "TradeWalletService",
        wallets_manager: 'WalletsManager',
        dao_facade: "DaoFacade",
        referral_id_service: "ReferralIdService",
        user: "User",
        filter_manager: "FilterManager",
        account_age_witness_service: "AccountAgeWitnessService",
        trade_statistics_manager: 'TradeStatisticsManager',
        arbitrator_manager: "ArbitratorManager",
        mediator_manager: "MediatorManager",
        refund_agent_manager: "RefundAgentManager",
        key_ring: "KeyRing",
        fee_service: "FeeService",
        btc_fee_receiver_service: "BtcFeeReceiverService",
        delayed_payout_tx_receiver_service: "DelayedPayoutTxReceiverService",
    ):
        self.open_offer_manager = open_offer_manager
        self.p2p_service = p2p_service
        self.btc_wallet_service = btc_wallet_service
        self.bsq_wallet_service = bsq_wallet_service
        self.trade_wallet_service = trade_wallet_service
        self.wallets_manager = wallets_manager
        self.dao_facade = dao_facade
        self.referral_id_service = referral_id_service
        self.user = user
        self.filter_manager = filter_manager
        self.account_age_witness_service = account_age_witness_service
        self.trade_statistics_manager = trade_statistics_manager
        self.arbitrator_manager = arbitrator_manager
        self.mediator_manager = mediator_manager
        self.refund_agent_manager = refund_agent_manager
        self.key_ring = key_ring
        self.fee_service = fee_service
        self.btc_fee_receiver_service = btc_fee_receiver_service
        self.delayed_payout_tx_receiver_service = delayed_payout_tx_receiver_service
