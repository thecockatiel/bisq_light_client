from bisq.common.protocol.network.network_payload import NetworkPayload
import pb_pb2 as protobuf

class ProofOfWork(NetworkPayload):
    def __init__(self, payload: bytes, counter: int, challenge: bytes,
                 difficulty: float, duration: int, solution: bytes, version: int):
        self.payload = payload
        self.counter = counter
        self.challenge = challenge
        self.difficulty = difficulty
        self.duration = duration
        self.solution = solution
        self.version = version

    def to_proto_message(self):
        return protobuf.ProofOfWork(
            payload=self.payload,
            counter=self.counter,
            challenge=self.challenge,
            difficulty=self.difficulty,
            duration=self.duration,
            solution=self.solution,
            version=self.version
        )

    @staticmethod
    def from_proto(proto: protobuf.ProofOfWork):
        return ProofOfWork(
            payload=proto.payload,
            counter=proto.counter,
            challenge=proto.challenge,
            difficulty=proto.difficulty,
            duration=proto.duration,
            solution=proto.solution,
            version=proto.version
        )

    def __str__(self):
        return (f"ProofOfWork{{\n"
                f"     counter={self.counter},\n"
                f"     difficulty={self.difficulty},\n"
                f"     duration={self.duration},\n"
                f"     version={self.version}\n"
                f"}}")

