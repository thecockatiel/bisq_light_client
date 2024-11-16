class ProtobufferException(IOError):
    def __init__(self, message, cause=None):
        super().__init__(message)
        self.__cause__ = cause