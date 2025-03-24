from typing import TYPE_CHECKING, Any, Optional, Sequence, Union

from bisq.core.exceptions.illegal_state_exception import IllegalStateException
from bitcoinj.base.coin import Coin
from bitcoinj.core.legacy_address import LegacyAddress
from bitcoinj.core.segwit_address import SegwitAddress
from bitcoinj.core.utils import encode_mpi, sha1
from bitcoinj.core.verification_exception import VerificationException
from bitcoinj.script.script_opcodes import is_opcode
from bitcoinj.script.script_utils import ScriptUtils
from bitcoinj.crypto.transaction_signature import TransactionSignature
from bitcoinj.script.script_chunk import chunk_to_string, is_shortest_possible_push_data
from bitcoinj.script.script_error import ScriptError
from bitcoinj.script.script_exception import ScriptException
from bitcoinj.script.script_pattern import ScriptPattern
from bitcoinj.script.script_type import ScriptType
from bitcoinj.script.script_verify_flag import ScriptVerifyFlag
from electrum_min.bitcoin import opcodes
from electrum_min.crypto import hash_160, ripemd, sha256, sha256d
from electrum_ecc import ECPubkey
from electrum_min.transaction import (
    MalformedBitcoinScript,
    OPPushDataGeneric,
    match_script_against_template,
    script_GetOp,
)

if TYPE_CHECKING:
    from bitcoinj.crypto.deterministic_key import DeterministicKey
    from bitcoinj.core.transaction import Transaction
    from bitcoinj.core.address import Address
    from bitcoinj.core.network_parameters import NetworkParameters

