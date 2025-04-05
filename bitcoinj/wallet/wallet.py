from datetime import datetime, timezone
import random
from threading import Lock
from bitcoinj.core.insufficient_money_exception import InsufficientMoneyException
from bitcoinj.core.transaction_confidence_source import TransactionConfidenceSource
from bitcoinj.core.transaction_input import TransactionInput
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.script.script import Script
from bitcoinj.script.script_exception import ScriptException
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.wallet.coin_selector import CoinSelector
from bitcoinj.wallet.exceptions.could_not_adjust_downwards import (
    CouldNotAdjustDownwards,
)
from bitcoinj.wallet.exceptions.dusty_send_requested_exception import (
    DustySendRequestedException,
)
from bitcoinj.wallet.exceptions.exceeded_max_transaction_size import (
    ExceededMaxTransactionSize,
)
from bitcoinj.wallet.exceptions.multiple_op_return_requested import (
    MultipleOpReturnRequested,
)
from bitcoinj.wallet.fee_calculation import FeeCalculation
from electrum_min import bitcoin
from utils.aio import as_future
from bisq.common.setup.log_setup import get_logger
from asyncio import Future
from collections.abc import Callable
import time
from typing import TYPE_CHECKING, Literal, Mapping, Optional, Union
from bisq.common.crypto.hash import get_sha256_ripemd160_hash
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.core.network_parameters import NetworkParameters
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.transaction_confidence import TransactionConfidence
from bitcoinj.core.transaction_confidence_type import TransactionConfidenceType
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.crypto.deterministic_key import DeterministicKey
from bitcoinj.script.script_type import ScriptType
from electrum_min.transaction import (
    PartialTransaction,
    PartialTxInput as ElectrumPartialTxInput,
    TxOutput as ElectrumTxOutput,
    PartialTxOutput as ElectrumPartialTxOutput,
)
from electrum_min.network import Network, TxBroadcastServerReturnedError
from electrum_min.util import (
    EventListener,
    InvalidPassword,
    TxMinedInfo,
    event_listener,
)
from utils.concurrency import ThreadSafeSet
from utils.data import SimpleProperty
from utils.preconditions import check_argument, check_not_none, check_state

if TYPE_CHECKING:
    from bitcoinj.wallet.coin_selection import CoinSelection
    from bitcoinj.wallet.send_request import SendRequest
    from electrum_min.wallet import Abstract_Wallet
    from bitcoinj.wallet.listeners.wallet_change_event_listener import (
        WalletChangeEventListener,
    )

logger = get_logger(__name__)


