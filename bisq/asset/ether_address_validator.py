
from bisq.asset.regex_address_validator import RegexAddressValidator


class EtherAddressValidator(RegexAddressValidator):
    """
    original bisq note:
    
    Validates an Ethereum address using the regular expression on record in
    https://github.com/ethereum/web3.js/blob/bd6a890/lib/utils/utils.js#L405
    
    Note that this implementation is widely used, not just
    for actual Ether address validation, but also for
    Erc20Token implementations and other Ethereum-based Asset
    implementations.
    """
    
    def __init__(self, error_msg_i18n_key: str = None):
        super().__init__(r'^(0x)?[0-9a-fA-F]{40}$', error_msg_i18n_key)