# TODO
class Script:
    ALL_VERIFY_FLAGS = set([
        flag for flag in ScriptVerifyFlag
    ])
    MAX_SCRIPT_ELEMENT_SIZE = 520  # bytes
    MAX_OPS_PER_SCRIPT = 201
    MAX_STACK_SIZE = 1000
    MAX_PUBKEYS_PER_MULTISIG = 20
    MAX_SCRIPT_SIZE = 10000
    SIG_SIZE = 75
    # Max number of sigops allowed in a standard p2sh redeem script
    MAX_P2SH_SIGOPS = 15

    def __init__(self, program: Optional[bytes] = None):
        self._program = program if program is not None else bytes()
        self._decoded: tuple[int, Optional[bytes], Union[int, Any]] = None
        self.address = None
    
    @property
    def program(self):
        return self._program

    @program.setter
    def program(self, value: bytes):
        self._program = value
        self._decoded = None
    
    @property
    def decoded(self):
        if self._decoded is None:
            self._decoded = [x for x in script_GetOp(self.program)]
        return self._decoded
    
    def __hash__(self):
        return hash(self.program)
    
    def __eq__(self, value):
        if isinstance(value, Script):
            return self.program == value.program
        if isinstance(value, bytes):
            return self.program == value
        return False
    
    def __str__(self):
        if self.decoded:
            return " ".join([chunk_to_string(x) for x in self.decoded])
        else:
            return "<empty>"

    def hex(self) -> str:
        return self.program.hex()

    def get_to_address(self, params: "NetworkParameters") -> "Address":
        # p2pkh
        if ScriptPattern.is_p2pkh(self):
            return LegacyAddress(params, False, self.decoded[2][1])

        # p2sh
        if ScriptPattern.is_p2sh(self):
            return LegacyAddress(params, True, self.decoded[1][1])

        # segwit address (version 0)
        if ScriptPattern.is_witness_v0(self):
            return SegwitAddress.from_hash(self.decoded[1][1], params, 0)

        # segwit address (version 1-16)
        future_witness_versions = list(range(opcodes.OP_1, opcodes.OP_16 + 1))
        for witver, opcode in enumerate(future_witness_versions, start=1):
            match = [opcode, OPPushDataGeneric(lambda x: 2 <= x <= 40)]
            if match_script_against_template(self.decoded, match):
                return SegwitAddress.from_hash(self.decoded[1][1], params, witver)

        return MalformedBitcoinScript("Unknown script type")

    def get_script_type(self) -> Optional["ScriptType"]:
        if ScriptPattern.is_p2pkh(self):
            return ScriptType.P2PKH
        elif ScriptPattern.is_p2sh(self):
            return ScriptType.P2SH
        elif ScriptPattern.is_p2wpkh(self):
            return ScriptType.P2WPKH
        elif ScriptPattern.is_p2wsh(self):
            return ScriptType.P2WSH
        else:
            return None

    def correctly_spends(self, tx_containing_this: "Transaction", script_sig_index: int, witness_elements: Sequence[bytes], value: Coin, script_pub_key: Union["Script", bytes], verify_flags: set["ScriptVerifyFlag"]) -> bool:
        from bitcoinj.script.script_builder import ScriptBuilder
        if isinstance(script_pub_key, bytes):
            script_pub_key = Script(script_pub_key)
        
        if ScriptPattern.is_p2wpkh(script_pub_key):
            # For SegWit, full validation isn't implemented. So we simply check the signature. P2SH_P2WPKH is handled
            # by the P2SH code for now.
            if len(witness_elements) < 2:
                raise ScriptException(ScriptError.SCRIPT_ERR_WITNESS_PROGRAM_WITNESS_EMPTY, "".join(x.hex() for x in witness_elements))
            
            signature = None
            try:
                signature = TransactionSignature.decode_from_bitcoin(witness_elements[0], True, True)
            except Exception as e:
                raise ScriptException(ScriptError.SCRIPT_ERR_SIG_DER, "Cannot decode", e)
            pubkey = ECPubkey(witness_elements[1])
            script_code = ScriptBuilder.create_p2pkh_output_script(pubkey.get_public_key_bytes())
            sig_hash = tx_containing_this.hash_for_witness_signature(script_sig_index, script_code, value, signature.sig_hash_mode, False)
            valid_sig = pubkey.ecdsa_verify(signature.to_sig64(), sig_hash)
            if not valid_sig:
                raise ScriptException(ScriptError.SCRIPT_ERR_CHECKSIGVERIFY, "Invalid signature")
        elif ScriptPattern.is_p2pkh(script_pub_key):
            if len(self.decoded) != 2:
                raise ScriptException(ScriptError.SCRIPT_ERR_SCRIPT_SIZE, f"Invalid size: {len(self.decoded)}")
            
            signature = None
            try:
                # self.decoded[0][1] ~= chunks.get(0).data
                signature = TransactionSignature.decode_from_bitcoin(self.decoded[0][1], True, True)
            except Exception as e:
                raise ScriptException(ScriptError.SCRIPT_ERR_SIG_DER, "Cannot decode", e)
            pubkey = ECPubkey(self.decoded[1][1]) # self.decoded[1][1] ~= chunks.get(1).data
            sig_hash = tx_containing_this.hash_for_signature(script_sig_index, script_pub_key, signature.sig_hash_mode, False)
            valid_sig = pubkey.ecdsa_verify(signature.to_sig64(), sig_hash)
            if not valid_sig:
                raise ScriptException(ScriptError.SCRIPT_ERR_CHECKSIGVERIFY, "Invalid signature")
        else:
            # Clone the transaction because executing the script involves editing it, and if we die, we'll leave
            # the tx half broken (also it's not so thread safe to work on it directly.
            from bitcoinj.core.transaction import Transaction
            try:
                tx_containing_this = Transaction(tx_containing_this.params, tx_containing_this.bitcoin_serialize())
                tx_containing_this._electrum_transaction.deserialize()
            except Exception as e:
                # Should not happen unless we were given a totally broken transaction.
                raise 
                
            
            if len(self.program) > Script.MAX_SCRIPT_SIZE or len(script_pub_key.program) > Script.MAX_SCRIPT_SIZE:
                raise ScriptException(ScriptError.SCRIPT_ERR_SCRIPT_SIZE, "Script larger than 10,000 bytes")

            stack = list[bytes]()
            p2sh_stack: Optional[list[bytes]] = None

            self.execute_script(tx_containing_this, script_sig_index, self, stack, verify_flags)
            if ScriptVerifyFlag.P2SH in verify_flags:
                p2sh_stack = stack.copy()
            self.execute_script(tx_containing_this, script_sig_index, script_pub_key, stack, verify_flags)

            if len(stack) == 0:
                raise ScriptException(ScriptError.SCRIPT_ERR_EVAL_FALSE, "Stack empty at end of script execution.")

            stack_copy = stack.copy()
            if not ScriptUtils.cast_to_bool(stack.pop()):
                raise ScriptException(ScriptError.SCRIPT_ERR_EVAL_FALSE, f"Script resulted in a non-true stack: {ScriptUtils.stack_to_string(stack_copy)}")
            
            # P2SH is pay to script hash. It means that the scriptPubKey has a special form which is a valid
            # program but it has "useless" form that if evaluated as a normal program always returns true.
            # Instead, miners recognize it as special based on its template - it provides a hash of the real scriptPubKey
            # and that must be provided by the input. The goal of this bizarre arrangement is twofold:
            # 
            # (1) You can sum up a large, complex script (like a CHECKMULTISIG script) with an address that's the same
            #     size as a regular address. This means it doesn't overload scannable QR codes/NFC tags or become
            #     un-wieldy to copy/paste.
            # (2) It allows the working set to be smaller: nodes perform best when they can store as many unspent outputs
            #     in RAM as possible, so if the outputs are made smaller and the inputs get bigger, then it's better for
            #     overall scalability and performance.

            if ScriptVerifyFlag.P2SH in verify_flags and ScriptPattern.is_p2sh(script_pub_key):
                for opcode, data, _ in self.decoded:
                    if opcode > opcodes.OP_16:
                        raise ScriptException(ScriptError.SCRIPT_ERR_SIG_PUSHONLY, "Attempted to spend a P2SH scriptPubKey with a script that contained script ops")

                script_pub_key_bytes = p2sh_stack.pop()
                script_pub_key_p2sh = Script(script_pub_key_bytes)

                self.execute_script(tx_containing_this, script_sig_index, script_pub_key_p2sh, p2sh_stack, verify_flags)

                if len(p2sh_stack) == 0:
                    raise ScriptException(ScriptError.SCRIPT_ERR_EVAL_FALSE, "P2SH stack empty at end of script execution.")

                p2sh_stack_copy = p2sh_stack.copy()
                if not ScriptUtils.cast_to_bool(p2sh_stack.pop()):
                    raise ScriptException(ScriptError.SCRIPT_ERR_EVAL_FALSE, f"P2SH script execution resulted in a non-true stack: {ScriptUtils.stack_to_string(p2sh_stack_copy)}")

    @staticmethod
    def equals_range(a: bytes, start: int, b: bytes):
        if start + len(b) > len(a):
            return False
        for i in range(len(b)):
            if a[i + start] != b[i]:
                return False
        return True
    
    @staticmethod
    def remove_all_instances_of_op(input_script: bytes, chunk_to_remove: Union[int, bytes]) -> bytes:
        """Returns the script bytes of inputScript with all instances of the specified script object removed"""
        if isinstance(chunk_to_remove, int):
            chunk_to_remove = bytes([chunk_to_remove])
        
        # We usually don't end up removing anything 
        output = bytearray()
        cursor = 0

        while cursor < len(input_script):
            skip = Script.equals_range(input_script, cursor, chunk_to_remove)
            
            opcode = input_script[cursor] & 0xFF
            cursor += 1
            
            additional_bytes = 0
            if 0 <= opcode < opcodes.OP_PUSHDATA1:
                additional_bytes = opcode
            elif opcode == opcodes.OP_PUSHDATA1:
                additional_bytes = (0xFF & input_script[cursor]) + 1
            elif opcode == opcodes.OP_PUSHDATA2:
                additional_bytes = int.from_bytes(input_script[cursor:cursor+2], 'little') + 2
            elif opcode == opcodes.OP_PUSHDATA4:
                additional_bytes = int.from_bytes(input_script[cursor:cursor+4], 'little') + 4

            if not skip:
                output.append(opcode)
                output.extend(input_script[cursor:cursor + additional_bytes])
                
            cursor += additional_bytes

        return bytes(output)
    
    @staticmethod
    def execute_script(tx_containing_this: "Transaction", index: int, script: "Script", stack: list[bytes], verify_flags: set["ScriptVerifyFlag"]) -> None:
        op_count = 0
        last_code_sep_location = 0

        altstack = []
        if_stack = []
        
        disabled_opcodes = {
            opcodes.OP_CAT, opcodes.OP_SUBSTR, opcodes.OP_LEFT, opcodes.OP_RIGHT,
            opcodes.OP_INVERT, opcodes.OP_AND, opcodes.OP_OR, opcodes.OP_XOR,
            opcodes.OP_2MUL, opcodes.OP_2DIV, opcodes.OP_MUL, opcodes.OP_DIV,
            opcodes.OP_MOD, opcodes.OP_LSHIFT, opcodes.OP_RSHIFT
        }

        for opcode, data, start_location in script.decoded:
            should_execute = not (False in if_stack)

            # Check stack element size
            if data is not None and len(data) > Script.MAX_SCRIPT_ELEMENT_SIZE:
                raise ScriptException(ScriptError.SCRIPT_ERR_PUSH_SIZE, "Attempted to push a data string larger than 520 bytes")

            # Note how OP_RESERVED does not count towards the opcode limit.
            if opcode > opcodes.OP_16:
                op_count += 1
                if op_count > Script.MAX_OPS_PER_SCRIPT:
                    raise ScriptException(ScriptError.SCRIPT_ERR_OP_COUNT, "More script operations than is allowed")

            # Disabled opcodes.
            if opcode in disabled_opcodes:
                raise ScriptException(ScriptError.SCRIPT_ERR_DISABLED_OPCODE, "Script included a disabled Script Op.")

            if should_execute and opcodes.OP_0 <= opcode <= opcodes.OP_PUSHDATA4:
                # Check minimal push
                if ScriptVerifyFlag.MINIMALDATA in verify_flags and not is_shortest_possible_push_data(opcode, data):
                    raise ScriptException(ScriptError.SCRIPT_ERR_MINIMALDATA, "Script included a not minimal push operation.")

                if opcode == opcodes.OP_0:
                    stack.append(b'')
                else:
                    stack.append(data)
            
            elif should_execute or (opcodes.OP_IF <= opcode <= opcodes.OP_ENDIF):
                if opcode == opcodes.OP_IF:
                    if not should_execute:
                        if_stack.append(False)
                        continue
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_UNBALANCED_CONDITIONAL, "Attempted OP_IF on an empty stack")
                    if_stack.append(ScriptUtils.cast_to_bool(stack.pop()))
                    continue
                elif opcode == opcodes.OP_NOTIF:
                    if not should_execute:
                        if_stack.append(False)
                        continue
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_UNBALANCED_CONDITIONAL, "Attempted OP_NOTIF on an empty stack")
                    if_stack.append(not ScriptUtils.cast_to_bool(stack.pop()))
                    continue
                elif opcode == opcodes.OP_ELSE:
                    if not if_stack:
                        raise ScriptException(ScriptError.SCRIPT_ERR_UNBALANCED_CONDITIONAL, "Attempted OP_ELSE without OP_IF/NOTIF")
                    if_stack[-1] = not if_stack[-1]
                    continue
                elif opcode == opcodes.OP_ENDIF:
                    if not if_stack:
                        raise ScriptException(ScriptError.SCRIPT_ERR_UNBALANCED_CONDITIONAL, "Attempted OP_ENDIF without OP_IF/NOTIF")
                    if_stack.pop()
                    continue
                
                # OP_0 is no opcode
                elif opcode == opcodes.OP_1NEGATE:
                    stack.append(bytes(reversed(encode_mpi(-1, False))))
                elif opcodes.OP_1 <= opcode <= opcodes.OP_16:
                    stack.append(bytes(reversed(encode_mpi(ScriptUtils.decode_from_op_n(opcode), False))))
                elif opcode == opcodes.OP_NOP:
                    pass
                elif opcode == opcodes.OP_VERIFY:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_VERIFY on an empty stack")
                    if not ScriptUtils.cast_to_bool(stack.pop()):
                        raise ScriptException(ScriptError.SCRIPT_ERR_VERIFY, "OP_VERIFY failed")
                elif opcode == opcodes.OP_RETURN:
                    raise ScriptException(ScriptError.SCRIPT_ERR_OP_RETURN, "Script called OP_RETURN")
                elif opcode == opcodes.OP_TOALTSTACK:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_TOALTSTACK on an empty stack")
                    altstack.append(stack.pop())
                elif opcode == opcodes.OP_FROMALTSTACK:
                    if len(altstack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_ALTSTACK_OPERATION, "Attempted OP_FROMALTSTACK on an empty altstack")
                    stack.append(altstack.pop())
                elif opcode == opcodes.OP_2DROP:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_2DROP on a stack with size < 2")
                    stack.pop()
                    stack.pop()
                elif opcode == opcodes.OP_2DUP:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_2DUP on a stack with size < 2")
                    stack.extend(stack[-2:])
                elif opcode == opcodes.OP_3DUP:
                    if len(stack) < 3:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_3DUP on a stack with size < 3")
                    stack.extend(stack[-3:])
                elif opcode == opcodes.OP_2OVER:
                    if len(stack) < 4:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_2OVER on a stack with size < 4")
                    stack.extend(stack[-4:-2])
                elif opcode == opcodes.OP_2ROT:
                    if len(stack) < 6:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_2ROT on a stack with size < 6")
                    stack[-6], stack[-5], stack[-4], stack[-3], stack[-2], stack[-1] = stack[-4], stack[-3], stack[-2], stack[-1], stack[-6], stack[-5]
                elif opcode == opcodes.OP_2SWAP:
                    if len(stack) < 4:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_2SWAP on a stack with size < 4")
                    stack[-4], stack[-3], stack[-2], stack[-1] = stack[-2], stack[-1], stack[-4], stack[-3]
                elif opcode == opcodes.OP_IFDUP:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_IFDUP on an empty stack")
                    if ScriptUtils.cast_to_bool(stack[-1]):
                        stack.append(stack[-1])
                elif opcode == opcodes.OP_DEPTH:
                    stack.append(bytes(reversed(encode_mpi(len(stack), False))))
                elif opcode == opcodes.OP_DROP:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_DROP on an empty stack")
                    stack.pop()
                elif opcode == opcodes.OP_DUP:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_DUP on an empty stack")
                    stack.append(stack[-1])
                elif opcode == opcodes.OP_NIP:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_NIP on a stack with size < 2")
                    OPNIPtmpChunk = stack.pop()
                    stack.pop()
                    stack.append(OPNIPtmpChunk)
                elif opcode == opcodes.OP_OVER:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_OVER on a stack with size < 2")
                    stack.append(stack[-2])
                elif opcode == opcodes.OP_PICK or opcode == opcodes.OP_ROLL:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_PICK/OP_ROLL on an empty stack")
                    val = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    if val < 0 or val >= len(stack):
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "OP_PICK/OP_ROLL attempted to get data deeper than stack size")
                    if opcode == opcodes.OP_ROLL:
                        stack.append(stack.pop(-val-1))
                    else:
                        stack.append(stack[-val-1])
                elif opcode == opcodes.OP_ROT:
                    if len(stack) < 3:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_ROT on a stack with size < 3")
                    stack[-3], stack[-2], stack[-1] = stack[-2], stack[-1], stack[-3]
                elif opcode == opcodes.OP_SWAP or opcode == opcodes.OP_TUCK:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_SWAP on a stack with size < 2")
                    stack[-2], stack[-1] = stack[-1], stack[-2]
                    if opcode == opcodes.OP_TUCK:
                        stack.append(stack[-2])
                elif opcode == opcodes.OP_SIZE:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_SIZE on an empty stack")
                    stack.append(bytes(reversed(encode_mpi(len(stack[-1]), False))))
                elif opcode == opcodes.OP_EQUAL:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_EQUAL on a stack with size < 2")
                    stack.append(b'\x01' if stack.pop() == stack.pop() else b'')
                elif opcode == opcodes.OP_EQUALVERIFY:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_EQUALVERIFY on a stack with size < 2")
                    if stack.pop() != stack.pop():
                        raise ScriptException(ScriptError.SCRIPT_ERR_EQUALVERIFY, "OP_EQUALVERIFY: non-equal data")
                elif opcode in {opcodes.OP_1ADD, opcodes.OP_1SUB, opcodes.OP_NEGATE, opcodes.OP_ABS, opcodes.OP_NOT, opcodes.OP_0NOTEQUAL}:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted a numeric op on an empty stack")
                    num = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    if opcode == opcodes.OP_1ADD:
                        num += 1
                    elif opcode == opcodes.OP_1SUB:
                        num -= 1
                    elif opcode == opcodes.OP_NEGATE:
                        num = -num
                    elif opcode == opcodes.OP_ABS:
                        num = abs(num)
                    elif opcode == opcodes.OP_NOT:
                        num = 0 if num != 0 else 1
                    elif opcode == opcodes.OP_0NOTEQUAL:
                        num = 1 if num != 0 else 0
                    else:
                        raise RuntimeError("Unreachable. opcode should have been matched a case.")
                            
                    stack.append(bytes(reversed(encode_mpi(num, False))))
                elif opcode in {opcodes.OP_ADD, opcodes.OP_SUB, opcodes.OP_BOOLAND, opcodes.OP_BOOLOR, opcodes.OP_NUMEQUAL, opcodes.OP_NUMNOTEQUAL, opcodes.OP_LESSTHAN, opcodes.OP_GREATERTHAN, opcodes.OP_LESSTHANOREQUAL, opcodes.OP_GREATERTHANOREQUAL, opcodes.OP_MIN, opcodes.OP_MAX}:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted a numeric op on a stack with size < 2")
                    num2 = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    num1 = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    if opcode == opcodes.OP_ADD:
                        result = num1 + num2
                    elif opcode == opcodes.OP_SUB:
                        result = num1 - num2
                    elif opcode == opcodes.OP_BOOLAND:
                        result = 1 if num1 != 0 and num2 != 0 else 0
                    elif opcode == opcodes.OP_BOOLOR:
                        result = 1 if num1 != 0 or num2 != 0 else 0
                    elif opcode == opcodes.OP_NUMEQUAL:
                        result = 1 if num1 == num2 else 0
                    elif opcode == opcodes.OP_NUMNOTEQUAL:
                        result = 1 if num1 != num2 else 0
                    elif opcode == opcodes.OP_LESSTHAN:
                        result = 1 if num1 < num2 else 0
                    elif opcode == opcodes.OP_GREATERTHAN:
                        result = 1 if num1 > num2 else 0
                    elif opcode == opcodes.OP_LESSTHANOREQUAL:
                        result = 1 if num1 <= num2 else 0
                    elif opcode == opcodes.OP_GREATERTHANOREQUAL:
                        result = 1 if num1 >= num2 else 0
                    elif opcode == opcodes.OP_MIN:
                        result = min(num1, num2)
                    elif opcode == opcodes.OP_MAX:
                        result = max(num1, num2)
                    else:
                        raise RuntimeError("Opcode switched at runtime?")
                    stack.append(bytes(reversed(encode_mpi(result, False))))
                elif opcode == opcodes.OP_NUMEQUALVERIFY:
                    if len(stack) < 2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_NUMEQUALVERIFY on a stack with size < 2")
                    num2 = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    num1 = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    if num1 != num2:
                        raise ScriptException(ScriptError.SCRIPT_ERR_NUMEQUALVERIFY, "OP_NUMEQUALVERIFY failed")
                elif opcode == opcodes.OP_WITHIN:
                    if len(stack) < 3:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_WITHIN on a stack with size < 3")
                    num3 = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    num2 = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    num1 = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
                    if num2 <= num1 < num3:
                        stack.append(bytes(reversed(encode_mpi(1, False))))
                    else:
                        stack.append(bytes(reversed(encode_mpi(0, False))))
                elif opcode == opcodes.OP_RIPEMD160:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_RIPEMD160 on an empty stack")
                    stack.append(ripemd(stack.pop()))
                elif opcode == opcodes.OP_SHA1:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_SHA1 on an empty stack")
                    stack.append(sha1(stack.pop()))
                elif opcode == opcodes.OP_SHA256:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_SHA256 on an empty stack")
                    stack.append(sha256(stack.pop()))
                elif opcode == opcodes.OP_HASH160:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_HASH160 on an empty stack")
                    stack.append(hash_160(stack.pop()))
                elif opcode == opcodes.OP_HASH256:
                    if len(stack) < 1:
                        raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_HASH256 on an empty stack")
                    stack.append(sha256d(stack.pop()))
                elif opcode == opcodes.OP_CODESEPARATOR:
                    last_code_sep_location = start_location
                elif opcode == opcodes.OP_CHECKSIG or opcode == opcodes.OP_CHECKSIGVERIFY:
                    if tx_containing_this is None:
                        raise ValueError("Script attempted signature check but no tx was provided")
                    Script.execute_check_sig(tx_containing_this, index, script, stack, last_code_sep_location, opcode, verify_flags)
                elif opcode == opcodes.OP_CHECKMULTISIG or opcode == opcodes.OP_CHECKMULTISIGVERIFY:
                    if tx_containing_this is None:
                        raise ValueError("Script attempted signature check but no tx was provided")
                    op_count = Script.execute_multi_sig(tx_containing_this, index, script, stack, op_count, last_code_sep_location, opcode, verify_flags)
                elif opcode == opcodes.OP_CHECKLOCKTIMEVERIFY:
                    if ScriptVerifyFlag.CHECKLOCKTIMEVERIFY not in verify_flags:
                        # not enabled; treat as a NOP2
                        if ScriptVerifyFlag.DISCOURAGE_UPGRADABLE_NOPS in verify_flags:
                            raise ScriptException(ScriptError.SCRIPT_ERR_DISCOURAGE_UPGRADABLE_NOPS, f"Script used a reserved opcode {opcode}")
                    else:
                        Script.execute_check_lock_time_verify(tx_containing_this, index, stack, verify_flags)
                elif opcode == opcodes.OP_CHECKSEQUENCEVERIFY:
                    if ScriptVerifyFlag.CHECKSEQUENCEVERIFY not in verify_flags:
                        # not enabled; treat as a NOP3
                        if ScriptVerifyFlag.DISCOURAGE_UPGRADABLE_NOPS in verify_flags:
                            raise ScriptException(ScriptError.SCRIPT_ERR_DISCOURAGE_UPGRADABLE_NOPS, f"Script used a reserved opcode {opcode}")
                    else:   
                        Script.execute_check_sequence_verify(tx_containing_this, index, stack, verify_flags)
                elif opcode in {opcodes.OP_NOP1, opcodes.OP_NOP4, opcodes.OP_NOP5, opcodes.OP_NOP6, opcodes.OP_NOP7, opcodes.OP_NOP8, opcodes.OP_NOP9, opcodes.OP_NOP10}:
                    if ScriptVerifyFlag.DISCOURAGE_UPGRADABLE_NOPS in verify_flags:
                        raise ScriptException(ScriptError.SCRIPT_ERR_DISCOURAGE_UPGRADABLE_NOPS, f"Script used a reserved opcode {opcode}")
                else:
                    raise ScriptException(ScriptError.SCRIPT_ERR_BAD_OPCODE, f"Script used a reserved or disabled opcode: {opcode}")

            if ((len(stack) + len(altstack)) > Script.MAX_STACK_SIZE) or ((len(stack) + len(altstack)) < 0):
                raise ScriptException(ScriptError.SCRIPT_ERR_STACK_SIZE, "Stack size exceeded range")

        if if_stack:
            raise ScriptException(ScriptError.SCRIPT_ERR_UNBALANCED_CONDITIONAL, "OP_IF/OP_NOTIF without OP_ENDIF")
    
    
    @staticmethod
    def execute_check_lock_time_verify(tx_containing_this: "Transaction", index: int, stack: list[bytes], verify_flags: set["ScriptVerifyFlag"]) -> None:
        if len(stack) < 1:
            raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_CHECKLOCKTIMEVERIFY on a stack with size < 1")

        # Thus as a special case we tell CScriptNum to accept up
        # to 5-byte bignums to avoid year 2038 issue.
        n_lock_time = ScriptUtils.cast_to_int(stack[-1], ScriptVerifyFlag.MINIMALDATA in verify_flags, 5)

        if n_lock_time < 0:
            raise ScriptException(ScriptError.SCRIPT_ERR_NEGATIVE_LOCKTIME, "Negative locktime")

        # There are two kinds of nLockTime, need to ensure we're comparing apples-to-apples
        tx_lock_time = tx_containing_this.lock_time
        from bitcoinj.core.transaction import Transaction
        if not (
            (tx_lock_time < Transaction.LOCKTIME_THRESHOLD and n_lock_time < Transaction.LOCKTIME_THRESHOLD) or
            (tx_lock_time >= Transaction.LOCKTIME_THRESHOLD and n_lock_time >= Transaction.LOCKTIME_THRESHOLD)
        ):
            raise ScriptException(ScriptError.SCRIPT_ERR_UNSATISFIED_LOCKTIME, "Locktime requirement type mismatch")

        # Now that we know we're comparing apples-to-apples, the
        # comparison is a simple numeric one.
        if n_lock_time > tx_lock_time:
            raise ScriptException(ScriptError.SCRIPT_ERR_UNSATISFIED_LOCKTIME, "Locktime requirement not satisfied")

        # Finally the nLockTime feature can be disabled and thus
        # CHECKLOCKTIMEVERIFY bypassed if every txin has been
        # finalized by setting nSequence to maxint. The
        # transaction would be allowed into the blockchain, making
        # the opcode ineffective.
        # 
        # Testing if this vin is not final is sufficient to
        # prevent this condition. Alternatively we could test all
        # inputs, but testing just this input minimizes the data
        # required to prove correct CHECKLOCKTIMEVERIFY execution.
        if not tx_containing_this.inputs[index].has_sequence:
            raise ScriptException(ScriptError.SCRIPT_ERR_UNSATISFIED_LOCKTIME, "Transaction contains a final transaction input for a CHECKLOCKTIMEVERIFY script")
        
    @staticmethod
    def execute_check_sequence_verify(tx_containing_this: "Transaction", index: int, stack: list[bytes], verify_flags: set["ScriptVerifyFlag"]) -> None:
        if len(stack) < 1:
            raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_CHECKSEQUENCEVERIFY on a stack with size < 1")

        # Note that elsewhere numeric opcodes are limited to
        # operands in the range -2**31+1 to 2**31-1, however it is
        # legal for opcodes to produce results exceeding that
        # range. This limitation is implemented by CScriptNum's
        # default 4-byte limit.
        # 
        # Thus as a special case we tell CScriptNum to accept up
        # to 5-byte bignums, which are good until 2**39-1, well
        # beyond the 2**32-1 limit of the nSequence field itself.
        n_sequence = ScriptUtils.cast_to_int(stack[-1], ScriptVerifyFlag.MINIMALDATA in verify_flags, 5)

        # In the rare event that the argument may be < 0 due to some arithmetic being done first,
        # you can always use 0 MAX CHECKSEQUENCEVERIFY.
        if n_sequence < 0:
            raise ScriptException(ScriptError.SCRIPT_ERR_NEGATIVE_LOCKTIME, "Negative sequence")

        # To provide for future soft-fork extensibility, if the operand has the disabled lock-time flag set,
        # CHECKSEQUENCEVERIFY behaves as a NOP.
        from bitcoinj.core.transaction_input import TransactionInput
        if (n_sequence & TransactionInput.SEQUENCE_LOCKTIME_DISABLE_FLAG) != 0:
            return

        # Compare the specified sequence number with the input.
        Script.check_sequence(n_sequence, tx_containing_this, index)
        
    @staticmethod
    def check_sequence(n_sequence: int, tx_containing_this: "Transaction", index: int) -> None:
        # Relative lock times are supported by comparing the passed
        # in operand to the sequence number of the input.
        tx_to_sequence = tx_containing_this.inputs[index].nsequence

        # Fail if the transaction's version number is not set high
        # enough to trigger BIP 68 rules.
        if tx_containing_this.version < 2:
            raise ScriptException(ScriptError.SCRIPT_ERR_UNSATISFIED_LOCKTIME, "Transaction version is < 2")

        # Sequence numbers with their most significant bit set are not
        # consensus constrained. Testing that the transaction's sequence
        # number does not have this bit set prevents using this property
        # to get around a CHECKSEQUENCEVERIFY check.
        from bitcoinj.core.transaction_input import TransactionInput
        if (tx_to_sequence & TransactionInput.SEQUENCE_LOCKTIME_DISABLE_FLAG) != 0:
            raise ScriptException(ScriptError.SCRIPT_ERR_UNSATISFIED_LOCKTIME, "Sequence disable flag is set")

        # Mask off any bits that do not have consensus-enforced meaning
        # before doing the integer comparisons
        n_lock_time_mask = TransactionInput.SEQUENCE_LOCKTIME_TYPE_FLAG | TransactionInput.SEQUENCE_LOCKTIME_MASK
        tx_to_sequence_masked = tx_to_sequence & n_lock_time_mask
        n_sequence_masked = n_sequence & n_lock_time_mask

        # There are two kinds of nSequence: lock-by-blockheight
        # and lock-by-blocktime, distinguished by whether
        # n_sequence_masked < TransactionInput.SEQUENCE_LOCKTIME_TYPE_FLAG.
        #
        # We want to compare apples to apples, so fail the script
        # unless the type of n_sequence_masked being tested is the same as
        # the n_sequence_masked in the transaction.
        if not ((tx_to_sequence_masked < TransactionInput.SEQUENCE_LOCKTIME_TYPE_FLAG and n_sequence_masked < TransactionInput.SEQUENCE_LOCKTIME_TYPE_FLAG) or
                (tx_to_sequence_masked >= TransactionInput.SEQUENCE_LOCKTIME_TYPE_FLAG and n_sequence_masked >= TransactionInput.SEQUENCE_LOCKTIME_TYPE_FLAG)):
            raise ScriptException(ScriptError.SCRIPT_ERR_UNSATISFIED_LOCKTIME, "Relative locktime requirement type mismatch")

        # Now that we know we're comparing apples-to-apples, the
        # comparison is a simple numeric one.
        if n_sequence_masked > tx_to_sequence_masked:
            raise ScriptException(ScriptError.SCRIPT_ERR_UNSATISFIED_LOCKTIME, "Relative locktime requirement not satisfied")

    @staticmethod
    def execute_check_sig(tx_containing_this: "Transaction", index: int, script: "Script", stack: list[bytes], last_code_sep_location: int, opcode: int, verify_flags: set["ScriptVerifyFlag"]) -> None:
        if len(stack) < 2:
            raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_CHECKSIG(VERIFY) on a stack with size < 2")
        
        require_canonical = (
            ScriptVerifyFlag.STRICTENC in verify_flags or
            ScriptVerifyFlag.DERSIG in verify_flags or
            ScriptVerifyFlag.LOW_S in verify_flags
        )
        
        pub_key = stack.pop()
        sig_bytes = stack.pop()

        prog = script.program
        connected_script = prog[last_code_sep_location:]

        out_stream = bytearray()
        try:
            ScriptUtils.write_bytes(out_stream, sig_bytes)
        except:
            raise # cannot happen
        connected_script = Script.remove_all_instances_of_op(connected_script, bytes(out_stream))
        
        sig_valid = False
        try:
            signature = TransactionSignature.decode_from_bitcoin(sig_bytes, require_canonical, ScriptVerifyFlag.LOW_S in verify_flags)
            sig_hash = tx_containing_this.hash_for_signature(index, connected_script, signature.sig_hash_flags)
            sig_valid = ECPubkey(pub_key).ecdsa_verify(signature.to_sig64(), sig_hash)
        except VerificationException.NoncanonicalSignature as e:
            raise ScriptException(ScriptError.SCRIPT_ERR_SIG_DER, "Script contains non-canonical signature")
        except Exception as e:
            # FIXME: brittle message checking
            if pub_key and 'Bad signature' not in str(e):
                raise ScriptException(ScriptError.SCRIPT_ERR_SIG_DER, "Signature parsing failed", e)

        if opcode == opcodes.OP_CHECKSIG:
            stack.append(b'\x01' if sig_valid else b'')
        elif opcode == opcodes.OP_CHECKSIGVERIFY:
            if not sig_valid:
                raise ScriptException(ScriptError.SCRIPT_ERR_CHECKSIGVERIFY, "Script failed OP_CHECKSIGVERIFY")
            
    @staticmethod
    def execute_multi_sig(tx_containing_this: "Transaction", index: int, script: "Script", stack: list[bytes], op_count: int, last_code_sep_location: int, opcode: int, verify_flags: set["ScriptVerifyFlag"]) -> int:
        if len(stack) < 1:
            raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_CHECKMULTISIG(VERIFY) on a stack with size < 1")

        require_canonical = (
            ScriptVerifyFlag.STRICTENC in verify_flags or
            ScriptVerifyFlag.DERSIG in verify_flags or
            ScriptVerifyFlag.LOW_S in verify_flags
        )

        pub_key_count = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
        if pub_key_count < 0 or pub_key_count > Script.MAX_PUBKEYS_PER_MULTISIG:
            raise ScriptException(ScriptError.SCRIPT_ERR_PUBKEY_COUNT, "OP_CHECKMULTISIG(VERIFY) with pubkey count out of range")

        op_count += pub_key_count
        if op_count > Script.MAX_OPS_PER_SCRIPT:
            raise ScriptException(ScriptError.SCRIPT_ERR_OP_COUNT, "Total op count > 201 during OP_CHECKMULTISIG(VERIFY)")
        if len(stack) < pub_key_count + 1:
            raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_CHECKMULTISIG(VERIFY) on a stack with size < num_of_pubkeys + 2")
        
        pubkeys = list[bytes]()
        for _ in range(pub_key_count):
            pubkeys.append(stack.pop())
        
        sig_count = ScriptUtils.cast_to_int(stack.pop(), ScriptVerifyFlag.MINIMALDATA in verify_flags)
        if sig_count < 0 or sig_count > pub_key_count:
            raise ScriptException(ScriptError.SCRIPT_ERR_SIG_COUNT, "OP_CHECKMULTISIG(VERIFY) with sig count out of range")
        if len(stack) < sig_count + 1:
            raise ScriptException(ScriptError.SCRIPT_ERR_INVALID_STACK_OPERATION, "Attempted OP_CHECKMULTISIG(VERIFY) on a stack with size < num_of_pubkeys + num_of_signatures + 3")
        
        sigs = list[bytes]()
        for _ in range(sig_count):
            sigs.append(stack.pop())
            
        prog = script.program
        connected_script = prog[last_code_sep_location:]
        
        for sig in sigs:
            out_stream = bytearray()
            try:
                ScriptUtils.write_bytes(out_stream, sig)
            except:
                raise # Cannot happen
            connected_script = Script.remove_all_instances_of_op(connected_script, bytes(out_stream))
            
        valid = True
        while len(sigs) > 0:
            pub_key = pubkeys.pop(0)
            try:
                sig = TransactionSignature.decode_from_bitcoin(sigs[0], require_canonical, False)
                sig_hash = tx_containing_this.hash_for_signature(index, connected_script, sig.sig_hash_flags)
                if ECPubkey(pub_key).ecdsa_verify(sig.to_sig64(), sig_hash):
                    sigs.pop(0)
            except:
                # There is (at least) one exception that could be hit here (EOFException, if the sig is too short)
                # Because I can't verify there aren't more, we use a very generic Exception catch
                pass
            
            if len(sigs) > len(pubkeys):
                valid = False
                break
            
        null_dummy = stack.pop()
        if ScriptVerifyFlag.NULLDUMMY in verify_flags and len(null_dummy) > 0:
            raise ScriptException(ScriptError.SCRIPT_ERR_SIG_NULLFAIL, f"OP_CHECKMULTISIG(VERIFY) with non-null nulldummy: {null_dummy.hex()}")
        
        if opcode == opcodes.OP_CHECKMULTISIG:
            stack.append(b'\x01' if valid else b'')
        elif opcode == opcodes.OP_CHECKMULTISIGVERIFY:
            if not valid:
                raise ScriptException(ScriptError.SCRIPT_ERR_SIG_NULLFAIL, "Script failed OP_CHECKMULTISIGVERIFY")
        
        return op_count
        
    @staticmethod
    def create_input_script(signature: bytes, pubkey: bytes = None):
        array = bytearray()
        if pubkey is not None:
            ScriptUtils.write_bytes(array, signature) + ScriptUtils.write_bytes(array, pubkey)
        else:
            ScriptUtils.write_bytes(signature)
        return bytes(array)
    
    @staticmethod
    def get_sig_op_count(chunks: list[tuple[int, Optional[bytes], int]], accurate: bool):
        sig_ops = 0
        last_op_code = opcodes.OP_INVALIDOPCODE
        for chunk in chunks:
            if is_opcode(chunk[0]):
                if chunk[0] == opcodes.OP_CHECKSIG or chunk[0] == opcodes.OP_CHECKSIGVERIFY:
                    sig_ops += 1
                elif chunk[0] == opcodes.OP_CHECKMULTISIG or chunk[0] == opcodes.OP_CHECKMULTISIGVERIFY:
                    if accurate and opcodes.OP_1 <= last_op_code <= opcodes.OP_16:
                        sig_ops += ScriptUtils.decode_from_op_n(last_op_code)
                    else:
                        sig_ops += 20
                last_op_code = chunk[0]
        return sig_ops
    
    @staticmethod
    def get_program_sig_op_count(program: bytes):
        chunks = []
        try:
            for x in script_GetOp(program):
                chunks.append(x)
        except:
            # Ignore errors and count up to the parse-able length
            pass
        return Script.get_sig_op_count(chunks, False)
    
    def get_number_of_signatures_required_to_spend(self):
        if ScriptPattern.is_sent_to_multi_sig(self):
            # for N of M CHECKMULTISIG script we will need N signatures to spend
            n_chunk = self.decoded[0]
            return ScriptUtils.decode_from_op_n(n_chunk[0])
        elif ScriptPattern.is_p2pkh(self) or ScriptPattern.is_p2pk(self):
            # P2PKH and P2PK require single sig
            return 1
        elif ScriptPattern.is_p2sh(self):
            raise IllegalStateException("For P2SH number of signatures depends on redeem script")
        else:
            raise IllegalStateException("Unsupported script type")

    def get_number_of_bytes_required_to_spend(self, key: "DeterministicKey", redeem_script):
        if ScriptPattern.is_p2sh(self):
            raise NotImplementedError("P2SH spending not yet supported")
        elif ScriptPattern.is_sent_to_multi_sig(self):
            # scriptSig: OP_0 <sig> [sig] [sig...]
            return self.get_number_of_signatures_required_to_spend() * Script.SIG_SIZE + 1
        elif ScriptPattern.is_p2pk(self):
            # scriptSig: <sig>
            return Script.SIG_SIZE
        elif ScriptPattern.is_p2pkh(self):
            # scriptSig: <sig> <pubkey>
            # uncompressed_pub_key_size = 65 # very conservative
            return Script.SIG_SIZE + (len(key.get_pub_key()) if key.get_pub_key() else 65)
        elif ScriptPattern.is_p2wpkh(self):
            # scriptSig is empty
            # witness: <sig> <pubKey>
            # compressed_pub_key_size = 33
            return Script.SIG_SIZE + (len(key.get_pub_key()) if key.get_pub_key() else 33)
        else:
            raise IllegalStateException("Unsupported script type")
