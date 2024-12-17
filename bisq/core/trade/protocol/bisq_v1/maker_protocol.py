from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.trade.protocol.bisq_v1.messages.inputs_for_deposit_tx_request import (
        InputsForDepositTxRequest,
    )


class MakerProtocol(ABC):
    @abstractmethod
    def handle_take_offer_request(
        self,
        message: "InputsForDepositTxRequest",
        maker: "NodeAddress",
        error_message_handler: "ErrorMessageHandler",
    ):
        pass
