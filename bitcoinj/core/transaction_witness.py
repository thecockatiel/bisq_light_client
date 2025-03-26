from typing import Optional, Union
from bitcoinj.crypto.ec_utils import is_compressed_pubkey
from bitcoinj.crypto.transaction_signature import TransactionSignature
from bitcoinj.script.script import Script
from electrum_min.bitcoin import construct_witness
from utils.java_compat import java_bytes_hashcode
from utils.preconditions import check_argument
from utils.python_helpers import classproperty


MAX_INITIAL_ARRAY_LENGTH = 20


class TransactionWitness:
    __slots__ = ("_pushed",)
    EMPTY: "TransactionWitness" = None

    def __init__(self, push_count=0):
        self._pushed: list[bytes] = [None] * min(push_count, MAX_INITIAL_ARRAY_LENGTH)

    @property
    def witness_elements(self):
        return self._pushed
    
    def construct_witness(self):
        """constructs a witness from the pushes and returns it"""
        return bytes.fromhex(construct_witness(self._pushed))

    @staticmethod
    def redeem_p2wpkh(signature: Optional[TransactionSignature], pub_key_bytes: bytes):
        """
        Creates the stack pushes necessary to redeem a P2WPKH output. If given signature is null, an empty push will be used as a placeholder.
        """
        check_argument(
            is_compressed_pubkey(pub_key_bytes), "only compressed keys allowed"
        )
        witness = TransactionWitness(2)
        witness.set_push(
            0, signature.encode_to_bitcoin() if signature is not None else bytes()
        )  # signature
        witness.set_push(1, pub_key_bytes)  # pubkey
        return witness

    @staticmethod
    def redeem_p2wsh(witness_script: Union["Script", bytes], *signatures: TransactionSignature):
        """
        Creates the stack pushes necessary to redeem a P2WSH output.
        """
        if isinstance(witness_script, Script):
            witness_script = witness_script.program
        witness = TransactionWitness(len(signatures) + 2)
        witness.set_push(0, bytes())
        for i, signature in enumerate(signatures):
            witness.set_push(i + 1, signature.encode_to_bitcoin())
        witness.set_push(len(signatures) + 1, witness_script)
        return witness

    def get_push(self, index: int):
        return self._pushed[index]

    def get_push_count(self):
        return len(self._pushed)

    def set_push(self, i: int, value: bytes):
        while i >= len(self._pushed):
            self._pushed.append(bytes())
        self._pushed[i] = value

    def __str__(self):
        string_pushes = []
        for j in range(self.get_push_count()):
            push = self.get_push(j)
            if push is None:
                string_pushes.append("NULL")
            elif len(push) == 0:
                string_pushes.append("EMPTY")
            else:
                string_pushes.append(push.hex())
        return " ".join(string_pushes)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, TransactionWitness):
            return False
        if len(self._pushed) != len(other._pushed):
            return False
        for i in range(len(self._pushed)):
            if self._pushed[i] != other._pushed[i]:
                return False
        return True

    def __hash__(self):
        result = 1
        for push in self._pushed:
            result = 31 * result + (0 if push is None else java_bytes_hashcode(push))
        return result


TransactionWitness.EMPTY = TransactionWitness(0)
