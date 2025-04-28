from datetime import timedelta
from typing import TYPE_CHECKING, cast
import json
from bisq.asset.crypto_note_utils import CryptoNoteException, get_raw_spend_key_and_view_key
from bisq.common.app.dev_env import DevEnv
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.core.trade.txproof.asset_tx_proof_parser import AssetTxProofParser
from bisq.core.trade.txproof.xmr.xmr_expected_response_dto import XmrExpectedResponseDto
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_detail import XmrTxProofRequestDetail
from bisq.core.trade.txproof.xmr.xmr_tx_proof_request_result import XmrTxProofRequestResult


if TYPE_CHECKING:
    from bisq.core.trade.txproof.xmr.xmr_tx_proof_model import XmrTxProofModel
    

class XmrTxProofParser(AssetTxProofParser["XmrTxProofRequestResult", "XmrTxProofModel"]):
    MAX_DATE_TOLERANCE = timedelta(hours=2)

    def __init__(self):
        super().__init__()
        self.logger = get_ctx_logger(__name__)
    
    def parse(self, json_txt: str, model: "XmrTxProofModel" = None) -> "XmrTxProofRequestResult":
        if model is None:
            raise ValueError("XmrTxProofParser requires a model")

        tx_hash = model.tx_hash
        
        try:
            json_data = cast(XmrExpectedResponseDto, json.loads(json_txt))
            if not json_data:
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Empty json"))
            
            # there should always be "data" and "status" at the top level
            if not isinstance(json_data.get("data", None), dict) or not isinstance(json_data.get("status", None), str):
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Missing data / status fields"))
                
            data = json_data["data"]
            status = json_data["status"]
            
            if status == "fail":
                # The API returns "fail" until the transaction has successfully reached the mempool or if request
                # contained invalid data.
                # We return TX_NOT_FOUND which will cause a retry later
                return XmrTxProofRequestResult.PENDING.with_detail(XmrTxProofRequestDetail.TX_NOT_FOUND)
            elif status != "success":
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Unhandled status value"))

            # validate that the address matches
            json_address = data.get("address", None)
            if not json_address:
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Missing address field"))
            
            expected_address_hex = get_raw_spend_key_and_view_key(model.recipient_address)
            if json_address.lower() != expected_address_hex.lower():
                self.logger.warning(f"Address from json result (convertToRawHex):\n{json_address}\nExpected (convertToRawHex):\n{expected_address_hex}\nRecipient address:\n{model.recipient_address}")
                return XmrTxProofRequestResult.FAILED.with_detail(XmrTxProofRequestDetail.ADDRESS_INVALID)

            # validate that the txHash matches
            json_tx_hash = data.get("tx_hash", None)
            if not json_tx_hash:
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Missing tx_hash field"))
            
            if json_tx_hash.lower() != tx_hash.lower():
                self.logger.warning(f"tx_hash mismatch: got {json_tx_hash}, expected {tx_hash}")
                return XmrTxProofRequestResult.FAILED.with_detail(XmrTxProofRequestDetail.TX_HASH_INVALID)

            # validate that the txKey matches
            # The API use viewkey param as txKey for our operation mode
            json_tx_key = data.get("viewkey", None)
            if not json_tx_key:
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Missing viewkey field"))
            if json_tx_key.lower() != model.tx_key.lower():
                self.logger.warning(f"tx_key mismatch: got {json_tx_key}, expected {model.tx_key}")
                return XmrTxProofRequestResult.FAILED.with_detail(XmrTxProofRequestDetail.TX_KEY_INVALID)

            # validate that the txDate matches within tolerance
            # (except that in dev mode we let this check pass anyway)
            json_timestamp = data.get("tx_timestamp", None)
            if json_timestamp is None:
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Missing tx_timestamp field"))
            json_timestamp = int(json_timestamp)
            trade_date_seconds = int(model.trade_date.timestamp())
            difference = trade_date_seconds - json_timestamp
            # Accept up to 2 hours difference. Some tolerance is needed if users clock is out of sync
            if difference > XmrTxProofParser.MAX_DATE_TOLERANCE.total_seconds() and not DevEnv.is_dev_mode():
                self.logger.warning(f"tx_timestamp mismatch: got {json_timestamp}, trade date {trade_date_seconds}, difference {difference}")
                return XmrTxProofRequestResult.FAILED.with_detail(XmrTxProofRequestDetail.TRADE_DATE_NOT_MATCHING)

            # calculate how many confirms are still needed
            json_confirmations = data.get("tx_confirmations", None)
            if json_confirmations is None:
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Missing tx_confirmations field"))
            json_confirmations = int(json_confirmations)
            self.logger.info(f"Confirmations: {json_confirmations}, xmr tx_hash: {tx_hash}")


            # iterate through the list of outputs, one of them has to match the amount we are trying to verify.
            # check that the "match" field is true as well as validating the amount value
            # (except that in dev mode we allow any amount as valid)
            json_outputs = data.get("outputs", None)
            if not isinstance(json_outputs, list) or not json_outputs:
                return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error("Missing or invalid outputs field"))

            any_match_found = False
            amount_matches = False
            
            for output in json_outputs:
                if output.get("match"):
                    any_match_found = True
                    amount = int(output.get("amount", -1))
                    amount_matches = amount == model.amount
                    if amount_matches:
                        break
                    self.logger.warning(f"output amount mismatch: got {amount}, expected {model.amount}")
            
            # None of the outputs had a match entry
            if not any_match_found:
                return XmrTxProofRequestResult.FAILED.with_detail(XmrTxProofRequestDetail.NO_MATCH_FOUND)
            
            # None of the outputs had a match entry
            if not amount_matches:
                return XmrTxProofRequestResult.FAILED.with_detail(XmrTxProofRequestDetail.AMOUNT_NOT_MATCHING)

            confirms_required = model.get_num_required_confirmations()
            if json_confirmations < confirms_required:
                return XmrTxProofRequestResult.PENDING.with_detail(XmrTxProofRequestDetail.PENDING_CONFIRMATIONS.with_num_confirmations(json_confirmations))
            
            return XmrTxProofRequestResult.SUCCESS.with_detail(XmrTxProofRequestDetail.SUCCESS.with_num_confirmations(json_confirmations))

        except json.JSONDecodeError as e:
            return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error(f"JSON parse error: {str(e)}"))
        except CryptoNoteException as e:
            return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.ADDRESS_INVALID.with_error(str(e)))
        except Exception as e:
            return XmrTxProofRequestResult.ERROR.with_detail(XmrTxProofRequestDetail.API_INVALID.with_error(str(e)))

