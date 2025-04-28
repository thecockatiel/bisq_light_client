from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional

from bisq.core.dao.burningman.accounting.blockchain.accounting_block import (
    AccountingBlock,
)
from bisq.core.dao.burningman.accounting.blockchain.accounting_tx import AccountingTx
from bisq.core.dao.burningman.accounting.blockchain.accounting_tx_output import (
    AccountingTxOutput,
)
from bisq.core.dao.burningman.accounting.blockchain.accounting_tx_type import (
    AccountingTxType,
)
from bisq.core.dao.burningman.accounting.blockchain.temp.temp_accounting_tx import (
    TempAccountingTx,
)

from bisq.core.dao.state.model.blockchain.script_type import ScriptType
from bisq.core.util.string_utils import hex_decode_last_4_bytes
from bitcoinj.base.coin import Coin
from bitcoinj.core.transaction_input import TransactionInput


if TYPE_CHECKING:
    from bisq.core.dao.node.full.rpc.dto.raw_dto_block import RawDtoBlock
    from bisq.core.dao.burningman.accounting.blockchain.temp.temp_accounting_input import (
        TempAccountingTxInput,
    )
    from bisq.core.dao.burningman.accounting.blockchain.temp.temp_accounting_output import (
        TempAccountingTxOutput,
    )
    from bisq.core.dao.burningman.burning_man_accounting_service import (
        BurningManAccountingService,
    )


