from bisq.common.payload import Payload
import grpc_pb2


class BsqBalanceInfo(Payload):
    EMPTY: "BsqBalanceInfo" = None  # initialized after class creation

    def __init__(
        self,
        available_balance: int,
        unverified_balance: int,
        unconfirmed_change_balance: int,
        locked_for_voting_balance: int,
        lockup_bonds_balance: int,
        unlocking_bonds_balance: int,
    ):
        # All balances are in BSQ satoshis.
        self.available_balance = available_balance
        self.unverified_balance = unverified_balance
        self.unconfirmed_change_balance = unconfirmed_change_balance
        self.locked_for_voting_balance = locked_for_voting_balance
        self.lockup_bonds_balance = lockup_bonds_balance
        self.unlocking_bonds_balance = unlocking_bonds_balance

    @staticmethod
    def value_of(
        available_balance: int,
        unverified_balance: int,
        unconfirmed_change_balance: int,
        locked_for_voting_balance: int,
        lockup_bonds_balance: int,
        unlocking_bonds_balance: int,
    ) -> "BsqBalanceInfo":
        # Convenience for creating a model instance instead of a proto.
        return BsqBalanceInfo(
            available_balance,
            unverified_balance,
            unconfirmed_change_balance,
            locked_for_voting_balance,
            lockup_bonds_balance,
            unlocking_bonds_balance,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    # JAVA TODO rename availableConfirmedBalance in proto if possible
    def to_proto_message(self):
        return grpc_pb2.BsqBalanceInfo(
            available_confirmed_balance=self.available_balance,
            unverified_balance=self.unverified_balance,
            unconfirmed_change_balance=self.unconfirmed_change_balance,
            locked_for_voting_balance=self.locked_for_voting_balance,
            lockup_bonds_balance=self.lockup_bonds_balance,
            unlocking_bonds_balance=self.unlocking_bonds_balance,
        )

    @staticmethod
    def from_proto(proto: grpc_pb2.BsqBalanceInfo) -> "BsqBalanceInfo":
        return BsqBalanceInfo(
            proto.available_confirmed_balance,
            proto.unverified_balance,
            proto.unconfirmed_change_balance,
            proto.locked_for_voting_balance,
            proto.lockup_bonds_balance,
            proto.unlocking_bonds_balance,
        )

    def __str__(self) -> str:
        return (
            f"BsqBalanceInfo{{availableBalance={self.available_balance}, "
            f"unverifiedBalance={self.unverified_balance}, "
            f"unconfirmedChangeBalance={self.unconfirmed_change_balance}, "
            f"lockedForVotingBalance={self.locked_for_voting_balance}, "
            f"lockupBondsBalance={self.lockup_bonds_balance}, "
            f"unlockingBondsBalance={self.unlocking_bonds_balance}}}"
        )


BsqBalanceInfo.EMPTY = BsqBalanceInfo(-1, -1, -1, -1, -1, -1)
