from typing import TYPE_CHECKING, List, Optional
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.btc.wallet.wallet_service import WalletService
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bisq.common.taskrunner.task import Task

if TYPE_CHECKING:
    from bisq.core.offer.placeoffer.bisq_v1.place_offer_model import PlaceOfferModel
    from bisq.common.taskrunner.task_runner import TaskRunner

class CloneAddressEntryForSharedMakerFee(Task['PlaceOfferModel']):
    def __init__(self, task_handler: 'TaskRunner[PlaceOfferModel]', model: 'PlaceOfferModel'):
        super().__init__(task_handler, model)
        
    def run(self):
        self.run_intercept_hook()

        offer = self.model.offer
        maker_fee_tx_id = offer.offer_fee_payment_tx_id
        wallet_service = self.model.wallet_service
        
        for reserved_for_trade_entry in wallet_service.get_address_entries(AddressEntryContext.RESERVED_FOR_TRADE):
            found_tx_id = self._find_tx_id(reserved_for_trade_entry.get_address())
            if found_tx_id and found_tx_id == maker_fee_tx_id:
                wallet_service.get_or_clone_address_entry_with_offer_id(reserved_for_trade_entry, offer.id)
                self.complete()
                return

        self.failed()

    def _find_tx_id(self, address: Address) -> Optional[str]:
        """
        Look up the most recent transaction with unspent outputs associated with the given address
        and return the txId if found.
        """
        wallet_service = self.model.wallet_service
        transactions = wallet_service.get_all_recent_transactions(False)
        
        for transaction in transactions:
            for output in transaction.outputs:
                if (wallet_service.is_transaction_output_mine(output) and 
                        WalletService.is_output_script_convertible_to_address(output)):
                    address_string = WalletService.get_address_string_from_output(output)
                    # make sure the output is still unspent
                    if (address_string is not None and 
                            address_string == str(address) and 
                            output.spent_by is None):
                        return str(transaction.get_tx_id())
        
        return None
