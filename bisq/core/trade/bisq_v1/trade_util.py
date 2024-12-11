from typing import TYPE_CHECKING, Tuple, Optional

from bisq.common.util.utilities import bytes_as_hex_string

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.btc.wallet.btc_wallet_service import BtcWalletService 
    from bisq.core.trade.model.bisq_v1.trade import Trade

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

