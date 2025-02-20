class DtoSignatureScript:
    def __init__(self, asm: str = None, hex: str = None):
        self.asm = asm
        self.hex = hex

    def get_json_dict(self) -> dict:
        result = {
            "asm": self.asm,
            "hex": self.hex,
        }
        # remove null values
        return {k: v for k, v in result.items() if v is not None}

    @staticmethod
    def from_json_dict(json_dict: dict) -> "DtoSignatureScript":
        return DtoSignatureScript(
            asm=json_dict.get("asm", None),
            hex=json_dict.get("hex", None),
        )

    def __eq__(self, value):
        if not isinstance(value, DtoSignatureScript):
            return False
        return self.asm == value.asm and self.hex == value.hex

    def __hash__(self):
        return hash((self.asm, self.hex))
