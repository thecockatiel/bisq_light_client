from typing import TYPE_CHECKING

from bisq.common.crypto.crypto_exception import CryptoException
from bisq.common.crypto.encryption import Encryption, rsa
from bisq.common.crypto.hash import get_sha256_hash
from bisq.common.crypto.sealed_and_signed import SealedAndSigned
from bisq.common.crypto.sig import Sig
from bisq.common.protocol.network.network_envelope import NetworkEnvelope
from bisq.common.protocol.protobuffer_exception import ProtobufferException
from bisq.core.network.crypto.decrypted_data_tuple import DecryptedDataTuple
from bisq.core.network.p2p.decrypted_message_with_pub_key import DecryptedMessageWithPubKey
import pb_pb2 as protobuf
from google.protobuf import message

if TYPE_CHECKING:
    from bisq.common.crypto.key_pair import KeyPair
    from bisq.common.crypto.key_ring import KeyRing
    from bisq.common.crypto.pub_key_ring import PubKeyRing
    from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver

class EncryptionService:
    def __init__(self, key_ring: 'KeyRing', network_proto_resolver: 'NetworkProtoResolver'):
        self.key_ring = key_ring
        self.network_proto_resolver = network_proto_resolver

    def encrypt_and_sign(self, pub_key_ring: 'PubKeyRing', network_envelope: NetworkEnvelope) -> SealedAndSigned:
        return self.encrypt_hybrid_with_signature(network_envelope, self.key_ring.signature_key_pair, pub_key_ring.encryption_pub_key)

    def decrypt_hybrid_with_signature(self, sealed_and_signed: SealedAndSigned, private_key: rsa.RSAPrivateKey) -> DecryptedDataTuple:
        """
        Args:
            sealed_and_signed (SealedAndSigned): The sealed and signed message to be decrypted.
            private_key (rsa.RSAPrivateKey): The RSA private key used to decrypt the secret key.
        Returns:
            DecryptedDataTuple: A tuple containing the decrypted payload and the public key used for the signature.
        Raises:
            CryptoException: If the signature verification fails.
            ProtobufferException: If there is an error parsing the protocol buffer message.
        """
        secret_key = Encryption.decrypt_secret_key(sealed_and_signed.encrypted_secret_key, private_key)
        if not Sig.verify(sealed_and_signed.sig_public_key,
                           get_sha256_hash(sealed_and_signed.encrypted_payload_with_hmac),
                           sealed_and_signed.signature):
            raise CryptoException("Signature verification failed.")

        try:
            bytes_ = Encryption.decrypt_payload_with_hmac(sealed_and_signed.encrypted_payload_with_hmac, secret_key)
            envelope = protobuf.NetworkEnvelope.FromString(bytes_)
            decrypted_payload = self.network_proto_resolver.from_proto(envelope)
            return DecryptedDataTuple(decrypted_payload, sealed_and_signed.sig_public_key)
        except message.DecodeError as e:
            raise ProtobufferException("Unable to parse protobuffer message.", e)

    def decrypt_and_verify(self, sealed_and_signed: SealedAndSigned) -> DecryptedMessageWithPubKey:
        decrypted_data_tuple = self.decrypt_hybrid_with_signature(sealed_and_signed, self.key_ring.encryption_key_pair.private_key)
        return DecryptedMessageWithPubKey(network_envelope=decrypted_data_tuple.network_envelope, signature_pub_key=decrypted_data_tuple.sig_public_key)

    @staticmethod
    def encrypt_payload_with_hmac(network_envelope: NetworkEnvelope, secret_key: bytes) -> bytes:
        return Encryption.encrypt_payload_with_hmac(network_envelope.to_proto_network_envelope().SerializeToString(), secret_key)

    @staticmethod
    def encrypt_hybrid_with_signature(payload: NetworkEnvelope, signature_key_pair: 'KeyPair',
                                      encryption_public_key: rsa.RSAPublicKey) -> SealedAndSigned:
        """
        Args:
            payload (NetworkEnvelope): The data to be encrypt.
            signature_key_pair (KeyPair): The key pair for signing.
            encryption_public_key (rsa.RSAPublicKey): The public key used for encryption.
        Returns:
            SealedAndSigned
        """
        #  Create a symmetric key
        secret_key = Encryption.generate_secret_key(256)

        # Encrypt secretKey with receiver's publicKey
        encrypted_secret_key = Encryption.encrypt_secret_key(secret_key, encryption_public_key)

        # Encrypt with sym key payload with appended hmac
        encrypted_payload_with_hmac = EncryptionService.encrypt_payload_with_hmac(payload, secret_key)

        # sign hash of encryptedPayloadWithHmac
        hash = get_sha256_hash(encrypted_payload_with_hmac)
        signature = Sig.sign(signature_key_pair.private_key, hash)

        # Pack all together
        return SealedAndSigned(encrypted_secret_key=encrypted_secret_key,
                               encrypted_payload_with_hmac=encrypted_payload_with_hmac,
                               signature=signature,
                               sig_public_key=signature_key_pair.public_key)
