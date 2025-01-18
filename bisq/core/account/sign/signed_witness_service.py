import base64
from datetime import timedelta
from bisq.common.crypto.encryption import ECPrivkey, ECPubkey, Encryption, dsa
from bisq.common.crypto.hash import get_ripemd160_hash
from bisq.common.crypto.sig import Sig
from utils.time import get_time_ms
from typing import TYPE_CHECKING, Collection, Optional, Union
from bisq.common.setup.log_setup import get_logger
from bisq.core.account.sign.signed_witness_verification_method import SignedWitnessVerificationMethod
from bisq.core.network.p2p.bootstrap_listener import BootstrapListener
from bitcoinj.base.coin import Coin
from bisq.common.user_thread import UserThread
from bisq.core.account.sign.signed_witness import SignedWitness

if TYPE_CHECKING:
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.core.account.sign.signed_witness_storage_service import SignedWitnessStorageService
    from bisq.core.filter.filter_manager import FilterManager
    from bisq.core.network.p2p.p2p_service import P2PService
    from bisq.core.network.p2p.persistence.append_only_data_store_service import AppendOnlyDataStoreService
    from bisq.core.network.p2p.storage.storage_byte_array import StorageByteArray
    from bisq.core.support.dispute.arbitration.arbitrator.arbitrator_manager import ArbitratorManager
    from bisq.core.user.user import User
    from bisq.core.account.witness.account_age_witness import AccountAgeWitness

logger = get_logger(__name__)


