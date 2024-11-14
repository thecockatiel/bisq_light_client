class ResourceNotFoundException(Exception):
    def __init__(self, path: str):
        super().__init__(f"Resource not found: path = {path}")