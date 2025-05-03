from typing import TYPE_CHECKING, List
from datetime import datetime, timezone

from bisq.common.config.config import Config
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from utils.java_compat import java_cmp_str
from utils.preconditions import check_argument
from bisq.core.btc.wallet.trade_wallet_service import TradeWalletService
from bisq.core.dao.burningman.burning_man_service import BurningManService
from utils.python_helpers import classproperty

if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.block import Block
    from bisq.core.dao.state.dao_state_service import DaoStateService

class DelayedPayoutTxReceiverService(DaoStateListener):
    """
    Used in the trade protocol for creating and verifying the delayed payout transaction.
    Requires to be deterministic.
    Changes in the parameters related to the receivers list could break verification of the peers
    delayed payout transaction in case not both are using the same version.
    """
    
    # Activation date for bugfix of receiver addresses getting overwritten by a new compensation
    # requests change address.
    # See: https://github.com/bisq-network/bisq/issues/6699
    BUGFIX_6699_ACTIVATION_DATE = datetime(2023, 7, 24)
    # See: https://github.com/bisq-network/proposals/issues/412
    PROPOSAL_412_ACTIVATION_DATE = datetime(2024, 5, 1)

    # We don't allow to get further back than 767950 (the block height from Dec. 18th 2022).
    @classproperty
    def MIN_SNAPSHOT_HEIGHT(cls):
        # TODO: double check for access timing
        if Config.BASE_CURRENCY_NETWORK_VALUE.is_regtest():
            return 0
        else:
            return 767950

    # One part of the limit for the min. amount to be included in the DPT outputs.
    # The miner fee rate multiplied by 2 times the output size is the other factor.
    # The higher one of both is used. 1000 sat is about 2 USD @ 20k price.
    DPT_MIN_OUTPUT_AMOUNT = 1000

    # If at DPT there is some leftover amount due to capping of some receivers (burn share is
    # max. ISSUANCE_BOOST_FACTOR times the issuance share) we send it to legacy BM if it is larger
    # than DPT_MIN_REMAINDER_TO_LEGACY_BM, otherwise we spend it as miner fee.
    # 25000 sat is about 5 USD @ 20k price. We use a rather high value as we want to avoid that the legacy BM
    # gets still payouts.
    DPT_MIN_REMAINDER_TO_LEGACY_BM = 25000

    # Min. fee rate for DPT. If fee rate used at take offer time was higher we use that.
    # We prefer a rather high fee rate to not risk that the DPT gets stuck if required fee rate would
    # spike when opening arbitration.
    DPT_MIN_TX_FEE_RATE = 10

    ###########################################################################################

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        burning_man_service: "BurningManService",
    ) -> None:
        self.dao_state_service = dao_state_service
        self.burning_man_service = burning_man_service
        self.current_chain_height = 0

        self.dao_state_service.add_dao_state_listener(self)
        last_block = self.dao_state_service.last_block
        if last_block:
            self.apply_block(last_block)

    def shut_down(self):
        self.dao_state_service.remove_dao_state_listener(self)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoStateListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_parse_block_complete_after_batch_processing(self, block: "Block"):
        self.apply_block(block)

    def apply_block(self, block: "Block") -> None:
        self.current_chain_height = block.height

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # We use a snapshot blockHeight to avoid failed trades in case maker and taker have different block heights.
    # The selection is deterministic based on DAO data.
    # The block height is the last mod(10) height from the range of the last 10-20 blocks (139 -> 120; 140 -> 130, 141 -> 130).
    # We do not have the latest dao state by that but can ensure maker and taker have the same block.
    def get_burning_man_selection_height(self) -> int:
        return self.get_snapshot_height(
            self.dao_state_service.genesis_block_height,
            self.current_chain_height,
            10,
        )

    def get_receivers(
        self,
        burning_man_selection_height: int,
        input_amount: int,
        trade_tx_fee: int,
        is_bugfix_6699_activated: bool = True,
        is_proposal_412_activated: bool = True,
    ) -> List[tuple[int, str]]:
        check_argument(
            burning_man_selection_height >= self.MIN_SNAPSHOT_HEIGHT,
            f"Selection height must be >= {self.MIN_SNAPSHOT_HEIGHT}"
        )

        burning_man_candidates = (
            self.burning_man_service.get_active_burning_man_candidates(
                burning_man_selection_height,
                not is_proposal_412_activated,
            )
        )

        # We need to use the same txFeePerVbyte value for both traders.
        # We use the tradeTxFee value which is calculated from the average of taker fee tx size and deposit tx size.
        # Otherwise, we would need to sync the fee rate of both traders.
        # In case of very large taker fee tx we would get a too high fee, but as fee rate is anyway rather
        # arbitrary and volatile we are on the safer side. The delayed payout tx is published long after the
        # take offer event and the recommended fee at that moment might be very different to actual
        # recommended fee. To avoid that the delayed payout tx would get stuck due too low fees we use a
        # min. fee rate of 10 sat/vByte.

        # Deposit tx has a clearly defined structure, so we know the size. It is only one optional output if range amount offer was taken.
        # Smallest tx size is 246. With additional change output we add 32. To be safe we use the largest expected size.
        tx_size = 278.0  # Deposit tx has defined structure
        tx_fee_per_vbyte = max(DelayedPayoutTxReceiverService.DPT_MIN_TX_FEE_RATE, round(trade_tx_fee / tx_size))

        if not burning_man_candidates:
            # If there are no compensation requests (e.g. at dev testing) we fall back to the legacy BM
            spendable_amount = self.get_spendable_amount(
                1, input_amount, tx_fee_per_vbyte
            )
            return [
                (
                    spendable_amount,
                    self.burning_man_service.get_legacy_burning_man_address(
                        burning_man_selection_height
                    ),
                )
            ]

        spendable_amount = self.get_spendable_amount(
            len(burning_man_candidates), input_amount, tx_fee_per_vbyte
        )
        # We only use outputs >= 1000 sat or at least 2 times the cost for the output (32 bytes).
        # If we remove outputs it will be distributed to the remaining receivers.
        min_output_amount = max(DelayedPayoutTxReceiverService.DPT_MIN_OUTPUT_AMOUNT, tx_fee_per_vbyte * 32 * 2)
        # Sanity check that max share of a non-legacy BM is 20% over MAX_BURN_SHARE (taking into account potential increase due adjustment)
        max_output_amount = round(
            spendable_amount * (BurningManService.MAX_BURN_SHARE * 1.2)
        )
        # We accumulate small amounts which gets filtered out and subtract it from 1 to get an adjustment factor
        # used later to be applied to the remaining burningmen share.
        adjustment = 1.0 - sum(
            candidate.capped_burn_amount_share
            for candidate in burning_man_candidates
            if candidate.get_receiver_address(is_bugfix_6699_activated) is not None
            and round(candidate.capped_burn_amount_share * spendable_amount)
            < min_output_amount
        )

        # JAVA FIXME: The small outputs should be filtered out before adjustment, not afterwards. Otherwise, outputs of
        #  amount just under 1000 sats or 64 * fee-rate could get erroneously included and lead to significant
        #  underpaying of the DPT (by perhaps around 5-10% per erroneously included output).
        receivers: list[tuple[int, str]] = []
        for candidate in burning_man_candidates:
            receiver_address = candidate.get_receiver_address(is_bugfix_6699_activated)
            if not receiver_address:
                continue

            capped_burn_amount_share = (
                candidate.capped_burn_amount_share / adjustment
            )
            amount = round(capped_burn_amount_share * spendable_amount)

            if min_output_amount <= amount <= max_output_amount:
                receivers.append((amount, receiver_address))

        receivers.sort(key=lambda x: (x[0], java_cmp_str(x[1])))

        total_output_value = sum(r[0] for r in receivers)
        if total_output_value < spendable_amount:
            available = spendable_amount - total_output_value
            # If the available is larger than DPT_MIN_REMAINDER_TO_LEGACY_BM we send it to legacy BM
            # Otherwise we use it as miner fee
            if available > DelayedPayoutTxReceiverService.DPT_MIN_REMAINDER_TO_LEGACY_BM:
                receivers.append(
                    (
                        available,
                        self.burning_man_service.get_legacy_burning_man_address(
                            burning_man_selection_height
                        ),
                    )
                )

        return receivers

    @staticmethod
    def get_spendable_amount(
        num_outputs: int, input_amount: int, tx_fee_per_vbyte: int
    ) -> int:
        # Output size: 32 bytes
        # Tx size without outputs: 51 bytes
        tx_size = 51 + num_outputs * 32  # Min value: txSize=83
        miner_fee = tx_fee_per_vbyte * tx_size # Min value: minerFee=830
        # We need to make sure we have at least 1000 sat as defined in TradeWalletService
        miner_fee = max(TradeWalletService.MIN_DELAYED_PAYOUT_TX_FEE.value, miner_fee)
        return input_amount - miner_fee

    @staticmethod
    def get_snapshot_height(genesis_height: int, height: int, grid: int) -> int:
        return DelayedPayoutTxReceiverService.get_snapshot_height_internal(
            genesis_height,
            height,
            grid,
            DelayedPayoutTxReceiverService.MIN_SNAPSHOT_HEIGHT,
        )

    # Borrowed from DaoStateSnapshotService. We prefer to not reuse to avoid dependency to an unrelated domain.
    @staticmethod
    def get_snapshot_height_internal(
        genesis_height: int, height: int, grid: int, min_snapshot_height: int
    ) -> int:
        if height > (genesis_height + 3 * grid):
            ratio = round(height / grid)
            return max(min_snapshot_height, ratio * grid - grid)
        return max(min_snapshot_height, genesis_height)
