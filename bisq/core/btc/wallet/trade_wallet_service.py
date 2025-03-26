from typing import TYPE_CHECKING, Iterable, Optional

from bisq.common.config.config import Config
from bisq.common.crypto.encryption import ECPrivkey
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.setup.log_setup import get_logger
from bisq.core.btc.exceptions.transaction_verification_exception import (
    TransactionVerificationException,
)
from bisq.core.btc.exceptions.wallet_exception import WalletException
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.model.inputs_and_change_output import InputsAndChangeOutput
from bisq.core.btc.model.prepared_deposit_tx_and_maker_inputs import (
    PreparedDepositTxAndMakerInputs,
)
from bisq.core.btc.setup.wallet_config import WalletConfig
from bisq.core.btc.setup.wallets_setup import WalletsSetup
from bisq.core.btc.wallet.btc_coin_selector import BtcCoinSelector
from bisq.core.btc.wallet.restrictions import Restrictions
from bisq.core.btc.wallet.tx_broadcaster import TxBroadcaster
from bisq.core.btc.wallet.wallet_service import WalletService
from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bisq.core.locale.res import Res
from bisq.core.user.preferences import Preferences
from bitcoinj.base.coin import Coin
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.core.transaction_input import TransactionInput
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_output import TransactionOutput
from bitcoinj.core.transaction_sig_hash import TransactionSigHash
from bitcoinj.core.transaction_witness import TransactionWitness
from bitcoinj.crypto.transaction_signature import TransactionSignature
from bitcoinj.script.script import Script
from bitcoinj.script.script_builder import ScriptBuilder
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.wallet.send_request import SendRequest
from bitcoinj.wallet.wallet import Wallet
from electrum_min.crypto import hash_160
from utils.preconditions import check_argument, check_not_none
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.address import Address
from bisq.core.btc.raw_transaction_input import RawTransactionInput
from electrum_min.transaction import (
    PartialTxInput as ElectrumPartialTxInput,
    TxOutpoint as ElectrumTxOutpoint,
    multisig_script,
)
from electrum_min import bitcoin


if TYPE_CHECKING:
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bisq.core.btc.wallet.tx_broadcaster_callback import TxBroadcasterCallback


logger = get_logger(__name__)


