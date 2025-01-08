from bitcoinj.core.utils import decode_mpi
from bitcoinj.script.script_error import ScriptError
from bitcoinj.script.script_exception import ScriptException
from electrum_min.bitcoin import opcodes

class ScriptUtils:
    
    @staticmethod
    def stack_to_string(stack: list[bytes]):
        parts = [f'[{push.hex()}]' for push in stack]
        return ' '.join(parts)

    @staticmethod
    def cast_to_bool(data: bytes) -> bool:
        for i in range(len(data)):
            # "Can be negative zero" - Bitcoin Core (see OpenSSL's BN_bn2mpi)
            if data[i] != 0:
                return not (i == len(data) - 1 and (data[i] & 0xFF) == 0x80)
        return False

    @staticmethod
    def decode_from_op_n(opcode: int):
        if not ((opcode == opcodes.OP_0 or opcode == opcodes.OP_1NEGATE) or (opcodes.OP_1 <= opcode <= opcodes.OP_16)):
            raise ValueError(f"decode_from_op_n called on non OP_N opcode: {opcodes[opcode].name}")
        if opcode == opcodes.OP_0:
            return 0
        elif opcode == opcodes.OP_1NEGATE:
            return -1
        else:
            return opcode + 1 - opcodes.OP_1
        
    @staticmethod
    def encode_to_op_n(value: int):
        if value < -1 or value > 16:
            raise ValueError(f"encode_to_op_n called for {value} which we cannot encode in an opcode.")
        if value == 0:
            return opcodes.OP_0
        elif value == -1:
            return opcodes.OP_1NEGATE
        else:
            return value - 1 + opcodes.OP_1

    @staticmethod
    def cast_to_int(data: bytes, require_minimal: bool, max_length = 4) -> int:
        """Cast a script chunk to an int"""
        if len(data) > max_length:
            raise ScriptException(ScriptError.SCRIPT_ERR_UNKNOWN_ERROR, f"Script attempted to use an integer larger than {max_length} bytes")

        if require_minimal and len(data) > 0:
            # Check that the number is encoded with the minimum possible number of bytes.
            #
            # If the most-significant-byte - excluding the sign bit - is zero
            # then we're not minimal. Note how this test also rejects the
            # negative-zero encoding, 0x80.
            if (data[-1] & 0x7f) == 0:
            # One exception: if there's more than one byte and the most significant bit of the
            # second-most-significant-byte is set it would conflict with the sign bit.
            # An example of this case is +-255, which encode to 0xff00 and 0xff80 respectively.
            # (big-endian).
                if len(data) <= 1 or (data[-2] & 0x80) == 0:
                    raise ScriptException(ScriptError.SCRIPT_ERR_UNKNOWN_ERROR, "non-minimally encoded script number")

        return decode_mpi(bytes(reversed(data)), False)

    @staticmethod
    def write_bytes(array: bytearray, buf: bytes):
        """
        Writes out the given byte buffer to the output stream with the correct opcode prefix
        
        To write an integer call writeBytes(out, Utils.reverseBytes(Utils.encodeMPI(val, false)));
        """
        if len(buf) < opcodes.OP_PUSHDATA1:
            array.append(len(buf))
            array.extend(buf)
        elif len(buf) < 256:
            array.append(opcodes.OP_PUSHDATA1)
            array.append(len(buf))
            array.extend(buf)
        elif len(buf) < 65536:
            array.append(opcodes.OP_PUSHDATA2)
            array.extend(len(buf).to_bytes(2, 'little'))
            array.extend(buf)
        else:
            raise RuntimeError("Unimplemented")
