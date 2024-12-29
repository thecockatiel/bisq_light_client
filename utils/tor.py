import asyncio
import socket
from typing import Optional, Tuple

def is_tor_socks_port(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=10) as s:
            # mimic "tor-resolve 0.0.0.0".
            # see https://github.com/spesmilo/electrum/issues/7317#issuecomment-1369281075
            # > this is a socks5 handshake, followed by a socks RESOLVE request as defined in
            # > [tor's socks extension spec](https://github.com/torproject/torspec/blob/7116c9cdaba248aae07a3f1d0e15d9dd102f62c5/socks-extensions.txt#L63),
            # > resolving 0.0.0.0, which being an IP, tor resolves itself without needing to ask a relay.
            s.send(b'\x05\x01\x00\x05\xf0\x00\x03\x070.0.0.0\x00\x00')
            if s.recv(1024) == b'\x05\x00\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00':
                return True
    except socket.error:
        pass
    return False

async def is_tor_socks_port_async(host: str, port: int) -> bool:
    writer = None
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(b'\x05\x01\x00\x05\xf0\x00\x03\x070.0.0.0\x00\x00')
        await writer.drain()

        response = await reader.read(1024)
        
        return response == b'\x05\x00\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        
    except (ConnectionError, asyncio.TimeoutError):
        return False
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()
        
    
def detect_tor_socks_proxy() -> Optional[Tuple[str, int]]:
    # Probable ports for Tor to listen at
    candidates = [
        ("127.0.0.1", 9050),
        ("127.0.0.1", 9150),
    ]
    for net_addr in candidates:
        if is_tor_socks_port(*net_addr):
            return net_addr
    return None