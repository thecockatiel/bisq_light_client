from bisq.core.btc.model.address_entry_context import AddressEntryContext
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none, check_argument


class BuyerAsMakerCreatesAndSignsDepositTx(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            trade_amount = check_not_none(
                self.trade.get_amount(), "trade.get_amount() must not be None"
            )

            wallet_service = self.process_model.btc_wallet_service
            id = self.process_model.offer.id
            trading_peer = self.process_model.trade_peer
            offer = check_not_none(self.trade.get_offer())

            maker_input_amount = offer.buyer_security_deposit
            address_entry_optional = wallet_service.get_address_entry(
                id, AddressEntryContext.MULTI_SIG
            )
            check_argument(
                address_entry_optional is not None,
                "addressEntryOptional must be present",
            )
            maker_multi_sig_address_entry = address_entry_optional
            self.process_model.btc_wallet_service.set_coin_locked_in_multi_sig_address_entry(
                maker_multi_sig_address_entry, maker_input_amount.value
            )
            wallet_service.save_address_entry_list()

            ms_output_amount = (
                maker_input_amount.add(self.trade.trade_tx_fee)
                .add(offer.seller_security_deposit)
                .add(trade_amount)
            )

            taker_raw_transaction_inputs = check_not_none(
                trading_peer.raw_transaction_inputs
            )
            check_argument(
                all(
                    self.process_model.trade_wallet_service.is_p2wh(input)
                    for input in taker_raw_transaction_inputs
                ),
                "all taker_raw_transaction_inputs must be P2WH",
            )
            taker_change_output_value = trading_peer.change_output_value
            taker_change_address_string = trading_peer.change_output_address
            maker_address = wallet_service.get_or_create_address_entry(
                self.process_model.offer.id,
                AddressEntryContext.RESERVED_FOR_TRADE,
            ).get_address()
            maker_change_address = (
                wallet_service.get_fresh_address_entry().get_address()
            )
            buyer_pub_key = self.process_model.my_multi_sig_pub_key
            seller_pub_key = check_not_none(trading_peer.multi_sig_pub_key)
            check_argument(
                buyer_pub_key == maker_multi_sig_address_entry.pub_key,
                f"buyerPubKey from AddressEntry must match the one from the trade data. trade id = {self.process_model.offer.id}",
            )

            result = self.process_model.trade_wallet_service.buyer_as_maker_creates_and_signs_deposit_tx(
                maker_input_amount,
                ms_output_amount,
                taker_raw_transaction_inputs,
                taker_change_output_value,
                taker_change_address_string,
                maker_address,
                maker_change_address,
                buyer_pub_key,
                seller_pub_key,
            )

            self.process_model.prepared_deposit_tx = result.deposit_transaction
            self.process_model.raw_transaction_inputs = result.raw_maker_inputs

            self.process_model.trade_manager.request_persistence()

            self.complete()
        except Exception as e:
            self.failed(exc=e)
