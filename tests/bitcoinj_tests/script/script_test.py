import json
from pathlib import Path
import unittest
 
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.sha_256_hash import Sha256Hash
from bitcoinj.core.transaction import Transaction
from bitcoinj.core.transaction_input import TransactionInput
from bitcoinj.core.transaction_out_point import TransactionOutPoint
from bitcoinj.core.transaction_sig_hash import TransactionSigHash
from bitcoinj.core.utils import encode_mpi
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.params.test_net3_params import TestNet3Params
from bitcoinj.params.main_net_params import MainNetParams
from bitcoinj.script.script import Script
from bitcoinj.script.script_error import ScriptError
from bitcoinj.script.script_exception import ScriptException
from bitcoinj.script.script_opcodes import get_opcode
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.script.script_utils import ScriptUtils
from bitcoinj.script.script_verify_flag import ScriptVerifyFlag
from electrum_min.bitcoin import opcodes
from electrum_min.transaction import SerializationError, TxInput, TxOutpoint, TxOutput 

TESTNET = TestNet3Params()
MAINNET = MainNetParams()

sig_program = "47304402202b4da291cc39faf8433911988f9f49fc5c995812ca2f94db61468839c228c3e90220628bff3ff32ec95825092fa051cba28558a981fcf59ce184b14f2e215e69106701410414b38f4be3bb9fa0f4f32b74af07152b2f2f630bc02122a491137b6c523e46f18a0d5034418966f93dfc37cc3739ef7b2007213a302b7fba161557f4ad644a1c"
pubkey_prog = "76a91433e81a941e64cda12c6a299ed322ddbdd03f8d0e88ac"

# to simplify test the generated script programs hex comes from bitcoinj java tests

