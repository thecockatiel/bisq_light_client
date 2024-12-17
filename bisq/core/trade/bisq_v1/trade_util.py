from typing import TYPE_CHECKING, Tuple, Optional

from bisq.common.handlers.error_message_handler import ErrorMessageHandler
from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.util.utilities import bytes_as_hex_string

if TYPE_CHECKING:
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.node_address import NodeAddress
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService 
    from bisq.core.trade.model.bisq_v1.trade import Trade

def _assert_not_none(value, message: str):
    """Asserts that the given value is not None."""
    if value is None:
        raise ValueError(message)
    return True

# TODO: implement rest?
class TradeUtil:
    """This class contains trade utility methods."""
    
    def __init__(self, btc_wallet_service: "BtcWalletService", key_ring: "KeyRing"):
        self.btc_wallet_service = btc_wallet_service
        self.key_ring = key_ring
        
    def get_available_addresses(self, trade: "Trade") -> Optional[Tuple[str, str]]:
        """
        Returns (MULTI_SIG, TRADE_PAYOUT) if and only if both are AVAILABLE,
        otherwise None.
        """
        addresses = self.get_trade_addresses(trade)
        if addresses is None:
            return None
            
        available_addresses = [e.get_address_string() for e in self.btc_wallet_service.get_available_address_entries()]
        if addresses[0] not in available_addresses or addresses[1] not in available_addresses:
            return None
            
        return addresses
        
    def get_trade_addresses(self, trade: "Trade") -> Optional[Tuple[str, str]]:
        """
        Returns (MULTI_SIG, TRADE_PAYOUT) addresses as strings if they're known by the
        wallet.
        """
        contract = trade.contract
        if contract is None:
            return None
            
        # Get multisig address
        is_my_role_buyer = contract.is_my_role_buyer(self.key_ring.pub_key_ring)
        multi_sig_pub_key = (contract.buyer_multi_sig_pub_key
                            if is_my_role_buyer 
                            else contract.seller_multi_sig_pub_key)
        if multi_sig_pub_key is None:
            return None
            
        multi_sig_pub_key_string = bytes_as_hex_string(multi_sig_pub_key)
        multi_sig_addresses = [
            e for e in self.btc_wallet_service.get_address_entry_list_as_immutable_list()
            if e.get_key_pair().eckey.get_public_key_hex() == multi_sig_pub_key_string # TODO: Check DeterministicKey later
        ]
        if not multi_sig_addresses:
            return None
        multi_sig_address = multi_sig_addresses[0]
            
        # Get payout address
        payout_address = (contract.buyer_payout_address_string 
                         if is_my_role_buyer 
                         else contract.seller_payout_address_string)
        payout_address_entries = [
            e for e in self.btc_wallet_service.get_address_entry_list_as_immutable_list()
            if e.get_address_string() == payout_address
        ]
        if not payout_address_entries:
            return None
            
        return multi_sig_address.get_address_string(), payout_address
    
    @staticmethod
    def apply_filter(trade_model: "TradeModel",
                    filter_manager: "FilterManager",
                    node_address: "NodeAddress",
                    payment_account_payload: Optional["PaymentAccountPayload"],
                    complete: ResultHandler,
                    failed: ErrorMessageHandler) -> None:
        """Apply trading filters to check if trade should be allowed."""
        if filter_manager.is_node_address_banned(node_address):
            failed(f"Other trader is banned by their node address.\n"
                                      f"tradingPeerNodeAddress={node_address}")
        elif filter_manager.is_offer_id_banned(trade_model.get_id()):
            failed(f"Offer ID is banned.\nOffer ID={trade_model.get_id()}")
        elif (trade_model.get_offer() is not None and
              filter_manager.is_currency_banned(trade_model.get_offer().currency_code)):
            failed(f"Currency is banned.\n"
                                      f"Currency code={trade_model.get_offer().currency_code}")
        elif _assert_not_none(trade_model.get_offer()) and filter_manager.is_payment_method_banned(trade_model.get_offer().payment_method):
            failed(f"Payment method is banned.\n"
                                      f"Payment method={trade_model.get_offer().payment_method.id}")
        elif payment_account_payload is not None and filter_manager.are_peers_payment_account_data_banned(payment_account_payload):
            failed(f"Other trader is banned by their trading account data.\n"
                                      f"paymentAccountPayload={payment_account_payload.get_payment_details()}")
        elif filter_manager.require_update_to_new_version_for_trading():
            failed("Your version of Bisq is not compatible for trading anymore. "
                                      "Please update to the latest Bisq version at https://bisq.network/downloads.")
        else:
            complete()


