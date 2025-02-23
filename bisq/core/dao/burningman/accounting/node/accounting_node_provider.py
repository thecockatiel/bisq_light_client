from typing import TYPE_CHECKING
from bisq.common.setup.log_setup import get_logger
from bisq.core.user.preferences import Preferences

if TYPE_CHECKING:
    from bisq.core.dao.burningman.accounting.node.lite.accounting_lite_node import (
        AccountingLiteNode,
    )
    from bisq.core.dao.burningman.accounting.node.full.accounting_full_node import (
        AccountingFullNode,
    )
    from bisq.core.dao.burningman.accounting.node.accounting_node import AccountingNode

logger = get_logger(__name__)


class AccountingNodeProvider:
    def __init__(
        self,
        lite_node: "AccountingLiteNode",
        full_node: "AccountingFullNode",
        is_bm_full_node_from_options: bool,
        preferences: "Preferences",
    ):
        rpc_user = preferences.get_rpc_user()
        rpc_pw = preferences.get_rpc_pw()
        rpc_data_set = rpc_user and rpc_pw and preferences.get_block_notify_port() > 0
        full_bm_accounting_node = preferences.is_full_bm_accounting_node()

        if (full_bm_accounting_node or is_bm_full_node_from_options) and rpc_data_set:
            logger.error(
                "Using full accounting node is not supported yet. falling back to lite node"
            )
            self.accounting_node: "AccountingNode" = lite_node
        else:
            self.accounting_node: "AccountingNode" = lite_node
