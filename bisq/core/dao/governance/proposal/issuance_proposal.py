from abc import ABC, abstractmethod
from bitcoinj.base.coin import Coin
from bitcoinj.core.address import Address
from bisq.common.config.config import Config


class IssuanceProposal(ABC):
    """Interface for proposals which can lead to new BSQ issuance. requires the implementor to have a `config` attribute."""

    config: "Config"

    @abstractmethod
    def get_requested_bsq(self) -> Coin:
        pass

    @abstractmethod
    def get_bsq_address(self) -> str:
        pass

    @abstractmethod
    def get_tx_id(self) -> str:
        pass

    def get_address(self) -> Address:
        # Remove leading 'B'
        underlying_btc_address = self.get_bsq_address()[1:]
        return Address.from_string(
            underlying_btc_address, Config.BASE_CURRENCY_NETWORK_VALUE.parameters
        )
