from collections import defaultdict
from typing import TYPE_CHECKING, Collection, List, Optional
from bisq.core.network.p2p.inventory.model.deviation_severity import DeviationSeverity
from bisq.core.network.p2p.inventory.model.deviation_type import DeviationType

if TYPE_CHECKING:
    from bisq.core.network.p2p.inventory.model.request_info import RequestInfo
    from bisq.core.network.p2p.inventory.model.inventory_item import InventoryItem


class DeviationOfHashes(DeviationType):
    def get_deviation_severity(
        self,
        collection: Collection[List["RequestInfo"]],
        value: Optional[str],
        inventory_item: "InventoryItem",
        current_block_height: str,
    ) -> DeviationSeverity:

        deviation_severity = DeviationSeverity.OK
        if value is None:
            return deviation_severity

        same_hashes_per_hash_list: defaultdict[str, int] = defaultdict(int)

        for request_list in collection:
            if not request_list:
                continue

            last_request = request_list[-1]  # We use last item only
            request_height = last_request.data_map.get(
                inventory_item.get_cls().DAO_STATE_CHAIN_HEIGHT  # small trick for circular dependency fix
            )

            if not (request_height and current_block_height == request_height.value):
                continue

            data = last_request.data_map.get(inventory_item)
            if not data or data.value is None:
                continue

            same_hashes_per_hash_list[data.value] = (
                same_hashes_per_hash_list[data.value] + 1
            )

        if len(same_hashes_per_hash_list) > 1:
            # Convert to list of tuples and sort
            same_hashes_per_hash_list_sorted = sorted(
                [(k, v) for k, v in same_hashes_per_hash_list.items()],
                key=lambda x: x[1],
                reverse=True,
            )

            # It could be that first and any following list entry has same number of hashes, but we ignore that as
            # it is reason enough to alert the operators in case not all hashes are the same.
            if same_hashes_per_hash_list_sorted[0][0] == value:
                # We are in the majority group.
                # We also set a warning to make sure the operators act quickly and to check if there are
                # more severe issues.
                deviation_severity = DeviationSeverity.WARN
            else:
                deviation_severity = DeviationSeverity.ALERT

        return deviation_severity
