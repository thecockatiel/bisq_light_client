from pathlib import Path
from bisq.common.file.json_file_manager import JsonFileManager
from bisq.common.util.utilities import bytes_as_hex_string
from bisq.core.util.json_util import JsonUtil
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from bisq.core.trade.model.tradable_list import TradableList
    from bisq.core.trade.model.bisq_v1.trade import Trade
    from bisq.core.trade.model.tradable import Tradable

@dataclass
class DelayedPayoutHash:
    trade_id: str
    delayed_payout_tx: str

_T = TypeVar('T', bound='Tradable')

class DumpDelayedPayoutTx:
    def __init__(self, storage_dir: Path, dump_delayed_payout_txs: bool):
        self.dump_delayed_payout_txs = dump_delayed_payout_txs
        self.json_file_manager = JsonFileManager(storage_dir)

    
    def maybe_dump_delayed_payout_txs(self, tradable_list: 'TradableList[_T]', file_name: str) -> None:
        if not self.dump_delayed_payout_txs:
            return

        delayed_payout_hashes = [
            DelayedPayoutHash(
                trade_id=trade.get_id(),
                delayed_payout_tx=bytes_as_hex_string(trade.delayed_payout_tx_bytes)
            )
            for trade in tradable_list
            if isinstance(trade, Trade)
        ]
        
        self.json_file_manager.write_to_disc_threaded(JsonUtil.object_to_json(delayed_payout_hashes), file_name)
