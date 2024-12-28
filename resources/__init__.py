import os
from pathlib import Path

__resource_dir = os.path.split(os.path.realpath(__file__))[0]

def __resource_path(*parts):
    return os.path.join(__resource_dir, *parts)

def resource_readlines(resource_name: str) -> str:
    try:
        with open(__resource_path(resource_name), 'r') as f:
            return f.readlines()
    except FileNotFoundError:
            return None

def get_resources_path():
    return Path(__resource_dir)
