
from bisq.core.trade.protocol.bisq_v1.messages.delayed_payout_tx_signature_response import DelayedPayoutTxSignatureResponse
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bisq.core.util.validator import Validator


class SellerProcessDelayedPayoutTxSignatureResponse(TradeTask):
    
    def run(self):
        try:
            self.run_intercept_hook()
            response = self.process_model.trade_message
            assert response is not None
            if not isinstance(response, DelayedPayoutTxSignatureResponse):
                raise ValueError(f"Unexpected message type at SellerProcessDelayedPayoutTxSignatureResponse: {response.__class__.__name__}")
            Validator.check_trade_id(self.process_model.offer_id, response)
            
            self.process_model.trade_peer.delayed_payout_tx_signature = response.delayed_payout_tx_buyer_signature
            
            self.process_model.trade_wallet_service.seller_adds_buyer_witnesses_to_deposit_tx(
                self.process_model.deposit_tx,
                self.process_model.btc_wallet_service.get_tx_from_serialized_tx(response.deposit_tx),
            )
            
            # update to the latest peer address of our peer if the message is correct
            self.trade.trading_peer_node_address = self.process_model.temp_trading_peer_node_address
            
            self.process_model.trade_manager.request_persistence()
            
            self.complete()
        except Exception as e:
            self.failed(exc=e)
            