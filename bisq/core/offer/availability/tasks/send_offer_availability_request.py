from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.taskrunner.task import Task
from bisq.common.taskrunner.task_runner import TaskRunner
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.offer.availability.offer_availability_model import OfferAvailabilityModel
from bisq.core.offer.availability.messages.offer_availability_request import OfferAvailabilityRequest
from bisq.core.offer.offer_state import OfferState


class SendOfferAvailabilityRequest(Task[OfferAvailabilityModel]):
    
    def __init__(self, task_handler: TaskRunner[OfferAvailabilityModel], model: OfferAvailabilityModel):
        super().__init__(task_handler, model)
        self.logger = get_ctx_logger(__name__)
        
    def run(self):
        try:
            self.run_intercept_hook()
            
            burning_man_selection_height = self.model.delayed_payout_tx_receiver_service.get_burning_man_selection_height()
            message = OfferAvailabilityRequest(
                offer_id=self.model.offer.id,
                pub_key_ring=self.model.pub_key_ring,
                takers_trade_price=self.model.get_takers_trade_price(),
                is_taker_api_user=self.model.is_taker_api_user,
                burning_man_selection_height=burning_man_selection_height
            )
            self.logger.info(f"Send {message.__class__.__name__} with offerId {message.offer_id} and uid {message.uid} to peer {self.model.peer_node_address}")

            class MessageListener(SendDirectMessageListener):
                def on_arrived(self_):
                    self.logger.info(f"{message.__class__.__name__} arrived at peer: offerId={message.offer_id}; uid={message.uid}")
                    self.complete()
                    
                def on_fault(self_, error_message: str):
                    self.logger.error(f"Sending {message.__class__.__name__} failed: uid={message.uid}; peer={self.model.peer_node_address}; error={error_message}")
                    self.model.offer.state = OfferState.MAKER_OFFLINE
            
            self.model.p2p_service.send_encrypted_direct_message(
                self.model.peer_node_address,
                self.model.offer.pub_key_ring,
                message,
                MessageListener()
            )
            
        except Exception as e:
            self.model.offer.error_message = f"An error occurred.\nError message:\n{str(e)}"
            self.failed(exc=e)

