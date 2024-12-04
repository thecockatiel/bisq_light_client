from enum import Enum, IntEnum

# NOTE: Keep up to date with https://github.com/bisq-network/bisq/blob/master/core/src/main/java/bisq/core/trade/statistics/ReferralId.java

class ReferralId(IntEnum):
    """
    Those are random ids which can be assigned to a market maker or API provider who generates trade volume for Bisq.
    
    The assignment process is that a partner requests a referralId from the core developers and if accepted they get
    assigned an ID. With the ID we can quantify the generated trades from that partner from analysing the trade
    statistics. Compensation requests will be based on that data.
    """

    REF_ID_342 = 0
    REF_ID_768 = 1
    REF_ID_196 = 2
    REF_ID_908 = 3
    REF_ID_023 = 4
    REF_ID_605 = 5
    REF_ID_896 = 6
    REF_ID_183 = 7
