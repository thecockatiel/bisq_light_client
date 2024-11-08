from collections import defaultdict
from typing import TYPE_CHECKING, Collection, Dict, List, Optional
from bisq.core.network.p2p.inventory.model.deviation_severity import DeviationSeverity
from bisq.core.network.p2p.inventory.model.deviation_type import DeviationType

if TYPE_CHECKING:
    from bisq.core.network.p2p.inventory.model.request_info import RequestInfo
    from bisq.core.network.p2p.inventory.model.inventory_item import InventoryItem


class DeviationByIntegerDiff(DeviationType):
    def __init__(self, warn_trigger: int, alert_trigger: int):
        self.warn_trigger = warn_trigger
        self.alert_trigger = alert_trigger

    def get_deviation_severity(
        self,
        collection: Collection[List["RequestInfo"]],
        value: Optional[str],
        inventory_item: "InventoryItem",
    ) -> DeviationSeverity:
        deviation_severity = DeviationSeverity.OK
        if value is None:
            return deviation_severity

        same_items_by_value: defaultdict[str, int] = defaultdict(int)

        for item_list in collection:
            if not item_list:
                continue

            last_item = item_list[-1]  # Get last item only
            data = last_item.data_map.get(inventory_item)

            if not data or data.value is None:
                continue

            same_items_by_value[data.value] = same_items_by_value[data.value] + 1

        if len(same_items_by_value) > 1:
            # Convert to list of tuples and sort
            same_items = [(k, v) for k, v in same_items_by_value.items()]
            same_items.sort(key=lambda x: x[1], reverse=True)

            majority = same_items[0][0]
            if majority != value:
                majority_as_int = int(majority)
                value_as_int = int(value)
                diff = abs(majority_as_int - value_as_int)

                if diff >= self.alert_trigger:
                    deviation_severity = DeviationSeverity.ALERT
                elif diff >= self.warn_trigger:
                    deviation_severity = DeviationSeverity.WARN
                else:
                    deviation_severity = DeviationSeverity.OK

        return deviation_severity
