
from datetime import datetime, timezone
from bisq.core.locale.currency_util import is_crypto_currency
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask


class VerifyPeersAccountAgeWitness(TradeTask):
    
    def run(self):
        try:
            self.run_intercept_hook()
            offer = self.trade.get_offer()
            assert offer is not None
            if is_crypto_currency(offer.currency_code):
                self.complete()
                return
            
            account_age_witness_service = self.process_model.account_age_witness_service
            trading_peer = self.process_model.trade_peer
            
            peers_payment_account_payload = trading_peer.payment_account_payload
            assert peers_payment_account_payload is not None, "Peers payment_account_payload must not be None"
            
            peers_pub_key_ring = trading_peer.pub_key_ring
            assert peers_pub_key_ring is not None, "peers_pub_key_ring must not be None"

            nonce = trading_peer.account_age_witness_nonce
            assert nonce is not None
            
            signature = trading_peer.account_age_witness_signature
            assert signature is not None

            current_date = trading_peer.current_date
            # In case the peer has an older version we get 0, so we use our time instead
            peers_current_date = datetime.fromtimestamp(current_date/1000) if current_date > 0 else datetime.now()

            error_msg = []
            is_valid = account_age_witness_service.verify_account_age_witness(
                self.trade,
                peers_payment_account_payload,
                peers_current_date,
                peers_pub_key_ring,
                nonce,
                signature,
                lambda e: error_msg.append(e)
            )
            if is_valid:
                self.complete()
            else:
                self.failed(error_msg[0] if error_msg else "Account age witness verification failed")
        except Exception as e:
            self.failed(exc=e)