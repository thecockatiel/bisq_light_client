from typing import TYPE_CHECKING, Union
from bisq.common.setup.log_setup import get_logger
from bisq.common.util.math_utils import MathUtils
from bisq.core.dao.governance.proposal.proposal_validation_exception import ProposalValidationException
from bisq.core.exceptions.illegal_argument_exception import IllegalArgumentException
from bisq.core.locale.res import Res
from bisq.core.monetary.price import Price
from bisq.core.util.coin.coin_formatter import CoinFormatter
from bisq.core.util.coin.immutable_coin_formatter import ImmutableCoinFormatter
from bisq.core.util.decimal_format import DecimalFormat
from bisq.core.util.formatting_util import FormattingUtils
from bisq.core.util.parsing_utils import ParsingUtils
from bisq.core.util.validation.btc_address_validator import BtcAddressValidator
from bitcoinj.base.coin import Coin
from bitcoinj.base.utils.monetary_format import MonetaryFormat 
from bisq.core.dao.governance.param.param import Param
from bisq.core.dao.governance.param.param_type import ParamType
from bitcoinj.core.address import Address
from bitcoinj.core.address_format_exception import AddressFormatException

if TYPE_CHECKING:
    from bisq.common.config.config import Config

logger = get_logger(__name__)

# NOTE: locale change not supported in python impl

class BsqFormatter(CoinFormatter):
    use_bsq_address_format: bool = True # always true in java impl
    prefix = "B"
    
    def __init__(self, config: "Config"):
        super().__init__()
        self.config = config
        self.btc_coin_format = config.base_currency_network.parameters.get_monetary_format()
        self.monetary_format = MonetaryFormat().with_shift(6).code(6, "BSQ").with_min_decimals(2)
        self.immutable_coin_formatter = ImmutableCoinFormatter(self.monetary_format)
        self.amount_format: DecimalFormat = None
        self.market_cap_format: DecimalFormat = None
        self.switch_locale()

    def switch_locale(self):
        self.amount_format = DecimalFormat()
        self.amount_format.set_minimum_fraction_digits(2)
        self.amount_format.set_maximum_fraction_digits(2)
        self.market_cap_format = DecimalFormat()
        self.market_cap_format.set_maximum_fraction_digits(0)

    def get_address_from_bsq_address(self, encoded: str) -> Address:
        maybe_updated_encoded = encoded
        if self.use_bsq_address_format:
            maybe_updated_encoded = encoded[len(BsqFormatter.prefix):]

        try:
            return Address.from_string(maybe_updated_encoded, self.config.base_currency_network.parameters)
        except AddressFormatException as e:
            raise RuntimeError(e)

    def format_amount_with_group_separator_and_code(self, amount: "Coin"):
        return f"{self.amount_format.format(MathUtils.scale_down_by_power_of_10(amount.value, 2))} BSQ"

    def format_market_cap(self, usd_bsq_price: "Price", issued_amount: "Coin"):
        if usd_bsq_price is not None and issued_amount is not None:
            market_cap = usd_bsq_price.value * MathUtils.scale_down_by_power_of_10(issued_amount.value, 6)
            return f"{self.market_cap_format.format(int(market_cap))} USD"
        return ""

    def format_bsq_satoshis(self, satoshi: int) -> str:
        return FormattingUtils.format_coin(satoshi, self.monetary_format)

    def format_bsq_satoshis_with_code(self, satoshi: int) -> str:
        return FormattingUtils.format_coin_with_code(satoshi, self.monetary_format)

    def format_btc_satoshis(self, satoshi: int) -> str:
        return FormattingUtils.format_coin(satoshi, self.btc_coin_format)

    def format_btc_with_code(self, satoshi_or_coin: Union[int, "Coin"]) -> str:
        return FormattingUtils.format_coin_with_code(satoshi_or_coin, self.btc_coin_format)

    def format_btc(self, coin: Coin) -> str:
        return FormattingUtils.format_coin(coin.value, self.btc_coin_format)

    def parse_to_btc(self, input_str: str) -> Coin:
        return ParsingUtils.parse_to_coin(input_str, self.btc_coin_format)
    
    def format_param_value(self, param: "Param", value: str) -> str:
        if param.param_type == ParamType.UNDEFINED:
            # In case we add a new param old clients will not know that enum and fall back to UNDEFINED.
            return Res.get("shared.na")
        elif param.param_type == ParamType.BSQ:
            return self.format_coin_with_code(ParsingUtils.parse_to_coin(value, self))
        elif param.param_type == ParamType.BTC:
            return self.format_btc_with_code(self.parse_to_btc(value))
        elif param.param_type == ParamType.PERCENT:
            return FormattingUtils.format_to_percent_with_symbol(ParsingUtils.parse_percent_string_to_double(value))
        elif param.param_type == ParamType.BLOCK:
            return Res.get("dao.param.blocks", int(value))
        elif param.param_type == ParamType.ADDRESS:
            return value
        else:
            logger.warning(f"Param type {param.param_type} not handled at format_param_value")
            return Res.get("shared.na")

    def parse_param_value_to_coin(self, param: "Param", input_value: str) -> "Coin":
        if param.param_type == ParamType.BSQ:
            return ParsingUtils.parse_to_coin(input_value, self)
        elif param.param_type == ParamType.BTC:
            return self.parse_to_btc(input_value)
        else:
            raise IllegalArgumentException(f"Unsupported paramType. param: {param}")

    def parse_param_value_to_blocks(self, param: "Param", input_value: str) -> int:
        if param.param_type == ParamType.BLOCK:
            return int(input_value)
        else:
            raise IllegalArgumentException(f"Unsupported paramType. param: {param}")

    def parse_param_value_to_string(self, param: "Param", input_value: str) -> str:
        if param.param_type == ParamType.UNDEFINED:
            return Res.get("shared.na")
        elif param.param_type == ParamType.BSQ:
            return self.format_coin(self.parse_param_value_to_coin(param, input_value))
        elif param.param_type == ParamType.BTC:
            return self.format_btc(self.parse_param_value_to_coin(param, input_value))
        elif param.param_type == ParamType.PERCENT:
            return FormattingUtils.format_to_percent(ParsingUtils.parse_percent_string_to_double(input_value))
        elif param.param_type == ParamType.BLOCK:
            return str(self.parse_param_value_to_blocks(param, input_value))
        elif param.param_type == ParamType.ADDRESS:
            validation_result = BtcAddressValidator().validate(input_value)
            if validation_result.is_valid:
                return input_value
            else:
                raise ProposalValidationException(validation_result.error_message)
        else:
            logger.warning(f"Param type {param.param_type} not handled at parse_param_value_to_string")
            return Res.get("shared.na")
            
    def format_coin(self, coin_or_value, *, append_code=False, decimal_places=-1, decimal_aligned=False, max_number_of_digits=0):
        if append_code:
            return self.immutable_coin_formatter.format_coin_with_code(coin_or_value)
        else:
            return self.immutable_coin_formatter.format_coin(coin_or_value, decimal_places=decimal_places, decimal_aligned=decimal_aligned, max_number_of_digits=max_number_of_digits)

    def format_coin_with_code(self, coin_or_value):
        return self.format_coin(coin_or_value, append_code=True)

    def get_monetary_format(self):
        return self.monetary_format