from dataclasses import dataclass, field


@dataclass(frozen=True)
class Socks5Proxy:
    proxy_host: str
    proxy_port: int
    username: str = field(default=None)
    password: str = field(default=None)

    @property
    def url(self) -> str:
        if self.username is not None and self.password is not None:
            return f"socks5://{self.username}:{self.password}@{self.proxy_host}:{self.proxy_port}"
        return f"socks5://{self.proxy_host}:{self.proxy_port}"
