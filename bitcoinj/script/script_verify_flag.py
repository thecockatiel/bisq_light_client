from enum import IntEnum


class ScriptVerifyFlag(IntEnum):
    """
    Flags to pass to Script#correctlySpends
    Note currently only P2SH, DERSIG and NULLDUMMY are actually supported.
    """
    
    P2SH = 0
    """Enable BIP16-style subscript evaluation."""
    
    STRICTENC = 1
    """Passing a non-strict-DER signature or one with undefined hashtype to a checksig operation causes script failure."""
    
    DERSIG = 2
    """Passing a non-strict-DER signature to a checksig operation causes script failure (softfork safe, BIP66 rule 1)."""
    
    LOW_S = 3
    """Passing a non-strict-DER signature or one with S > order/2 to a checksig operation causes script failure."""
    
    NULLDUMMY = 4
    """Verify dummy stack item consumed by CHECKMULTISIG is of zero-length."""
    
    SIGPUSHONLY = 5
    """Using a non-push operator in the scriptSig causes script failure (softfork safe, BIP62 rule 2)."""
    
    MINIMALDATA = 6
    """Require minimal encodings for all push operations."""
    
    DISCOURAGE_UPGRADABLE_NOPS = 7
    """Discourage use of NOPs reserved for upgrades (NOP1-10)."""
    
    CLEANSTACK = 8
    """Require that only a single stack element remains after evaluation."""
    
    CHECKLOCKTIMEVERIFY = 9
    """Enable CHECKLOCKTIMEVERIFY operation."""
    
    CHECKSEQUENCEVERIFY = 10
    """Enable CHECKSEQUENCEVERIFY operation."""
