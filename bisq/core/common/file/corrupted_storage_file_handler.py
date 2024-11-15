from dataclasses import dataclass, field

from bisq.log_setup import get_logger

logger = get_logger(__name__)


@dataclass
class CorruptedStorageFileHandler:
    _files: list[str] = field(default_factory=list)

    def add_file(self, file_name: str):
        self._files.append(file_name)

    def get_files(self):
        if not self._files:
            return None

        if len(self._files) == 1 and self._files[0] == "ViewPathAsString":
            logger.debug(
                "We detected incompatible data base file for Navigation. "
                + "That is a minor issue happening with refactoring of UI classes "
                + "and we don't display a warning popup to the user."
            )
            return None

        return self._files
