import os
from pathlib import Path
import re
from typing import Union

# taken from Electrum with modifications

def user_data_dir():
    path = None
    if 'ANDROID_DATA' in os.environ:
        raise Exception ("Android not supported yet")
    elif os.name == 'posix':
        path = os.environ["HOME"]
    elif "APPDATA" in os.environ:
        path = os.environ["APPDATA"]
    elif "LOCALAPPDATA" in os.environ:
        path = os.environ["LOCALAPPDATA"]
    else:
        raise Exception("No home directory found in environment variables.")
    return Path(path)

def check_dir(dir_path: Union[str, Path]):
    """
    Ensures that `dir_path` is a non-null, existing and read-writeable directory.
    
    Parameters:
    dir_path (str): The path to the directory to check.
    
    Returns:
    Path: The given directory path, now validated.
    
    Raises:
    ValueError: If the directory is not valid.
    """
    if dir_path is None:
        raise ValueError("Directory must not be None")
    
    if isinstance(dir_path, str):
        dir_path = Path(dir_path)
    
    if not os.path.exists(dir_path):
        raise ValueError(f"Directory '{dir_path}' does not exist")
    
    if not os.path.isdir(dir_path):
        raise ValueError(f"Directory '{dir_path}' is not a directory")
    
    if not os.access(dir_path, os.R_OK):
        raise ValueError(f"Directory '{dir_path}' is not readable")
    
    if not os.access(dir_path, os.W_OK):
        raise ValueError(f"Directory '{dir_path}' is not writable")
    
    return dir_path
