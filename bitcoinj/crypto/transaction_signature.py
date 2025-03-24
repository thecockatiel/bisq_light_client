from bitcoinj.core.signature_decode_exception import SignatureDecodeException
from bitcoinj.core.transaction_sig_hash import TransactionSigHash
from bitcoinj.core.verification_exception import VerificationException
from electrum_ecc import (
    CURVE_ORDER,
    ecdsa_der_sig_from_r_and_s,
    ecdsa_sig64_from_r_and_s,
    get_r_and_s_from_ecdsa_der_sig,
) 

HALF_CURVE_ORDER = CURVE_ORDER // 2


def _is_s_canonical(s: int) -> bool:
    return s <= HALF_CURVE_ORDER


# TODO
class TransactionSignature:

    def __init__(self, r: int, s: int, sig_hash_flags: int):
        self.r = r
        self.s = s
        self.sig_hash_flags = sig_hash_flags

    def to_der(self):
        return ecdsa_der_sig_from_r_and_s(self.r, self.s)
    
    def to_sig64(self):
        return ecdsa_sig64_from_r_and_s(self.r, self.s)

    def encode_to_bitcoin(self):
        return self.to_der() + bytes([self.sig_hash_flags])

    @property
    def sig_hash_mode(self) -> "TransactionSigHash":
        mode = self.sig_hash_flags & 0x1F
        if mode == TransactionSigHash.NONE.int_value:
            return TransactionSigHash.NONE
        elif mode == TransactionSigHash.SINGLE.int_value:
            return TransactionSigHash.SINGLE
        else:
            return TransactionSigHash.ALL

    @staticmethod
    def calc_sig_hash_value(mode: "TransactionSigHash", anyone_can_pay: bool) -> int:
        """ "Calculates the byte used in the protocol to represent the combination of mode and anyoneCanPay."""
        # enforce compatibility since this code was made before the SigHash enum was updated
        if not (
            mode == TransactionSigHash.ALL
            or mode == TransactionSigHash.NONE
            or mode == TransactionSigHash.SINGLE
        ):
            raise ValueError("Invalid sig_hash mode")

        sighash_flags = mode.int_value
        if anyone_can_pay:
            sighash_flags |= TransactionSigHash.ANYONECANPAY.int_value

        return sighash_flags

    @staticmethod
    def is_encoding_canonical(signature: bytes):
        """
        Returns true if the given signature is has canonical encoding, and will thus be accepted as standard by
        Bitcoin Core. DER and the SIGHASH encoding allow for quite some flexibility in how the same structures
        are encoded, and this can open up novel attacks in which a man in the middle takes a transaction and then
        changes its signature such that the transaction hash is different but it's still valid. This can confuse wallets
        and generally violates people's mental model of how Bitcoin should work, thus, non-canonical signatures are now
        not relayed by default.
        """
        # See Bitcoin Core's IsCanonicalSignature, https://bitcointalk.org/index.php?topic=8392.msg127623#msg127623
        # A canonical signature exists of: <30> <total len> <02> <len R> <R> <02> <len S> <S> <hashtype>
        # Where R and S are not negative (their first byte has its highest bit not set), and not
        # excessively padded (do not start with a 0 byte, unless an otherwise negative number follows,
        # in which case a single 0 byte is necessary and even required).

        # Empty signatures, while not strictly DER encoded, are allowed.
        if len(signature) == 0:
            return True

        if len(signature) < 9 or len(signature) > 73:
            return False

        hash_type = (
            signature[-1] & 0xFF
        ) & ~TransactionSigHash.ANYONECANPAY.int_value  # mask the byte to prevent sign-extension hurting us
        if (
            hash_type < TransactionSigHash.ALL.int_value
            or hash_type > TransactionSigHash.SINGLE.int_value
        ):
            return False

        #                    "wrong type"                  "wrong length marker"
        if (signature[0] & 0xFF) != 0x30 or (signature[1] & 0xFF) != len(signature) - 3:
            return False

        len_r = signature[3] & 0xFF
        if 5 + len_r >= len(signature) or len_r == 0:
            return False
        len_s = signature[5 + len_r] & 0xFF

        if len_r + len_s + 7 != len(signature) or len_s == 0:
            return False

        #       R value type mismatch              R value negative
        if (signature[2] & 0xFF) != 0x02 or (signature[4] & 0x80) == 0x80:
            return False
        if len_r > 1 and signature[4] == 0x00 and (signature[5] & 0x80) != 0x80:
            return False  # R value excessively padded

        #        S value type mismatch                    S value negative
        if (signature[len_r + 4] & 0xFF) != 0x02 or (
            signature[len_r + 6] & 0x80
        ) == 0x80:
            return False

        if (
            len_s > 1
            and signature[len_r + 6] == 0x00
            and (signature[len_r + 7] & 0x80) != 0x80
        ):
            return False  # S value excessively padded

        return True

    @staticmethod
    def decode_from_bitcoin(
        bytes_: bytes,
        require_canonical_encoding: bool,
        require_canonical_s_value: bool,
        flags: int = None,
        anyone_can_pay: bool = False,
    ) -> "TransactionSignature":
        """
        Returns a decoded signature.

        Args:
            bytes_ (bytes): The bytes representing the Bitcoin signature.
            require_canonical_encoding (bool): If the encoding of the signature must be canonical.
            require_canonical_s_value (bool): If the S-value must be canonical (below half the order of the curve).
        Returns:
            bytes: The decoded signature.
        Raises:
            SignatureDecodeException: if the signature is unparseable in some way.
            VerificationException: if the signature is invalid.
        """

        if (
            require_canonical_encoding
            and not TransactionSignature.is_encoding_canonical(bytes_)
        ):
            raise VerificationException.NoncanonicalSignature()

        try:
            r, s = get_r_and_s_from_ecdsa_der_sig(bytes_[:-1])
        except Exception as e:
            raise SignatureDecodeException(e)
        if require_canonical_s_value and not _is_s_canonical(s):
            # its canonical if s is below half the order of the curve
            raise VerificationException("S-value is not canonical.")

        # In Bitcoin, any value of the final byte is valid, but not necessarily canonical. See docs for
        # isEncodingCanonical to learn more about this. So we must store the exact byte found.
        return TransactionSignature(
            r,
            s,
            (
                TransactionSignature.calc_sig_hash_value(flags, anyone_can_pay)
                if flags
                else bytes_[-1]
            ),
        )
