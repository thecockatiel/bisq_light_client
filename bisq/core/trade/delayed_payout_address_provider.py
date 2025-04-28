from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING

from bisq.core.dao.governance.param.param import Param

if TYPE_CHECKING:
    from bisq.core.dao.dao_facade import DaoFacade

class DelayedPayoutAddressProvider:
    INITIAL_BM_ADDRESS = (
        "1BVxNn3T12veSK6DgqwU4Hdn7QHcDDRag7"  # Initial DAO donation address
    )
    BM2019_ADDRESS = "3EtUWqsGThPtjwUczw27YCo6EWvQdaPUyp"  # burning2019
    BM2_ADDRESS = "3A8Zc1XioE2HRzYfbb5P8iemCS72M6vRJV"  # burningman2
    # burningman3 https://github.com/bisq-network/roles/issues/80#issuecomment-723577776
    BM3_ADDRESS = "34VLFgtFKAtwTdZ5rengTT2g2zC99sWQLC"

    @staticmethod
    def get_delayed_payout_address(dao_facade: "DaoFacade"):
        address = dao_facade.get_param_value(Param.RECIPIENT_BTC_ADDRESS)
        if DelayedPayoutAddressProvider.is_outdated_address(address):
            logger = get_ctx_logger(__name__)
            logger.warning(
                "Outdated delayed payout address. "
                + "This can be the case if the DAO is deactivated or if the user has an invalid DAO state."
                + "We set the address to the recent one (BM3_ADDRESS)."
            )
            return DelayedPayoutAddressProvider.get_address()
        return address

    @staticmethod
    def is_outdated_address(address):
        return address in [
            DelayedPayoutAddressProvider.INITIAL_BM_ADDRESS,
            DelayedPayoutAddressProvider.BM2019_ADDRESS,
            DelayedPayoutAddressProvider.BM2_ADDRESS,
        ]

    @staticmethod
    def get_address():
        return DelayedPayoutAddressProvider.BM3_ADDRESS
