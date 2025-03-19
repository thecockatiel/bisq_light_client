from bisq.core.payment.xmr_account_delegate import XmrAccountDelegate
from bisq.core.trade.protocol.bisq_v1.tasks.trade_task import TradeTask
from utils.preconditions import check_not_none
import uuid

from utils.time import get_time_ms


class MaybeCreateSubAccount(TradeTask):

    def run(self):
        try:
            self.run_intercept_hook()
            parent_account = check_not_none(
                self.process_model.payment_account,
                "payment_account should not be None in MaybeCreateSubAccount",
            )

            # This is a seller task, so no need to check for it
            if (
                not self.trade.get_offer().is_xmr
                or not parent_account.extra_data
                or not XmrAccountDelegate.account_is_using_sub_addresses(parent_account)
            ):
                self.complete()
                return

            # In case we are a seller using XMR sub addresses we clone the account, add it as xmrAccount and
            # increment from the highest subAddressIndex from all our subAccounts grouped by the subAccountId (mainAddress + accountIndex).
            payment_account = self.process_model.trade_manager.clone_account(
                check_not_none(parent_account)
            )
            xmr_account_delegate = XmrAccountDelegate(payment_account)
            # We overwrite some fields
            xmr_account_delegate.id = str(uuid.uuid4())
            xmr_account_delegate.trade_id = self.trade.get_id()
            xmr_account_delegate.creation_date = get_time_ms()
            # We add our cloned account as xmrAccount and apply the incremented index and subAddress.

            # We need to store that globally, so we use the user object.
            sub_accounts_by_id = self.process_model.user.sub_accounts_by_id
            sub_accounts_by_id.setdefault(xmr_account_delegate.sub_account_id, set())
            sub_accounts = sub_accounts_by_id[xmr_account_delegate.sub_account_id]

            # At first subAccount we use the index of the parent account and decrement by 1 as we will increment later in the code
            initial_sub_account_index = (
                xmr_account_delegate.sub_address_index_as_long - 1
            )
            max_sub_address_index = max(
                (
                    XmrAccountDelegate.get_sub_address_index_as_long(sub_account)
                    for sub_account in sub_accounts
                ),
                default=initial_sub_account_index,
            )

            # Always increment, use the (decremented) initialSubAccountIndex or the next after max
            max_sub_address_index += 1

            # Prefix subAddressIndex to account name
            xmr_account_delegate.account_name = (
                f"[{max_sub_address_index}] {parent_account.account_name}"
            )
            xmr_account_delegate.sub_address_index = str(max_sub_address_index)
            xmr_account_delegate.create_and_set_new_sub_address()
            sub_accounts.add(xmr_account_delegate.account)

            # Now we set our xmrAccount as paymentAccount
            self.process_model.payment_account = xmr_account_delegate.account
            # We got set the accountId from the parent account at the ProcessModel constructor. We update it to the subAccounts id.
            self.process_model.account_id = xmr_account_delegate.id
            self.process_model.user.request_persistence()

            self.complete()

        except Exception as e:
            self.failed(exc=e)
