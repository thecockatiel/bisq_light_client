import os
from pathlib import Path

# taken from Electrum with modifications

def user_dir():
    path = None
    if "BISQLIGHTDIR" in os.environ:
        path = os.environ["BISQLIGHTDIR"]
    elif 'ANDROID_DATA' in os.environ:
        raise Exception ("Android not supported yet")
    elif os.name == 'posix':
        path = os.path.join(os.environ["HOME"], ".bisq_light")
    elif "APPDATA" in os.environ:
        path = os.path.join(os.environ["APPDATA"], "bisq_light")
    elif "LOCALAPPDATA" in os.environ:
        path = os.path.join(os.environ["LOCALAPPDATA"], "bisq_light")
    else:
        raise Exception("No home directory found in environment variables.")
    return Path(path)
