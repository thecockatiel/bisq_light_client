import re
import logging
from typing import Optional, List, Set, Collection
from bisq.common.config.config import Config 
from bisq.core.network.p2p.node_address import NodeAddress
from bisq.core.network.p2p.seed.seed_node_repository import SeedNodeRepository
from resources import resource_readlines

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# If a new BaseCurrencyNetwork type gets added we need to add the resource file for it as well!
# Singleton?
class DefaultSeedNodeRepository(SeedNodeRepository):
    pattern = re.compile(r"^([a-z0-9]+\.onion:\d+)")
    ENDING = ".seednodes"

    def __init__(self, config: Config):
        self.config = config
        self.cache: Set[NodeAddress] = set()

    def reload(self):
        try:
            if self.config.seed_nodes:
                self.cache.clear()
                self.cache.update(NodeAddress.from_full_address(s) for s in self.config.seed_nodes)
                return

            self.cache.clear()
            result = self.get_seed_node_addresses_from_property_file("btc_mainnet") # Note: Hard coded
            self.cache.update(result)

            filter_provided_seed_nodes = {self.get_node_address(n) for n in self.config.filter_provided_seed_nodes if n}
            self.cache.update(filter_provided_seed_nodes)

            banned_seed_nodes = {self.get_node_address(n) for n in self.config.banned_seed_nodes if n}
            self.cache.difference_update(banned_seed_nodes)

            logger.info("Seed nodes: %s", self.cache)
        except Exception as e:
            logger.error("exception in DefaultSeedNodeRepository", exc_info=e)
            raise

    @staticmethod
    def get_seed_node_addresses_from_property_file(file_name: str) -> List[NodeAddress]:
        list = []
        seed_node_file = resource_readlines(f"{file_name}{DefaultSeedNodeRepository.ENDING}")
        if seed_node_file:
            for line in seed_node_file:
                matcher = DefaultSeedNodeRepository.pattern.match(line)
                if matcher:
                    list.append(NodeAddress.from_full_address(matcher.group(1)))

                if line.startswith("localhost") or line.startswith("bisq-seednode-"):
                    full_address = line.split(" (@")[0]
                    list.append(NodeAddress.from_full_address(full_address))
        return list

    def get_seed_node_addresses(self) -> Collection[NodeAddress]:
        if not self.cache:
            self.reload()
        return self.cache

    def is_seed_node(self, node_address: NodeAddress) -> bool:
        if not self.cache:
            self.reload()
        return node_address in self.cache

    def get_node_address(self, n: str) -> Optional[NodeAddress]:
        try:
            return NodeAddress.from_full_address(n)
        except Exception as e:
            logger.error("exception when filtering banned seednodes", exc_info=e)
            return None