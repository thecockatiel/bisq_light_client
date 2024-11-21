
from bisq.common.config.config import Config
from bisq.common.setup.log_setup import get_logger

logger = get_logger(__name__)

class DevEnv:
    
    # NOTE: The following comments are for original java implementation, but they are not relevant for python implementation, Yet.
    # The UI got set the private dev key so the developer does not need to do anything and can test those features.
    # Features: Arbitration registration (alt+R at account), Alert/Update (alt+m), private message to a
    # peer (click user icon and alt+r), filter/block offers by various data like offer ID (cmd + f).
    # The user can set a program argument to ignore all of those privileged network_messages. They are intended for
    # emergency cases only (beside update message and arbitrator registration).
    DEV_PRIVILEGE_PUB_KEY = "027a381b5333a56e1cc3d90d3a7d07f26509adf7029ed06fc997c656621f8da1ee"
    DEV_PRIVILEGE_PRIV_KEY = "6ac43ea1df2a290c1c8391736aa42e4339c5cb4f110ff0257a13b63211977b7a"
    
    @staticmethod
    def get_dev_privilege_pub_keys():
        return [DevEnv.DEV_PRIVILEGE_PUB_KEY]
    
    @staticmethod
    def setup(config: Config):
        DevEnv.set_dev_mode(config.use_dev_mode)
    
    # If set to true we ignore several UI behavior like confirmation popups as well dummy accounts are created and
    # offers are filled with default values. Intended to make dev testing faster.
    _dev_mode = False
    
    @staticmethod
    def is_dev_mode():
        return DevEnv._dev_mode
    
    @staticmethod
    def set_dev_mode(dev_mode: bool):
        DevEnv._dev_mode = dev_mode
        
    @staticmethod
    def log_error_and_throw_if_dev_mode(message: str):
        logger.error(message)
        if DevEnv.is_dev_mode():
            raise RuntimeError(message)
        
    @staticmethod
    def is_dao_trading_activated():
        return True