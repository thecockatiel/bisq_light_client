class NetworkNotReadyException(RuntimeError):
    def __init__(self):
        super().__init__("You must have bootstrapped before adding data to the P2P network.")
