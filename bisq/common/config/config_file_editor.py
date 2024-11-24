from pathlib import Path
from bisq.common.config.config_file_option import ConfigFileOption
from bisq.common.config.config_file_reader import ConfigFileReader
from bisq.common.setup.log_setup import get_logger
from typing import Optional

logger = get_logger(__name__)

class ConfigFileEditor:
    
    def __init__(self, file: Path):
        self.file = file
        self.reader = ConfigFileReader(file)
            
    def set_option(self, name: str, arg: Optional[str] = None) -> None:
        self.try_create(self.file)
        lines = self.reader.get_lines()
        
        try:
            file_already_contains_target_option = False
            new_lines = []
            
            for line in lines:
                if ConfigFileOption.is_option(line):
                    existing_option = ConfigFileOption.parse(line)
                    if existing_option.name == name:
                        file_already_contains_target_option = True
                        if existing_option.arg != arg:
                            new_option = ConfigFileOption(name, arg)
                            new_lines.append(str(new_option))
                            logger.warning(f"Overwrote existing config file option '{existing_option}' as '{new_option}'")
                            continue
                new_lines.append(line)
                
            if not file_already_contains_target_option:
                new_lines.append(str(ConfigFileOption(name, arg)))
                
            with open(self.file, 'w') as f:
                f.write('\n'.join(new_lines))
                
        except IOError as ex:
            raise IOError(f"Could not write to config file: {ex}")

    def clear_option(self, name: str) -> None:
        if not self.file.exists():
            return

        lines = self.reader.get_lines()
        new_lines = []
        for line in lines:
            if ConfigFileOption.is_option(line):
                option = ConfigFileOption.parse(line)
                if option.name == name:
                    logger.debug(f"Cleared existing config file option '{option}'")
                    continue
            new_lines.append(line)
        try:
            with open(self.file, 'w') as f:
                f.write('\n'.join(new_lines))
        except IOError as ex:
            raise IOError(f"Could not write to config file: {ex}")

    def try_create(self, file: Path) -> None:
        try:
            if not file.exists():
                file.touch()
                logger.info(f"Created config file '{file}'")
        except IOError as ex:
            raise IOError(f"Could not create config file: {ex}")