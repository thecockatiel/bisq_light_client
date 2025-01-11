from bisq.core.dao.dao_setup_service import DaoSetupService
from bisq.core.dao.state.dao_state_listener import DaoStateListener
from utils.data import ObservableList
from bisq.core.dao.governance.voteresult.vote_result_exception import (
    VoteResultException,
)


# TODO
class VoteResultService(DaoStateListener, DaoSetupService):

    def __init__(self):
        self.vote_result_exceptions = ObservableList["VoteResultException"]()

    def add_listeners(self):
        pass

    def start(self):
        pass
