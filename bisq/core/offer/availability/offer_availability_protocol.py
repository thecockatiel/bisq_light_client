from datetime import timedelta
from bisq.common.setup.log_setup import get_ctx_logger
from typing import TYPE_CHECKING, Optional
from bisq.common.taskrunner.task_runner import TaskRunner
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from bisq.core.network.p2p.ack_message import AckMessage
from bisq.core.network.p2p.ack_message_source_type import AckMessageSourceType
from bisq.core.network.p2p.send_direct_message_listener import SendDirectMessageListener
from bisq.core.offer.availability.messages.offer_message import OfferMessage
from bisq.core.offer.availability.tasks.process_offer_availability_response import ProcessOfferAvailabilityResponse
from bisq.core.offer.availability.tasks.send_offer_availability_request import SendOfferAvailabilityRequest
from bisq.core.util.validator import Validator
from bisq.core.offer.offer_state import OfferState
from bisq.core.offer.availability.messages.offer_availability_response import OfferAvailabilityResponse

if TYPE_CHECKING:
    from bisq.core.offer.availability.offer_availability_model import OfferAvailabilityModel
    from bisq.common.handlers.error_message_handler import ErrorMessageHandler
    from bisq.common.handlers.result_handler import ResultHandler
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.network.p2p.decrypted_message_with_pub_key import (
        DecryptedMessageWithPubKey,
    )


class OfferAvailabilityProtocol:
    TIMEOUT_SEC = 90

    def __init__(self,
                 model: 'OfferAvailabilityModel', 
                 result_handler: 'ResultHandler',
                 error_message_handler: 'ErrorMessageHandler'):
        self.logger = get_ctx_logger(__name__)
        self.model = model
        self.result_handler = result_handler
        self.error_message_handler = error_message_handler
        
        self.task_runner: Optional['TaskRunner[OfferAvailabilityModel]'] = None
        self.timeout_timer: Optional['Timer'] = None
        
        def message_listener(decrypted_message_with_pub_key: 'DecryptedMessageWithPubKey', peers_node_address: 'NodeAddress'):
            network_envelope = decrypted_message_with_pub_key.network_envelope
            if isinstance(network_envelope, OfferMessage):
                offer_message = network_envelope
                Validator.non_empty_string_of(offer_message.offer_id)
                if (isinstance(network_envelope, OfferAvailabilityResponse) and 
                    self.model.offer.id == offer_message.offer_id):
                    self.handle_offer_availability_response(network_envelope, peers_node_address)
        
        self.decrypted_direct_message_listener = message_listener

    def cleanup(self):
        self.stop_timeout()
        self.model.p2p_service.remove_decrypted_direct_message_listener(self.decrypted_direct_message_listener)

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Called from UI
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def send_offer_availability_request(self):
        # reset
        self.model.offer.state = OfferState.UNKNOWN

        self.model.p2p_service.add_decrypted_direct_message_listener(self.decrypted_direct_message_listener)
        self.model.peer_node_address = self.model.offer.maker_node_address

        self.task_runner = TaskRunner(
            self.model,
            lambda: self.handle_task_runner_success("TaskRunner at sendOfferAvailabilityRequest completed", None),
            lambda error_msg: self.handle_task_runner_fault(error_msg, None)
        )
        self.task_runner.add_tasks(SendOfferAvailabilityRequest)
        self.start_timeout()
        self.task_runner.run()

    def cancel(self):
        self.task_runner.cancel()
        self.cleanup()
        
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Incoming message handling
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def handle_offer_availability_response(self, message: 'OfferAvailabilityResponse', peers_node_address: 'NodeAddress'):
        self.logger.info(f"Received handleOfferAvailabilityResponse from {peers_node_address} with offerId {message.offer_id} and uid {message.uid}")

        self.stop_timeout()
        self.start_timeout()
        self.model.message = message

        self.task_runner = TaskRunner(
            self.model,
            lambda: self._complete_offer_availability_response(message),
            lambda error_msg: self.handle_task_runner_fault(error_msg, message)
        )
        self.task_runner.add_tasks(ProcessOfferAvailabilityResponse)
        self.task_runner.run()

    def _complete_offer_availability_response(self, message: "OfferAvailabilityResponse"):
        self.handle_task_runner_success("TaskRunner at handle OfferAvailabilityResponse completed", message)
        self.stop_timeout()
        self.result_handler()

    def start_timeout(self):
        if self.timeout_timer is None:
            self.timeout_timer = UserThread.run_after(
                self._handle_timeout,
                timedelta(seconds=OfferAvailabilityProtocol.TIMEOUT_SEC),
            )
        else:
            self.logger.warning("timeoutTimer already created. That must not happen.")

    def stop_timeout(self):
        if self.timeout_timer is not None:
            self.timeout_timer.stop()
            self.timeout_timer = None

    def _handle_timeout(self):
        self.logger.debug(f"Timeout reached at {self}")
        self.model.offer.state = OfferState.MAKER_OFFLINE
        self.error_message_handler("Timeout reached: Peer has not responded.")

    def handle_task_runner_success(self, info: str, message: Optional['OfferAvailabilityResponse']):
        self.logger.debug(f"handleTaskRunnerSuccess {info}")

        if message is not None:
            self.send_ack_message(message, True, None)

    def handle_task_runner_fault(self, error_message: str, message: Optional['OfferAvailabilityResponse']):
        self.logger.error(error_message)

        self.stop_timeout()
        self.error_message_handler(error_message)

        if message is not None:
            self.send_ack_message(message, False, error_message)

    def send_ack_message(self, message: 'OfferAvailabilityResponse', result: bool, error_message: Optional[str]):
        offer_id = message.offer_id
        source_uid = message.uid
        makers_node_address = self.model.peer_node_address
        makers_pub_key_ring = self.model.offer.pub_key_ring
        
        self.logger.info(f"Send AckMessage for OfferAvailabilityResponse to peer {makers_node_address} "
                   f"with offerId {offer_id} and sourceUid {source_uid}")

        ack_message = AckMessage(
            sender_node_address=self.model.p2p_service.network_node.node_address_property.value,
            source_type=AckMessageSourceType.OFFER_MESSAGE,
            source_msg_class_name=message.__class__.__name__,
            source_uid=source_uid,
            source_id=offer_id,
            success=result,
            error_message=error_message
        )
        
        class MessageListener(SendDirectMessageListener):
            def on_arrived(self_):
                self.logger.info(f"AckMessage for OfferAvailabilityResponse arrived at makersNodeAddress {makers_node_address}. "
                        f"offerId={offer_id}, sourceUid={ack_message.source_uid}")

            def on_fault(self_, error_msg: str):
                self.logger.error(f"AckMessage for OfferAvailabilityResponse failed. AckMessage={ack_message}, "
                            f"makersNodeAddress={makers_node_address}, errorMessage={error_msg}")
            


        self.model.p2p_service.send_encrypted_direct_message(
            makers_node_address,
            makers_pub_key_ring,
            ack_message,
            MessageListener()
        )


