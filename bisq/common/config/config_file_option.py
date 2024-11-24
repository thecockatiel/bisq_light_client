class ConfigFileOption:
    def __init__(self, name: str, arg: str | None):
        self.name = name
        self.arg = arg

    @staticmethod
    def is_option(line: str) -> bool:
        return bool(line) and not line.startswith("#")

    @staticmethod
    def parse(option: str) -> 'ConfigFileOption':
        if "=" not in option:
            return ConfigFileOption(option, None)

        tokens = ConfigFileOption.clean(option).split("=")
        name = tokens[0].strip()
        arg = tokens[1].strip() if len(tokens) > 1 else ""
        return ConfigFileOption(name, arg)

    def __str__(self) -> str:
        return f"{self.name}{'=' + self.arg if self.arg is not None else ''}"

    @staticmethod
    def clean(option: str) -> str:
        return option.strip().replace("\\:", ":")
