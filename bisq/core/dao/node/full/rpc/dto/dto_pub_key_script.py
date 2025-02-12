from typing import TYPE_CHECKING

from bisq.common.config.config import Config
from bitcoinj.script.script import Script


if TYPE_CHECKING:
    from bisq.core.dao.state.model.blockchain.script_type import ScriptType


class DtoPubKeyScript:

    def __init__(
        self,
        asm: str,
        hex: str,
        req_sigs: int,
        type: "ScriptType",
        addresses: list[str],
    ):
        self.asm = asm
        self.hex = hex
        self.req_sigs = req_sigs
        self.type = type
        self.addresses = addresses
        if not self.addresses:
            # Addresses are not provided by bitcoin RPC from v22 onwards.
            # However they are exported into the DAO classes (and therefore a component of the DAO state hash)
            # so we must generate address from the hex script using BitcoinJ.
            # (n.b. the DAO only ever uses/expects one address)
            try:
                address = str(
                    Script(bytes.fromhex(self.hex)).get_to_address(
                        Config.BASE_CURRENCY_NETWORK_VALUE.parameters
                    )
                )
                self.addresses = [address]
                self.req_sigs = 1
            except:
                # certain scripts e.g. OP_RETURN do not resolve to an address
                # in that case do not provide an address to the RawTxOutput
                pass

    def get_json_dict(self):
        result = {
            "asm": self.asm,
            "hex": self.hex,
            "reqSigs": self.req_sigs,
            "type": self.type.json_name,
            "addresses": self.addresses,
        }

        # remove null values
        result = {k: v for k, v in result.items() if v is not None}

        return result

    def from_json_dict(json_dict: dict):
        return DtoPubKeyScript(
            json_dict.get("asm", None),
            json_dict.get("hex", None),
            json_dict.get("reqSigs", None),
            ScriptType.from_json_name([json_dict.get("type", None)]),
            json_dict.get("addresses", None),
        )
