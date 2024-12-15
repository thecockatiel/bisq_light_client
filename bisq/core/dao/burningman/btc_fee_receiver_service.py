from bisq.core.dao.state.dao_state_listener import DaoStateListener


# TODO
class BtcFeeReceiverService(DaoStateListener):

    def get_address(self) -> str:
        raise RuntimeError("BtcFeeReceiverService.get_address Not implemented yet")
