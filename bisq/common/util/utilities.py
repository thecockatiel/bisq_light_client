import platform

def get_sys_info():
    return f"System info: os.name={platform.system()}; os.version={platform.version()}; os.arch={platform.machine()}; platform={platform.platform()}"
