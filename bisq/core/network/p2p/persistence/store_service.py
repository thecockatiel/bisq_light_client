
 
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar
from collections.abc import Callable
from bisq.common.file.file_util import resource_to_file
from bisq.common.file.resource_not_found_exception import ResourceNotFoundException
from bisq.common.protocol.persistable.persistable_envelope import PersistableEnvelope
from bisq.common.setup.log_setup import get_logger

if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager
    
logger = get_logger(__name__)

T = TypeVar(
    "T", bound=PersistableEnvelope
) 

class StoreService(Generic[T], ABC):
    """ 
    Base class for handling of persisted data.
    
    We handle several different cases:
    
    1   Check if local db file exists.
    1a  If it does not exist try to read the resource file.
    1aa If the resource file exists we copy it and use that as our local db file. We are done.
    1ab If the resource file does not exist we create a new fresh/empty db file. We are done.
    1b  If we have already a local db file we read it. We are done.
    """
    
    def __init__(self, storage_dir: Path, persistence_manager: "PersistenceManager[T]"):
        self.storage_dir = storage_dir
        self.persistence_manager = persistence_manager
        self.store: T = None
        
    def request_persistence(self):
        self.persistence_manager.request_persistence()
    
    @abstractmethod
    def get_file_name(self):
        pass
    
    def read_from_resources(self, postfix: str, complete_handler: Callable[[], None]):
        file_name = self.get_file_name()
        self.make_file_from_resource_file(file_name, postfix)
        try:
            self.read_store(lambda persisted: complete_handler())
        except:
            self.make_file_from_resource_file(file_name, postfix)
            self.read_store(lambda persisted: complete_handler())
    
    # Uses synchronous execution on the userThread. Only used by tests. The async methods should be used by app code.
    def read_from_resources_sync(self, postfix: str):
        file_name = self.get_file_name()
        self.make_file_from_resource_file(file_name, postfix)
        try:
            self.read_store_sync()
        except:
            self.make_file_from_resource_file(file_name, postfix)
            self.read_store_sync()
            
    def make_file_from_resource_file(self, file_name: str, postfix: str):
        if not self.storage_dir.exists():
            try:
                self.storage_dir.mkdir(parents=True, exist_ok=True)
            except:
                logger.warning(f"make dir failed.\ndbDir={self.storage_dir.absolute()}")
                
        resource_file_name = f"{file_name}_{postfix}"
        destination_file = self.storage_dir.joinpath(resource_file_name)
        if not destination_file.exists():
            try:
                logger.debug(f"We copy resource to file: resourceFileName={resource_file_name}, destinationFile={destination_file}")
                resource_to_file(resource_file_name, destination_file)
                return True
            except ResourceNotFoundException as e:
                logger.error(f"Could not find resourceFile {resource_file_name}. That is expected if none is provided yet.")
            except Exception as e:
                logger.error(f"Could not copy resourceFile {resource_file_name} to {destination_file.absolute()}.\n {e}", exc_info=e)
        else:
            logger.debug(f"No resource file was copied. {file_name} exists already.")
        return False
    
    def read_store(self, complete_handler: Callable[[T], None], file_name: str = None):
        if file_name is None:
            file_name = self.get_file_name()
        def on_persisted(persisted: T):
            self.store = persisted
            self.initialize_persistence_manager()
            complete_handler(persisted)
        
        def create_default():
            on_persisted(self.create_store())
            
        self.persistence_manager.read_persisted(result_handler=on_persisted, or_else=create_default, file_name=file_name)
        
    # Uses synchronous execution on the userThread. Only used by tests. The async methods should be used by app code.
    def get_store_sync(self, file_name: str):
        store = self.persistence_manager.get_persisted(file_name)
        if store is None:
            store = self.create_store()
        return store
    
    # Uses synchronous execution on the userThread. Only used by tests. The async methods should be used by app code.
    def read_store_sync(self):
        self.store = self.get_store_sync(self.get_file_name())
        self.initialize_persistence_manager()
        
    @abstractmethod
    def initialize_persistence_manager(self):
        pass
    
    @abstractmethod
    def create_store(self) -> T:
        pass