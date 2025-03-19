from bisq.common.crypto.hash import get_keccak1600_hash
from bisq.core.xmr.knaccc.monero.address.block_base58 import BlockBase58
from bisq.core.xmr.knaccc.monero.address.byte_util import ByteUtil
from bisq.core.xmr.knaccc.monero.address.exceptions.invalid_wallet_address_exception import (
    InvalidWalletAddressException,
)
from bisq.core.xmr.knaccc.monero.crypto.crypto_util import CryptoUtil
from bisq.core.xmr.knaccc.monero.crypto.scalar import Scalar
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_field_element import (
    Ed25519EncodedFieldElement,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_encoded_group_element import (
    Ed25519EncodedGroupElement,
)
from bisq.core.xmr.org.nem.core.crypto.ed25519.arithmetic.ed25519_group import (
    Ed25519Group,
)
from electrum_min.bitcoin import base_decode, base_encode


class WalletAddress:
    PUBLIC_ADDRESS_PREFIX = 18
    PUBLIC_INTEGRATED_ADDRESS_PREFIX = 19
    PUBLIC_SUBADDRESS_PREFIX = 42

    def __init__(self, base58_wallet_address: str):
        self.base58 = base58_wallet_address
        pos = 0
        decoded = BlockBase58.decode(base58_wallet_address)
        if decoded is None:
            raise InvalidWalletAddressException("cannot decode base58 address")
        self.hex = decoded.hex()

        self.network_byte = self.hex[0:2]
        pos += 2
        if not (
            self.network_byte
            == ByteUtil.byte_to_hex(WalletAddress.PUBLIC_ADDRESS_PREFIX)
            or self.network_byte
            == ByteUtil.byte_to_hex(WalletAddress.PUBLIC_INTEGRATED_ADDRESS_PREFIX)
            or self.network_byte
            == ByteUtil.byte_to_hex(WalletAddress.PUBLIC_SUBADDRESS_PREFIX)
        ):
            raise InvalidWalletAddressException(
                f"Unrecognized address type: {self.network_byte} (hex)"
            )

        self.public_spend_key_hex = self.hex[pos : pos + 64]
        pos += 64
        self.public_view_key_hex = self.hex[pos : pos + 64]
        pos += 64

        self.integrated_payment_id = None
        if self.network_byte == ByteUtil.byte_to_hex(
            self.PUBLIC_INTEGRATED_ADDRESS_PREFIX
        ):
            self.integrated_payment_id = self.hex[pos : pos + 16]
            pos += 16

        self.checksum = self.hex[pos : pos + 8]
        pos += 8

        recalculated_checksum_hex = get_keccak1600_hash(
            bytes.fromhex(
                self.network_byte
                + self.public_spend_key_hex
                + self.public_view_key_hex
                + (self.integrated_payment_id or "")
            )
        ).hex()[:8]

        if self.checksum != recalculated_checksum_hex:
            raise InvalidWalletAddressException("Checksum does not match")

    @property
    def is_subaddress(self) -> bool:
        return self.network_byte == ByteUtil.byte_to_hex(
            WalletAddress.PUBLIC_SUBADDRESS_PREFIX
        )

    def __str__(self):
        return self.base58

    G = Ed25519Group.BASE_POINT

    @staticmethod
    def get_subaddress_public_spend_key_bytes(
        private_view_key: Scalar,
        public_spend_key_bytes: bytes,
        account_id: int,
        subaddress_id: int,
    ) -> bytes:
        if account_id == 0 and subaddress_id == 0:
            raise RuntimeError("Not to be called for the base wallet address")

        data = (
            b"SubAddr\0"
            + private_view_key.bytes
            + ByteUtil.long_to_little_endian_uint32_byte_array(account_id)
            + ByteUtil.long_to_little_endian_uint32_byte_array(subaddress_id)
        )
        m = CryptoUtil.hash_to_scalar(data)
        M = WalletAddress.G.scalar_multiply(Ed25519EncodedFieldElement(m.bytes))
        B = Ed25519EncodedGroupElement(public_spend_key_bytes).decode()
        D = B.add(M.to_cached())
        return D.encode().get_raw()

    @staticmethod
    def _get_subaddress_base58(
        private_view_key: Scalar,
        public_spend_key_bytes: bytes,
        account_id: int,
        subaddress_id: int,
    ) -> str:
        D = Ed25519EncodedGroupElement(
            WalletAddress.get_subaddress_public_spend_key_bytes(
                private_view_key, public_spend_key_bytes, account_id, subaddress_id
            )
        ).decode()
        D.precompute_for_scalar_multiplication()
        C = D.scalar_multiply(Ed25519EncodedFieldElement(private_view_key.bytes))

        subaddress_bytes = (
            bytes([WalletAddress.PUBLIC_SUBADDRESS_PREFIX])
            + D.encode().get_raw()
            + C.encode().get_raw()
        )
        hex_str = subaddress_bytes.hex()
        calculated_checksum_hex = get_keccak1600_hash(bytes.fromhex(hex_str)).hex()[:8]
        hex_str += calculated_checksum_hex
        return BlockBase58.encode(bytes.fromhex(hex_str))

    def get_subaddress_base58(
        self, private_view_key_hex: str, account_id: int, subaddress_id: int
    ) -> str:
        if not self.check_private_view_key(private_view_key_hex):
            raise InvalidWalletAddressException(
                "Wrong private view key for main address"
            )
        return WalletAddress._get_subaddress_base58(
            Scalar(private_view_key_hex),
            bytes.fromhex(self.public_spend_key_hex),
            account_id,
            subaddress_id,
        )

    def check_private_view_key(self, private_view_key: str) -> bool:
        return WalletAddress.is_private_key_reduced(
            private_view_key
        ) and WalletAddress.does_private_key_resolve_to_public_key(
            private_view_key, self.public_view_key_hex
        )

    @staticmethod
    def is_private_key_reduced(private_key_hex: str) -> bool:
        input_bytes = bytes.fromhex(private_key_hex)
        reduced_bytes = CryptoUtil.sc_reduce32(input_bytes)
        return input_bytes == reduced_bytes

    @staticmethod
    def does_private_key_resolve_to_public_key(
        private_key_hex: str, public_key_hex: str
    ) -> bool:
        m = Scalar(private_key_hex)
        M = WalletAddress.G.scalar_multiply(Ed25519EncodedFieldElement(m.bytes))
        generated_pub_key = M.encode().get_raw()
        return generated_pub_key == bytes.fromhex(public_key_hex)
