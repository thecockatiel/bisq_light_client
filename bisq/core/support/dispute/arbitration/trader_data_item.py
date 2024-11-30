from dataclasses import dataclass, field
from bisq.common.crypto.sig import dsa
from bisq.core.account.witness.account_age_witness import AccountAgeWitness
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bitcoinj.base.coin import Coin

#  TODO consider to move to signed witness domain
@dataclass(eq=True, frozen=True, unsafe_hash=True)
class TraderDataItem:
    payment_account_payload: PaymentAccountPayload = field(hash=False, compare=False)
    account_age_witness: AccountAgeWitness = field(hash=True, compare=True)
    trade_amount: Coin = field(hash=False, compare=False)
    peers_pub_key: dsa.DSAPublicKey = field(hash=False, compare=False)