class ScriptTest(unittest.TestCase):

    def test_script_sig(self):
       sig_prg_bytes = bytes.fromhex(sig_program)
       script = Script(sig_prg_bytes)
       self.assertEqual("PUSHDATA(71)[304402202b4da291cc39faf8433911988f9f49fc5c995812ca2f94db61468839c228c3e90220628bff3ff32ec95825092fa051cba28558a981fcf59ce184b14f2e215e69106701] PUSHDATA(65)[0414b38f4be3bb9fa0f4f32b74af07152b2f2f630bc02122a491137b6c523e46f18a0d5034418966f93dfc37cc3739ef7b2007213a302b7fba161557f4ad644a1c]",
                str(script))
       
    def test_script_pub_key(self):
        pubkey_bytes = bytes.fromhex(pubkey_prog)
        script = Script(pubkey_bytes)
        self.assertEqual("DUP HASH160 PUSHDATA(20)[33e81a941e64cda12c6a299ed322ddbdd03f8d0e] EQUALVERIFY CHECKSIG",
                str(script))

    def test_multi_sig(self):
        program_hex = "522102be12b1e799142e22a6d0ab2efe891ebdf5890f70271570559fe1292afe7d51b52102f7d5a7a18bf4f2e232913a9f53197dee4608ed1c229581e8436a04635e329eb62103cffd9b77ab278dd341752c85a4a915efecdc4fffa7f8e54c7cfd3537e49d14cf53ae"
        script = Script(bytes.fromhex(program_hex))
        self.assertTrue(ScriptPattern.is_sent_to_multi_sig(script))
        program_hex = "532103030ef1cadefea1bd6eed313166df0b69150af749555f0ddc0804575ecfdb38dc2103418573686d34b8bdb387a126bfe70d5607d1af5316bb278d5e07d373c34f5819210384b2604b709bd39b83cb5f1c4cbd8ccd8f0318c67c52caa5208673e8fb8a20fb53ae"
        script = Script(bytes.fromhex(program_hex))
        self.assertTrue(ScriptPattern.is_sent_to_multi_sig(script))
        program_hex = "2102c30d8996d5772229edf81eab11b7b63959924664c54e82a11399d0eb1a4b74c3ac" # has one key
        script = Script(bytes.fromhex(program_hex))
        self.assertFalse(ScriptPattern.is_sent_to_multi_sig(script))
    
    def test_p2sh_output_script(self):
        program_hex = "a9142ac4b0b501117cc8119c5797b519538d4942e90e87"
        script = Script(bytes.fromhex(program_hex))
        self.assertTrue(ScriptPattern.is_p2sh(script))
        
    def test_mutli_sig_hash(self):
        multi_sig_script = Script(bytes.fromhex("5221025878e270211662a27181cf4d6ad4d2cf0e69a98a3815c086f587c7e9388d87182103fc85980e3fac1f3d8a5c3223c3ef5bffc1bd42d2cc42add8c3899cc66e7f1906210215b5bd050869166a70a7341b4f216e268b7c6c7504576dcea2cce7d11cc9a35f53ae"))
        spend_tx = Transaction(TESTNET, bytes.fromhex("0100000001d324b34c80c2e611b23c92ed1be31729b2856ae439d54b237a296d618425e9120100000000ffffffff0140420f00000000001976a914edc96705498831b16782d439fa93164bc5c8db6f88ac00000000"))
        hash_for_sig_in_java = "35cf8fbfd6a4bfe6133bdcbfde381a5097fef16e084b3f5890cd894618ee8e59"
        hash_for_sig_in_python = spend_tx.hash_for_signature(0, multi_sig_script, TransactionSigHash.ALL, False).hex()
        self.assertEqual(hash_for_sig_in_java, hash_for_sig_in_python)
        
    def test_op0(self):
        tx = Transaction(TESTNET, bytes.fromhex("01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff00ffffffff0000000000"))
        script = Script(bytes.fromhex("00"))
        stack = []
        Script.execute_script(tx, 0, script, stack, Script.ALL_VERIFY_FLAGS)
        self.assertEqual(0, len(stack[0]), "OP_0 push length")

    def parse_script_string(self, string: str):
        words = string.split()
        out = bytearray()

        for w in words:
            if w == "":
                continue
            if w.isdigit() or (w.startswith('-') and w[1:].isdigit()):
                val = int(w)
                if -1 <= val <= 16:
                    out.append(ScriptUtils.encode_to_op_n(val))
                else:
                    ScriptUtils.write_bytes(out, bytes(reversed(encode_mpi(val, False))))
            elif w.startswith("0x"):
                out.extend(bytes.fromhex(w[2:]))
            elif len(w) >= 2 and w.startswith("'") and w.endswith("'"):
                ScriptUtils.write_bytes(out, w[1:-1].encode('utf-8'))
            elif get_opcode(w) != opcodes.OP_INVALIDOPCODE:
                out.append(get_opcode(w))
            elif w.startswith("OP_") and get_opcode(w[3:]) != opcodes.OP_INVALIDOPCODE:
                out.append(get_opcode(w[3:]))
            else:
                raise RuntimeError(f"Invalid word: '{w}'")

        return Script(bytes(out))
    
    def parse_verify_flags(self, string: str):
        flags = set()
        if string != "NONE":
            for flag in string.split(","):
                try:
                    flags.add(ScriptVerifyFlag[flag.strip()])
                except KeyError:
                    print(f"Cannot handle verify flag {flag} -- ignored.")
        return flags
    
    def test_data_driven_scripts(self):
        data = {}
        with open(Path(__file__).parent.joinpath("script_tests.json")) as f:
            data = json.load(f)
            
        for test in data:
            if len(test) == 1:
                continue # skip comment
            if len(test) > 4 and 'with not enough bytes' in test[4]:
                # skip disabled test for python
                continue
            verify_flags = self.parse_verify_flags(test[2])
            expected_error = ScriptError.from_mnemonic(test[3])
            try:
                script_sig = self.parse_script_string(test[0])
                script_pub_key = self.parse_script_string(test[1])
                tx_credit = self.build_crediting_transaction(script_pub_key)
                tx_spend = self.build_spending_transaction(tx_credit, script_sig)
                script_sig.correctly_spends(tx_spend, 0, None, None, script_pub_key, verify_flags)
                if expected_error != ScriptError.SCRIPT_ERR_OK:
                    self.fail(f"Expected error {expected_error} but no error was thrown")
            except ScriptException as e:
                if expected_error != e.args[0]:
                    self.fail(f"Expected error {expected_error} but got {e.args[0]}")
    
    def build_crediting_transaction(self, script: Script):
        tx = Transaction(TESTNET)
        tx.version = 1
        tx.lock_time = 0
        
        tx_input = TxInput(
            prevout=TxOutpoint(bytes(32), 4294967295),
            nsequence=TransactionInput.NO_SEQUENCE,
            script_sig=bytes([0,0]),
            is_coinbase_output=False,
            witness=None,
        )
        setattr(tx_input, "_TxInput__scriptpubkey", bytes([0,0]))
        tx._electrum_transaction._inputs = [tx_input]
        tx._electrum_transaction._outputs = [
            TxOutput(
                scriptpubkey=script.program,
                value=0,
            )
        ]
        return tx
    
    def build_spending_transaction(self, crediting_tx: Transaction, script: Script):
        tx = Transaction(TESTNET)
        tx.version = 1
        tx.lock_time = 0
        tx._electrum_transaction._inputs = [
            TxInput(
                prevout=TxOutpoint(bytes(32), 4294967295),
                nsequence=TransactionInput.NO_SEQUENCE,
                script_sig=script.program,
                is_coinbase_output=False,
                witness=None,
            )
        ]
        tx._electrum_transaction._outputs = [
            TxOutput(
                scriptpubkey=bytes(),
                value=crediting_tx.outputs[0].value,
            )
        ]
        return tx
    
    def parse_script_pubkeys(self, inputs: list):
        script_pub_keys = {}
        for input in inputs:
            hash = input[0]
            index = input[1]
            if index == -1:
                index = 4294967295
            script = input[2]
            script_pub_keys[TransactionOutPoint(index, hash)] = self.parse_script_string(script)
        return script_pub_keys
    
    def test_data_driven_valid_transaction(self):
        data = {}
        with open(Path(__file__).parent.joinpath("tx_valid.json")) as f:
            data = json.load(f)
            
        for test in data:
            if isinstance(test, list) and len(test) == 1 and isinstance(test[0], str):
                continue # skip comment
            transaction = None
            try:
                script_pub_keys = self.parse_script_pubkeys(test[0])
                transaction = Transaction(TESTNET, bytes.fromhex(test[1]))
                Transaction.verify(TESTNET, transaction)
                verify_flags = self.parse_verify_flags(test[2])
                
                for i, input in enumerate(transaction.inputs):
                    self.assertTrue(input.outpoint in script_pub_keys)
                    input.get_script_sig().correctly_spends(transaction, i, None, None, script_pub_keys[input.outpoint], verify_flags)
            except Exception as e:
                print(e)
                if transaction:
                    print(transaction)
                print("----------------------------------------------------------------")
                print(f"test that failed: {test}")
                print("----------------------------------------------------------------")
                raise
    
    def test_data_driven_invalid_transaction(self):
        data = {}
        with open(Path(__file__).parent.joinpath("tx_invalid.json")) as f:
            data = json.load(f)
            
        for test in data:
            if isinstance(test, list) and len(test) == 1 and isinstance(test[0], str):
                continue # skip comment
            
            script_pub_keys = self.parse_script_pubkeys(test[0])
            transaction = Transaction(TESTNET, bytes.fromhex(test[1]))
            verify_flags = self.parse_verify_flags(test[2])
            valid = True
            
            try:
                Transaction.verify(TESTNET, transaction)
            except VerificationException as e:
                valid = False
                if isinstance(e.args[0], SerializationError):
                    continue # cannot check further because it throws error when enumerating inputs
            
            out_points = set[TransactionOutPoint]()
            for i, input in enumerate(transaction.inputs):
                if input.outpoint in out_points:
                    valid = False
                out_points.add(input.outpoint)
            
            for i, input in enumerate(transaction.inputs):
                if not valid:
                    break
                self.assertTrue(input.outpoint in script_pub_keys)
                try:
                    input.get_script_sig().correctly_spends(transaction, i, None, None, script_pub_keys[input.outpoint], verify_flags)
                except VerificationException as e:
                    valid = False
            
            if valid:
                print("----------------------------------------------------------------")
                print(f"test that failed: {test}")
                print("----------------------------------------------------------------")
                self.fail("Test was expected to be invalid, but was valid instead")
    
if __name__ == '__main__':
    unittest.main()