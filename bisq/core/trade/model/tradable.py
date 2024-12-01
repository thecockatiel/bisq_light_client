from typing import TYPE_CHECKING, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from bisq.common.protocol.persistable.persistable_payload import PersistablePayload

if TYPE_CHECKING:
    from bisq.core.monetary.volume import Volume
    from bisq.core.network.p2p.node_address import NodeAddress
    from bitcoinj.base.coin import Coin
    from bisq.core.offer.offer import Offer
    from bisq.core.trade.model.trade_model import TradeModel
    from bisq.core.monetary.price import Price


class Tradable(PersistablePayload, ABC):
    @abstractmethod
    def get_offer(self) -> 'Offer':
        pass

    @abstractmethod
    def get_date(self) -> datetime:
        pass

    @abstractmethod
    def get_id(self) -> str:
        pass

    @abstractmethod
    def get_short_id(self) -> str:
        pass

    def as_trade_model(self) -> Optional['TradeModel']:
        return self if isinstance(self, TradeModel) else None

    def get_optional_volume(self) -> Optional['Volume']:
        if trade_model := self.as_trade_model():
            return trade_model.get_volume()
        return self.get_offer().volume

    def get_optional_price(self) -> Optional['Price']:
        if trade_model := self.as_trade_model():
            return trade_model.get_price()
        return self.get_offer().get_price()

    def get_optional_amount(self) -> Optional['Coin']:
        if trade_model := self.as_trade_model():
            return trade_model.get_amount()
        return None

    def get_optional_amount_as_long(self) -> Optional[int]:
        if trade_model := self.as_trade_model():
            return trade_model.get_amount_as_long()
        return None

    def get_optional_tx_fee(self) -> Optional['Coin']:
        if trade_model := self.as_trade_model():
            return trade_model.get_tx_fee()
        return None

    def get_optional_taker_fee(self) -> Optional['Coin']:
        if trade_model := self.as_trade_model():
            return trade_model.get_taker_fee()
        return None

    def get_optional_maker_fee(self) -> Optional['Coin']:
        if trade_model := self.as_trade_model():
            return trade_model.get_maker_fee()
        return self.get_offer().maker_fee

    def get_optional_trading_peer_node_address(self) -> Optional['NodeAddress']:
        if trade_model := self.as_trade_model():
            return trade_model.trading_peer_node_address
        return None