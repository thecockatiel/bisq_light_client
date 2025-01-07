# copied over from electrum and changed to map so that we don't need to substring the OP_ prefix out every time we need it.
from electrum_min.bitcoin import opcodes


opcode_to_name = {
    # push value
    0x00: "0",
    0x4c: "PUSHDATA1",
    0x4d: "PUSHDATA2",
    0x4e: "PUSHDATA4",
    0x4f: "1NEGATE",
    0x50: "RESERVED",
    0x51: "1",
    0x52: "2",
    0x53: "3",
    0x54: "4",
    0x55: "5",
    0x56: "6",
    0x57: "7",
    0x58: "8",
    0x59: "9",
    0x5a: "10",
    0x5b: "11",
    0x5c: "12",
    0x5d: "13",
    0x5e: "14",
    0x5f: "15",
    0x60: "16",

    # control
    0x61: "NOP",
    0x62: "VER",
    0x63: "IF",
    0x64: "NOTIF",
    0x65: "VERIF",
    0x66: "VERNOTIF",
    0x67: "ELSE",
    0x68: "ENDIF",
    0x69: "VERIFY",
    0x6a: "RETURN",

    # stack ops
    0x6b: "TOALTSTACK",
    0x6c: "FROMALTSTACK",
    0x6d: "2DROP",
    0x6e: "2DUP",
    0x6f: "3DUP",
    0x70: "2OVER",
    0x71: "2ROT",
    0x72: "2SWAP",
    0x73: "IFDUP",
    0x74: "DEPTH",
    0x75: "DROP",
    0x76: "DUP",
    0x77: "NIP",
    0x78: "OVER",
    0x79: "PICK",
    0x7a: "ROLL",
    0x7b: "ROT",
    0x7c: "SWAP",
    0x7d: "TUCK",

    # splice ops
    0x7e: "CAT",
    0x7f: "SUBSTR",
    0x80: "LEFT",
    0x81: "RIGHT",
    0x82: "SIZE",

    # bit logic
    0x83: "INVERT",
    0x84: "AND",
    0x85: "OR",
    0x86: "XOR",
    0x87: "EQUAL",
    0x88: "EQUALVERIFY",
    0x89: "RESERVED1",
    0x8a: "RESERVED2",

    # numeric
    0x8b: "1ADD",
    0x8c: "1SUB",
    0x8d: "2MUL",
    0x8e: "2DIV",
    0x8f: "NEGATE",
    0x90: "ABS",
    0x91: "NOT",
    0x92: "0NOTEQUAL",

    0x93: "ADD",
    0x94: "SUB",
    0x95: "MUL",
    0x96: "DIV",
    0x97: "MOD",
    0x98: "LSHIFT",
    0x99: "RSHIFT",

    0x9a: "BOOLAND",
    0x9b: "BOOLOR",
    0x9c: "NUMEQUAL",
    0x9d: "NUMEQUALVERIFY",
    0x9e: "NUMNOTEQUAL",
    0x9f: "LESSTHAN",
    0xa0: "GREATERTHAN",
    0xa1: "LESSTHANOREQUAL",
    0xa2: "GREATERTHANOREQUAL",
    0xa3: "MIN",
    0xa4: "MAX",

    0xa5: "WITHIN",

    # crypto
    0xa6: "RIPEMD160",
    0xa7: "SHA1",
    0xa8: "SHA256",
    0xa9: "HASH160",
    0xaa: "HASH256",
    0xab: "CODESEPARATOR",
    0xac: "CHECKSIG",
    0xad: "CHECKSIGVERIFY",
    0xae: "CHECKMULTISIG",
    0xaf: "CHECKMULTISIGVERIFY",

    # expansion
    0xb0: "NOP1",
    0xb1: "CHECKLOCKTIMEVERIFY",
    0xb2: "CHECKSEQUENCEVERIFY",
    0xb3: "NOP4",
    0xb4: "NOP5",
    0xb5: "NOP6",
    0xb6: "NOP7",
    0xb7: "NOP8",
    0xb8: "NOP9",
    0xb9: "NOP10",

    0xff: "INVALIDOPCODE",    
}

def get_opcode_name(opcode: int):
    return opcode_to_name.get(opcode, f"NON_OP({opcode})")

def get_push_data_name(opcode: int):
    return opcode_to_name.get(opcode, f"PUSHDATA({opcode})")

def is_opcode(opcode: int):
    return opcode > opcodes.OP_PUSHDATA4
