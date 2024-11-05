from dataclasses import dataclass, field


@dataclass(frozen=True)
class Socks5Proxy:
    host: str
    port: int
    username: str = field(default=None)
    password: str = field(default=None)

    @property
    def url(self) -> str:
        if self.username is not None and self.password is not None:
            return f"socks5://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"socks5://{self.host}:{self.port}"
