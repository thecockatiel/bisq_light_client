from pathlib import Path
from typing import Optional, Union

__resource_dir = Path(__file__).parent
core_resource_dir = __resource_dir.joinpath("data", "core", "src", "main", "resources")
p2p_resource_dir = __resource_dir.joinpath("data", "p2p", "src", "main", "resources")


def core_resource_readlines(resource_name: Union[str, Path]) -> Optional[list[str]]:
    try:
        with open(core_resource_dir.joinpath(resource_name), "r") as f:
            return f.readlines()
    except FileNotFoundError:
        return None
