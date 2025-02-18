from enum import IntEnum


class BondState(IntEnum):
    """
    Holds the different states of a bond.
    Used also in string properties ("dao.bond.bondState.*")
    """

    UNDEFINED = 0
    READY_FOR_LOCKUP = 1  # Accepted by voting (if role) but no lockup tx made yet.
    LOCKUP_TX_PENDING = (
        2  # Tx broadcasted but not confirmed. Used only by tx publisher.
    )
    LOCKUP_TX_CONFIRMED = 3
    UNLOCK_TX_PENDING = (
        4  # Tx broadcasted but not confirmed. Used only by tx publisher.
    )
    UNLOCK_TX_CONFIRMED = 5
    UNLOCKING = 6  # Lock time still not expired
    UNLOCKED = 7  # Fully unlocked
    CONFISCATED = 8  # Bond got confiscated by DAO voting

    @property
    def is_active(self):
        return self in {
            BondState.LOCKUP_TX_CONFIRMED,
            BondState.UNLOCK_TX_PENDING,
            BondState.UNLOCK_TX_CONFIRMED,
            BondState.UNLOCKING,
        }
