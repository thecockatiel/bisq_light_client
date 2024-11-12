# TODO: THIS CLASS IS INCOMPLETE. made to work with DefaultSeedNodeRepository

from dataclasses import dataclass, field

from utils.dir import user_data_dir

@dataclass(frozen=True)
class Config:
    seed_nodes: list = field(default_factory=list)
    filter_provided_seed_nodes: list = field(default_factory=list)
    banned_seed_nodes: list = field(default_factory=list)
    app_data_dir: str = field(default_factory=str)

CONFIG = Config(
    app_data_dir=user_data_dir()
)