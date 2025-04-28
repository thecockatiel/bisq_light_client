from bisq.common.setup.log_setup import get_ctx_logger
from typing import List, Optional
import random
 
from bisq.common.config.config import Config
 

class PriceFeedNodeAddressProvider:
    DEFAULT_NODES = [
        "http://ro7nv73awqs3ga2qtqeqawrjpbxwarsazznszvr6whv7tes5ehffopid.onion/",  # @alexej996
        "http://runbtcpn7gmbj5rgqeyfyvepqokrijem6rbw7o5wgqbguimuoxrmcdyd.onion"    # @runbtc
    ]

    def __init__(self, config: "Config", providers: List[str], use_localhost_for_p2p: bool):
        self.logger = get_ctx_logger(__name__)
        self.config = config
        self.providers_from_program_args = providers
        self.use_localhost_for_p2p = use_localhost_for_p2p
        
        self.provider_list: list[str] = []
        self.base_url = ""
        self.banned_nodes: Optional[list[str]] = None
        self.index = 0

        random.shuffle(PriceFeedNodeAddressProvider.DEFAULT_NODES)
        
        self.apply_banned_nodes(self.config.banned_price_relay_nodes)

    def apply_banned_nodes(self, banned_nodes: Optional[List[str]]) -> None:
        self.banned_nodes = banned_nodes
        self._fill_provider_list()
        self.select_next_provider_base_url()

        if banned_nodes:
            self.logger.info(f"Excluded provider nodes from filter: nodes={banned_nodes}, selected provider baseUrl={self.base_url}, providerList={self.provider_list}")

    def select_next_provider_base_url(self) -> None:
        if self.provider_list:
            if self.index >= len(self.provider_list):
                self.index = 0

            self.base_url = self.provider_list[self.index]
            self.index += 1

            if len(self.provider_list) == 1 and self.config.base_currency_network.is_mainnet():
                self.logger.warning("We only have one provider")
        else:
            self.base_url = ""
            self.logger.warning(f"We do not have any providers. That can be if all providers are filtered or providers_from_program_args is set but empty. "
                  f"banned_nodes={self.banned_nodes}. providers_from_program_args={self.providers_from_program_args}")

    def _fill_provider_list(self) -> None:
        if not self.providers_from_program_args:
            if self.use_localhost_for_p2p:
                # NOTE: should be checked later
                # If we run in localhost mode we don't have the tor node running, so we need a clearnet host
                # Use localhost for using a locally running provider
                # providerAsString = Collections.singletonList("http://localhost:8080/");
                providers = ["https://price.bisq.wiz.biz/"]  # @wiz
            else:
                providers = PriceFeedNodeAddressProvider.DEFAULT_NODES
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
