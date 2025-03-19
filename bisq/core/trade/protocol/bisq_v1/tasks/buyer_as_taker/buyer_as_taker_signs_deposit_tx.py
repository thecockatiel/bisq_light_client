from bisq.common.crypto.hash import get_sha256_hash
from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from bitcoinj.base.coin import Coin
from utils.preconditions import check_argument, check_not_none


class BuyerAsTakerSignsDepositTx(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            contract_hash = get_sha256_hash(check_not_none(self.trade.contract_as_json))
            self.trade.contract_hash = contract_hash
            buyer_inputs = check_not_none(
                self.process_model.raw_transaction_inputs,
                "buyerInputs must not be None",
            )
            wallet_service = self.process_model.btc_wallet_service
            id = self.process_model.offer.id

            buyer_multi_sig_address_entry = wallet_service.get_address_entry(
                id, AddressEntryContext.MULTI_SIG
            )
            check_argument(
                buyer_multi_sig_address_entry,
                "buyer_multi_sig_address_entry must be present",
            )
            buyer_input = Coin.value_of(sum(input.value for input in buyer_inputs))

            multi_sig_value = buyer_input.subtract(self.trade.trade_tx_fee.multiply(2))
            self.process_model.btc_wallet_service.set_coin_locked_in_multi_sig_address_entry(
                buyer_multi_sig_address_entry, multi_sig_value.value
            )
            wallet_service.save_address_entry_list()

            offer = self.trade.get_offer()
            ms_output_amount = (
                offer.buyer_security_deposit.add(offer.seller_security_deposit)
                .add(self.trade.trade_tx_fee)
                .add(check_not_none(self.trade.get_amount()))
            )

            trading_peer = self.process_model.trade_peer
            buyer_multi_sig_pub_key = self.process_model.my_multi_sig_pub_key
            check_argument(
                buyer_multi_sig_pub_key == buyer_multi_sig_address_entry.pub_key,
                f"buyerMultiSigPubKey from AddressEntry must match the one from the trade data. trade id = {id}",
            )

            seller_inputs = check_not_none(trading_peer.raw_transaction_inputs)
            seller_multi_sig_pub_key = trading_peer.multi_sig_pub_key
            deposit_tx = self.process_model.trade_wallet_service.taker_signs_deposit_tx(
                False,
                self.process_model.prepared_deposit_tx,
                ms_output_amount,
                buyer_inputs,
                seller_inputs,
                buyer_multi_sig_pub_key,
                seller_multi_sig_pub_key,
            )
            self.process_model.deposit_tx = deposit_tx

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
