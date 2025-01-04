from typing import cast
from bisq.common.app.dev_env import DevEnv
from bisq.common.setup.log_setup import get_logger
from bisq.core.trade.txproof.asset_tx_proof_parser import AssetTxProofParser
from bisq.core.trade.txproof.xmr.xmr_expected_response_dto import XmrExpectedResponseDto
from bisq.core.trade.txproof.xmr.xmr_tx_proof_model import XmrTxProofModel
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_detail import (
    XmrTxProofRequestDetail,
)
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_result import (
    XmrTxProofRequestResult,
)
import json

logger = get_logger(__name__)


class XmrRawTxParser(AssetTxProofParser[XmrTxProofRequestResult, XmrTxProofModel]):

    def parse(self, json_txt: str, model=None):
        try:
            json_data = cast(XmrExpectedResponseDto, json.loads(json_txt))
            if not json_data:
                return XmrTxProofRequestResult.ERROR.with_detail(
                    XmrTxProofRequestDetail.API_INVALID.with_error("Empty json")
                )

            if (
                not isinstance(json_data.get("data", None), dict)
                or not isinstance(json_data.get("status", None), str)
            ):
                return XmrTxProofRequestResult.ERROR.with_detail(
                    XmrTxProofRequestDetail.API_INVALID.with_error(
                        "Missing data / status fields"
                    )
                )

            data = json_data["data"]
            status = json_data["status"]

            if status == "fail":
                # The API returns "fail" until the transaction has successfully reached the mempool or if request
                # contained invalid data.
                # We return TX_NOT_FOUND which will cause a retry later
                return XmrTxProofRequestResult.PENDING.with_detail(
                    XmrTxProofRequestDetail.TX_NOT_FOUND
                )
            elif status != "success":
                return XmrTxProofRequestResult.ERROR.with_detail(
                    XmrTxProofRequestDetail.API_INVALID.with_error(
                        "Unhandled status value"
                    )
                )
            
            unlock_time = json_data.get("unlock_time", None)
            if unlock_time is None:
                return XmrTxProofRequestResult.ERROR.with_detail(
                    XmrTxProofRequestDetail.API_INVALID.with_error(
                        "Missing unlock_time field"
                    )
                )

            unlock_time = int(unlock_time)
            if unlock_time != 0 and not DevEnv.is_dev_mode():
                logger.warning(f"Invalid unlock_time {unlock_time}")
                return XmrTxProofRequestResult.FAILED.with_detail(
                    XmrTxProofRequestDetail.INVALID_UNLOCK_TIME.with_error(
                        "Invalid unlock_time"
                    )
                )

            return XmrTxProofRequestResult.SUCCESS.with_detail(
                XmrTxProofRequestDetail.SUCCESS
            )

        except Exception as e:
            return XmrTxProofRequestResult.ERROR.with_detail(
                XmrTxProofRequestDetail.API_INVALID.with_error(str(e))
            )
