import asyncio
from typing import Protocol, runtime_checkable


@runtime_checkable
class AsyncHttpClient(Protocol):
    uid: str
    base_url: str
    has_pending_request: bool
    ignore_socks5_proxy: bool

    async def get(
        self,
        url: str,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        timeout: asyncio.TimeoutError = None,
    ) -> str: ...

    async def post(
        self,
        url: str,
        data: dict[str, str] = None,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        timeout: asyncio.TimeoutError = None,
    ) -> str: ...

    def shut_down(self) -> None: ...
