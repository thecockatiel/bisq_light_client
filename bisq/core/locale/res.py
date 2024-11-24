# TODO: Implemented partially since it was used widely, to complete later as needed.

class Res:
    
    @staticmethod
    def get(key: str, *args):
        return key
    
    @staticmethod
    def get_with_col(key: str, *args):
        return Res.get(key) + ":"