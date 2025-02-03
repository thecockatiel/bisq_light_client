from bisq.common.payload import Payload
from bisq.core.api.model.payment_account_payload_info import PaymentAccountPayloadInfo
import grpc_pb2


class ContractInfo(Payload):
    """
    A lightweight Trade Contract constructed from a trade's json contract.
    Many fields in the core Contract are ignored, but can be added as needed.
    """

    def __init__(
        self,
        buyer_node_address: str,
        seller_node_address: str,
        mediator_node_address: str,
        refund_agent_node_address: str,
        is_buyer_maker_and_seller_taker: bool,
        maker_account_id: str,
        taker_account_id: str,
        maker_payment_account_payload: "PaymentAccountPayloadInfo",
        taker_payment_account_payload: "PaymentAccountPayloadInfo",
        maker_payout_address_string: str,
        taker_payout_address_string: str,
        lock_time: int,
    ):
        self.buyer_node_address = buyer_node_address
        self.seller_node_address = seller_node_address
        self.mediator_node_address = mediator_node_address
        self.refund_agent_node_address = refund_agent_node_address
        self.is_buyer_maker_and_seller_taker = is_buyer_maker_and_seller_taker
        self.maker_account_id = maker_account_id
        self.taker_account_id = taker_account_id
        self.maker_payment_account_payload = maker_payment_account_payload
        self.taker_payment_account_payload = taker_payment_account_payload
        self.maker_payout_address_string = maker_payout_address_string
        self.taker_payout_address_string = taker_payout_address_string
        self.lock_time = lock_time

    # For transmitting TradeInfo messages when no contract is available.
    # JAVA TODO Is this necessary as protobuf will send a DEFAULT_INSTANCE.
    @staticmethod
    def empty_contract():
        return ContractInfo(
            "",
            "",
            "",
            "",
            False,
            "",
            "",
            PaymentAccountPayloadInfo.empty_payment_account_payload(),
            PaymentAccountPayloadInfo.empty_payment_account_payload(),
            "",
            "",
            0,
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // PROTO BUFFER
    # ///////////////////////////////////////////////////////////////////////////////////////////

    @staticmethod
    def from_proto(proto: grpc_pb2.ContractInfo) -> "ContractInfo":
        return ContractInfo(
            proto.buyer_node_address,
            proto.seller_node_address,
            proto.mediator_node_address,
            proto.refund_agent_node_address,
            proto.is_buyer_maker_and_seller_taker,
            proto.maker_account_id,
            proto.taker_account_id,
            PaymentAccountPayloadInfo.from_proto(proto.maker_payment_account_payload),
            PaymentAccountPayloadInfo.from_proto(proto.taker_payment_account_payload),
            proto.maker_payout_address_string,
            proto.taker_payout_address_string,
            proto.lock_time,
        )

    def to_proto_message(self) -> grpc_pb2.ContractInfo:
        return grpc_pb2.ContractInfo(
            buyer_node_address=self.buyer_node_address,
            seller_node_address=self.seller_node_address,
            mediator_node_address=self.mediator_node_address,
            refund_agent_node_address=self.refund_agent_node_address,
            is_buyer_maker_and_seller_taker=self.is_buyer_maker_and_seller_taker,
            maker_account_id=self.maker_account_id,
            taker_account_id=self.taker_account_id,
            maker_payment_account_payload=self.maker_payment_account_payload.to_proto_message(),
            taker_payment_account_payload=self.taker_payment_account_payload.to_proto_message(),
            maker_payout_address_string=self.maker_payout_address_string,
            taker_payout_address_string=self.taker_payout_address_string,
            lock_time=self.lock_time,
        )
