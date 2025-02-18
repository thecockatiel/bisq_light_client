from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Iterator, Optional, TypeVar
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.wallet.wallet_transactions_change_listener import (
    WalletTransactionsChangeListener,
)
from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.governance.bond.bond_consensus import BondConsensus
from bisq.core.dao.governance.bond.bond_state import BondState
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from bisq.core.dao.state.model.blockchain.tx_type import TxType
from bitcoinj.script.script_pattern import ScriptPattern
from utils.data import ObservableList
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.btc.wallet.bsq_wallet_service import BsqWalletService
    from bisq.core.dao.state.dao_state_service import DaoStateService
    from bisq.core.dao.state.model.blockchain.tx import Tx
    from bisq.core.dao.state.model.blockchain.tx_output import TxOutput
    from bisq.core.dao.governance.bond.bond import Bond
    from bisq.core.dao.governance.bond.bonded_asset import BondedAsset


_B = TypeVar("B", bound="Bond")
_T = TypeVar("T", bound="BondedAsset")


logger = get_logger(__name__)


class BondRepository(
    Generic[_B, _T], DaoSetupService, WalletTransactionsChangeListener, ABC
):
    """
    Collect bonds and bond asset data from other sources and provides access to the collection.
    Gets updated after a new block is parsed or at bsqWallet transaction change to detect also state changes by
    unconfirmed txs.
    """

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        bsq_wallet_service: "BsqWalletService",
    ):
        self._dao_state_service = dao_state_service
        self._bsq_wallet_service = bsq_wallet_service

        # These maps are just for convenience. The data which are used to fill the maps are stored in the DaoState (role, txs).
        self._bond_by_uid_map: dict[str, _B] = {}
        self._bonded_asset_by_hash_map: Optional[dict[bytes, _T]] = None
        self.bonds: ObservableList[_B] = ObservableList()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        class Listener(DaoStateListener):
            def on_parse_block_complete_after_batch_processing(self_, block):
                self.update()

        self._dao_state_service.add_dao_state_listener(Listener())
        self._bsq_wallet_service.add_wallet_transactions_change_listener(self)

    def start(self):
        self.update()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // WalletTransactionsChangeListener
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def on_wallet_transactions_change(self):
        self.update()

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def is_bonded_asset_already_in_bond(self, bonded_asset: _T) -> bool:
        return (
            bonded_asset.uid in self._bond_by_uid_map
            and self._bond_by_uid_map[bonded_asset.uid].lockup_tx_id is not None
        )

    def get_active_bonds(self) -> list[_B]:
        return [bond for bond in self.bonds if bond.is_active]

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Protected
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @abstractmethod
    def create_bond(self, bonded_asset: _T) -> _B:
        pass

    @abstractmethod
    def update_bond(self, bond: _B, bonded_asset: _T, lockup_tx_output: "TxOutput"):
        pass

    @abstractmethod
    def get_bonded_asset_stream(self) -> Iterator[_T]:
        pass

    def get_bonded_asset_by_hash_map(self) -> dict[bytes, _T]:
        if self._bonded_asset_by_hash_map:
            return self._bonded_asset_by_hash_map
        self._bonded_asset_by_hash_map = {
            asset.hash: asset for asset in self.get_bonded_asset_stream()
        }
        return self._bonded_asset_by_hash_map

    def update(self):
        ts = get_time_ms()
        logger.debug("update")
        self._bonded_asset_by_hash_map = None
        for bonded_asset in self.get_bonded_asset_stream():
            uid = bonded_asset.uid
            if uid not in self._bond_by_uid_map:
                self._bond_by_uid_map[uid] = self.create_bond(bonded_asset)
            bond = self._bond_by_uid_map[uid]

            for lockup_tx_output in self._dao_state_service.get_lockup_tx_outputs():
                self.update_bond(bond, bonded_asset, lockup_tx_output)

        self._update_bond_state_from_unconfirmed_lockup_txs()
        self._update_bond_state_from_unconfirmed_unlock_txs()

        self.bonds.set_all(self._bond_by_uid_map.values())
        logger.debug(f"update took {get_time_ms() - ts} ms")

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def _update_bond_state_from_unconfirmed_lockup_txs(self):
        for bonded_asset in self.get_bonded_asset_stream():
            if self.is_lockup_tx_unconfirmed(self._bsq_wallet_service, bonded_asset):
                bond = self._bond_by_uid_map.get(bonded_asset.uid, None)
                if bond and bond.bond_state == BondState.READY_FOR_LOCKUP:
                    bond.bond_state = (
                        BondState.CONFISCATED
                        if self.is_confiscated(bond)
                        else BondState.LOCKUP_TX_PENDING
                    )

    def _update_bond_state_from_unconfirmed_unlock_txs(self):
        for bonded_asset in self.get_bonded_asset_stream():
            if self.is_unlock_tx_unconfirmed(self._bsq_wallet_service, bonded_asset):
                bond = self._bond_by_uid_map.get(bonded_asset.uid, None)
                if bond and bond.bond_state == BondState.LOCKUP_TX_CONFIRMED:
                    bond.bond_state = (
                        BondState.CONFISCATED
                        if self.is_confiscated(bond)
                        else BondState.UNLOCK_TX_PENDING
                    )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Static
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def apply_bond_state(
        dao_state_service: "DaoStateService",
        bond: "Bond",
        lockup_tx: "Tx",
        lockup_tx_output: "TxOutput",
    ):
        if bond.bond_state not in [
            BondState.LOCKUP_TX_PENDING,
            BondState.UNLOCK_TX_PENDING,
        ]:
            bond.bond_state = BondState.LOCKUP_TX_CONFIRMED

        bond.lockup_tx_id = lockup_tx.id
        # We use the tx time as we want to have a unique time for all users
        bond.lockup_date = lockup_tx.time
        bond.amount = lockup_tx.locked_amount
        bond.lock_time = lockup_tx.lock_time

        if not dao_state_service.is_unspent(lockup_tx_output.get_key()):
            # Lockup is already spent (in unlock tx)
            spent_info = dao_state_service.get_spent_info(lockup_tx_output)
            if spent_info:
                unlock_tx_id = spent_info.tx_id
                unlock_tx = dao_state_service.get_tx(unlock_tx_id)
                if unlock_tx and unlock_tx.tx_type == TxType.UNLOCK:
                    # cross check if it is in daoStateService.getUnlockTxOutputs() ?
                    bond.unlock_tx_id = unlock_tx.id
                    bond.bond_state = BondState.UNLOCK_TX_CONFIRMED
                    bond.unlock_date = unlock_tx.time
                    if dao_state_service.is_unlocking_and_unspent_tx_id(unlock_tx.id):
                        bond.bond_state = BondState.UNLOCKING
                    else:
                        bond.bond_state = BondState.UNLOCKED

        if (
            bond.lockup_tx_id
            and dao_state_service.is_confiscated_lockup_tx_output(bond.lockup_tx_id)
        ) or (
            bond.unlock_tx_id
            and dao_state_service.is_confiscated_unlock_tx_output(bond.unlock_tx_id)
        ):
            bond.bond_state = BondState.CONFISCATED

    @staticmethod
    def is_lockup_tx_unconfirmed(
        bsq_wallet_service: "BsqWalletService", bonded_asset: "BondedAsset"
    ) -> bool:
        # TODO: double check later
        return any(
            BondConsensus.get_hash_from_op_return_data(script.decoded[1][1])
            == bonded_asset.hash
            for tx in bsq_wallet_service.get_pending_wallet_transactions_stream()
            if tx.outputs
            for output in [tx.outputs[-1]]
            if ScriptPattern.is_op_return(script := output.get_script_pub_key())
            and len(script.decoded) > 1
            and script.decoded[1][1] is not None
        )

    @staticmethod
    def is_unlock_tx_unconfirmed(
        bsq_wallet_service: "BsqWalletService",
        dao_state_service: "DaoStateService",
        bonded_asset: "BondedAsset",
    ) -> bool:
        # TODO: double check later
        return any(
            BondConsensus.get_hash_from_op_return_data(output.op_return_data)
            == bonded_asset.hash
            for tx in bsq_wallet_service.get_pending_wallet_transactions_stream()
            if len(tx.inputs) > 1
            #  We need to iterate all inputs
            for input in tx.inputs
            if input.connected_output is not None
            # The output at the lockupTx must be index 0
            and input.connected_output.index == 0
            and input.connected_output.parent is not None
            if (
                output := dao_state_service.get_lockup_op_return_tx_output(
                    input.connected_output.parent.get_tx_id()
                )
            )
            is not None
            and output.op_return_data is not None
        )

    @staticmethod
    def is_confiscated(bond: "Bond", dao_state_service: "DaoStateService") -> bool:
        return (
            bond.lockup_tx_id is not None
            and dao_state_service.is_confiscated_lockup_tx_output(bond.lockup_tx_id)
        ) or (
            bond.unlock_tx_id is not None
            and dao_state_service.is_confiscated_unlock_tx_output(bond.unlock_tx_id)
        )
