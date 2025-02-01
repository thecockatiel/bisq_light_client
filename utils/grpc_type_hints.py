import grpc

class HandlerCallDetails(grpc.HandlerCallDetails):
    method: str
    invocation_metadata: tuple[str, str]

