from typing import Sequence
from .bip32 import normalize_bip32_derivation
from .simple_config import SimpleConfig
from . import keystore
from .storage import WalletStorage
from .wallet_db import WalletDB
from .mnemonic import Mnemonic
from .elogging import get_logger
from .util import UserFacingException
from .wallet import Standard_Wallet, Abstract_Wallet


_logger = get_logger(__name__)


class NoSyncDeterministicWallet(Standard_Wallet):

    def __init__(self, db: "WalletDB", *, config: "SimpleConfig"):
        Standard_Wallet.__init__(self, db, config=config)

    def synchronize(self):
        # We deliberately make synchronize a noop to not generate new addresses
        # because bisq is supposed to manage the addresses
        pass

def create_new_bisq_wallet(*, path, config: SimpleConfig, derivation_path: str, passphrase=None,
                password=None, seed: str=None,encrypt_file=True, seed_type=None, gap_limit=None) -> dict:
    """Create a new wallet for bisq"""
    storage = WalletStorage(path)
    if storage.file_exists():
        raise UserFacingException("Remove the existing wallet first!")
    db = WalletDB('', storage=storage, upgrade=True)
    if not seed:
        seed = Mnemonic('en').make_seed(seed_type=seed_type, num_bits=256) # 24 words
    root_seed = keystore.bip39_to_seed(seed, passphrase=passphrase)
    derivation_path = normalize_bip32_derivation(derivation_path)
    k = keystore.from_bip43_rootseed(root_seed, derivation=derivation_path, xtype="p2wpkh")
    k.add_seed(seed)
    db.put('keystore', k.dump())
    db.put('wallet_type', 'standard')
    if k.can_have_deterministic_lightning_xprv():
        db.put('lightning_xprv', k.get_lightning_xprv(None))
    if gap_limit is not None:
        db.put('gap_limit', gap_limit)
    wallet = NoSyncDeterministicWallet(db, config=config)
    wallet.update_password(old_pw=None, new_pw=password, encrypt_storage=encrypt_file)
    msg = "Please keep your seed in a safe place; if you lose it, you will not be able to restore your wallet."
    wallet.save_db()
    return {'seed': seed, 'wallet': wallet, 'msg': msg}