class AccountingBlockParser:
    def __init__(self, burning_man_accounting_service: "BurningManAccountingService"):
        self.logger = get_ctx_logger(__name__)
        self.burning_man_accounting_service = burning_man_accounting_service

    def parse(self, raw_dto_block: "RawDtoBlock"):
        burning_man_name_by_address = (
            self.burning_man_accounting_service.get_burning_man_name_by_address()
        )
        genesis_tx_id = self.burning_man_accounting_service.genesis_tx_id

        # We filter early for first output address match. DPT txs have multiple outputs which need to match and will be checked later.
        receiver_addresses = burning_man_name_by_address.keys()
        txs = list(
            filter(
                lambda x: x is not None,
                (
                    self._to_accounting_tx(
                        temp_accounting_tx, burning_man_name_by_address, genesis_tx_id
                    )
                    for temp_accounting_tx in (
                        TempAccountingTx(raw_tx) for raw_tx in raw_dto_block.tx
                    )
                    if temp_accounting_tx.outputs
                    and temp_accounting_tx.outputs[0].address in receiver_addresses
                ),
            )
        )

        # Time in raw_dto_block is in seconds
        time_in_sec = int(raw_dto_block.time)
        truncated_hash = hex_decode_last_4_bytes(raw_dto_block.hash)
        truncated_previous_block_hash = hex_decode_last_4_bytes(
            raw_dto_block.previous_block_hash
        )
        return AccountingBlock(
            raw_dto_block.height,
            time_in_sec,
            truncated_hash,
            truncated_previous_block_hash,
            txs,
        )

    # We cannot know for sure if it's a DPT or BTC fee tx as we do not have the spending tx output with more
    # data for verification as we do not keep the full blockchain data for lookup unspent tx outputs.
    # The DPT can be very narrowly detected. The BTC fee txs might have false positives.
    def _to_accounting_tx(
        self,
        temp_accounting_tx: "TempAccountingTx",
        burning_man_name_by_address: dict[str, str],
        genesis_tx_id: str,
    ) -> Optional["AccountingTx"]:
        if genesis_tx_id == temp_accounting_tx.tx_id:
            return None

        receiver_addresses = burning_man_name_by_address.keys()
        # DPT has 1 input from P2WSH with lock time and sequence number set.
        # We only use native segwit P2SH, so we expect a txInWitness
        inputs = temp_accounting_tx.inputs
        outputs = temp_accounting_tx.outputs
        # Max DPT output amount is currently 4 BTC. Max. security deposit is 50% of trade amount.
        # We give some extra headroom to cover potential future changes.
        # We store value as integer in protobuf to safe space, so max. possible value is 21.47483647 BTC.
        max_dpt_value = 6 * Coin.COIN().value  # 6 BTC in satoshis
        if (
            len(inputs) == 1
            and self._is_valid_time_lock(temp_accounting_tx, inputs[0])
            and self._do_all_outputs_match_receivers(outputs, receiver_addresses)
            and self._is_witness_data_wp2sh(inputs[0].tx_in_witness)
            and all(
                self._is_expected_script_type(output, temp_accounting_tx)
                for output in outputs
            )
            and all(output.value <= max_dpt_value for output in outputs)
        ):
            accounting_tx_outputs = tuple(
                AccountingTxOutput(
                    output.value, burning_man_name_by_address[output.address]
                )
                for output in outputs
            )
            return AccountingTx(
                AccountingTxType.DPT_TX, accounting_tx_outputs, temp_accounting_tx.tx_id
            )

        # BTC trade fee tx has 2 or 3 outputs.
        # First output to receiver, second reserved for trade and an optional 3rd for change.
        # Address check is done in parse method above already.
        # Amounts are in a certain range but as fee can change with DAO param changes we cannot set hard limits.
        # The min. trade fee in Nov. 2022 is 5000 sat. We use 2500 as lower bound.
        # The largest taker fee for a 2 BTC trade is about 0.023 BTC (2_300_000 sat).
        # We use 10_000_000 sat as upper bound to give some headroom for future fee increase and to cover some
        # exceptions like SiaCoin having a 4 BTC limit.
        # Inputs are not constrained.
        # We store value as integer in protobuf to safe space, so max. possible value is 21.47483647 BTC.
        first_output = outputs[0]
        if (
            2 <= len(outputs) <= 3
            and 2500 < first_output.value < 10_000_000
            and self._is_expected_script_type(first_output, temp_accounting_tx)
        ):
            # We only keep first output.
            name = burning_man_name_by_address[first_output.address]
            return AccountingTx(
                AccountingTxType.BTC_TRADE_FEE_TX,
                (AccountingTxOutput(first_output.value, name),),
                temp_accounting_tx.tx_id,
            )

        return None

    # java TODO not sure if other ScriptType are to be expected
    def _is_expected_script_type(
        self, tx_output: "TempAccountingTxOutput", accounting_tx: "TempAccountingTx"
    ) -> bool:
        result = tx_output.script_type in {
            ScriptType.PUB_KEY_HASH,
            ScriptType.SCRIPT_HASH,
            ScriptType.WITNESS_V0_KEYHASH,
        }
        if not result:
            self.logger.error(
                f"isExpectedScriptType txOutput.getScriptType()={tx_output.script_type}, txId={accounting_tx.tx_id}"
            )
        return result

    # All outputs need to be to receiver addresses (incl. legacy BM)
    def _do_all_outputs_match_receivers(
        self, outputs: tuple["TempAccountingTxOutput"], receiver_addresses: set[str]
    ) -> bool:
        return all(output.address in receiver_addresses for output in outputs)

    def _is_valid_time_lock(
        self, accounting_tx: "TempAccountingTx", first_input: "TempAccountingTxInput"
    ) -> bool:
        # Need to be 0xfffffffe
        return (
            accounting_tx.is_valid_dpt_lock_time
            and first_input.sequence == TransactionInput.NO_SEQUENCE - 1
        )

    #   Example txInWitness: [, 304502210098fcec3ac1c1383d40159587b42e8b79cb3e793004d6ccb080bfb93f02c15f93022039f014eb933c59f988d68a61aa7a1c787f08d94bd0b222104718792798e43e3c01, 304402201f8b37f3b8b5b9944ca88f18f6bb888c5a48dc5183edf204ae6d3781032122e102204dc6397538055d94de1ab683315aac7d87289be0c014569f7b3fa465bf70b6d401, 5221027f6da96ede171617ce79ec305a76871ecce21ad737517b667fc9735f2dc342342102d8d93e02fb0833201274b47a302b47ff81c0b3510508eb0444cb1674d0d8a6d052ae]
    def _is_witness_data_wp2sh(self, tx_in_witness: tuple[str, str, str, str]) -> bool:
        # txInWitness from the 2of2 multiSig has 4 chunks.
        # 0 byte, sig1, sig2, redeemScript
        if len(tx_in_witness) != 4:
            self.logger.error(f"txInWitness chunks size not 4 .txInWitness={tx_in_witness}")
            return False

        # First chunk is 0 byte (empty string)
        if tx_in_witness[0]:
            self.logger.error(f"txInWitness[0] not empty .txInWitness={tx_in_witness}")
            return False

        # The 2 signatures are 70 - 73 bytes
        min_sig_length = 140
        max_sig_length = 146
        first_sig_length = len(tx_in_witness[1])
        if first_sig_length < min_sig_length or first_sig_length > max_sig_length:
            self.logger.error(f"firstSigLength wrong .txInWitness={tx_in_witness}")
            return False
        second_sig_length = len(tx_in_witness[2])
        if second_sig_length < min_sig_length or second_sig_length > max_sig_length:
            self.logger.error(f"secondSigLength wrong .txInWitness={tx_in_witness}")
            return False

        redeem_script = tx_in_witness[3]
        if len(redeem_script) != 142:
            self.logger.error(f"redeemScript not valid length .txInWitness={tx_in_witness}")
            return False

        # OP_2 pub1 pub2 OP_2 OP_CHECKMULTISIG
        # In hex: "5221" + PUB_KEY_1 + "21" + PUB_KEY_2 + "52ae";
        # PubKeys are 33 bytes -> length 66 in hex
        separator = redeem_script[70:72]
        result = (
            redeem_script.startswith("5221")
            and redeem_script.endswith("52ae")
            and separator == "21"
        )
        if not result:
            self.logger.error(f"redeemScript not valid .txInWitness={tx_in_witness}")
        return result
