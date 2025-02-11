from enum import IntEnum

from bisq.core.locale.res import Res


class ProposalType(IntEnum):
    UNDEFINED = 0
    COMPENSATION_REQUEST = 1
    REIMBURSEMENT_REQUEST = 2
    CHANGE_PARAM = 3
    BONDED_ROLE = 4
    CONFISCATE_BOND = 5
    GENERIC = 6
    REMOVE_ASSET = 7

    @property
    def display_name(self):
        return Res.get("dao.proposal.type." + self.name)

    @property
    def short_display_name(self):
        return Res.get("dao.proposal.type.short." + self.name)
