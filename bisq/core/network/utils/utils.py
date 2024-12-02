import socket
from contextlib import closing
import random
import re

_onion_v3_re = re.compile(r'^[a-z2-7]{56}\.onion$')

class Utils:
    @staticmethod
    def find_free_system_port():
        try:
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.bind(('', 0))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return s.getsockname()[1]
        except:
            return random.randint(50000, 60000)

    @staticmethod
    def is_v3_address(address: str):
        return bool(re.match(_onion_v3_re, address))
