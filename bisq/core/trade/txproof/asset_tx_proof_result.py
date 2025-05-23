from enum import Enum
from utils.hackyway import create_fake_copy_of_instance

class AssetTxProofResult(Enum):
    UNDEFINED = True

    FEATURE_DISABLED = True
    TRADE_LIMIT_EXCEEDED = True
    INVALID_DATA = True  # Peer provided invalid data. Might be a scam attempt (e.g. txKey reused)
    PAYOUT_TX_ALREADY_PUBLISHED = True
    DISPUTE_OPENED = True

    REQUESTS_STARTED = False
    PENDING = False

    # All services completed with a success state
    COMPLETED = True

    # Any service had an error (network, API service)
    ERROR = True

    # Any service failed. Might be that the tx is invalid.
    FAILED = True
    
    def __init__(self, is_terminal: bool):
        # If isTerminal is set it means that we stop the service
        self.is_terminal = is_terminal
        self.details = ""
        self.num_success_results = 0
        self.num_required_success_results = 0
        self.num_confirmations = 0
        self.num_required_confirmations = 0

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __str__(self):
        return f"AssetTxProofResult{{\n     details='{self.details}'" + \
               f",\n     isTerminal={self.is_terminal}" + \
               f",\n     numSuccessResults={self.num_success_results}" + \
               f",\n     numRequiredSuccessResults={self.num_required_success_results}" + \
               f",\n     numConfirmations={self.num_confirmations}" + \
               f",\n     numRequiredConfirmations={self.num_required_confirmations}" + \
               f"\n}} {super().__str__()}"

    def with_num_success_results(self, num_success_results: int) -> 'AssetTxProofResult':
        return create_fake_copy_of_instance(self, {"num_success_results": num_success_results})

    def with_num_required_success_results(self, num_required_success_results: int) -> 'AssetTxProofResult':
        return create_fake_copy_of_instance(self, {"num_required_success_results": num_required_success_results})

    def with_num_confirmations(self, num_confirmations: int) -> 'AssetTxProofResult':
        return create_fake_copy_of_instance(self, {"num_confirmations": num_confirmations})

    def with_num_required_confirmations(self, num_required_confirmations: int) -> 'AssetTxProofResult':
        return create_fake_copy_of_instance(self, {"num_required_confirmations": num_required_confirmations})

    def with_details(self, details: str) -> 'AssetTxProofResult':
        return create_fake_copy_of_instance(self, {"details": details})

