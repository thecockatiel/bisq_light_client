

from pathlib import Path
from bisq.common.config.config import Config
from utils.aio import as_future
from twisted.internet import reactor
from twisted.internet.defer import Deferred

from bisq.core.network.p2p.network.new_tor import NewTor
from bisq.common.setup.log_setup import get_user_logger, refresh_base_logger_handlers, setup_log_for_test, switch_std_handler_to
from utils.dir import user_data_dir
 
config = Config("bisq_light_client", user_data_dir())
data_dir = Path(__file__).parent.joinpath(".testdata")
data_dir.mkdir(exist_ok=True, parents=True)
logger = setup_log_for_test("run_tor", data_dir)

async def main():
    tor_dir = data_dir.joinpath("tor")
    tor_dir.mkdir(mode=0o700, exist_ok=True, parents=True)
    tor = await NewTor(
        data_dir,
        tor_dir,
        config.torrc_file,
        "SocksPort=9050,ControlPort=9052",
        None,
        True,
    ).get_tor()
    await as_future(Deferred())
    
if __name__ == '__main__':
    future = as_future(main())
    future.add_done_callback(lambda f: reactor.stop())
    reactor.run()