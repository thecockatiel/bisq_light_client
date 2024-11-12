# TODO: THIS CLASS IS INCOMPLETE. made to work with DefaultSeedNodeRepository

from dataclasses import dataclass, field

from utils.dir import user_data_dir

@dataclass(frozen=True)
class Config:
    seed_nodes: list = field(default_factory=list)
    filter_provided_seed_nodes: list = field(default_factory=list)
    banned_seed_nodes: list = field(default_factory=list)
    app_data_dir: str = field(default_factory=str)
    msg_throttle_per_sec: int = field(default=200)
    msg_throttle_per_10_sec: int = field(default=1000)
    send_msg_throttle_trigger: int = field(default=20)
    send_msg_throttle_sleep: int = field(default=50)
    

CONFIG = Config(
    app_data_dir=str(user_data_dir())
)