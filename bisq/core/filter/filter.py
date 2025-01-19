import base64
from datetime import timedelta
from typing import Optional
from bisq.common.crypto.sig import Sig, DSA
from bisq.common.exclude_for_hash_aware_proto import ExcludeForHashAwareProto
from bisq.common.protocol.network.get_data_response_priority import GetDataResponsePriority
from bisq.common.protocol.proto_util import ProtoUtil
from bisq.common.util.extra_data_map_validator import ExtraDataMapValidator
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.filter.payment_account_filter import PaymentAccountFilter
from bisq.core.network.p2p.storage.payload.expirable_payload import ExpirablePayload
from bisq.core.network.p2p.storage.payload.protected_storage_payload import ProtectedStoragePayload
import proto.pb_pb2 as protobuf
from utils.ordered_containers import OrderedSet
from utils.time import get_time_ms

class Filter(ProtectedStoragePayload, ExpirablePayload, ExcludeForHashAwareProto):
    TTL = int(timedelta(days=180).total_seconds() * 1000)

    def __init__(self,
                 banned_offer_ids: list[str],
                 node_addresses_banned_from_trading: list[str],
                 banned_auto_conf_explorers: list[str],
                 banned_payment_accounts: list[PaymentAccountFilter],
                 banned_currencies: list[str],
                 banned_payment_methods: list[str],
                 arbitrators: list[str],
                 seed_nodes: list[str],
                 price_relay_nodes: list[str],
                 prevent_public_btc_network: bool,
                 btc_nodes: list[str],
                 disable_dao: bool,
                 disable_dao_below_version: str,
                 disable_trade_below_version: str,
                 mediators: list[str],
                 refund_agents: list[str],
                 banned_account_witness_signer_pub_keys: list[str],
                 btc_fee_receiver_addresses: list[str],
                 owner_pub_key: "DSA.DsaKey" = None,
                 owner_pub_key_bytes: bytes = None,
                 creation_date: int = None,
                 extra_data_map: dict[str, str] = None,
                 signature_as_base64: Optional[str] = None,
                 signer_pub_key_as_hex: str = None,
                 banned_privileged_dev_pub_keys: list[str] = None,
                 disable_auto_conf: bool = None,
                 node_addresses_banned_from_network: OrderedSet[str] = None,
                 disable_mempool_validation: bool = None,
                 disable_api: bool = None,
                 disable_pow_message: bool = None,
                 pow_difficulty: float = None,
                 enabled_pow_versions: list[int] = None,
                 maker_fee_btc: int = None,
                 taker_fee_btc: int = None,
                 maker_fee_bsq: int = None,
                 taker_fee_bsq: int = None,
                 delayed_payout_payment_accounts: list[PaymentAccountFilter] = None,
                 added_btc_nodes: list[str] = None,
                 added_seed_nodes: list[str] = None,
                 uid: str = '') -> None:
        self.banned_offer_ids = banned_offer_ids
        self.node_addresses_banned_from_trading = node_addresses_banned_from_trading
        self.banned_auto_conf_explorers = banned_auto_conf_explorers
        self.banned_payment_accounts = banned_payment_accounts
        self.banned_currencies = banned_currencies
        self.banned_payment_methods = banned_payment_methods
        self.arbitrators = arbitrators
        self.seed_nodes = seed_nodes
        self.price_relay_nodes = price_relay_nodes
        self.prevent_public_btc_network = prevent_public_btc_network
        self.btc_nodes = btc_nodes
        # SignatureAsBase64 is not set initially as we use the serialized data for signing. We set it after signature is
        # created by cloning the object with a non-null sig.
        self.signature_as_base64 = signature_as_base64
        # The pub EC key from the dev who has signed and published the filter (different to ownerPubKeyBytes)
        self.signer_pub_key_as_hex = signer_pub_key_as_hex
        # The pub key used for the data protection in the p2p storage
        self.owner_pub_key_bytes = owner_pub_key_bytes
        self.disable_dao = disable_dao
        self.disable_dao_below_version = disable_dao_below_version
        self.disable_trade_below_version = disable_trade_below_version
        self.mediators = mediators
        self.refund_agents = refund_agents
        
        self.banned_account_witness_signer_pub_keys = banned_account_witness_signer_pub_keys
        
        self.btc_fee_receiver_addresses = btc_fee_receiver_addresses
        
        self.creation_date = creation_date or get_time_ms()
        
        self.banned_privileged_dev_pub_keys = banned_privileged_dev_pub_keys or []
        
        # Should be only used in emergency case if we need to add data but do not want to break backward compatibility
        # The hash of the data is not unique anymore if the only change have been at
        # the ExcludeForHash annotated fields.
        self.extra_data_map = ExtraDataMapValidator.get_validated_extra_data_map(extra_data_map)

        self.owner_pub_key: "DSA.DsaKey" = owner_pub_key
        
        # added at v1.3.8
        self.disable_auto_conf = disable_auto_conf or False
        
        # added at v1.5.5
        self.node_addresses_banned_from_network = node_addresses_banned_from_network or OrderedSet()
        self.disable_api = disable_api or False
        
        # added at v1.6.0
        self.disable_mempool_validation = disable_mempool_validation or False
        
        # added at BsqSwap release
        self.disable_pow_message = disable_pow_message or False
        # 2 ** effective-number-of-leading-zeros for pow for BSQ swap offers, when using Hashcash (= version 0), and
        # a similar difficulty for Equihash (= versions 1) or later schemes. Difficulty of 2 ** 8 (= 256) requires
        # 0.856 ms in average, 2 ** 15 (= 32768) about 100 ms. See HashCashServiceTest for more info.
        self.pow_difficulty = pow_difficulty or 0.0
        # Enabled PoW version numbers in reverse order of preference, starting with 0 for Hashcash.
        self.enabled_pow_versions = enabled_pow_versions or []
        
        # Added at v 1.8.0
        # BSQ fee gets updated in proposals repo (e.g. https://github.com/bisq-network/proposals/issues/345)
        self.maker_fee_btc = maker_fee_btc or 0
        self.taker_fee_btc = taker_fee_btc or 0
        self.maker_fee_bsq = maker_fee_bsq or 0
        self.taker_fee_bsq = taker_fee_bsq or 0
        
        # Added at v1.9.13
        self.delayed_payout_payment_accounts = delayed_payout_payment_accounts or []
        
        # Added at v 1.9.16
        self.added_btc_nodes = added_btc_nodes or [] # excludeForHash
        self.added_seed_nodes = added_seed_nodes or [] # excludeForHash
        
        # As we might add more ExcludeForHash we want to ensure to have a unique identifier.
        # The hash of the data is not unique anymore if the only change have been at
        # the ExcludeForHash annotated fields.
        self.uid = uid
        
        if self.owner_pub_key_bytes is not None:
            self.owner_pub_key = Sig.get_public_key_from_bytes(self.owner_pub_key_bytes)
        elif self.owner_pub_key is not None:
            self.owner_pub_key_bytes = Sig.get_public_key_bytes(self.owner_pub_key)
        else:
            raise ValueError("either owner_pub_key or owner_pub_key_bytes must be set")

    # After we have created the signature from the filter data we clone it and apply the signature
    @staticmethod
    def clone_with_sig(filter_obj: 'Filter', signature_as_base64: str) -> 'Filter':
        filter_dict = filter_obj.__dict__.copy()
        del filter_dict['signature_as_base64']
        return Filter(**filter_dict, signature_as_base64=signature_as_base64)

    # Used for signature verification as we created the sig without the signatureAsBase64 field we set it to null again
    @staticmethod
    def clone_without_sig(filter_obj: 'Filter') -> 'Filter':
        filter_dict = filter_obj.__dict__.copy()
        del filter_dict['signature_as_base64']
        return Filter(**filter_dict, signature_as_base64=None)

    def to_proto_message(self) -> 'protobuf.StoragePayload':
        return self.to_proto(False)

    def to_proto(self, serialize_for_hash: bool = False) -> 'protobuf.StoragePayload':
        return protobuf.StoragePayload(
            filter=self.to_filter_proto(serialize_for_hash)
        )

    def to_filter_proto(self, serialize_for_hash: bool = False) -> 'protobuf.Filter':
        filter = self.get_filter_builder()
        if serialize_for_hash:
            # excludeForHash
            filter.ClearField("addedBtcNodes") # Weird protobuf names
            filter.ClearField("addedSeedNodes") # Weird protobuf names
            
        return filter
    
    def get_filter_builder(self) -> protobuf.Filter:
        payment_account_filters = [
            account.to_proto_message() for account in self.banned_payment_accounts
        ]

        delayed_payout_payment_accounts = [
            account.to_proto_message() for account in self.delayed_payout_payment_accounts
        ]
        
        builder = protobuf.Filter(
            banned_offer_ids=self.banned_offer_ids,
            node_addresses_banned_from_trading=self.node_addresses_banned_from_trading,
            banned_payment_accounts=payment_account_filters,
            banned_currencies=self.banned_currencies,
            banned_payment_methods=self.banned_payment_methods,
            arbitrators=self.arbitrators,
            seed_nodes=self.seed_nodes,
            price_relay_nodes=self.price_relay_nodes,
            prevent_public_btc_network=self.prevent_public_btc_network,
            btc_nodes=self.btc_nodes,
            disable_dao=self.disable_dao,
            disable_dao_below_version=self.disable_dao_below_version,
            disable_trade_below_version=self.disable_trade_below_version,
            mediators=self.mediators,
            refundAgents=self.refund_agents, # weird protobuf names
            bannedSignerPubKeys=self.banned_account_witness_signer_pub_keys, # weird protobuf names
            btc_fee_receiver_addresses=self.btc_fee_receiver_addresses,
            owner_pub_key_bytes=self.owner_pub_key_bytes,
            signer_pub_key_as_hex=self.signer_pub_key_as_hex,
            creation_date=self.creation_date,
            bannedPrivilegedDevPubKeys=self.banned_privileged_dev_pub_keys, # weird protobuf names
            disable_auto_conf=self.disable_auto_conf,
            banned_auto_conf_explorers=self.banned_auto_conf_explorers,
            node_addresses_banned_from_network=list(self.node_addresses_banned_from_network),
            disable_mempool_validation=self.disable_mempool_validation,
            disable_api=self.disable_api,
            disable_pow_message=self.disable_pow_message,
            pow_difficulty=self.pow_difficulty,
            enabled_pow_versions=self.enabled_pow_versions,
            maker_fee_btc=self.maker_fee_btc,
            taker_fee_btc=self.taker_fee_btc,
            maker_fee_bsq=self.maker_fee_bsq,
            taker_fee_bsq=self.taker_fee_bsq,
            delayedPayoutPaymentAccounts=delayed_payout_payment_accounts, # weird protobuf names
            addedBtcNodes=self.added_btc_nodes, # weird protobuf names
            addedSeedNodes=self.added_seed_nodes, # weird protobuf names
            uid=self.uid
        )

        if self.signature_as_base64:
            builder.signature_as_base64 = self.signature_as_base64
        if self.extra_data_map:
            builder.extra_data.update(self.extra_data_map)

        return builder

    @staticmethod
    def from_proto(proto: 'protobuf.Filter') -> 'Filter':
        banned_payment_accounts = [
            PaymentAccountFilter.from_proto(account) 
            for account in proto.banned_payment_accounts
        ]

        delayed_payout_payment_accounts = [
            PaymentAccountFilter.from_proto(account) 
            for account in proto.delayedPayoutPaymentAccounts
        ]
        
        return Filter(
            banned_offer_ids=ProtoUtil.protocol_string_list_to_list(proto.banned_offer_ids),
            node_addresses_banned_from_trading=ProtoUtil.protocol_string_list_to_list(proto.node_addresses_banned_from_trading),
            banned_auto_conf_explorers=ProtoUtil.protocol_string_list_to_list(proto.banned_auto_conf_explorers),
            banned_payment_accounts=banned_payment_accounts,
            banned_currencies=ProtoUtil.protocol_string_list_to_list(proto.banned_currencies),
            banned_payment_methods=ProtoUtil.protocol_string_list_to_list(proto.banned_payment_methods),
            arbitrators=ProtoUtil.protocol_string_list_to_list(proto.arbitrators),
            seed_nodes=ProtoUtil.protocol_string_list_to_list(proto.seed_nodes),
            price_relay_nodes=ProtoUtil.protocol_string_list_to_list(proto.price_relay_nodes),
            prevent_public_btc_network=proto.prevent_public_btc_network,
            btc_nodes=ProtoUtil.protocol_string_list_to_list(proto.btc_nodes),
            disable_dao=proto.disable_dao,
            disable_dao_below_version=proto.disable_dao_below_version,
            disable_trade_below_version=proto.disable_trade_below_version,
            mediators=ProtoUtil.protocol_string_list_to_list(proto.mediators),
            refund_agents=ProtoUtil.protocol_string_list_to_list(proto.refundAgents),  
            banned_account_witness_signer_pub_keys=ProtoUtil.protocol_string_list_to_list(proto.bannedSignerPubKeys),
            btc_fee_receiver_addresses=ProtoUtil.protocol_string_list_to_list(proto.btc_fee_receiver_addresses),
            owner_pub_key_bytes=proto.owner_pub_key_bytes,
            creation_date=proto.creation_date,
            extra_data_map=dict(proto.extra_data) if proto.extra_data else None,
            signature_as_base64=proto.signature_as_base64,
            signer_pub_key_as_hex=proto.signer_pub_key_as_hex,
            banned_privileged_dev_pub_keys=ProtoUtil.protocol_string_list_to_list(proto.bannedPrivilegedDevPubKeys),
            disable_auto_conf=proto.disable_auto_conf,
            node_addresses_banned_from_network=ProtoUtil.protocol_string_list_to_set(proto.node_addresses_banned_from_network),
            disable_mempool_validation=proto.disable_mempool_validation,
            disable_api=proto.disable_api,
            disable_pow_message=proto.disable_pow_message,
            pow_difficulty=proto.pow_difficulty,
            enabled_pow_versions=list(proto.enabled_pow_versions),
            maker_fee_btc=proto.maker_fee_btc,
            taker_fee_btc=proto.taker_fee_btc,
            maker_fee_bsq=proto.maker_fee_bsq,
            taker_fee_bsq=proto.taker_fee_bsq,
            delayed_payout_payment_accounts=delayed_payout_payment_accounts,
            added_btc_nodes=ProtoUtil.protocol_string_list_to_list(proto.addedBtcNodes),
            added_seed_nodes=ProtoUtil.protocol_string_list_to_list(proto.addedSeedNodes),
            uid=proto.uid
        )

    def get_data_response_priority(self):
        return GetDataResponsePriority.HIGH

    def get_ttl(self) -> int:
        return self.TTL
    
    def get_owner_pub_key(self):
        return self.owner_pub_key
    
    def get_extra_data_map(self):
        return self.extra_data_map

    def __str__(self):
        return (f"Filter{{\n"
                f"     banned_offer_ids={self.banned_offer_ids},\n"
                f"     node_addresses_banned_from_trading={self.node_addresses_banned_from_trading},\n"
                f"     banned_auto_conf_explorers={self.banned_auto_conf_explorers},\n"
                f"     banned_payment_accounts={self.banned_payment_accounts},\n"
                f"     banned_currencies={self.banned_currencies},\n"
                f"     banned_payment_methods={self.banned_payment_methods},\n"
                f"     arbitrators={self.arbitrators},\n"
                f"     seed_nodes={self.seed_nodes},\n"
                f"     price_relay_nodes={self.price_relay_nodes},\n"
                f"     prevent_public_btc_network={self.prevent_public_btc_network},\n"
                f"     btc_nodes={self.btc_nodes},\n"
                f"     signature_as_base64='{self.signature_as_base64}',\n"
                f"     signer_pub_key_as_hex='{self.signer_pub_key_as_hex}',\n"
                f"     owner_pub_key_bytes={bytes_as_hex_string(self.owner_pub_key_bytes)},\n"
                f"     disable_dao={self.disable_dao},\n"
                f"     disable_dao_below_version='{self.disable_dao_below_version}',\n"
                f"     disable_trade_below_version='{self.disable_trade_below_version}',\n"
                f"     mediators={self.mediators},\n"
                f"     refund_agents={self.refund_agents},\n"
                f"     banned_account_witness_signer_pub_keys={self.banned_account_witness_signer_pub_keys},\n"
                f"     btc_fee_receiver_addresses={self.btc_fee_receiver_addresses},\n"
                f"     creation_date={self.creation_date},\n"
                f"     banned_privileged_dev_pub_keys={self.banned_privileged_dev_pub_keys},\n"
                f"     extra_data_map={self.extra_data_map},\n"
                f"     owner_pub_key={self.owner_pub_key},\n"
                f"     disable_auto_conf={self.disable_auto_conf},\n"
                f"     node_addresses_banned_from_network={self.node_addresses_banned_from_network},\n"
                f"     disable_mempool_validation={self.disable_mempool_validation},\n"
                f"     disable_api={self.disable_api},\n"
                f"     disable_pow_message={self.disable_pow_message},\n"
                f"     pow_difficulty={self.pow_difficulty},\n"
                f"     enabled_pow_versions={self.enabled_pow_versions},\n"
                f"     maker_fee_btc={self.maker_fee_btc},\n"
                f"     taker_fee_btc={self.taker_fee_btc},\n"
                f"     maker_fee_bsq={self.maker_fee_bsq},\n"
                f"     taker_fee_bsq={self.taker_fee_bsq},\n"
                f"     added_btc_nodes={self.added_btc_nodes},\n"
                f"     added_seed_nodes={self.added_seed_nodes},\n"
                f"     uid='{self.uid}'\n"
                f"}}")