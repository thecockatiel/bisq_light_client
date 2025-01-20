
class ConsensusCritical:
    """
    Marker interface for classes which are critical in the vote consensus process. Any changes in that class might cause
    consensus failures with older versions.
    """
    pass
