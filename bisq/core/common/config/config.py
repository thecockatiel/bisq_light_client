# TODO: THIS CLASS IS INCOMPLETE. made to work with DefaultSeedNodeRepository

from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    def __init__(self):
        self.seed_nodes = []
        self.filter_provided_seed_nodes = []
        self.banned_seed_nodes = []

config = None