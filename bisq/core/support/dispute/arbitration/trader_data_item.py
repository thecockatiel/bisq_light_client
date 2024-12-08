from dataclasses import dataclass, field
from bisq.common.crypto.sig import Sig, dsa
from bisq.core.account.witness.account_age_witness import AccountAgeWitness
from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload
from bitcoinj.base.coin import Coin

#  TODO consider to move to signed witness domain
@dataclass(eq=True, frozen=True)
class TraderDataItem:
    payment_account_payload: PaymentAccountPayload = field(hash=False, compare=False)
    account_age_witness: AccountAgeWitness = field(hash=True, compare=True)
    trade_amount: Coin = field(hash=False, compare=False)
    peers_pub_key: dsa.DSAPublicKey = field(hash=False, compare=False)

    def __hash__(self):
        return hash((self.payment_account_payload, self.account_age_witness, self.trade_amount, Sig.get_public_key_bytes(self.peers_pub_key)))
