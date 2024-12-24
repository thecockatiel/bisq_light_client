from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from global_container import GlobalContainer
    from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost


class CorePersistedDataHost:

    @staticmethod
    def get_persisted_data_hosts(global_container: "GlobalContainer"):
        persisted_data_hosts: list["PersistedDataHost"] = []
        persisted_data_hosts.append(global_container.preferences)
        persisted_data_hosts.append(global_container.user)
        persisted_data_hosts.append(global_container.address_entry_list)
        persisted_data_hosts.append(global_container.open_offer_manager)
        persisted_data_hosts.append(global_container.trade_manager)
        persisted_data_hosts.append(global_container.closed_tradable_manager)
        persisted_data_hosts.append(global_container.bsq_swap_trade_manager)
        persisted_data_hosts.append(global_container.failed_trades_manager)
        persisted_data_hosts.append(global_container.arbitration_dispute_list_service)
        persisted_data_hosts.append(global_container.mediation_dispute_list_service)
        persisted_data_hosts.append(global_container.refund_dispute_list_service)
        persisted_data_hosts.append(global_container.p2p_data_storage)
        persisted_data_hosts.append(global_container.peer_manager)
        persisted_data_hosts.append(global_container.mailbox_message_service)
        persisted_data_hosts.append(global_container.ignored_mailbox_service)
        persisted_data_hosts.append(global_container.removed_payloads_service)
        # rest of the implementation of java were dao related, so we did not add them here
        return persisted_data_hosts