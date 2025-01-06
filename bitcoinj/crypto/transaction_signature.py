from bitcoinj.core.transaction_sig_hash import TransactionSigHash


#TODO
class TransactionSignature:
    
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
        if len(signature) < 9 or len(signature) > 73:
            return False
        
        hash_type = (signature[-1] & 0xff) & ~TransactionSigHash.ANYONECANPAY.int_value # mask the byte to prevent sign-extension hurting us
        if hash_type < TransactionSigHash.ALL.int_value or hash_type > TransactionSigHash.SINGLE.int_value:
            return False
        
        #                    "wrong type"                  "wrong length marker"
        if (signature[0] & 0xff) != 0x30 or (signature[1] & 0xff) != len(signature) - 3:
            return False
        
        len_r = signature[3] & 0xff
        if 5 + len_r >= len(signature) or len_r == 0:
            return False
        len_s = signature[5 + len_r] & 0xff
        
        if len_r + len_s + 7 != len(signature) or len_s == 0:
            return False
        
        #       R value type mismatch              R value negative
        if (signature[2] & 0xff) != 0x02 or (signature[4] & 0x80) == 0x80:
            return False
        if len_r > 1 and signature[4] == 0x00 and (signature[5] & 0x80) != 0x80:
            return False # R value excessively padded
        
        #        S value type mismatch                    S value negative
        if (signature[len_r + 4] & 0xff) != 0x02 or (signature[len_r + 6] & 0x80) == 0x80:
            return False
        
        if len_s > 1 and signature[len_r + 6] == 0x00 and (signature[len_r + 7] & 0x80) != 0x80:
            return False # S value excessively padded
        
        return True
        