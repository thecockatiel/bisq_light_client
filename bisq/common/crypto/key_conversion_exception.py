class KeyConversionException(RuntimeError):
    def __init__(self, msg=None, cause=None):
        super().__init__(msg)
        self.cause = cause