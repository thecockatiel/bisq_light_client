from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional

from bisq.core.network.p2p.inventory.model.deviation_severity import DeviationSeverity

if TYPE_CHECKING:
    from bisq.core.network.p2p.inventory.model.inventory_item import InventoryItem


class RequestInfo:
    """
    request_start_time is in ms
    """
    
    def __init__(self, request_start_time: int):
        self.request_start_time = request_start_time
        self.response_time: int = 0
        self.error_message: Optional[str] = None
        self.data_map: Dict["InventoryItem", "RequestInfo.Data"] = {}

    def get_display_value(self, inventory_item: "InventoryItem") -> str:
        value = self.get_value(inventory_item)
        return value if value is not None else "n/a"

    def get_value(self, inventory_item: "InventoryItem") -> Optional[str]:
        if inventory_item in self.data_map:
            return self.data_map[inventory_item].value
        return None

    def has_error(self) -> bool:
        return bool(self.error_message)

    @dataclass(frozen=True)
    class Data:
        value: str
        average: Optional[float]
        deviation: float
        deviation_severity: DeviationSeverity
        persistent_warning: bool
        persistent_alert: bool

        def __str__(self) -> str:
            return (
                "InventoryData{\n"
                f"     value='{self.value}'\n"
                f"     average={self.average}\n"
                f"     deviation={self.deviation}\n"
                f"     deviation_severity={self.deviation_severity}\n"
                f"     persistent_warning={self.persistent_warning}\n"
                f"     persistent_alert={self.persistent_alert}\n"
                "}"
            )
