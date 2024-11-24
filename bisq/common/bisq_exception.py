class BisqException(RuntimeError):
    def __init__(self, cause: Exception, message: str):
        super().__init__(message)
        self.__cause__ = cause
