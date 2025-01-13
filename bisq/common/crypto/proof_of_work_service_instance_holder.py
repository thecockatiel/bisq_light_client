

from typing import TYPE_CHECKING, Optional

from bisq.common.crypto.hash_cash_service import HashCashService


if TYPE_CHECKING:
    from bisq.common.crypto.proof_of_work_service import ProofOfWorkService


POW_INSTANCE_HOLDER: list["ProofOfWorkService"] = [
    HashCashService(),
    
]

def pow_service_for_version(version: int) -> Optional["ProofOfWorkService"]:
    return POW_INSTANCE_HOLDER[version] if 0 <= version < len(POW_INSTANCE_HOLDER) else None
