
def Singleton(cls):
    """
    A class decorator that implements the Singleton pattern.
    Can be used with any class regardless of inheritance.
    """
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
        
    return get_instance