# TODO
class TradeWalletService:
    MIN_DELAYED_PAYOUT_TX_FEE = Coin.value_of(1000)

    def __init__(self, wallets_setup: "WalletsSetup", preferences: "Preferences"):
        self._wallets_setup = wallets_setup
        self._preferences = preferences
        self._wallet_config: Optional["WalletConfig"] = None
        self._wallet: Optional["Wallet"] = None
        self._password: Optional[str] = None

        self._wallets_setup.add_setup_completed_handler(
            lambda: (
                setattr(self, "_wallet_config", self._wallets_setup.wallet_config),
                setattr(self, "_wallet", self._wallets_setup.btc_wallet),
            )
        )

    @property
    def params(self):
        return Config.BASE_CURRENCY_NETWORK_VALUE.parameters

    def set_password(self, password: str):
        self._password = password

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Trade fee
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_btc_trading_fee_tx(
        self,
        funding_address: "Address",
        reserved_for_trade_address: "Address",
        change_address: "Address",
        reserved_funds_for_offer: Coin,
        use_savings_wallet: bool,
        trading_fee: Coin,
        tx_fee: Coin,
        fee_receiver_address: str,
        do_broadcast: bool,
        callback: "TxBroadcasterCallback",
    ) -> "Transaction":
        trading_fee_tx = Transaction(self.params)
        send_request = None
        try:
            trading_fee_tx.add_output(
                TransactionOutput.from_coin_and_address(
                    trading_fee,
                    Address.from_string(fee_receiver_address, self.params),
                    trading_fee_tx,
                )
            )
            # the reserved amount we need for the trade we send to our trade reservedForTradeAddress
            trading_fee_tx.add_output(
                TransactionOutput.from_coin_and_address(
                    reserved_funds_for_offer,
                    reserved_for_trade_address,
                    trading_fee_tx,
                )
            )

            # we allow spending of unconfirmed tx (double spend risk is low and usability would suffer if we need to
            # wait for 1 confirmation)
            # In case of double spend we will detect later in the trade process and use a ban score to penalize bad behaviour (not impl. yet)
            send_request = SendRequest.for_tx(trading_fee_tx)
            send_request.shuffle_outputs = False
            send_request.password = self._password
            if use_savings_wallet:
                send_request.coin_selector = BtcCoinSelector(
                    self._wallets_setup.get_addresses_by_context(
                        AddressEntryContext.AVAILABLE
                    ),
                    self._preferences.get_ignore_dust_threshold(),
                )
            else:
                send_request.coin_selector = BtcCoinSelector(
                    funding_address,
                    self._preferences.get_ignore_dust_threshold(),
                )
            # We use a fixed fee
            send_request.fee = tx_fee
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False

            # Change is optional in case of overpay or use of funds from savings wallet
            send_request.change_address = change_address

            check_not_none(self._wallet, "Wallet must not be None")
            self._wallet.complete_tx(send_request)

            if self._remove_dust(trading_fee_tx):
                # TODO check if works as expected
                trading_fee_tx = check_not_none(
                    self._wallet.sign_tx(self._password, trading_fee_tx),
                    "Failed to sign trading_fee_tx",
                )

            WalletService.print_tx("trading_fee_tx", trading_fee_tx)

            if do_broadcast and callback:
                self.broadcast_tx(trading_fee_tx, callback)

            return trading_fee_tx
        except Exception as e:
            if self._wallet and send_request and send_request.coin_selector:
                logger.error(
                    f"Balance for coin selector at create_btc_trading_fee_tx = {self._wallet.get_coin_selector_balance(send_request.coin_selector).to_friendly_string()}"
                )
            logger.error(
                f"create_btc_trading_fee_tx failed: trading_fee_tx={trading_fee_tx}, tx_outputs={trading_fee_tx.outputs}"
            )
            raise e

    def complete_bsq_trading_fee_tx(
        self,
        prepared_bsq_tx: "Transaction",
        funding_address: "Address",
        reserved_for_trade_address: "Address",
        change_address: "Address",
        reserved_funds_for_offer: Coin,
        use_savings_wallet: bool,
        tx_fee: Coin,
    ) -> "Transaction":
        try:
            # preparedBsqTx has following structure:
            # inputs [1-n] BSQ inputs
            # outputs [0-1] BSQ change output
            # mining fee: burned BSQ fee

            # We add BTC mining fee. Result tx looks like:
            # inputs [1-n] BSQ inputs
            # inputs [1-n] BTC inputs
            # outputs [0-1] BSQ change output
            # outputs [1] BTC reservedForTrade output
            # outputs [0-1] BTC change output
            # mining fee: BTC mining fee + burned BSQ fee

            # In case all BSQ were burnt as fees we have no receiver output and it might be that there are no change outputs
            # We need to guarantee that min. 1 valid output is added (OP_RETURN does not count). So we use a higher input
            # for BTC to force an additional change output.

            prepared_bsq_tx_inputs_size = len(prepared_bsq_tx.inputs)
            has_bsq_outputs = len(prepared_bsq_tx.outputs) > 0

            # If there are no BSQ change outputs, an output larger than the burnt BSQ amount has to be added as the first
            # output to make sure the reserved funds are in output 1. Deposit tx input creation depends on the reserve
            # being output 1. The amount has to be larger than the BSQ input to ensure the inputs get burnt.
            # The BTC change_address is used, so it might get used for both output 0 and output 2.
            if not has_bsq_outputs:
                bsq_input_value = Coin.value_of(
                    sum(
                        (tx_input.value for tx_input in prepared_bsq_tx.inputs),
                        0,
                    )
                )
                prepared_bsq_tx.add_output(
                    TransactionOutput.from_coin_and_address(
                        bsq_input_value.add(Coin.value_of(1)),
                        change_address,
                        prepared_bsq_tx,
                    )
                )

            # The reserved amount we need for the trade we send to our trade reserved_for_trade_address
            prepared_bsq_tx.add_output(
                reserved_funds_for_offer, reserved_for_trade_address
            )

            # We allow spending of unconfirmed tx (double spend risk is low and usability would suffer if we need to
            # wait for 1 confirmation).
            # In case of double spend, we will detect later in the trade process and use a ban score to penalize bad behavior (not implemented yet). (JAVA TODO?)

            send_request = SendRequest.for_tx(prepared_bsq_tx)
            send_request.shuffle_outputs = False
            send_request.password = self._password

            if use_savings_wallet:
                send_request.coin_selector = BtcCoinSelector(
                    self._wallets_setup.get_addresses_by_context(
                        AddressEntryContext.AVAILABLE
                    ),
                    self._preferences.get_ignore_dust_threshold(),
                )
            else:
                send_request.coin_selector = BtcCoinSelector(
                    funding_address,
                    self._preferences.get_ignore_dust_threshold(),
                )

            # We use a fixed fee
            send_request.fee = tx_fee
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False

            send_request.sign_inputs = False

            # Change is optional in case of overpay or use of funds from savings wallet
            send_request.change_address = change_address

            check_not_none(self._wallet, "Wallet must not be None")
            self._wallet.complete_tx(send_request)
            result_tx = send_request.tx
            self._remove_dust(result_tx)

            # Sign all BTC inputs # TODO check if works as expected
            result_tx = check_not_none(
                self._wallet.sign_tx(self._password, result_tx),
                "Failed to sign tx at complete_bsq_trading_fee_tx",
            )
            for i in range(prepared_bsq_tx_inputs_size, len(result_tx.inputs)):
                tx_input = result_tx.inputs[i]
                check_argument(
                    tx_input.connected_output is not None
                    and tx_input.connected_output.is_for_wallet(self._wallet),
                    "tx_input.connected_output is not in our wallet. That must not happen.",
                )
                WalletService.check_script_sig(result_tx, tx_input, i)

            WalletService.check_wallet_consistency(self._wallet)
            WalletService.verify_transaction(result_tx)

            WalletService.print_tx(
                f"{Res.base_currency_code} wallet: Signed tx", result_tx
            )
            return result_tx
        except Exception as e:
            logger.error(
                f"complete_bsq_trading_fee_tx errored: prepared_bsq_tx={prepared_bsq_tx}"
            )
            raise e

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Deposit tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def taker_creates_deposit_tx_inputs(
        self,
        take_offer_fee_tx: "Transaction",
        input_amount: Coin,
        tx_fee: Coin,
    ) -> "InputsAndChangeOutput":
        # We add the mining fee 2 times to the deposit tx:
        # 1. Will be spent when publishing the deposit tx (paid by buyer)
        # 2. Will be added to the MS amount, so when publishing the payout tx the fee is already there and the outputs are not changed by fee reduction
        # The fee for the payout will be paid by the seller.

        """
        The tx we create has that structure:

            IN[0]  input from taker fee tx > inputAmount (including tx fee) (unsigned)
            OUT[0] dummyOutputAmount (inputAmount - tx fee)

            We are only interested in the inputs.
            We get the exact input value from the taker fee tx so we don't create a change output.
        """

        # inputAmount includes the tx fee. So we subtract the fee to get the dummyOutputAmount.
        dummy_output_amount = input_amount.subtract(tx_fee)

        dummy_tx = Transaction(self.params)
        # The output is just used to get the right inputs and change outputs, so we use an anonymous ECKey, as it will never be used for anything.
        # We don't care about fee calculation differences between the real tx and that dummy tx as we use a static tx fee.
        dummy_address = SegwitAddress.from_key(
            ECPrivkey.generate_random_key(), self.params
        )
        dummy_output = TransactionOutput.from_coin_and_address(
            dummy_output_amount, dummy_address, dummy_tx
        )
        dummy_tx.add_output(dummy_output)

        # Find the needed inputs to pay the output, optionally add 1 change output.
        # Normally only 1 input and no change output is used, but we support multiple inputs and 1 change output.
        # Our spending transaction output is from the create offer fee payment.

        # We created the take offer fee tx in the structure that the second output is for the funds for the deposit tx.
        reserved_for_trade_output = take_offer_fee_tx.outputs[1]
        check_argument(
            reserved_for_trade_output.get_value() == input_amount,
            "Reserve amount does not equal input amount",
        )
        dummy_tx.add_input(reserved_for_trade_output)

        WalletService.verify_transaction(dummy_tx)

        # WalletService.print_tx("dummyTx", dummy_tx)

        raw_transaction_input_list = [
            self._get_raw_input_from_transaction_input(tx_input)
            for tx_input in dummy_tx.inputs
            if check_not_none(
                tx_input.connected_output, "tx_input.connected_output must not be None"
            )
            and check_not_none(
                tx_input.connected_output.parent,
                "tx_input.connected_output.parent must not be None",
            )
            and check_not_none(
                tx_input.get_value(), "tx_input.get_value() must not be None"
            )
        ]

        # JAVA TODO changeOutputValue and changeOutputAddress is not used as taker spends exact amount from fee tx.
        # Change is handled already at the fee tx creation so the handling of a change output for the deposit tx
        # can be removed here. We still keep it atm as we prefer to not introduce a larger
        # refactoring. When new trade protocol gets implemented this can be cleaned.
        # The maker though can have a change output if the taker takes less as the max. offer amount!
        return InputsAndChangeOutput(raw_transaction_input_list, 0, None)

    def seller_as_maker_creates_deposit_tx(
        self,
        maker_input_amount: Coin,
        ms_output_amount: Coin,
        taker_raw_transaction_inputs: list["RawTransactionInput"],
        taker_change_output_value: int,
        taker_change_address_string: Optional[str],
        maker_address: "Address",
        maker_change_address: "Address",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "PreparedDepositTxAndMakerInputs":
        return self._maker_creates_deposit_tx(
            maker_is_buyer=False,
            maker_input_amount=maker_input_amount,
            ms_output_amount=ms_output_amount,
            taker_raw_transaction_inputs=taker_raw_transaction_inputs,
            taker_change_output_value=taker_change_output_value,
            taker_change_address_string=taker_change_address_string,
            maker_address=maker_address,
            maker_change_address=maker_change_address,
            buyer_pub_key=buyer_pub_key,
            seller_pub_key=seller_pub_key,
        )

    def buyer_as_maker_creates_and_signs_deposit_tx(
        self,
        maker_input_amount: Coin,
        ms_output_amount: Coin,
        taker_raw_transaction_inputs: list["RawTransactionInput"],
        taker_change_output_value: int,
        taker_change_address_string: Optional[str],
        maker_address: "Address",
        maker_change_address: "Address",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "PreparedDepositTxAndMakerInputs":
        return self._maker_creates_deposit_tx(
            maker_is_buyer=True,
            maker_input_amount=maker_input_amount,
            ms_output_amount=ms_output_amount,
            taker_raw_transaction_inputs=taker_raw_transaction_inputs,
            taker_change_output_value=taker_change_output_value,
            taker_change_address_string=taker_change_address_string,
            maker_address=maker_address,
            maker_change_address=maker_change_address,
            buyer_pub_key=buyer_pub_key,
            seller_pub_key=seller_pub_key,
        )

    def _maker_creates_deposit_tx(
        self,
        maker_is_buyer: bool,
        maker_input_amount: Coin,
        ms_output_amount: Coin,
        taker_raw_transaction_inputs: list["RawTransactionInput"],
        taker_change_output_value: int,
        taker_change_address_string: Optional[str],
        maker_address: "Address",
        maker_change_address: "Address",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "PreparedDepositTxAndMakerInputs":
        check_argument(
            taker_raw_transaction_inputs,
            "taker_raw_transaction_inputs must not be empty",
        )

        # First we construct a dummy TX to get the inputs and outputs we want to use for the real deposit tx.
        # Similar to the way we did in the taker_creates_deposit_tx_inputs method.
        dummy_tx = Transaction(self.params)
        # The output is just used to get the right inputs and change outputs, so we use an anonymous ECKey, as it will never be used for anything.
        # We don't care about fee calculation differences between the real tx and that dummy tx as we use a static tx fee.
        dummy_address = SegwitAddress.from_key(
            ECPrivkey.generate_random_key(), self.params
        )
        dummy_output = TransactionOutput.from_coin_and_address(
            maker_input_amount, dummy_address, dummy_tx
        )
        dummy_tx.add_output(dummy_output)
        self._add_available_inputs_and_change_outputs(
            dummy_tx, maker_address, maker_change_address
        )
        # Normally we have only 1 input but we support multiple inputs if the user has paid in with several transactions.
        maker_inputs = dummy_tx.inputs
        maker_output = None

        # We don't support more than 1 optional change output
        check_argument(len(dummy_tx.outputs) < 3, "len(dummy_tx.outputs) >= 3")

        # Only save change outputs, the dummy output is ignored (that's why we start with index 1)
        if len(dummy_tx.outputs) > 1:
            maker_output = dummy_tx.outputs[1]

        # Now we construct the real deposit tx
        prepared_deposit_tx = Transaction(self.params)

        maker_raw_transaction_inputs = []
        if maker_is_buyer:
            # Add buyer inputs
            for input in maker_inputs:
                prepared_deposit_tx.add_input(input)
                maker_raw_transaction_inputs.append(
                    self._get_raw_input_from_transaction_input(input)
                )

            # Add seller inputs
            # The seller's input is not signed, so we attach empty script bytes
            for raw_transaction_input in taker_raw_transaction_inputs:
                prepared_deposit_tx.add_input(
                    self._get_transaction_input(
                        prepared_deposit_tx, None, raw_transaction_input
                    )
                )
        else:
            # Taker is buyer role

            # Add buyer inputs
            # The seller's input is not signed, so we attach empty script bytes
            for raw_transaction_input in taker_raw_transaction_inputs:
                prepared_deposit_tx.add_input(
                    self._get_transaction_input(
                        prepared_deposit_tx, None, raw_transaction_input
                    )
                )

            # Add seller inputs
            for input in maker_inputs:
                prepared_deposit_tx.add_input(input)
                maker_raw_transaction_inputs.append(
                    self._get_raw_input_from_transaction_input(input)
                )

        # Add MultiSig output
        multisig_script_bytes = self._get_x_of_threshold_multi_sig_output_script(
            (seller_pub_key, buyer_pub_key), 2, False
        )

        # Tx fee for deposit tx will be paid by buyer.
        hashed_multi_sig_output = TransactionOutput.from_coin_and_script(
            ms_output_amount,
            multisig_script_bytes,
            prepared_deposit_tx,
        )
        prepared_deposit_tx.add_output(hashed_multi_sig_output)

        taker_transaction_output = None
        if taker_change_output_value > 0 and taker_change_address_string is not None:
            taker_transaction_output = TransactionOutput.from_coin_and_address(
                Coin.value_of(taker_change_output_value),
                Address.from_string(taker_change_address_string, self.params),
                prepared_deposit_tx,
            )

        if maker_is_buyer:
            # Add optional buyer outputs
            if maker_output:
                prepared_deposit_tx.add_output(maker_output)

            # Add optional seller outputs
            if taker_transaction_output:
                prepared_deposit_tx.add_output(taker_transaction_output)
        else:
            # Taker is buyer role

            # Add optional seller outputs
            if taker_transaction_output:
                prepared_deposit_tx.add_output(taker_transaction_output)

            # Add optional buyer outputs
            if maker_output:
                prepared_deposit_tx.add_output(maker_output)

        start = 0 if maker_is_buyer else len(taker_raw_transaction_inputs)
        end = len(maker_inputs) if maker_is_buyer else len(prepared_deposit_tx.inputs)
        # TODO: check sign
        prepared_deposit_tx = check_not_none(
            self._wallet.sign_tx(self._password, prepared_deposit_tx),
            "Failed to sign prepared_deposit_tx",
        )
        for i in range(start, end):
            tx_input = prepared_deposit_tx.inputs[i]
            WalletService.check_script_sig(prepared_deposit_tx, tx_input, i)

        # TODO: FIXME: hack
        prepared_deposit_tx.version = 1

        WalletService.print_tx("maker_creates_deposit_tx", prepared_deposit_tx)
        WalletService.verify_transaction(prepared_deposit_tx)

        return PreparedDepositTxAndMakerInputs(
            raw_maker_inputs=maker_raw_transaction_inputs,
            deposit_transaction=prepared_deposit_tx.bitcoin_serialize(),
        )

    def taker_signs_deposit_tx(
        self,
        taker_is_seller: bool,
        makers_deposit_tx_serialized: bytes,
        ms_output_amount: Coin,
        buyer_inputs: list["RawTransactionInput"],
        seller_inputs: list["RawTransactionInput"],
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "Transaction":
        makers_deposit_tx = Transaction(self.params, makers_deposit_tx_serialized)

        check_argument(buyer_inputs, "buyer_inputs must not be empty")
        check_argument(seller_inputs, "seller_inputs must not be empty")

        # Check if maker's MultiSig script is identical to the taker's
        hashed_multi_sig_output_script = (
            self._get_x_of_threshold_multi_sig_output_script(
                (seller_pub_key, buyer_pub_key), 2, False
            )
        )
        if (
            makers_deposit_tx.outputs[0].script_pub_key
            != hashed_multi_sig_output_script
        ):
            raise TransactionVerificationException(
                "Maker's hashed_multi_sig_output_script does not match taker's hashed_multi_sig_output_script"
            )

        # Check if maker's MultiSig output value is identical to the taker's
        if not makers_deposit_tx.outputs[0].get_value() == ms_output_amount:
            raise TransactionVerificationException(
                "Maker's MultiSig output amount does not match taker's MultiSig output amount"
            )

        # The outpoints are not available from the serialized makers_deposit_tx, so we cannot use that tx directly, but we use it to construct a new deposit_tx
        deposit_tx = Transaction(self.params)

        if taker_is_seller:
            # Add buyer inputs and apply signature
            # We grab the signature from the makersDepositTx and apply it to the new tx input
            for i, buyer_input in enumerate(buyer_inputs):
                makers_input = makers_deposit_tx.inputs[i]
                makers_script_sig_program = makers_input.script_sig
                input = self._get_transaction_input(
                    deposit_tx, makers_script_sig_program, buyer_input
                )
                script_pub_key = check_not_none(
                    input.connected_output
                ).get_script_pub_key()
                if len(makers_script_sig_program) == 0 and not ScriptPattern.is_p2wh(
                    script_pub_key
                ):
                    raise TransactionVerificationException(
                        "Non-segwit inputs from maker not signed."
                    )
                if makers_input.witness:
                    input.witness = makers_input.witness
                deposit_tx.add_input(input)

            # Add seller inputs
            for seller_input in seller_inputs:
                deposit_tx.add_input(
                    self._get_transaction_input(deposit_tx, None, seller_input)
                )
        else:
            # Taker is buyer
            # Add buyer inputs
            for buyer_input in buyer_inputs:
                deposit_tx.add_input(
                    self._get_transaction_input(deposit_tx, None, buyer_input)
                )

            # Add seller inputs
            # We grab the signature from the makersDepositTx and apply it to the new tx input
            for i, k in zip(
                range(len(buyer_inputs), len(makers_deposit_tx.inputs)),
                range(len(makers_deposit_tx.inputs) - len(buyer_inputs)),
            ):
                # We get the deposit tx unsigned if maker is seller
                deposit_tx.add_input(
                    self._get_transaction_input(deposit_tx, None, seller_inputs[k])
                )

        # Add all outputs from makers_deposit_tx to deposit_tx
        for output in makers_deposit_tx.outputs:
            deposit_tx.add_output(output)

        WalletService.print_tx("makersDepositTx", makers_deposit_tx)

        # Sign inputs
        start = len(buyer_inputs) if taker_is_seller else 0
        end = len(deposit_tx.inputs) if taker_is_seller else len(buyer_inputs)
        deposit_tx = check_not_none(
            self._wallet.sign_tx(self._password, deposit_tx),
            "Failed to sign deposit_tx",
        )
        for i in range(start, end):
            WalletService.check_script_sig(deposit_tx, deposit_tx.inputs[i], i)

        WalletService.print_tx("takerSignsDepositTx", deposit_tx)

        WalletService.verify_transaction(deposit_tx)
        WalletService.check_wallet_consistency(self._wallet)

        return deposit_tx

    def seller_as_maker_finalizes_deposit_tx(
        self,
        my_deposit_tx: "Transaction",
        takers_deposit_tx: "Transaction",
        num_takers_inputs: int,
    ) -> None:
        # We add takers signature from his inputs and add it to out tx which was already signed earlier.
        for i in range(num_takers_inputs):
            takers_input = takers_deposit_tx.inputs[i]
            takers_script_sig = takers_input.script_sig
            tx_input = my_deposit_tx.inputs[i]
            tx_input.script_sig = takers_script_sig
            if takers_input.witness:
                tx_input.witness = takers_input.witness

        WalletService.print_tx("seller_as_maker_finalizes_deposit_tx", my_deposit_tx)
        WalletService.verify_transaction(my_deposit_tx)

    def seller_adds_buyer_witnesses_to_deposit_tx(
        self,
        my_deposit_tx: "Transaction",
        buyers_deposit_tx_with_witness: "Transaction",
    ) -> None:
        number_inputs = len(my_deposit_tx.inputs)
        for i in range(number_inputs):
            tx_input = my_deposit_tx.inputs[i]
            witness_from_buyer = buyers_deposit_tx_with_witness.inputs[i].witness

            if not tx_input.witness and witness_from_buyer:
                tx_input.witness = witness_from_buyer

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Delayed payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def create_delayed_unsigned_payout_tx(
        self,
        deposit_tx: "Transaction",
        receivers: list[tuple[int, str]],
        lock_time: int,
    ) -> "Transaction":
        deposit_tx_output = deposit_tx.outputs[0]
        delayed_payout_tx = Transaction(self.params)
        delayed_payout_tx.add_input(deposit_tx_output)
        self._apply_lock_time(lock_time, delayed_payout_tx)
        check_argument(receivers, "receivers must not be empty")
        for receiver in receivers:
            delayed_payout_tx.add_output(
                TransactionOutput.from_coin_and_address(
                    Coin.value_of(receiver[0]),
                    Address.from_string(receiver[1], self.params),
                    delayed_payout_tx,
                )
            )
        # TODO: FIXME: hack
        delayed_payout_tx.version = 1
        WalletService.print_tx(
            "Unsigned delayedPayoutTx ToDonationAddress", delayed_payout_tx
        )
        WalletService.verify_transaction(delayed_payout_tx)
        return delayed_payout_tx

    def sign_delayed_payout_tx(
        self,
        delayed_payout_tx: "Transaction",
        prepared_deposit_tx: "Transaction",
        my_multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> bytes:
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            (seller_pub_key, buyer_pub_key), 2
        )
        delayed_payout_tx_input_value = prepared_deposit_tx.outputs[0].get_value()
        sig_hash = delayed_payout_tx.hash_for_witness_signature(
            0,
            redeem_script,
            delayed_payout_tx_input_value,
            TransactionSigHash.ALL,
            False,
        )
        check_not_none(my_multi_sig_key_pair, "my_multi_sig_key_pair must not be None")
        # LowRSigningKey is enabled in electrum_ecc by default
        my_signature = my_multi_sig_key_pair.ecdsa_sign(sig_hash, self._password)
        WalletService.print_tx("delayedPayoutTx for sig creation", delayed_payout_tx)
        WalletService.verify_transaction(delayed_payout_tx)
        return my_signature

    def finalize_unconnected_delayed_payout_tx(
        self,
        delayed_payout_tx: "Transaction",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
        buyer_signature: bytes,
        seller_signature: bytes,
        input_value: Coin,
    ) -> "Transaction":
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            (seller_pub_key, buyer_pub_key), 2
        )
        buyer_tx_signature = TransactionSignature.decode_from_der(
            buyer_signature, TransactionSigHash.ALL, False
        )
        seller_tx_signature = TransactionSignature.decode_from_der(
            seller_signature, TransactionSigHash.ALL, False
        )
        witness = TransactionWitness.redeem_p2wsh(
            redeem_script, seller_tx_signature, buyer_tx_signature
        ).construct_witness()
        input = delayed_payout_tx.inputs[0]
        input.script_sig = b""
        input.witness = witness

        WalletService.print_tx("finalizeDelayedPayoutTx", delayed_payout_tx)
        WalletService.verify_transaction(delayed_payout_tx)

        if check_not_none(input_value).is_less_than(
            delayed_payout_tx.get_output_sum().add(
                TradeWalletService.MIN_DELAYED_PAYOUT_TX_FEE
            )
        ):
            raise TransactionVerificationException(
                "Delayed payout tx is paying less than the minimum allowed tx fee"
            )

        script_pub_key = self._get_x_of_threshold_multi_sig_output_script(
            (seller_pub_key, buyer_pub_key), 2, False
        )
        input.get_script_sig().correctly_spends(
            delayed_payout_tx,
            0,
            input.witness_elements,
            input_value,
            script_pub_key,
            Script.ALL_VERIFY_FLAGS,
        )
        return delayed_payout_tx

    def finalize_delayed_payout_tx(
        self,
        delayed_payout_tx: "Transaction",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
        buyer_signature: bytes,
        seller_signature: bytes,
    ) -> "Transaction":
        input = delayed_payout_tx.inputs[0]
        self.finalize_unconnected_delayed_payout_tx(
            delayed_payout_tx,
            buyer_pub_key,
            seller_pub_key,
            buyer_signature,
            seller_signature,
            input.get_value(),
        )

        WalletService.check_wallet_consistency(self._wallet)
        assert (
            input.connected_output is not None
        ), "input.connected_output must not be None"
        input.verify(input.connected_output)
        return delayed_payout_tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Standard payout tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def buyer_signs_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_payout_address_string: str,
        seller_payout_address_string: str,
        multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> bytes:
        prepared_payout_tx = self._create_payout_tx(
            deposit_tx,
            buyer_payout_amount,
            seller_payout_amount,
            buyer_payout_address_string,
            seller_payout_address_string,
        )

        # MultiSig redeem script
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            (seller_pub_key, buyer_pub_key), 2
        )

        # MultiSig output from previous transaction is at index 0
        hashed_multi_sig_output = deposit_tx.outputs[0]
        if ScriptPattern.is_p2sh(hashed_multi_sig_output.get_script_pub_key()):
            sig_hash = prepared_payout_tx.hash_for_signature(
                0, redeem_script, TransactionSigHash.ALL, False
            )
        else:
            input_value = hashed_multi_sig_output.get_value()
            sig_hash = prepared_payout_tx.hash_for_witness_signature(
                0, redeem_script, input_value, TransactionSigHash.ALL, False
            )

        check_not_none(multi_sig_key_pair, "multi_sig_key_pair must not be None")
        buyer_signature = multi_sig_key_pair.ecdsa_sign(sig_hash, self._password)

        WalletService.print_tx("prepared payoutTx", prepared_payout_tx)
        WalletService.verify_transaction(prepared_payout_tx)

        return buyer_signature

    def seller_signs_and_finalizes_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_signature: bytes,
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_payout_address_string: str,
        seller_payout_address_string: str,
        multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "Transaction":
        payout_tx = self._create_payout_tx(
            deposit_tx,
            buyer_payout_amount,
            seller_payout_amount,
            buyer_payout_address_string,
            seller_payout_address_string,
        )

        # MultiSig redeem script
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            (seller_pub_key, buyer_pub_key), 2
        )

        # MultiSig output from previous transaction is at index 0
        hashed_multi_sig_output = deposit_tx.outputs[0]
        hashed_multi_sig_output_is_legacy = ScriptPattern.is_p2sh(
            hashed_multi_sig_output.get_script_pub_key()
        )

        if hashed_multi_sig_output_is_legacy:
            sig_hash = payout_tx.hash_for_signature(
                0, redeem_script, TransactionSigHash.ALL, False
            )
        else:
            input_value = hashed_multi_sig_output.get_value()
            sig_hash = payout_tx.hash_for_witness_signature(
                0, redeem_script, input_value, TransactionSigHash.ALL, False
            )

        check_not_none(multi_sig_key_pair, "multi_sig_key_pair must not be None")
        seller_signature = multi_sig_key_pair.ecdsa_sign(sig_hash, self._password)

        buyer_tx_signature = TransactionSignature.decode_from_der(
            buyer_signature, TransactionSigHash.ALL, False
        )
        seller_tx_signature = TransactionSignature.decode_from_der(
            seller_signature, TransactionSigHash.ALL, False
        )

        # Take care of order of signatures. Need to be reversed here.
        input = payout_tx.inputs[0]
        if hashed_multi_sig_output_is_legacy:
            # TODO
            raise IllegalStateException(
                "We don't support legacy multi sig output at the moment"
            )
        else:
            input.script_sig = b""
            witness = TransactionWitness.redeem_p2wsh(
                redeem_script, seller_tx_signature, buyer_tx_signature
            ).construct_witness()
            input.witness = witness

        WalletService.print_tx("payout_tx", payout_tx)
        WalletService.verify_transaction(payout_tx)
        WalletService.check_wallet_consistency(self._wallet)
        WalletService.check_script_sig(payout_tx, input, 0)
        check_not_none(
            input.connected_output, "input.connected_output must not be None"
        )
        input.verify(input.connected_output)

        return payout_tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Mediated payoutTx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def sign_mediated_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_payout_address_string: str,
        seller_payout_address_string: str,
        my_multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
    ) -> "bytes":
        prepared_payout_tx = self._create_payout_tx(
            deposit_tx,
            buyer_payout_amount,
            seller_payout_amount,
            buyer_payout_address_string,
            seller_payout_address_string,
        )

        # MultiSig redeem script
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            (seller_pub_key, buyer_pub_key), 2
        )

        # MultiSig output from previous transaction is at index 0
        hashed_multi_sig_output = deposit_tx.outputs[0]
        hashed_multi_sig_output_is_legacy = ScriptPattern.is_p2sh(
            hashed_multi_sig_output.get_script_pub_key()
        )

        if hashed_multi_sig_output_is_legacy:
            sig_hash = prepared_payout_tx.hash_for_signature(
                0, redeem_script, TransactionSigHash.ALL, False
            )
        else:
            input_value = hashed_multi_sig_output.get_value()
            sig_hash = prepared_payout_tx.hash_for_witness_signature(
                0, redeem_script, input_value, TransactionSigHash.ALL, False
            )

        check_not_none(my_multi_sig_key_pair, "my_multi_sig_key_pair must not be None")
        my_signature = my_multi_sig_key_pair.ecdsa_sign(sig_hash, self._password)

        WalletService.print_tx(
            "prepared mediated payoutTx for sig creation", prepared_payout_tx
        )
        WalletService.verify_transaction(prepared_payout_tx)

        return my_signature

    def finalize_mediated_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_signature: bytes,
        seller_signature: bytes,
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_payout_address: str,
        seller_payout_address: str,
        multi_sig_key_pair: "DeterministicKey",
        buyer_multi_sig_pub_key: bytes,
        seller_multi_sig_pub_key: bytes,
    ) -> "Transaction":
        payout_tx = self._create_payout_tx(
            deposit_tx,
            buyer_payout_amount,
            seller_payout_amount,
            buyer_payout_address,
            seller_payout_address,
        )

        # MultiSig redeem script
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            (seller_multi_sig_pub_key, buyer_multi_sig_pub_key), 2
        )

        # MultiSig output from previous transaction is at index 0
        hashed_multi_sig_output = deposit_tx.outputs[0]
        hashed_multi_sig_output_is_legacy = ScriptPattern.is_p2sh(
            hashed_multi_sig_output.get_script_pub_key()
        )

        check_not_none(multi_sig_key_pair, "multi_sig_key_pair must not be None")

        buyer_tx_signature = TransactionSignature.decode_from_der(
            buyer_signature, TransactionSigHash.ALL, False
        )
        seller_tx_signature = TransactionSignature.decode_from_der(
            seller_signature, TransactionSigHash.ALL, False
        )

        # Take care of order of signatures. Need to be reversed here.
        input = payout_tx.inputs[0]
        if hashed_multi_sig_output_is_legacy:
            # TODO
            raise IllegalStateException(
                "We don't support legacy multi sig output at the moment"
            )
        else:
            input.script_sig = b""
            witness = TransactionWitness.redeem_p2wsh(
                redeem_script, seller_tx_signature, buyer_tx_signature
            ).construct_witness()
            input.witness = witness

        WalletService.print_tx("mediated payoutTx", payout_tx)
        WalletService.verify_transaction(payout_tx)
        WalletService.check_wallet_consistency(self._wallet)
        WalletService.check_script_sig(payout_tx, input, 0)
        check_not_none(
            input.connected_output, "input.connected_output must not be None"
        )
        input.verify(input.connected_output)

        return payout_tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Arbitrated payoutTx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def trader_sign_and_finalize_disputed_payout_tx(
        self,
        deposit_tx_serialized: bytes,
        arbitrator_signature: bytes,
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_address_string: str,
        seller_address_string: str,
        traders_multi_sig_key_pair: "DeterministicKey",
        buyer_pub_key: bytes,
        seller_pub_key: bytes,
        arbitrator_pub_key: bytes,
    ) -> "Transaction":
        deposit_tx = Transaction(self.params, deposit_tx_serialized)
        hashed_multi_sig_output = deposit_tx.outputs[0]
        payout_tx = Transaction(self.params)
        payout_tx.add_input(hashed_multi_sig_output)

        if buyer_payout_amount.is_positive():
            payout_tx.add_output(
                TransactionOutput.from_coin_and_address(
                    buyer_payout_amount,
                    Address.from_string(buyer_address_string, self.params),
                    payout_tx,
                )
            )

        if seller_payout_amount.is_positive():
            payout_tx.add_output(
                TransactionOutput.from_coin_and_address(
                    seller_payout_amount,
                    Address.from_string(seller_address_string, self.params),
                    payout_tx,
                )
            )

        # order of sigs matter
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            (arbitrator_pub_key, seller_pub_key, buyer_pub_key), 2
        )
        hashed_multi_sig_output_is_legacy = ScriptPattern.is_p2sh(
            hashed_multi_sig_output.get_script_pub_key()
        )

        if hashed_multi_sig_output_is_legacy:
            sig_hash = payout_tx.hash_for_signature(
                0, redeem_script, TransactionSigHash.ALL, False
            )
        else:
            input_value = hashed_multi_sig_output.get_value()
            sig_hash = payout_tx.hash_for_witness_signature(
                0, redeem_script, input_value, TransactionSigHash.ALL, False
            )

        check_not_none(
            traders_multi_sig_key_pair, "traders_multi_sig_key_pair must not be None"
        )
        # LowRSigningKey is enabled in electrum_ecc by default
        traders_signature = traders_multi_sig_key_pair.ecdsa_sign(
            sig_hash, self._password
        )

        input = payout_tx.inputs[0]
        # order of signatures matters: arbitrator, seller, buyer
        if hashed_multi_sig_output_is_legacy:
            raise IllegalStateException(
                "We don't support legacy multi sig output at the moment"
            )
        else:
            input.script_sig = b""
            witness = TransactionWitness.redeem_p2wsh(
                redeem_script, arbitrator_signature, traders_signature
            ).construct_witness()
            input.witness = witness

        WalletService.print_tx("disputed payoutTx", payout_tx)
        WalletService.verify_transaction(payout_tx)
        WalletService.check_wallet_consistency(self._wallet)
        WalletService.check_script_sig(payout_tx, input, 0)
        check_not_none(
            input.connected_output, "input.connected_output must not be None"
        )
        input.verify(input.connected_output)

        return payout_tx

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Emergency payoutTx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // BsqSwap tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Broadcast tx
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def broadcast_tx(
        self,
        tx: "Transaction",
        callback: "TxBroadcasterCallback",
        timeout_sec: Optional[int] = None,
    ) -> None:
        check_not_none(
            self._wallet_config,
            "WalletConfig must not be None at TradeWalletService.broadcast_tx",
        )
        TxBroadcaster.broadcast_tx(self._wallet, tx, callback, timeout_sec)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Misc
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_wallet_tx(self, tx_id: str) -> "Transaction":
        check_not_none(
            self._wallet,
            "Wallet must not be None at TradeWalletService.get_wallet_tx",
        )
        return self._wallet.get_transaction(tx_id)

    def commit_tx(self, tx: "Transaction") -> None:
        check_not_none(
            self._wallet,
            "Wallet must not be None at TradeWalletService.commit_tx",
        )
        self._wallet.maybe_add_transaction(tx)

    def get_cloned_transaction(self, tx: "Transaction") -> "Transaction":
        return Transaction(self.params, tx.bitcoin_serialize())

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private methods
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # JAVA NOTE:
    # This method might be replace by RawTransactionInput constructor taking the TransactionInput as param.
    # As we used segwit=false for the bitcoinSerialize method here we still keep it to not risk to break anything,
    # though it very likely should be fine to replace it with the RawTransactionInput constructor call.
    # DEPRECATED
    def _get_raw_input_from_transaction_input(
        self, input: "TransactionInput"
    ) -> "RawTransactionInput":
        check_not_none(input, "input must not be None")
        check_not_none(
            input.connected_output, "input.connected_output must not be None"
        )
        check_not_none(
            input.connected_output.parent,
            "input.connected_output.parent transaction must not be None",
        )
        check_not_none(input.get_value(), "input.get_value() must not be None")

        # bitcoin_serialize(False) is used just in case the serialized tx is parsed by a Bisq node still using
        # bitcoinj 0.14. This is not supposed to happen ever since Version.TRADE_PROTOCOL_VERSION was set to 3,
        # but it costs nothing to be on the safe side.
        # The serialized tx is just used to obtain its hash, so the witness data is not relevant.
        return RawTransactionInput(
            input.outpoint.index,
            input.connected_output.parent.bitcoin_serialize(False),
            input.get_value().value,
        )

    def _get_transaction_input(
        self,
        parent_transaction: "Transaction",
        script_program: Optional[bytes],
        raw_transaction_input: "RawTransactionInput",
    ) -> "TransactionInput":
        outpoint = self._get_connected_out_point(raw_transaction_input)
        tx_in = ElectrumPartialTxInput(
            prevout=ElectrumTxOutpoint(bytes.fromhex(outpoint.hash), outpoint.index),
            script_sig=script_program,
            nsequence=TransactionInput.NO_SEQUENCE,
        )
        tx_in.utxo = outpoint.connected_tx._electrum_transaction
        return TransactionInput(
            tx_in,
            parent_transaction,
            outpoint,
        )

    def _get_connected_out_point(self, raw_transaction_input: "RawTransactionInput"):
        return TransactionOutPoint.from_tx(
            Transaction(self.params, raw_transaction_input.parent_transaction),
            raw_transaction_input.index,
        )

    def is_p2wh(self, raw_transaction_input: "RawTransactionInput"):
        return ScriptPattern.is_p2wh(
            check_not_none(
                self._get_connected_out_point(raw_transaction_input).connected_output
            ).get_script_pub_key()
        )

    def _get_x_of_threshold_multi_sig_redeem_script(
        self,
        pubkeys: Iterable[bytes],
        threshold: int,
    ):
        return bytes.fromhex(multisig_script([key.hex() for key in pubkeys], threshold))

    def _get_x_of_threshold_multi_sig_output_script(
        self, pubkeys: Iterable[bytes], threshold: int, legacy: bool = False
    ):
        redeem_script = self._get_x_of_threshold_multi_sig_redeem_script(
            pubkeys, threshold
        )
        if legacy:
            # p2sh
            redeem_script = hash_160(redeem_script)
            return ScriptBuilder.create_p2sh_output_script(redeem_script).program
        else:
            # p2wsh
            redeem_script = get_sha256_hash(redeem_script)
            return ScriptBuilder.create_p2wsh_output_script(redeem_script).program

    def _create_payout_tx(
        self,
        deposit_tx: "Transaction",
        buyer_payout_amount: Coin,
        seller_payout_amount: Coin,
        buyer_address_string: str,
        seller_address_string: str,
    ) -> "Transaction":
        hashed_multi_sig_output = deposit_tx.outputs[0]
        transaction = Transaction(self.params)
        transaction.add_input(hashed_multi_sig_output)

        if buyer_payout_amount.is_positive():
            transaction.add_output(
                TransactionOutput.from_coin_and_address(
                    buyer_payout_amount,
                    Address.from_string(buyer_address_string, self.params),
                    transaction,
                )
            )

        if seller_payout_amount.is_positive():
            transaction.add_output(
                TransactionOutput.from_coin_and_address(
                    seller_payout_amount,
                    Address.from_string(seller_address_string, self.params),
                    transaction,
                )
            )

        check_argument(len(transaction.outputs) >= 1, "We need at least one output.")
        # TODO: FIXME: hack
        transaction.version = 1
        return transaction

    def _add_available_inputs_and_change_outputs(
        self, transaction: "Transaction", address: "Address", change_address: "Address"
    ) -> None:
        send_request = None
        try:
            # Let the framework do the work to find the right inputs
            send_request = SendRequest.for_tx(transaction)
            send_request.shuffle_outputs = False
            send_request.password = self._password
            # We use a fixed fee
            send_request.fee = Coin.ZERO()
            send_request.fee_per_kb = Coin.ZERO()
            send_request.ensure_min_required_fee = False
            # TODO: double check if following comment is True for our impl
            # We allow spending of unconfirmed tx (double spend risk is low and usability would suffer if we need to wait for 1 confirmation)
            send_request.coin_selector = BtcCoinSelector(
                address, self._preferences.get_ignore_dust_threshold()
            )
            # We use the same address in a trade for all transactions
            send_request.change_address = change_address
            # With the usage of complete_tx() we get all the work done with fee calculation, validation, and coin selection.
            # We don't commit that tx to the wallet as it will be changed later and it's not signed yet.
            # So it will not change the wallet balance.
            check_not_none(self._wallet, "Wallet must not be None")
            self._wallet.complete_tx(send_request)
        except Exception as e:
            if send_request and send_request.tx:
                logger.warning(
                    f"add_available_inputs_and_change_outputs: send_request.tx={send_request.tx}, send_request.tx.outputs={send_request.tx.outputs}"
                )
            raise WalletException(e) from e

    def _apply_lock_time(self, lock_time: int, transaction: "Transaction") -> None:
        check_argument(
            transaction.inputs,
            f"The transaction must have inputs. transaction={transaction}",
        )
        for tx_input in transaction.inputs:
            tx_input.nsequence = TransactionInput.NO_SEQUENCE - 1
        transaction.lock_time = lock_time

    # BISQ issue #4039: prevent dust outputs from being created.
    # check all the outputs in a proposed transaction, if any are below the dust threshold
    # remove them, noting the details in the log. returns 'true' to indicate if any dust was
    # removed.
    def _remove_dust(self, transaction: "Transaction") -> bool:
        original_transaction_outputs = transaction.outputs
        keep_transaction_outputs = []

        for transaction_output in original_transaction_outputs:
            if transaction_output.get_value().is_less_than(
                Restrictions.get_min_non_dust_output()
            ):
                logger.info(
                    f"Your transaction would have contained a dust output of {transaction_output}",
                )
            else:
                keep_transaction_outputs.append(transaction_output)

        # If dust was detected, keep_transaction_outputs will have fewer elements than original_transaction_outputs
        # Set the transaction outputs to what we saved in keep_transaction_outputs, thus discarding dust.
        if len(keep_transaction_outputs) != len(original_transaction_outputs):
            logger.info(
                "Dust output was detected and removed, the new output is as follows:"
            )
            transaction.clear_outputs()
            for transaction_output in keep_transaction_outputs:
                transaction.add_output(transaction_output)
                logger.info(f"{transaction_output}")
            return True  # Dust was removed

        return False  # No action necessary
