from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from bisq.core.dao.governance.myvote.my_vote import MyVote
    from bitcoinj.core.transaction import Transaction


class VoteRevealException(Exception):

    def __init__(
        self,
        *args,
        blind_vote_tx_id: Optional[str] = None,
        my_vote: Optional["MyVote"] = None,
        vote_reveal_tx: Optional["Transaction"] = None,
    ):
        super().__init__(*args)
        self.blind_vote_tx_id = blind_vote_tx_id
        self.my_vote = my_vote
        self.vote_reveal_tx = vote_reveal_tx

    def __str__(self):
        return (
            f"VoteRevealException{{\n"
            f"    voteRevealTx={self.vote_reveal_tx},\n"
            f"    blindVoteTxId='{self.blind_vote_tx_id}',\n"
            f"    myVote={self.my_vote}\n"
            f"}} {super().__str__()}"
        )
