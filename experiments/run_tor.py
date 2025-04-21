

from pathlib import Path
from bisq.common.config.config import Config
from utils.aio import as_future
from twisted.internet import reactor
from global_container import GlobalContainer, set_global_container
from twisted.internet.defer import Deferred

from bisq.core.network.p2p.network.new_tor import NewTor
from bisq.common.setup.log_setup import configure_logging
from utils.dir import user_data_dir

global_container = None
if __name__ == '__main__':
    global_container = GlobalContainer()
    config = Config("bisq_light_client", user_data_dir())
    global_container._config = config
    set_global_container(global_container)
    configure_logging(log_file=None, log_level=global_container.config.log_level)

async def main():
    base_dir = Path(__file__).parent.joinpath(".testdata")
    base_dir.mkdir(exist_ok=True, parents=True)
    tor_dir = base_dir.joinpath("tor")
    tor_dir.mkdir(mode=0o700, exist_ok=True, parents=True)
    tor = await NewTor(
        base_dir,
        tor_dir,
        global_container.config.torrc_file,
        "SocksPort=9050,ControlPort=9052",
        None,
        True,
    ).get_tor()
    await as_future(Deferred())
    
if __name__ == '__main__':
    future = as_future(main())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()