# TODO implement as needed
class Wallet(EventListener):

    def __init__(
        self,
        electrum_wallet: "Abstract_Wallet",
        electrum_network: "Network",
        network_params: "NetworkParameters",
    ):
        self._electrum_wallet = electrum_wallet
        self._electrum_network = electrum_network
        self._network_params = network_params
        self._change_listeners = ThreadSafeSet["WalletChangeEventListener"]()
        self._registered_for_callbacks = False
        self._new_tx_listeners = ThreadSafeSet[Callable[["Transaction"], None]]()
        self._tx_changed_listeners = ThreadSafeSet[Callable[["Transaction"], None]]()
        self._tx_verified_listeners = ThreadSafeSet[Callable[["Transaction"], None]]()
        self._tx_removed_listeners = ThreadSafeSet[Callable[["Transaction"], None]]()
        self.register_electrum_callbacks()
        self._last_balance = 0
        self._available_balance_property = SimpleProperty(Coin.ZERO())
        self._lock = Lock()

    @property
    def available_balance_property(self):
        return self._available_balance_property

    # //////////////////////////////////////////////////////////////////////
    # // Electrum bridge
    # //////////////////////////////////////////////////////////////////////

    def register_electrum_callbacks(self):
        if not self._registered_for_callbacks:
            self._registered_for_callbacks = True
            EventListener.register_callbacks(self)

    def unregister_electrum_callbacks(self):
        if self._registered_for_callbacks:
            self._registered_for_callbacks = False
            EventListener.unregister_callbacks(self)

    @event_listener
    def on_event_verified(self, wallet, txid, info):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

            wrapped_tx = None
            if self._tx_changed_listeners:
                wrapped_tx = self.get_transaction(txid)
                self.add_info_from_wallet(wrapped_tx)
                for listener in self._tx_changed_listeners:
                    listener(wrapped_tx)

            if self._tx_verified_listeners:
                if not wrapped_tx:
                    wrapped_tx = self.get_transaction(txid)
                    self.add_info_from_wallet(wrapped_tx)
                for listener in self._tx_verified_listeners:
                    listener(wrapped_tx)

    @event_listener
    def on_event_new_transaction(self, wallet, tx):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

            if self._new_tx_listeners:
                wrapped_tx = Transaction(self._network_params, tx)
                self.add_info_from_wallet(wrapped_tx)
                for listener in self._new_tx_listeners:
                    listener(wrapped_tx)

            if self._tx_changed_listeners:
                wrapped_tx = Transaction(self._network_params, tx)
                self.add_info_from_wallet(wrapped_tx)
                for listener in self._tx_changed_listeners:
                    listener(wrapped_tx)

    @event_listener
    def on_event_removed_transaction(self, wallet, tx):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

            if self._tx_removed_listeners:
                wrapped_tx = Transaction(self._network_params, tx)
                self.add_info_from_wallet(wrapped_tx)
                for listener in self._tx_removed_listeners:
                    listener(wrapped_tx)

    @event_listener
    def on_event_wallet_updated(self, wallet):
        if self._electrum_wallet == wallet:
            self.on_wallet_changed()

    def on_wallet_changed(self):
        for listener in self._change_listeners:
            listener(self)
        self._available_balance_property.set(
            Coin.value_of(self.get_available_balance())
        )

    @property
    def is_up_to_date(self):
        return self._electrum_wallet.is_up_to_date()

    # //////////////////////////////////////////////////////////////////////
    # // Bitcoinj Wallet API
    # //////////////////////////////////////////////////////////////////////

    def find_key_from_address(
        self,
        address: "Address",
    ) -> Optional["DeterministicKey"]:
        script_type = address.output_script_type
        if script_type == ScriptType.P2PKH or script_type == ScriptType.P2WPKH:
            keys = self._electrum_wallet.get_public_keys_with_deriv_info(str(address))
            if keys:
                first_item = next(iter(keys.items()))
                pubkey = first_item[0]
                keystore = first_item[1][0]
                derivation_suffix = first_item[1][1]
                return DeterministicKey(pubkey, keystore, derivation_suffix)
        return None

    def find_key_from_pub_key_hash(
        self,
        pub_key_hash: bytes,
        script_type: Optional["ScriptType"],
    ) -> Optional["DeterministicKey"]:
        if script_type == ScriptType.P2WPKH:
            address = str(SegwitAddress.from_hash(pub_key_hash, self._network_params))
        elif script_type == ScriptType.P2PKH:
            address = str(
                LegacyAddress.from_pub_key_hash(pub_key_hash, self._network_params)
            )
        else:
            try:
                address = str(
                    SegwitAddress.from_hash(pub_key_hash, self._network_params)
                )
            except:
                try:
                    address = str(
                        LegacyAddress.from_pub_key_hash(
                            pub_key_hash, self._network_params
                        )
                    )
                except:
                    address = None
            if not address:
                return None

        keys = self._electrum_wallet.get_public_keys_with_deriv_info(address)
        if keys:
            first_item = next(iter(keys.items()))
            pubkey = first_item[0]
            keystore = first_item[1][0]
            derivation_suffix = first_item[1][1]
            return DeterministicKey(pubkey, keystore, derivation_suffix)
        return None

    def find_key_from_pub_key(
        self,
        pub_key: bytes,
        script_type: Optional["ScriptType"],
    ) -> Optional["DeterministicKey"]:
        return self.find_key_from_pub_key_hash(
            get_sha256_ripemd160_hash(pub_key), script_type
        )

    def get_receiving_address(self) -> "Address":
        return Address.from_string(
            self._electrum_wallet.get_receiving_address(), self._network_params
        )

    def add_change_event_listener(self, listener: "WalletChangeEventListener"):
        self._change_listeners.add(listener)

    def remove_change_event_listener(self, listener: "WalletChangeEventListener"):
        if listener in self._change_listeners:
            self._change_listeners.discard(listener)
            return True
        return False

    def add_new_tx_listener(self, listener: Callable[["Transaction"], None]):
        self._new_tx_listeners.add(listener)

    def remove_new_tx_listener(self, listener: Callable[["Transaction"], None]):
        if listener in self._new_tx_listeners:
            self._new_tx_listeners.discard(listener)
            return True
        return False

    def add_tx_changed_listener(self, listener: Callable[["Transaction"], None]):
        self._tx_changed_listeners.add(listener)

    def remove_tx_changed_listener(self, listener: Callable[["Transaction"], None]):
        if listener in self._tx_changed_listeners:
            self._tx_changed_listeners.discard(listener)
            return True
        return False

    def add_tx_verified_listener(self, listener: Callable[["Transaction"], None]):
        self._tx_verified_listeners.add(listener)

    def remove_tx_verified_listener(self, listener: Callable[["Transaction"], None]):
        if listener in self._tx_verified_listeners:
            self._tx_verified_listeners.discard(listener)
            return True
        return False

    def add_tx_removed_listener(self, listener: Callable[["Transaction"], None]):
        self._tx_removed_listeners.add(listener)

    def remove_tx_removed_listener(self, listener: Callable[["Transaction"], None]):
        if listener in self._tx_removed_listeners:
            self._tx_removed_listeners.discard(listener)
            return True
        return False

    def decrypt(self, password: str):
        """removes wallet file password"""
        if not self.is_encrypted:
            raise IllegalStateException("Wallet is not encrypted")
        try:
            self._electrum_wallet.update_password(password, None)
        except InvalidPassword:
            raise IllegalArgumentException("Invalid password")

    def encrypt(self, password: str):
        """adds password to wallet file"""
        if self.is_encrypted:
            raise IllegalStateException("Wallet is already encrypted")
        # NOTE: this operation is io blocking, but should be fine
        self._electrum_wallet.update_password(None, password)

    def unlock(self, password: str):
        self._electrum_wallet.unlock(password)

    def lock(self):
        self._electrum_wallet.lock()

    @property
    def is_encrypted(self):
        return self._electrum_wallet.has_storage_encryption()

    @property
    def network_params(self):
        return self._network_params

    def stop(self):
        return self._electrum_wallet.stop()

    def start_network(self):
        self._electrum_wallet.start_network(self._electrum_network)
        self._maybe_broadcast_possibly_not_broadcasted_txs()

    def get_balances_for_display(self):
        """returns a set of balances for display purposes: confirmed and matured, unconfirmed, unmatured"""
        return self._electrum_wallet.get_balance()

    def get_available_balance(self) -> int:
        # see https://github.com/spesmilo/electrum/issues/8835
        return sum(
            utxo.value_sats() for utxo in self._electrum_wallet.get_spendable_coins()
        )

    def get_address_balance(self, address: Union["Address", str]) -> int:
        if isinstance(address, Address):
            address = str(address)
        return sum(
            utxo.value_sats()
            for utxo in self._electrum_wallet.get_spendable_coins([address])
        )

    def get_coin_selector_balance(self, coin_selector: "CoinSelector"):
        with self._lock:
            check_not_none(
                coin_selector,
                "coin_selector cannot be None at get_coin_selector_balance",
            )
            candidates = self.calculate_all_spend_candidates()
            selection = coin_selector.select(
                self.network_params.get_max_money(), candidates
            )
            return selection.value_gathered

    def get_issued_receive_addresses(self) -> list["Address"]:
        return [
            Address.from_string(address, self._network_params)
            for address in self._electrum_wallet.get_addresses()
        ]

    def is_address_unused(self, address: Union["Address", str]):
        if isinstance(address, Address):
            address = str(address)
        return self._electrum_wallet.is_address_unused(address)

    def is_mine(self, address: Union["Address", str]):
        if isinstance(address, Address):
            address = str(address)
        return self._electrum_wallet.is_mine(address)

    def get_transaction(self, txid: str) -> Optional["Transaction"]:
        e_tx = self._electrum_wallet.db.get_transaction(txid)
        if e_tx:
            tx = Transaction(self.network_params, e_tx)
            self.add_info_from_wallet(tx)
            return tx
        return None

    @property
    def last_block_seen_height(self):
        return self._electrum_wallet.adb.get_local_height()

    def get_transactions(self):
        """return an Generator that returns all transactions in the wallet, newest first"""
        with self._electrum_wallet.db.lock:
            reversed_it = reversed(self._electrum_wallet.db.transactions.copy().values())
        for tx in reversed_it:
            tx = Transaction(self.network_params, tx)
            self.add_info_from_wallet(tx)
            yield tx

    def _get_possibly_not_broadcasted_txs(self):
        """return an Generator that returns all transactions in the wallet that are possibly not yet broadcasted"""
        maybe_broadcast = self._electrum_wallet.get_maybe_broadcast_tx_ids()
        for tx_id, timestamp in maybe_broadcast.items():
            # cleanup txids older than a week
            if timestamp < time.time() - 7 * 24 * 60 * 60:
                self._electrum_wallet.remove_txid_from_maybe_broadcast(tx_id)
                continue
            tx = self.get_transaction(tx_id)
            if tx:
                yield tx

    def _maybe_broadcast_possibly_not_broadcasted_txs(self):
        def on_done(f: Future, tx: "Transaction"):
            remove = False
            try:
                f.result()
                logger.info(
                    f"Broadcasting completed for txid: {tx.get_tx_id()} wtxid: {tx.get_wtx_id()}"
                )
                remove = True
            except Exception as e:
                if isinstance(
                    e, TxBroadcastServerReturnedError
                ) or "program hash mismatch" in str(e):
                    remove = True
                else:
                    logger.warning(
                        f"Error when trying to broadcast tx at wallet start: {e}"
                    )
            if remove:
                self._electrum_wallet.remove_txid_from_maybe_broadcast(tx.get_tx_id())

        for tx in self._get_possibly_not_broadcasted_txs():
            logger.info(f"Broadcasting possibly not broadcasted tx: {tx}")
            as_future(self.broadcast_tx(tx)).add_done_callback(
                lambda f, tx=tx: on_done(f, tx)
            )

    def get_tx_mined_info(self, txid: str):
        return self._electrum_wallet.adb.get_tx_height(txid)

    def add_info_from_wallet(self, tx: "Transaction"):
        """populates prev_txs"""
        tx._electrum_transaction.add_info_from_wallet(self._electrum_wallet)
        tx.inputs.invalidate()
        tx.outputs.invalidate()
        tx.memo = self.get_label_for_txid(tx.get_tx_id())
        mined_info = self.get_tx_mined_info(tx.get_tx_id())
        if mined_info.timestamp:
            update_time = datetime.fromtimestamp(mined_info.timestamp)
            tx.update_time = update_time
            tx.included_in_best_chain_at = update_time
        tx.confidence = self._get_confidence_from_tx_mined_info(
            tx.get_tx_id(), mined_info
        )

    def get_label_for_txid(self, txid: str):
        return self._electrum_wallet.get_label_for_txid(txid)

    def maybe_add_transaction(self, tx: "Transaction"):
        """tries to add transaction to history of wallet and may raise error"""
        if tx.memo is not None:
            self._electrum_wallet.set_label(tx.get_tx_id(), tx.memo)
        existing_tx = self._electrum_wallet.db.get_transaction(tx.get_tx_id())
        if existing_tx:
            return Transaction(self.network_params, existing_tx)
        Transaction.verify(self.network_params, tx)
        self._electrum_wallet.adb.add_unverified_or_unconfirmed_tx(tx.get_tx_id(), 0)
        added = self._electrum_wallet.adb.add_transaction(
            tx._electrum_transaction, allow_unrelated=True, is_new=True
        )
        self._electrum_wallet.add_txid_to_maybe_broadcast(tx.get_tx_id())
        if not added:
            raise VerificationException(
                "Transaction could not be added to wallet history due to conflicts"
            )
        existing_tx = self._electrum_wallet.db.get_transaction(tx.get_tx_id())
        if not existing_tx:
            # unlikely, just in case
            raise IllegalStateException("Transaction was not added to wallet history")
        return Transaction(self.network_params, existing_tx)

    def is_transaction_pending(self, tx_id: str):
        with self._electrum_wallet.adb.lock:
            return (
                tx_id in self._electrum_wallet.adb.unconfirmed_tx
                or tx_id in self._electrum_wallet.adb.unverified_tx
            )

    def get_confidence_for_tx_id(
        self, tx_id: Optional[str]
    ) -> Optional["TransactionConfidence"]:
        if not tx_id:
            return None
        info = self.get_tx_mined_info(tx_id)
        return self._get_confidence_from_tx_mined_info(tx_id, info)

    def _get_confidence_from_tx_mined_info(self, tx_id: str, info: "TxMinedInfo"):
        if info.conf:
            return TransactionConfidence(
                tx_id,
                depth=self.last_block_seen_height - info.height,
                appeared_at_chain_height=info.height,
                confidence_type=TransactionConfidenceType.BUILDING,
                source=TransactionConfidenceSource.NETWORK,
                confirmations=info.conf,
            )
        else:
            is_pending = self.is_transaction_pending(tx_id)
            return TransactionConfidence(
                tx_id,
                depth=0,
                appeared_at_chain_height=info.height,
                confidence_type=(
                    TransactionConfidenceType.PENDING
                    if is_pending
                    else TransactionConfidenceType.UNKNOWN
                ),
                source=(
                    TransactionConfidenceSource.NETWORK  # TODO: need to add a way to keep track of ours vs others txs for validation
                    if is_pending
                    else TransactionConfidenceSource.UNKNOWN
                ),
            )

    async def broadcast_tx(self, tx: "Transaction", timeout: float = None):
        await self._electrum_network.broadcast_transaction(
            tx._electrum_transaction, timeout=timeout
        )
        self._electrum_wallet.remove_txid_from_maybe_broadcast(tx.get_tx_id())

    # TODO: needs checking
    def complete_tx(self, req: "SendRequest"):
        """
        Given a spend request containing an incomplete transaction,
        makes it valid by adding outputs and signed inputs according to the instructions in the request.
        The transaction in the request is modified by this method.
        """
        check_argument(req.coin_selector, "No coin selector provided")
        with self._lock:
            check_argument(
                not req.completed, "Given SendRequest has already been completed."
            )
            # Calculate the amount of value we need to import.
            value = 0
            for output in req.tx._electrum_transaction._outputs:
                value += output.value
            value = Coin.value_of(value)

            logger.info(
                f"Completing send tx with {len(req.tx._electrum_transaction._outputs)} outputs totalling {value.to_friendly_string()} and a fee of {req.fee_per_kb.to_friendly_string()}/vkB"
            )

            total_input = 0
            for input in req.tx._electrum_transaction._inputs:
                self._electrum_wallet.add_input_info(input)
                if input.value_sats() is not None:
                    total_input += input.value_sats()
                else:
                    logger.warning(
                        "SendRequest transaction already has inputs but we don't know how much they are worth - they will be added to fee."
                    )
            total_input = Coin.value_of(total_input)
            value = value.subtract(total_input)

            original_inputs = req.tx._electrum_transaction._inputs.copy()

            # Check for dusty sends and the OP_RETURN limit.
            if req.ensure_min_required_fee and not req.empty_wallet:
                op_return_count = 0
                for output in req.tx._electrum_transaction._outputs:
                    if TransactionOutput.is_dust(output):
                        raise DustySendRequestedException()
                    if ScriptPattern.is_op_return(Script(output.scriptpubkey)):
                        op_return_count += 1
                if op_return_count > 1:
                    # Only 1 OP_RETURN per transaction allowed.
                    raise MultipleOpReturnRequested()

            # Calculate a list of ALL potential candidates for spending and then ask a coin selector to provide us
            # with the actual outputs that'll be used to gather the required amount of value. In this way, users
            # can customize coin selection policies. The call below will ignore immature coinbases and outputs
            # we don't have the keys for.
            candidates = self.calculate_all_spend_candidates()

            best_change_output = None
            if not req.empty_wallet:
                # This can throw InsufficientMoneyException.
                fee_calculation = self._calculate_fee(
                    req, value, original_inputs, req.ensure_min_required_fee, candidates
                )
                best_coin_selection = fee_calculation.best_coin_selection
                best_change_output = fee_calculation.best_change_output
                updated_output_values = fee_calculation.updated_output_values
            else:
                # We're being asked to empty the wallet. What this means is ensuring "tx" has only a single output
                # of the total value we can currently spend as determined by the selector, and then subtracting the fee.
                check_state(
                    len(req.tx.outputs) == 1,
                    "Empty wallet TX must have a single output only.",
                )
                best_coin_selection = req.coin_selector.select(
                    self.network_params.get_max_money(), candidates
                )
                candidates = None  # Selector took ownership and might have changed candidates. Don't access again.
                req.tx.outputs[0].value = best_coin_selection.value_gathered.value
                logger.info(
                    f"  emptying {best_coin_selection.value_gathered.to_friendly_string()}"
                )

            for output in best_coin_selection.gathered:
                req.tx.add_input(output)

            if req.empty_wallet:
                base_fee = Coin.ZERO() if req.fee is None else req.fee
                fee_per_kb = Coin.ZERO() if req.fee_per_kb is None else req.fee_per_kb
                if not self._adjust_output_downwards_for_fee(
                    req.tx,
                    best_coin_selection,
                    base_fee,
                    fee_per_kb,
                    req.ensure_min_required_fee,
                ):
                    raise CouldNotAdjustDownwards()

            if updated_output_values:
                for i, updated_value in enumerate(updated_output_values):
                    req.tx._electrum_transaction._outputs[i].value = updated_value

            if best_change_output is not None:
                req.tx.add_output(best_change_output)
                logger.info(
                    f"  with {best_change_output.get_value().to_friendly_string()} change"
                )

            # Now shuffle the outputs to obfuscate which is the change.
            if req.shuffle_outputs:
                random.shuffle(req.tx._electrum_transaction._outputs)

            # Now sign the inputs, thus proving that we are entitled to redeem the connected outputs.
            if req.sign_inputs:
                # TODO: possibly wrong
                req.tx = self.sign_tx(req.password, req.tx)

            # Check size.
            size = len(req.tx.bitcoin_serialize())
            if size > 100000:  # MAX_STANDARD_TX_SIZE = 100000
                raise ExceededMaxTransactionSize()
            
            req.tx.finalize()

            calculated_fee = req.tx.get_fee()
            if calculated_fee:
                logger.info(
                    "  with a fee of {}/kB, {} for {} bytes".format(
                        calculated_fee.multiply(1000).divide(size).to_friendly_string(),
                        calculated_fee.to_friendly_string(),
                        size,
                    )
                )

            req.tx.memo = req.memo
            req.fee = calculated_fee
            req.completed = True
            logger.info(f"  completed: {req.tx}")

    def calculate_all_spend_candidates(self) -> list["TransactionOutput"]:
        """
        Returns a list of the outputs that can potentially be spent, i.e. that we have the keys for and are unspent
        according to our knowledge of the block chain.
        """
        return [
            TransactionOutput.from_utxo(utxo, self)
            for utxo in self._electrum_wallet.get_spendable_coins(confirmed_only=False)
        ]

    def sign_tx(
        self,
        password: Optional[str],
        tx: "Transaction",
    ):
        """returns partial tx if successful else None"""
        tx._electrum_transaction.add_info_from_wallet(self._electrum_wallet)
        result = self._electrum_wallet.sign_transaction(
            tx._electrum_transaction, password, ignore_warnings=True
        )
        if result:
            result.finalize_psbt()
            return tx
        return None

    def _calculate_fee(
        self,
        req: "SendRequest",
        value: "Coin",
        original_inputs: list["ElectrumPartialTxInput"],
        ensure_min_required_fee: bool,
        candidates: list["TransactionOutput"],
    ) -> "FeeCalculation":
        fee = Coin.ZERO()
        while True:
            result = FeeCalculation()
            tx = Transaction(self.network_params)
            self._add_supplied_inputs(tx, original_inputs)

            value_needed = value
            if not req.recipients_pay_fees:
                value_needed = value_needed.add(fee)

            for i, output in enumerate(req.tx._electrum_transaction._outputs):
                tx_output = TransactionOutput(
                    ElectrumTxOutput.from_network_bytes(output.serialize_to_network()),
                    tx,
                )
                if req.recipients_pay_fees:
                    # Subtract fee equally from each selected recipient
                    tx_output.value = (
                        tx_output.value
                        - fee.divide(len(req.tx._electrum_transaction._outputs)).value
                    )
                    # first receiver pays the remainder not divisible by output count
                    if i == 0:
                        # Subtract fee equally from each selected recipient
                        tx_output.value = (
                            tx_output.value
                            - fee.divide_and_remainder(
                                len(req.tx._electrum_transaction._outputs)
                            )[1].value
                        )
                    result.updated_output_values.append(Coin.value_of(tx_output.value))
                    if tx_output.get_min_non_dust_value() > tx_output.value:
                        raise CouldNotAdjustDownwards()
                tx.add_output(tx_output)

            # selector is allowed to modify candidates list
            selection = req.coin_selector.select(value_needed, candidates.copy())
            result.best_coin_selection = selection
            # Can we afford this?
            if selection.value_gathered < value_needed:
                value_missing = value_needed.subtract(selection.value_gathered)
                raise InsufficientMoneyException(value_missing)

            change = selection.value_gathered.subtract(value_needed)
            if change.is_greater_than(Coin.ZERO()):
                # The value of the inputs is greater than what we want to send. Just like in real life then,
                # we need to take back some coins ... this is called "change". Add another output that sends the change
                # back to us. The address comes either from the request or currentChangeAddress() as a default.
                change_address = req.change_address
                if not change_address:
                    change_address = (
                        self._electrum_wallet.get_single_change_address_for_new_transaction()
                    )
                    if not change_address:
                        raise IllegalStateException("No change address available")
                    change_address = Address.from_string(
                        change_address, self.network_params
                    )
                change_output = TransactionOutput.from_coin_and_address(
                    change, change_address, tx
                )
                if req.recipients_pay_fees and TransactionOutput.is_dust(change_output):
                    # We do not move dust-change to fees, because the sender would end up paying more than requested.
                    # This would be against the purpose of the all-inclusive feature.
                    # So instead we raise the change and deduct from the first recipient.
                    missing_to_not_be_dust = (
                        change_output.get_min_non_dust_value() - change_output.value
                    )
                    change_output.value = change_output.value + missing_to_not_be_dust
                    first_output = tx.outputs[0]
                    first_output.value = first_output.value - missing_to_not_be_dust
                    result.updated_output_values[0] = first_output.get_value()
                    if TransactionOutput.is_dust(first_output):
                        raise CouldNotAdjustDownwards()

                if TransactionOutput.is_dust(change_output):
                    # Never create dust outputs; if we would, just
                    # add the dust to the fee.
                    # Oscar comment: This seems like a way to make the condition below "if
                    # (!fee.isLessThan(feeNeeded))" to become true.
                    # This is a non-easy to understand way to do that.
                    # Maybe there are other effects I am missing
                    fee = fee.add(change_output.get_value())
                else:
                    tx.add_output(change_output)
                    result.best_change_output = change_output

            for selected_output in selection.gathered:
                input = tx.add_input(TransactionInput.from_output(selected_output))
                # If the scriptBytes don't default to none, our size calculations will be thrown off.
                check_state(not input.script_sig)
                check_state(not input.has_witness)

            vsize = tx.get_vsize() + self._estimate_virtual_bytes_for_signing(selection)

            base_fee_needed = Coin.ZERO() if req.fee is None else req.fee
            fee_per_kb_needed = req.fee_per_kb
            fee_needed = base_fee_needed.add(
                fee_per_kb_needed.multiply(vsize).divide(1000)
            )
            # REFERENCE_DEFAULT_MIN_TX_FEE: 1000 satoshis
            min_fee_needed = Coin.value_of(1000).multiply(vsize).divide(1000)
            if ensure_min_required_fee and fee_needed.is_less_than(min_fee_needed):
                fee_needed = min_fee_needed

            if not fee.is_less_than(fee_needed):
                # Done, enough fee included.
                break

            # Include more fee and try again.
            fee = fee_needed

        return result

    def _add_supplied_inputs(
        self, tx: "Transaction", original_inputs: list["ElectrumPartialTxInput"]
    ):
        for input in original_inputs:
            tx.add_input(TransactionInput.from_electrum_input(tx.params, input, tx))

    def _estimate_virtual_bytes_for_signing(self, selection: "CoinSelection"):
        vsize = 0
        for output in selection.gathered:
            try:
                script = output.get_script_pub_key()
                key = None
                if ScriptPattern.is_p2pkh(script):
                    key = self.find_key_from_pub_key_hash(
                        ScriptPattern.extract_hash_from_p2pkh(script), ScriptType.P2PKH
                    )
                    assert (
                        key is not None
                    ), "Coin selection includes unspendable outputs"
                    vsize += script.get_number_of_bytes_required_to_spend(key, None)
                elif ScriptPattern.is_p2wpkh(script):
                    key = self.find_key_from_pub_key_hash(
                        ScriptPattern.extract_hash_from_p2wpkh(script),
                        ScriptType.P2WPKH,
                    )
                    assert (
                        key is not None
                    ), "Coin selection includes unspendable outputs"
                    vsize += (
                        script.get_number_of_bytes_required_to_spend(key, None) + 3
                    ) // 4  # round up
                elif ScriptPattern.is_p2sh(script):
                    raise IllegalStateException("We don't support p2sh")
                else:
                    vsize += script.get_number_of_bytes_required_to_spend(key, None)
            except ScriptException as e:
                # If this happens it means an output script in a wallet tx could not be understood. That should never
                # happen, if it does it means the wallet has got into an inconsistent state.
                raise IllegalStateException(e)
        return vsize

    def _adjust_output_downwards_for_fee(
        self,
        tx: "Transaction",
        coin_selection: "CoinSelection",
        base_fee: "Coin",
        fee_per_kb: "Coin",
        ensure_min_required_fee: bool,
    ):
        REFERENCE_DEFAULT_MIN_TX_FEE = Coin.value_of(1000)
        vsize = tx.get_vsize() + self._estimate_virtual_bytes_for_signing(
            coin_selection
        )
        fee = base_fee.add(fee_per_kb.multiply(vsize).divide(1000))
        if ensure_min_required_fee and fee.is_less_than(REFERENCE_DEFAULT_MIN_TX_FEE):
            fee = REFERENCE_DEFAULT_MIN_TX_FEE
        output = tx.outputs[0]
        output.value = output.value - fee.value
        return not TransactionOutput.is_dust(output)

    def send_coins(self, send_request: "SendRequest"):
        self.complete_tx(send_request)
        self.maybe_add_transaction(send_request.tx)
        return as_future(self.broadcast_tx(send_request.tx))

    def add_electrum_info(self, tx: "Transaction"):
        tx._electrum_transaction.add_info_from_wallet(self._electrum_wallet)
        return tx

    def get_key_for_outpoint(
        self, outpoint: "TransactionOutPoint"
    ) -> Optional["DeterministicKey"]:
        connected_output = check_not_none(
            outpoint.connected_output, "Input is not connected so cannot retrieve key"
        )
        connected_script = connected_output.get_script_pub_key()
        if ScriptPattern.is_p2pkh(connected_script):
            address_bytes = ScriptPattern.extract_hash_from_p2pkh(connected_script)
            return self.find_key_from_pub_key_hash(address_bytes, ScriptType.P2PKH)
        elif ScriptPattern.is_p2wpkh(connected_script):
            address_bytes = ScriptPattern.extract_hash_from_p2wpkh(connected_script)
            return self.find_key_from_pub_key_hash(address_bytes, ScriptType.P2WPKH)
        elif ScriptPattern.is_p2pk(connected_script):
            pubkey_bytes = ScriptPattern.extract_key_from_p2pk(connected_script)
            return self.find_key_from_pub_key(pubkey_bytes, None)
        else:
            raise ScriptException(
                "Could not understand form of connected output script: "
                + str(connected_script)
            )
