from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Optional
from bisq.common.app.dev_env import DevEnv
from bisq.common.crypto.hash import get_ripemd160_hash, get_sha256_ripemd160_hash
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
from bisq.core.trade.model.bisq_v1.trade import Trade
import base64 
from bisq.common.crypto.sig import Sig
from bisq.core.util.json_util import JsonUtil
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.core.account.sign.signed_witness_service import SignedWitnessService
    from bisq.core.account.witness.account_age_witness import AccountAgeWitness
    from bisq.core.account.witness.account_age_witness_service import AccountAgeWitnessService
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.account.sign.signed_witness import SignedWitness
    from bisq.core.payment.payment_account import PaymentAccount
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.core.payment.payload.payment_account_payload import PaymentAccountPayload


logger = get_logger(__name__)

# Camel cased to match java's output on json dump
# TODO: compare json outputs of java with python
@dataclass
class AccountAgeWitnessDto:
    profileId: str
    hashAsHex: str
    date: int
    pubKeyBase64: str
    signatureBase64: str


@dataclass
class SignedWitnessDto:
    profileId: str
    hashAsHex: str
    accountAgeWitnessDate: int
    witnessSignDate: int
    pubKeyBase64: str
    signatureBase64: str

class AccountAgeWitnessUtils:
    def __init__(self, account_age_witness_service: "AccountAgeWitnessService",
                 signed_witness_service: "SignedWitnessService",
                 key_ring: "KeyRing"):
        self.account_age_witness_service = account_age_witness_service
        self.signed_witness_service = signed_witness_service
        self.key_ring = key_ring

    def log_signed_witnesses(self):
        """Log tree of signed witnesses"""
        orphan_signers = self.signed_witness_service.get_root_signed_witness_set(True)
        logger.info("Orphaned signed account age witnesses:")
        for w in orphan_signers:
            logger.info(f"{w.verification_method.name}: Signer PKH: {get_ripemd160_hash(w.signer_pub_key).hex()[:7]} "
                       f"Owner PKH: {get_ripemd160_hash(w.witness_owner_pub_key).hex()[:7]} "
                       f"time: {w.date}")
            self._log_child(w, "  ", [])

    def _log_child(self, sig_wit: "SignedWitness", init_string: str, excluded: list[StorageByteArray]):
        logger.info(f"{init_string}AEW: {sig_wit.account_age_witness_hash.hex()[:7]} "
                   f"PKH: {get_ripemd160_hash(sig_wit.witness_owner_pub_key).hex()[:7]} "
                   f"time: {sig_wit.date}")
        
        for w in self.signed_witness_service.get_signed_witness_map_values():
            storage_array = StorageByteArray(w.witness_owner_pub_key)
            if (storage_array not in excluded and 
                w.signer_pub_key == sig_wit.witness_owner_pub_key):
                excluded.append(storage_array)
                self._log_child(w, init_string + "  ", excluded)
                excluded.pop()

    def log_signers(self):
        """Log signers per AEW"""
        logger.info("Signers per AEW")
        signed_witness_map_values = self.signed_witness_service.get_signed_witness_map_values()
        for w in signed_witness_map_values:
            logger.info(f"AEW {w.account_age_witness_hash.hex()}")
            for ww in signed_witness_map_values:
                if w.signer_pub_key == ww.witness_owner_pub_key:
                    logger.info(f"  {ww.account_age_witness_hash.hex()} ")

    def log_unsigned_signer_pub_keys(self):
        logger.info("Unsigned signer pubkeys")
        for signed_witness in self.signed_witness_service.get_unsigned_signer_pub_keys():
            logger.info(f"PK hash {get_ripemd160_hash(signed_witness.signer_pub_key).hex()} "
                       f"date {signed_witness.date}")
            
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Debug logs
    # ///////////////////////////////////////////////////////////////////////////////////////////
    
    def get_witness_debug_log(self, payment_account_payload: "PaymentAccountPayload", 
                            pub_key_ring: "PubKeyRing") -> str:
        account_age_witness = self.account_age_witness_service.find_witness(
            payment_account_payload, pub_key_ring)
        
        if account_age_witness is None:
            account_input_data_with_salt = self.account_age_witness_service.get_account_input_data_with_salt(
                payment_account_payload)
            hash_bytes = get_sha256_ripemd160_hash(account_input_data_with_salt + 
                                                  pub_key_ring.signature_pub_key_bytes)
            return f"No accountAgeWitness found for paymentAccountPayload with hash {bytes_as_hex_string(hash_bytes)}"

        sign_state = self.account_age_witness_service.get_sign_state(account_age_witness)
        return f"{sign_state.name} {sign_state.get_display_string()}\n{account_age_witness}"

    def witness_debug_log(self, trade: "Trade", my_witness: Optional["AccountAgeWitness"]=None):
        # Log to find why accounts sometimes don't get signed as expected
        # JAVA TODO: Demote to debug or remove once account signing is working ok
        assert trade.contract is not None
        assert trade.contract.buyer_payment_account_payload is not None
        
        checking_sign_trade = True
        is_buyer = trade.contract.is_my_role_buyer(self.key_ring.pub_key_ring)
        witness = my_witness
        
        if witness is None:
            witness = (
                self.account_age_witness_service.get_my_witness(trade.contract.buyer_payment_account_payload)
                if is_buyer
                else self.account_age_witness_service.get_my_witness(trade.contract.seller_payment_account_payload)
            )
            checking_sign_trade = False
            
        is_sign_witness_trade = (
            self.account_age_witness_service.account_is_signer(witness) and
            not self.account_age_witness_service.peer_has_signed_witness(trade) and
            self.account_age_witness_service.trade_amount_is_sufficient(trade.amount_property.value)
        )
        
        logger.info(
            "AccountSigning debug log:\n"
            f"tradeId: {trade.get_id()}\n"
            f"is buyer: {is_buyer}\n"
            f"buyer account age witness info: {self.get_witness_debug_log(trade.contract.buyer_payment_account_payload, trade.contract.buyer_pub_key_ring)}\n"
            f"seller account age witness info: {self.get_witness_debug_log(trade.contract.seller_payment_account_payload, trade.contract.seller_pub_key_ring)}\n"
            f"checking for sign trade: {checking_sign_trade}\n" # Following cases added to use same logic as in seller signing check
            f"is myWitness signer: {self.account_age_witness_service.account_is_signer(witness)}\n"
            f"peer has signed witness: {self.account_age_witness_service.peer_has_signed_witness(trade)}\n"
            f"trade amount: {trade.amount_property.value}\n"
            f"trade amount is sufficient: {self.account_age_witness_service.trade_amount_is_sufficient(trade.amount_property.value)}\n"
            f"isSignWitnessTrade: {is_sign_witness_trade}"
        )

    @staticmethod
    def sign_account_age_and_bisq2_profile_id(account_age_witness_service: "AccountAgeWitnessService",
                                             account: "PaymentAccount",
                                             key_ring: "KeyRing",
                                             profile_id: str) -> Optional[str]:
        witness = account_age_witness_service.find_witness(account.payment_account_payload, 
                                                         key_ring.pub_key_ring)
        if not witness:
            return None
            
        if account_age_witness_service.is_filtered_witness(witness):
            raise ValueError("Invalid account age witness")
            
        hash_as_hex = witness.get_hash().hex()
        date = witness.date
        
        if date <= 0:
            raise ValueError("Date must be > 0")
            
        message = profile_id + hash_as_hex + str(date)
        signature_key_pair = key_ring.signature_key_pair
        signature_base64 = Sig.sign(signature_key_pair.private_key, message)
        pub_key_base64 = base64.b64encode(Sig.get_public_key_bytes(signature_key_pair.public_key)).decode('utf-8')
        
        dto = AccountAgeWitnessDto(
            profileId=profile_id,
            hashAsHex=hash_as_hex,
            date=date,
            pubKeyBase64=pub_key_base64,
            signatureBase64=signature_base64
        )
        
        return JsonUtil.object_to_json(dto)

    @staticmethod
    def sign_signed_witness_and_bisq2_profile_id(account_age_witness_service: "AccountAgeWitnessService",
                                                account: "PaymentAccount",
                                                key_ring: "KeyRing",
                                                profile_id: str) -> Optional[str]:

        witness = account_age_witness_service.find_witness(account.payment_account_payload, 
                                                         key_ring.pub_key_ring)
        if not witness:
            return None
            
        if account_age_witness_service.is_filtered_witness(witness):
            raise ValueError("Invalid account age witness")
            
        witness_sign_date = account_age_witness_service.get_witness_sign_date(witness)
        age_in_days = int((get_time_ms() - witness_sign_date) / (timedelta(days=1).total_seconds * 1000))
        
        if not DevEnv.is_dev_mode():
            if witness_sign_date <= 0:
                raise ValueError("Account is not signed yet")
            if age_in_days <= 60:
                raise ValueError("Account must have been signed at least 61 days ago")

        hash_as_hex = witness.get_hash().hex()
        date = witness.date
        
        if date <= 0:
            raise ValueError("AccountAgeWitness date must be > 0")
            
        message = profile_id + hash_as_hex + str(date) + str(witness_sign_date)
        signature_key_pair = key_ring.signature_key_pair
        signature_base64 = Sig.sign(signature_key_pair.private_key, message)
        pub_key_base64 = base64.b64encode(Sig.get_public_key_bytes(signature_key_pair.public_key)).decode('utf-8')
        
        dto = SignedWitnessDto(
            profileId=profile_id,
            hashAsHex=hash_as_hex,
            accountAgeWitnessDate=date,
            witnessSignDate=witness_sign_date,
            pubKeyBase64=pub_key_base64,
            signatureBase64=signature_base64
        )
        
        return JsonUtil.object_to_json(dto)


