import os
from pathlib import Path
from typing import List
from bisq.common.config.config_exception import ConfigException
from bisq.common.config.config_file_option import ConfigFileOption

class ConfigFileReader:
    def __init__(self, file_path: Path) -> None:
        self.file = file_path

    def get_lines(self) -> List[str]:
        if not self.file.exists():
            raise ConfigException(f"Config file {self.file} does not exist")

        if not self.file.is_file() or not os.access(self.file, os.R_OK):
            raise ConfigException(f"Config file {self.file} is not readable")

        try:
            with open(self.file, 'r') as f:
                return [self._clean_line(line) for line in f]
        except IOError as ex:
            raise IOError(f"Error reading config file: {ex}")

    def get_option_lines(self) -> List[str]:
        return [line for line in self.get_lines() if ConfigFileOption.is_option(line)]

    @staticmethod
    def _clean_line(line: str) -> str:
        return ConfigFileOption.clean(line) if ConfigFileOption.is_option(line) else line
