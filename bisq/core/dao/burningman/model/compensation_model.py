from typing import Optional


class CompensationModel:
    def __init__(
        self,
        address: str,
        is_custom_address: bool,
        amount: int,
        decayed_amount: int,
        height: int,
        tx_id: str,
        output_index: Optional[int],
        date: int,
        cycle_index: int,
    ):
        self.address = address
        self.is_custom_address = is_custom_address
        self.amount = amount
        self.decayed_amount = decayed_amount
        self.height = height
        self.tx_id = tx_id
        self.output_index = (
            output_index  # Only set for genesis tx outputs as needed for sorting
        )
        self.date = date
        self.cycle_index = cycle_index

    @staticmethod
    def from_compensation_request(
        address: str,
        is_custom_address: bool,
        amount: int,
        decayed_amount: int,
        height: int,
        tx_id: str,
        date: int,
        cycle_index: int,
    ) -> "CompensationModel":
        return CompensationModel(
            address,
            is_custom_address,
            amount,
            decayed_amount,
            height,
            tx_id,
            None,
            date,
            cycle_index,
        )

    @staticmethod
    def from_genesis_output(
        address: str,
        amount: int,
        decayed_amount: int,
        height: int,
        tx_id: str,
        output_index: int,
        date: int,
    ) -> "CompensationModel":
        return CompensationModel(
            address,
            False,
            amount,
            decayed_amount,
            height,
            tx_id,
            output_index,
            date,
            0,
        )

    def __str__(self):
        return (
            f"\n          CompensationModel{{"
            f"\r\n                address='{self.address}',"
            f"\r\n                isCustomAddress='{self.is_custom_address}',"
            f"\r\n               amount={self.amount},"
            f"\r\n               decayedAmount={self.decayed_amount},"
            f"\r\n               height={self.height},"
            f"\r\n               txId='{self.tx_id}',"
            f"\r\n               outputIndex={self.output_index},"
            f"\r\n               date={self.date},"
            f"\r\n               cycleIndex={self.cycle_index}"
            f"\r\n          }}"
        )

    def __eq__(self, other):
        if not isinstance(other, CompensationModel):
            return False
        return (
            self.address == other.address
            and self.is_custom_address == other.is_custom_address
            and self.amount == other.amount
            and self.decayed_amount == other.decayed_amount
            and self.height == other.height
            and self.tx_id == other.tx_id
            and self.output_index == other.output_index
            and self.date == other.date
            and self.cycle_index == other.cycle_index
        )

    def __hash__(self):
        return hash(
            (
                self.address,
                self.is_custom_address,
                self.amount,
                self.decayed_amount,
                self.height,
                self.tx_id,
                self.output_index,
                self.date,
                self.cycle_index,
            )
        )
