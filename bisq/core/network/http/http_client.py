from abc import ABC, abstractmethod


class HttpClient(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_attributes = [
            "uid",
            "base_url",
            "has_pending_request",
            "ignore_socks5_proxy",
        ]
        for attr in required_attributes:
            if not hasattr(self, attr):
                raise RuntimeError(f"You need to have '{attr}' in {self.__name__}")

    @abstractmethod
    def get(
        self,
        url: str,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
    ) -> str:
        pass

    @abstractmethod
    def post(
        self,
        url: str,
        data: dict[str, str] = None,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
    ) -> str:
        pass

    @abstractmethod
    def shut_down(self) -> None:
        pass