class SignedWitnessService:
    SIGNER_AGE_DAYS = 30
    SIGNER_AGE_MS = int(timedelta(days=SIGNER_AGE_DAYS).total_seconds() * 1000)
    MINIMUM_TRADE_AMOUNT_FOR_SIGNING = Coin.parse_coin("0.0025")

    def __init__(self, key_ring: 'KeyRing',
                 p2p_service: 'P2PService',
                 arbitrator_manager: 'ArbitratorManager',
                 signed_witness_storage_service: 'SignedWitnessStorageService',
                 append_only_data_store_service: 'AppendOnlyDataStoreService',
                 user: 'User',
                 filter_manager: 'FilterManager'):
        self.key_ring = key_ring
        self.p2p_service = p2p_service
        self.arbitrator_manager = arbitrator_manager
        self.signed_witness_storage_service = signed_witness_storage_service
        self.user = user
        self.filter_manager = filter_manager


        self.signed_witness_map: dict['StorageByteArray', 'SignedWitness'] = {}
        
        # This map keeps all SignedWitnesses with the same AccountAgeWitnessHash in a Set.
        # This avoids iterations over the signedWitnessMap for getting the set of such SignedWitnesses.
        self.signed_witness_set_by_account_age_witness_hash: dict['StorageByteArray', set['SignedWitness']] = {}
        
        # Iterating over all SignedWitnesses and do a byte array comparison is a bit expensive and
        # it is called at filtering the offer book many times, so we use a lookup map for fast
        # access to the set of SignedWitness which match the ownerPubKey.
        self.signed_witness_set_by_owner_pub_key: dict['StorageByteArray', set['SignedWitness']] = {}
        
        # The signature verification calls are rather expensive and called at filtering the offer book many times,
        # we cache the results using the hash as key. The hash is created from the accountAgeWitnessHash and the
        # signature.
        self.verify_signature_with_dsa_key_result_cache: dict['StorageByteArray', bool] = {}
        self.verify_signature_with_ec_key_result_cache: dict['StorageByteArray', bool] = {}

        # We need to add that early (before on_all_services_initialized) as it will be used at startup.
        append_only_data_store_service.add_service(signed_witness_storage_service)

    def on_all_services_initialized(self):
        self.p2p_service.p2p_data_storage.add_append_only_data_store_listener(
            lambda payload: self.add_to_map(payload) if isinstance(payload, SignedWitness) else None
        )
        
        # At startup the P2PDataStorage initializes earlier, otherwise we get the listener called.
        for e in self.signed_witness_storage_service.get_map().values():
            if isinstance(e, SignedWitness):
                self.add_to_map(e)

        if self.p2p_service.is_bootstrapped:
            self.on_bootstrap_complete()
        else:
            outer = self
            class Listener(BootstrapListener):
                def on_data_received(self):
                    outer.on_bootstrap_complete()
            
            self.p2p_service.add_p2p_service_listener(Listener())
        # JAVA TODO: Enable cleaning of signed witness list when necessary
        # self.clean_signed_witnesses();
        
    def on_bootstrap_complete(self):
        if self.user.registered_arbitrator is not None:
            UserThread.run_after(self.do_republish_all_signed_witnesses, timedelta(seconds=60))
            
    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // API
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def get_signed_witness_map_values(self) -> Collection['SignedWitness']:
        return self.signed_witness_map.values()

    def get_verified_witness_date_list(self, account_age_witness: "AccountAgeWitness") -> list[int]:
        """
        List of dates as timestamps when account_age_witness was signed.
        
        Witnesses that were added but are no longer considered signed won't be shown.
        """
        if not self.is_signed_account_age_witness(account_age_witness):
            return []
        
        signed_witnesses = self.get_signed_witness_set(account_age_witness)
        return sorted(
            witness.date for witness in signed_witnesses 
            if self.verify_signature(witness)
        )

    def get_witness_date_list(self, account_age_witness: "AccountAgeWitness") -> list[int]:
        """
        List of dates as timestamps when account_age_witness was signed.
        Not verifying that signatures are correct.
        """
        # We do not validate as it would not make sense to cheat oneself...
        signed_witnesses = self.get_signed_witness_set(account_age_witness)
        return sorted(witness.date for witness in signed_witnesses)

    def is_signed_by_arbitrator(self, account_age_witness: "AccountAgeWitness") -> bool:
        signed_witnesses = self.get_signed_witness_set(account_age_witness)
        return any(witness.is_signed_by_arbitrator for witness in signed_witnesses)

    def is_filtered_witness(self, account_age_witness: "AccountAgeWitness") -> bool:
        signed_witnesses = self.get_signed_witness_set(account_age_witness)
        return any(
            self.filter_manager.is_witness_signer_pub_key_banned(witness.witness_owner_pub_key.hex())
            for witness in signed_witnesses
        )

    def owner_pub_key(self, account_age_witness: "AccountAgeWitness") -> Optional[bytes]:
        signed_witnesses = self.get_signed_witness_set(account_age_witness)
        return next((witness.witness_owner_pub_key for witness in signed_witnesses), None)

    def owner_pub_key_as_string(self, account_age_witness: "AccountAgeWitness") -> str:
        signed_witnesses = self.get_signed_witness_set(account_age_witness)
        return next((witness.witness_owner_pub_key.hex() for witness in signed_witnesses), "")

    def get_signed_witness_set_by_owner_pub_key(self, owner_pub_key: bytes, excluded: list['StorageByteArray'] = None) -> set['SignedWitness']:
        if excluded is not None:
            # We go one level up by using the signer Key to lookup for SignedWitness objects which contain the signerKey as
            # witnessOwnerPubKey
            key = StorageByteArray(owner_pub_key)
            if key in self.signed_witness_set_by_owner_pub_key:
                up = self.signed_witness_set_by_owner_pub_key.get(key)
                return {
                    witness for witness in up 
                    if StorageByteArray(witness.signer_pub_key) not in excluded
                }
            else:
                return set()
        else:
            return {
                witness for witness in self.get_signed_witness_map_values()
                if witness.witness_owner_pub_key == owner_pub_key
            }

    def publish_own_signed_witness(self, signed_witness: 'SignedWitness') -> bool:
        if (signed_witness.witness_owner_pub_key != self.key_ring.pub_key_ring.signature_pub_key_bytes or
                not self.verify_signer(signed_witness)):
            return False

        logger.info(f"Publish own signedWitness {str(signed_witness)}")
        self.publish_signed_witness(signed_witness)
        return True
    
    def sign_and_publish_account_age_witness(self, 
                                           account_age_witness: 'AccountAgeWitness',
                                           ec_key: 'ECPrivkey',
                                           trade_amount: 'Coin' = None,
                                           peers_pub_key: Union[bytes, 'dsa.DSAPublicKey'] = None,
                                           time: int = None) -> Union[str, Optional['SignedWitness']]:
        
        if time is None:
            time = get_time_ms()
            
        if trade_amount is None:
            trade_amount = SignedWitnessService.MINIMUM_TRADE_AMOUNT_FOR_SIGNING
            
        if isinstance(peers_pub_key, dsa.DSAPublicKey):
            peers_pub_key = Encryption.get_public_key_bytes(peers_pub_key)
            
        #####
        
        if ec_key is not None:
            # Arbitrators sign with EC key
            if peers_pub_key is None:
                peers_pub_key = self.owner_pub_key(account_age_witness)

            if self.is_signed_account_age_witness(account_age_witness):
                err = f"Arbitrator trying to sign already signed accountagewitness {str(account_age_witness)}"
                logger.warning(err)
                return err
            
            if peers_pub_key is None:
                err = f"Trying to sign accountAgeWitness {str(account_age_witness)} \nwith owner pubkey=null"
                logger.warning(err)
                return err
            
            account_age_witness_hash = account_age_witness.get_hash()
            signature_base64 = base64.b64encode(ec_key.sign_message(account_age_witness_hash))
            signed_witness = SignedWitness(
                SignedWitnessVerificationMethod.ARBITRATOR,
                account_age_witness_hash=account_age_witness.get_hash(),
                signature=signature_base64,
                signer_pub_key=ec_key.get_public_key_bytes(),
                witness_owner_pub_key=peers_pub_key,
                date=time,
                trade_amount=trade_amount.value,
            )
            self.publish_signed_witness(signed_witness)
            logger.info(f"Arbitrator signed witness {str(signed_witness)}")
            return ""
        else:
            # Any peer can sign with DSA key
            if self.is_signed_account_age_witness(account_age_witness):
                logger.warning(f"Trader trying to sign already signed accountagewitness {str(account_age_witness)}")
                return None
            
            if self.is_sufficient_trade_amount_for_signing(trade_amount):
                logger.warning("Trader tried to sign account with too little trade amount")
                return None
            
            signature = Sig.sign(self.key_ring.signature_key_pair.private_key, account_age_witness.get_hash())
            signed_witness = SignedWitness(
                SignedWitnessVerificationMethod.TRADE,
                account_age_witness_hash=account_age_witness.get_hash(),
                signature=signature,
                signer_pub_key=Sig.get_public_key_bytes(self.key_ring.signature_key_pair.public_key),
                witness_owner_pub_key=peers_pub_key,
                date=time,
                trade_amount=trade_amount.value,
            )
            self.publish_signed_witness(signed_witness)
            logger.info(f"Trader signed witness {str(signed_witness)}")
            return signed_witness
    
    # Arbitrators sign with EC key
    def sign_trader_pub_key(self, ec_key: 'ECPrivkey', peers_pub_key: bytes, child_sign_time: int):
        time = child_sign_time - SignedWitnessService.SIGNER_AGE_MS - 1
        dummy_account_age_witness = AccountAgeWitness(get_ripemd160_hash(peers_pub_key) , time)
        return self.sign_and_publish_account_age_witness(dummy_account_age_witness, 
                                                         ec_key=ec_key,
                                                         trade_amount=SignedWitnessService.MINIMUM_TRADE_AMOUNT_FOR_SIGNING,
                                                         peers_pub_key=peers_pub_key,
                                                         time=child_sign_time)
        
    def self_sign_and_publish_account_age_witness(self, account_age_witness: 'AccountAgeWitness'):
        logger.info(f"Sign own accountAgeWitness {str(account_age_witness)}")
        self.sign_and_publish_account_age_witness(account_age_witness,
                                                  peers_pub_key=self.key_ring.signature_key_pair.public_key,
                                                  trade_amount=SignedWitnessService.MINIMUM_TRADE_AMOUNT_FOR_SIGNING)
        
    def verify_signature(self, signed_witness: 'SignedWitness') -> bool:
        if signed_witness.is_signed_by_arbitrator:
            return self._verify_signature_with_ec_key(signed_witness)
        else:
            return self._verify_signature_with_dsa_key(signed_witness)
        
    def _verify_signature_with_ec_key(self, signed_witness: 'SignedWitness') -> bool:
        _hash = StorageByteArray(signed_witness.get_hash())
        if _hash in self.verify_signature_with_ec_key_result_cache:
            return self.verify_signature_with_ec_key_result_cache[_hash]
        
        try:
            message = signed_witness.account_age_witness_hash.hex()
            signature_base64 = base64.b64encode(signed_witness.signature)
            ec_key = ECPubkey(signed_witness.signer_pub_key)
            if self.arbitrator_manager.is_public_key_in_list(ec_key.get_public_key_hex()):
                is_verified = ec_key.verify_message_hash(signature_base64, message)
                if not is_verified:
                    raise Exception("Signature verification failed at _verify_signature_with_ec_key")
                self.verify_signature_with_ec_key_result_cache[_hash] = True
                return True
            else:
                logger.warning("Provided EC key is not in list of valid arbitrators.")
                self.verify_signature_with_ec_key_result_cache[_hash] = False
                return False
        except Exception as e:
            logger.warning(f"verifySignature signedWitness failed. signedWitness={signed_witness}")
            logger.warning(f"Caused by {repr(e)}")
            self.verify_signature_with_ec_key_result_cache[_hash] = False
            return False
        
    def _verify_signature_with_dsa_key(self, signed_witness: 'SignedWitness') -> bool:
        _hash = StorageByteArray(signed_witness.get_hash())
        if _hash in self.verify_signature_with_dsa_key_result_cache:
            return self.verify_signature_with_dsa_key_result_cache[_hash]
        try:
            signature_pub_key = Sig.get_public_key_from_bytes(signed_witness.signer_pub_key)
            is_verified = Sig.verify(signature_pub_key, signed_witness.account_age_witness_hash, signed_witness.signature)
            if not is_verified:
                raise Exception("Signature verification failed at _verify_signature_with_dsa_key")
            self.verify_signature_with_dsa_key_result_cache[_hash] = True
            return True
        except Exception as e:
            logger.warning(f"verifySignature signedWitness failed. signedWitness={str(signed_witness)}")
            logger.warning(f"Caused by {repr(e)}")
            self.verify_signature_with_dsa_key_result_cache[_hash] = False
            return False
        
    def get_signed_witness_set(self, account_age_witness: 'AccountAgeWitness') -> set['SignedWitness']:
        key = StorageByteArray(account_age_witness.get_hash())
        return self.signed_witness_set_by_account_age_witness_hash.get(key, set())

    def get_arbitrators_signed_witness_set(self, account_age_witness: 'AccountAgeWitness') -> set['SignedWitness']:
        """SignedWitness objects signed by arbitrators"""
        return {
            witness for witness in self.get_signed_witness_set(account_age_witness)
            if witness.is_signed_by_arbitrator
        }

    def get_trusted_peer_signed_witness_set(self, account_age_witness: 'AccountAgeWitness') -> set['SignedWitness']:
        """SignedWitness objects signed by any other peer"""
        return {
            witness for witness in self.get_signed_witness_set(account_age_witness)
            if not witness.is_signed_by_arbitrator
        }

    def get_root_signed_witness_set(self, include_signed_by_arbitrator: bool) -> set['SignedWitness']:
        return {
            witness for witness in self.get_signed_witness_map_values()
            if (not self.get_signed_witness_set_by_owner_pub_key(witness.signer_pub_key, []) and
                (include_signed_by_arbitrator or 
                 witness.verification_method != SignedWitnessVerificationMethod.ARBITRATOR))
        }

    # Find first (in time) SignedWitness per missing signer
    def get_unsigned_signer_pub_keys(self) -> set['SignedWitness']:
        """Find first (in time) SignedWitness per missing signer"""
        oldest_unsigned_signers: dict['StorageByteArray', 'SignedWitness'] = {}
        for signed_witness in self.get_root_signed_witness_set(False):
            key = StorageByteArray(signed_witness.signer_pub_key)
            if key not in oldest_unsigned_signers or oldest_unsigned_signers[key].date > signed_witness.date:
                oldest_unsigned_signers[key] = signed_witness
        return set(oldest_unsigned_signers.values())

    def is_signed_account_age_witness(self, account_age_witness: 'AccountAgeWitness') -> bool:
        return self.is_signer_account_age_witness(
            account_age_witness, 
            get_time_ms() + SignedWitnessService.SIGNER_AGE_MS
        )

    def is_sufficient_trade_amount_for_signing(self, trade_amount: 'Coin') -> bool:
        return not trade_amount.is_less_than(SignedWitnessService.MINIMUM_TRADE_AMOUNT_FOR_SIGNING)

    def verify_signer(self, signed_witness: 'SignedWitness') -> bool:
        witnesses = self.get_signed_witness_set_by_owner_pub_key(
            signed_witness.witness_owner_pub_key, 
            []
        )
        return any(
            self.is_valid_signer_witness_internal(w, signed_witness.date, [])
            for w in witnesses
        )

    def is_signer_account_age_witness(self, account_age_witness: "AccountAgeWitness", time: int = None) -> bool:
        """
        Checks whether the account_age_witness has a valid signature from a peer/arbitrator and is allowed to sign
        other accounts.

        Args:
            account_age_witness: AccountAgeWitness to check
            time: time of signing

        Returns:
            True if account_age_witness is allowed to sign at time, False otherwise.
        """
        if time is None:
            time = get_time_ms()
        
        signed_witness_set = self.get_signed_witness_set(account_age_witness)
        return any(
            self.is_valid_signer_witness_internal(signed_witness, time, [])
            for signed_witness in signed_witness_set
        )

    def is_valid_signer_witness_internal(self, signed_witness: 'SignedWitness',
                                       child_signed_witness_date_ms: int,
                                       excluded_pub_keys: list['StorageByteArray']) -> bool:
        """
        Helper to is_valid_account_age_witness(account_age_witness)

        Args:
            signed_witness: the signed_witness to validate
            child_signed_witness_date_ms: the date the child SignedWitness was signed or current time if it is a leaf
            excluded_pub_keys: list to prevent recursive loops

        Returns:
            True if signed_witness is valid, False otherwise
        """
        if self.filter_manager.is_witness_signer_pub_key_banned(signed_witness.witness_owner_pub_key.hex()):
            return False

        if not self.verify_signature(signed_witness):
            return False

        if signed_witness.is_signed_by_arbitrator:
            # If signed by an arbitrator we don't have to check anything else
            return True

        if not self.verify_date(signed_witness, child_signed_witness_date_ms):
            return False

        if len(excluded_pub_keys) >= 2000:
            # Prevent DoS attack: an attacker floods the SignedWitness db with a long chain 
            # that takes lots of time to verify
            return False

        excluded_pub_keys.append(StorageByteArray(signed_witness.signer_pub_key))
        excluded_pub_keys.append(StorageByteArray(signed_witness.witness_owner_pub_key))
        
        # Iterate over signed_witness signers
        signer_signed_witness_set = self.get_signed_witness_set_by_owner_pub_key(
            signed_witness.signer_pub_key, 
            excluded_pub_keys
        )

        for signer_signed_witness in signer_signed_witness_set:
            if self.is_valid_signer_witness_internal(
                signer_signed_witness,
                signed_witness.date,
                excluded_pub_keys
            ):
                return True

        excluded_pub_keys.pop()
        excluded_pub_keys.pop()
        
        # If we have not returned in the loops or they have been empty we have not found a valid signer
        return False

    def verify_date(self, signed_witness: 'SignedWitness', child_signed_witness_date_ms: int) -> bool:
        child_signed_witness_date_minus_chargeback_period_ms = (
            child_signed_witness_date_ms - SignedWitnessService.SIGNER_AGE_MS
        )
        signed_witness_date_ms = signed_witness.date
        return signed_witness_date_ms <= child_signed_witness_date_minus_chargeback_period_ms

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // Private
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_to_map(self, signed_witness: 'SignedWitness'):
        if signed_witness.get_hash_as_byte_array() not in self.signed_witness_map:  
            self.signed_witness_map[signed_witness.get_hash_as_byte_array()] = signed_witness

        account_age_witness_hash = StorageByteArray(signed_witness.account_age_witness_hash)
        if account_age_witness_hash not in self.signed_witness_set_by_account_age_witness_hash:
            self.signed_witness_set_by_account_age_witness_hash[account_age_witness_hash] = set()
        self.signed_witness_set_by_account_age_witness_hash[account_age_witness_hash].add(signed_witness)

        owner_pub_key = StorageByteArray(signed_witness.witness_owner_pub_key)
        if owner_pub_key not in self.signed_witness_set_by_owner_pub_key:
            self.signed_witness_set_by_owner_pub_key[owner_pub_key] = set()
        self.signed_witness_set_by_owner_pub_key[owner_pub_key].add(signed_witness)

    def publish_signed_witness(self, signed_witness: 'SignedWitness'):
        if signed_witness.get_hash_as_byte_array() not in self.signed_witness_map:
            logger.info(f"broadcast signed witness {signed_witness}")
            # We set reBroadcast to True to achieve better resilience
            self.p2p_service.add_persistable_network_payload(signed_witness, True)
            self.add_to_map(signed_witness)

    def do_republish_all_signed_witnesses(self):
        for signed_witness in self.get_signed_witness_map_values():
            self.p2p_service.add_persistable_network_payload(signed_witness, True)

    def remove_signed_witness(self, signed_witness: 'SignedWitness'):
        self.signed_witness_map.pop(signed_witness.get_hash_as_byte_array(), None)

        account_age_witness_hash = StorageByteArray(signed_witness.account_age_witness_hash)
        if account_age_witness_hash in self.signed_witness_set_by_account_age_witness_hash:
            witness_set = self.signed_witness_set_by_account_age_witness_hash[account_age_witness_hash]
            witness_set.discard(signed_witness)
            if not witness_set:
                del self.signed_witness_set_by_account_age_witness_hash[account_age_witness_hash]

        owner_pub_key = StorageByteArray(signed_witness.witness_owner_pub_key)
        if owner_pub_key in self.signed_witness_set_by_owner_pub_key:
            witness_set = self.signed_witness_set_by_owner_pub_key[owner_pub_key]
            witness_set.discard(signed_witness)
            if not witness_set:
                del self.signed_witness_set_by_owner_pub_key[owner_pub_key]
