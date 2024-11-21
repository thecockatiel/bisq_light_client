from dataclasses import dataclass
from typing import List, Optional
import random
import logging

from bisq.common.config.config import Config

log = logging.getLogger(__name__)
    
class ProvidersRepository:
    DEFAULT_NODES: List[str] = [
        "http://ro7nv73awqs3ga2qtqeqawrjpbxwarsazznszvr6whv7tes5ehffopid.onion",  # @alexej996
        "http://runbtcpn7gmbj5rgqeyfyvepqokrijem6rbw7o5wgqbguimuoxrmcdyd.onion"    # @runbtc
    ]

    def __init__(self, config: Config, providers_from_program_args: List[str], use_localhost_for_p2p: bool) -> None:
        self.config: Config = config
        self.providers_from_program_args: List[str] = providers_from_program_args
        self.use_localhost_for_p2p: bool = use_localhost_for_p2p
        
        self.provider_list: List[str] = []
        self.base_url: str = ""
        self.banned_nodes: Optional[List[str]] = None
        self.index: int = 0

        random.shuffle(self.DEFAULT_NODES)
        self.apply_banned_nodes(config.banned_price_relay_nodes)

    def apply_banned_nodes(self, banned_nodes: Optional[List[str]]) -> None:
        self.banned_nodes = banned_nodes
        self._fill_provider_list()
        self.select_next_provider_base_url()

        if banned_nodes:
            log.info(f"Excluded provider nodes from filter: nodes={banned_nodes}, "
                    f"selected provider baseUrl={self.base_url}, providerList={self.provider_list}")

    def select_next_provider_base_url(self) -> None:
        if self.provider_list:
            if self.index >= len(self.provider_list):
                self.index = 0

            self.base_url = self.provider_list[self.index]
            self.index += 1

            if len(self.provider_list) == 1 and self.config.base_currency_network.is_mainnet():
                log.warning("We only have one provider")
        else:
            self.base_url = ""
            log.warning("We do not have any providers. That can be if all providers are filtered "
                       f"or providersFromProgramArgs is set but empty. bannedNodes={self.banned_nodes}. "
                       f"providersFromProgramArgs={self.providers_from_program_args}")

    def _fill_provider_list(self) -> None:
        providers: List[str]
        if not self.providers_from_program_args:
            if self.use_localhost_for_p2p:
                # If we run in localhost mode we don't have the tor node running, so we need a clearnet host
                # Use localhost for using a locally running provider
                # providerAsString = Collections.singletonList("http://localhost:8080/");
                providers = ["https://price.bisq.wiz.biz/"]  # @wiz
            else:
                providers = self.DEFAULT_NODES
        else:
            providers = self.providers_from_program_args

        checked_list = []
        for e in providers:
            cleaned_e = e.replace("http://", "").replace("/", "").replace(".onion", "")
            if not self.banned_nodes or not any(
                cleaned_e == banned
                for banned in self.banned_nodes
            ):
                if e.endswith("/"):
                    e = e[:-1]
                if not e.startswith("http"):
                    e = f"http://{e}"
                checked_list.append(e)
                
        self.provider_list = checked_list
