
from typing import Optional, Union
from bitcoinj.script.script_opcodes import get_opcode_name, get_push_data_name, is_opcode
from bitcoinj.script.script_utils import ScriptUtils
from electrum_min.bitcoin import opcodes

def is_push_data(op_code: int) -> bool:
    return op_code <= opcodes.OP_16

def is_shortest_possible_push_data(op_code: int, data: Union[bytes, None]) -> bool:
    if not is_push_data(op_code):
        raise ValueError(f"opcode {op_code} is not a pushdata opcode")
    if data is None:
        return True  # OP_N
    if len(data) == 0:
        return op_code == opcodes.OP_0
    if len(data) == 1:
        b = data[0]
        if 0x01 <= b <= 0x10:
            return op_code == opcodes.OP_1 + b - 1
        if b == 0x81:
            return op_code == opcodes.OP_1NEGATE
    if len(data) < opcodes.OP_PUSHDATA1:
        return op_code == len(data)
    if len(data) < 256:
        return op_code == opcodes.OP_PUSHDATA1
    if len(data) < 65536:
        return op_code == opcodes.OP_PUSHDATA2

    # can never be used, but implemented for completeness
    return op_code == opcodes.OP_PUSHDATA4

def chunk_to_string(chunk: tuple[int, Optional[bytes], int]):
    opcode, data, _ = chunk
    result = ""
    if is_opcode(opcode):
        result += get_opcode_name(opcode)
    elif data:
        # Data chunk
        result += get_push_data_name(opcode) + f"[{data.hex()}]"
    else:
        # small num
        result += ScriptUtils.decode_from_op_n(opcode)
    return result
