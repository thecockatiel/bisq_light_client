from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from bisq.common.file.json_file_manager import JsonFileManager
from bisq.core.dao.dao_setup_service import DaoSetupService

if TYPE_CHECKING:
    from bisq.core.dao.state.dao_state_service import DaoStateService


# TODO: implement later if necessary
class ExportJsonFilesService(DaoSetupService):

    def __init__(
        self,
        dao_state_service: "DaoStateService",
        storage_dir: Path,
        dump_blockchain_data: bool,
    ):
        self._dao_state_service = dao_state_service
        self._storage_dir = storage_dir
        self._dump_blockchain_data = dump_blockchain_data

        self._tx_file_manager: Optional["JsonFileManager"] = None
        self._tx_output_file_manager: Optional["JsonFileManager"] = None
        self._bsq_state_file_manager: Optional["JsonFileManager"] = None

        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="JsonExporter"
        )

    # ///////////////////////////////////////////////////////////////////////////////////////////
    # // DaoSetupService
    # ///////////////////////////////////////////////////////////////////////////////////////////

    def add_listeners(self):
        pass

    def start(self):
        pass

    def shut_down(self):
        if self._dump_blockchain_data and self._tx_file_manager is not None:
            self._tx_file_manager.shut_down()
            self._tx_output_file_manager.shut_down()
            self._bsq_state_file_manager.shut_down()
        if self._executor:
            self._executor.shutdown()
            self._executor = None

    def maybe_export_to_json(self):
        pass
