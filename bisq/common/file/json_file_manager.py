from utils.aio import run_in_thread
import asyncio
from pathlib import Path
from typing import Optional
from bisq.common.file.file_util import rename_file
from bisq.common.setup.log_setup import get_logger
import tempfile

logger = get_logger(__name__)

class JsonFileManager:
    _INSTANCES: list["JsonFileManager"] = []

    @classmethod
    def shut_down_all_instances(cls):
        for instance in cls._INSTANCES:
            instance.shut_down()

    def __init__(self, directory: Path):
        self.dir = Path(directory)
        self._last_write_future: Optional["asyncio.Future"] = None
        if not self.dir.exists():
            try:
                self.dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to create directory: {e}")

        JsonFileManager._INSTANCES.append(self)

    def shut_down(self):
        if self._last_write_future:
            self._last_write_future.cancel()

    def write_to_disc_threaded(self, json_data: str, file_name: str):
        self._last_write_future = run_in_thread(self.write_to_disc, json_data, file_name)
        return self._last_write_future

    def write_to_disc(self, json_data: str, file_name: str):
        json_file = self.dir.joinpath(f"{file_name}.json")
        
        try:
            # delete=True, delete_on_close=False ###### deletes the file on context manager exit
            with tempfile.NamedTemporaryFile(mode='w', dir=self.dir, delete=True, delete_on_close=False) as temp_file:
                temp_file.write(json_data + '\n')
                temp_file_path = temp_file.name
                temp_file.close()
                rename_file(Path(temp_file_path), json_file)
        except Exception as e:
            logger.error(f"Error writing to storage file {json_file}", exc_info=e)
