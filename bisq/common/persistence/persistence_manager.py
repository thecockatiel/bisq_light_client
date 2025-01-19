from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import threading
import os
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar, Generic, Optional, cast
from collections.abc import Callable
from bisq.common.app.dev_env import DevEnv
from bisq.common.file.file_util import create_new_file, create_temp_file, remove_and_backup_file, rename_file, rolling_backup
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_envelope import (
    PersistableEnvelope,
)
from bisq.common.timer import Timer
from bisq.common.user_thread import UserThread
from proto.delimited_protobuf import read_delimited, write_delimited
import proto.pb_pb2 as protobuf
from bisq.common.setup.log_setup import get_logger
from utils.concurrency import AtomicBoolean, AtomicInt
from utils.dir import check_dir
from utils.time import get_time_ms

if TYPE_CHECKING:
    from bisq.common.handlers.result_handler import ResultHandler
    from bisq.common.protocol.persistable.persistence_proto_resolver import (
        PersistenceProtoResolver,
    )
    from bisq.common.file.corrupted_storage_file_handler import (
        CorruptedStorageFileHandler,
    )

logger = get_logger(__name__)

T = TypeVar(
    "T", bound=PersistableEnvelope
)


class PersistenceManager(Generic[T]):
    """Responsible for reading persisted data and writing it on disk."""

    ALL_PERSISTENCE_MANAGERS: dict[str, "PersistenceManager"] = {}
    flush_at_shutdown_called = False
    all_services_initialized = AtomicBoolean(False)

    def __init__(
        self,
        dir: Path,
        persistence_proto_resolver: "PersistenceProtoResolver",
        corrupted_storage_file_handler: "CorruptedStorageFileHandler",
    ):
        self.dir = check_dir(dir)
        self.persistence_proto_resolver = persistence_proto_resolver
        self.corrupted_storage_file_handler = corrupted_storage_file_handler

        self.storage_file: Optional[Path] = None
        self.persistable: Optional[T] = None
        self.file_name: Optional[str] = None
        self.source: PersistenceManagerSource = (
            PersistenceManagerSource.PRIVATE_LOW_PRIO
        )
        self.used_temp_file_path: Optional[Path] = None
        self.persistence_requested = AtomicBoolean(False)
        self.timer: Optional[Timer] = None
        self.write_to_disk_executor: Optional[ThreadPoolExecutor] = None
        self.init_called = False
        self.read_called = False

    @staticmethod
    def on_all_services_initialized():
        PersistenceManager.all_services_initialized.set(True)
        for manager in PersistenceManager.ALL_PERSISTENCE_MANAGERS.values():
            # In case we got a requestPersistence call before we got initialized we trigger the timer for the
            # persist call
            if manager.persistence_requested.get():
                manager.maybe_start_timer_for_persistence()

    @staticmethod
    def flush_all_data_to_disk_at_backup(complete_handler: "ResultHandler"):
        PersistenceManager.flush_all_data_to_disk(complete_handler, False)

    @staticmethod
    def flush_all_data_to_disk_at_shutdown(complete_handler: "ResultHandler"):
        PersistenceManager.flush_all_data_to_disk(complete_handler, True)

    # We require being called only once from the global shutdown routine. As the shutdown routine has a timeout
    # and error condition where we call the method as well beside the standard path and it could be that those
    # alternative code paths call our method after it was called already, so it is a valid but rare case.
    # We add a guard to prevent repeated calls.
    @staticmethod
    def flush_all_data_to_disk(complete_handler: "ResultHandler", do_shutdown: bool):
        if not PersistenceManager.all_services_initialized.get():
            logger.warning(
                "Application has not completed start up yet so we do not flush data to disk."
            )
            complete_handler()
            return

        def flush():
            if do_shutdown:
                if PersistenceManager.flush_at_shutdown_called:
                    logger.warning("Flush called again. Ignoring repeated call.")
                    return
                else:
                    PersistenceManager.flush_at_shutdown_called = True

            logger.info("Start flushAllDataToDisk")
            open_instances = AtomicInt(len(PersistenceManager.ALL_PERSISTENCE_MANAGERS))

            if open_instances.get() == 0:
                logger.info("No PersistenceManager instances have been created yet.")
                complete_handler()
                return

            for persistence_manager in list(
                PersistenceManager.ALL_PERSISTENCE_MANAGERS.values()
            ):
                # For Priority.HIGH data we want to write to disk in any case to be on the safe side if we might have missed
                # a requestPersistence call after an important state update. Those are usually rather small data stores.
                # Otherwise we only persist if requestPersistence was called since the last persist call.
                # We also check if we have called read already to avoid a very early write attempt before we have ever
                # read the data, which would lead to a write of empty data
                # (fixes https://github.com/bisq-network/bisq/issues/4844).
                if persistence_manager.read_called and (
                    persistence_manager.source.flush_at_shutdown
                    or persistence_manager.persistence_requested.get()
                ):
                    # We always get our completeHandler called even if exceptions happen. In case a file write fails
                    # we still call our shutdown and count down routine as the completeHandler is triggered in any case.

                    # We get our result handler called from the write thread so we map back to user thread.
                    persistence_manager.persist_now(
                        lambda: PersistenceManager.on_write_completed(
                            complete_handler,
                            open_instances,
                            persistence_manager,
                            do_shutdown,
                        )
                    )
                else:
                    PersistenceManager.on_write_completed(
                        complete_handler,
                        open_instances,
                        persistence_manager,
                        do_shutdown,
                    )

        UserThread.execute(flush)

    @staticmethod
    def on_write_completed(
        complete_handler: "ResultHandler",
        open_instances: "AtomicInt",
        persistence_manager: "PersistenceManager",
        do_shutdown: bool,
    ):
        if do_shutdown:
            persistence_manager.shutdown()
        if open_instances.decrement_and_get() == 0:
            logger.info("flushAllDataToDisk completed")
            complete_handler()

    ###############################################################################

    def initialize(
        self, persistable: T, source: "PersistenceManagerSource", file_name: Optional[str] = None
    ):
        if PersistenceManager.flush_at_shutdown_called:
            logger.warning("Shutdown routine started. Ignoring initialize call.")
            return

        file_name = file_name or persistable.get_default_storage_file_name()

        if file_name in PersistenceManager.ALL_PERSISTENCE_MANAGERS:
            e = RuntimeError(
                f"We must not create multiple PersistenceManager instances for file {file_name}."
            )
            logger.error(str(e), exc_info=e)
            raise e

        if self.init_called:
            e = RuntimeError(
                f"We must not call initialize multiple times. PersistenceManager for file: {file_name}."
            )
            logger.error(str(e), exc_info=e)
            raise e

        self.init_called = True

        self.persistable = persistable
        self.file_name = file_name
        self.source = source
        self.storage_file = self.dir.joinpath(self.file_name)
        PersistenceManager.ALL_PERSISTENCE_MANAGERS[self.file_name] = self

    def shutdown(self):
        PersistenceManager.ALL_PERSISTENCE_MANAGERS.pop(self.file_name, None)

        if self.timer:
            self.timer.stop()

        if self.write_to_disk_executor:
            self.write_to_disk_executor.shutdown()

    ###########################################################################

    def read_persisted(
        self,
        result_handler: Callable[[T], None],
        or_else: Callable[[], None],
        file_name: str = None,
    ):
        if file_name == None:
            file_name = self.file_name
        assert file_name, "file_name cannot be null"

        if PersistenceManager.flush_at_shutdown_called:
            logger.warning(
                "We have started the shut down routine already. We ignore that readPersisted call."
            )
            return

        def read():
            persisted = self.get_persisted(file_name)
            if persisted:

                def run():
                    result_handler(persisted)
                    # NOTE: we don't implement next line for now since we don't know if python's gc needs help or not
                    # self.maybe_release_memory()

                UserThread.execute(run)
            else:
                UserThread.execute(or_else)

        threading.Thread(
            target=read, name="PersistenceManager-read-" + file_name
        ).start()

    def get_persisted(self, file_name: Optional[str] = None) -> Optional[T]:
        if PersistenceManager.flush_at_shutdown_called:
            logger.warning(
                "We have started the shut down routine already. We ignore that getPersisted call."
            )
            return None

        self.read_called = True

        file_name = file_name or self.file_name
        assert file_name, "file_name cannot be null"

        storage_file = self.dir.joinpath(file_name)
        if not storage_file.exists():
            return None

        ts = get_time_ms()
        try:
            with storage_file.open("rb") as f:
                proto = read_delimited(f, protobuf.PersistableEnvelope)
                persistable_envelope = self.persistence_proto_resolver.from_proto(proto)
                logger.info(f"Reading {file_name} completed in {get_time_ms() - ts} ms")
                return cast(T, persistable_envelope)
        except Exception as e:
            logger.error(f"Reading {file_name} failed with {e}.", exc_info=e)
            try:
                # We keep a backup which might be used for recovery
                remove_and_backup_file(
                    self.dir, storage_file, file_name, "backup_of_corrupted_data"
                )
                DevEnv.log_error_and_throw_if_dev_mode(str(e))
            except Exception as backup_e:
                logger.error(str(e), exc_info=backup_e)
                #  We swallow Exception if backup fails
            if self.corrupted_storage_file_handler:
                self.corrupted_storage_file_handler.add_file(storage_file.name)
        return None

    ###########################################################################

    def request_persistence(self):
        if PersistenceManager.flush_at_shutdown_called:
            logger.warning(
                "We have started the shut down routine already. We ignore that requestPersistence call."
            )
            return

        self.persistence_requested.set(True)

        # If we have not initialized yet we postpone the start of the timer and call maybeStartTimerForPersistence at
        # onAllServicesInitialized
        if not PersistenceManager.all_services_initialized.get():
            return

        self.maybe_start_timer_for_persistence()
        
    def _clear_timer(self):
        self.timer = None

    def maybe_start_timer_for_persistence(self):
        # We write to disk with a delay to avoid frequent write operations. Depending on the priority those delays
        # can be rather long.
        if not self.timer:
            def run():
                self.persist_now()
                UserThread.execute(self._clear_timer)
            self.timer = UserThread.run_after(run, timedelta(milliseconds=self.source.delay))

    def force_persist_now(self):
        # Tor Bridges settings are edited before app init completes, require persistNow to be forced, see writeToDisk()
        self.persist_now(force=True)

    def persist_now(
        self, complete_handler: Optional[Callable[[], None]] = None, force: bool = False
    ):
        ts = get_time_ms()
        try:
            # The serialisation is done on the user thread to avoid threading issue with potential mutations of the
            # persistable object. Keeping it on the user thread we are in a synchronize model.
            serialized = self.persistable.to_persistable_message()
            
            # For the write to disk task we use a thread. We do not have any issues anymore if the persistable objects
            # gets mutated while the thread is running as we have serialized it already and do not operate on the
            # reference to the persistable object.
            self.get_write_to_disk_executor().submit(self.write_to_disk, serialized, complete_handler, force)
            
            duration = get_time_ms() - ts
            if duration > 100:
                logger.info(f"Serializing {self.file_name} took {duration} msec")
        except Exception as e:
            logger.error(f"Error in saveToFile toProtoMessage: {self.persistable.__class__.__name__}, {self.file_name}", exc_info=e)
            raise RuntimeError(e)

    def write_to_disk(
        self, serialized: protobuf.PersistableEnvelope, complete_handler: Optional[Callable[[], None]], force: bool
    ):
        if not PersistenceManager.all_services_initialized.get() and not force:
            logger.warning("Application has not completed start up yet so we do not permit writing data to disk.")
            if complete_handler:
                UserThread.execute(complete_handler)
            return
         
        ts = get_time_ms()
        temp_file = None
        file_out = None

        try:
            # Before we write we backup existing file
            rolling_backup(self.dir, self.file_name, self.source.num_max_backup_files)

            if not self.dir.exists():
                try:
                    self.dir.mkdir(parents=True, exist_ok=True)
                except:
                    logger.warning(f"make dir failed {self.file_name}")

            # Create temp file
            if self.used_temp_file_path:
                temp_file = create_new_file(self.used_temp_file_path)
            else:
                temp_file = create_temp_file("temp_" + self.file_name, None, self.dir)
                
            # NOTE: the next line comment is from original bisq, so idk if that sth like that still applies. ignoring it as there isn't a deleteOnExit in python
            # Don't use a new temp file path each time, as that causes the delete-on-exit hook to leak memory:

            # Write data to temp file
            with temp_file.open('wb') as file_out:
                write_delimited(file_out, serialized)
                # Attempt to force the bits to hit the disk. In reality the OS or hard disk itself may still decide
                # to not write through to physical media for at least a few seconds, but this is the best we can do.
                file_out.flush()
                os.fsync(file_out.fileno())  # Force write to disk

            # Rename temp file to final storage file
            rename_file(temp_file, self.storage_file)
            self.used_temp_file_path = temp_file
            
        except Exception as e:
            # If an error occurred, don't attempt to reuse this path again, in case temp file cleanup fails.
            self.used_temp_file_path = None
            logger.error(f"Error at saveToFile, storageFile={self.file_name}", exc_info=e)
        finally:
            if temp_file and temp_file.exists():
                logger.warning(f"Temp file still exists after failed save. We will delete it now. storageFile={self.file_name}")
                try:
                    temp_file.unlink(missing_ok=True)
                except:
                    logger.error("Cannot delete temp file.")

            duration = get_time_ms() - ts
            if duration > 100:
                logger.info(f"Writing the serialized {self.file_name} completed in {duration} msec")
                
            self.persistence_requested.set(False)
            if complete_handler:
                UserThread.execute(complete_handler)
                
    def get_write_to_disk_executor(self):
        if self.write_to_disk_executor is None:
            self.write_to_disk_executor = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix=f"Write-{self.file_name}_to-disk"
            )
        return self.write_to_disk_executor

    def to_string(self):
        return (
            f"PersistenceManager(\n"
            f"    file_name='{self.file_name}',\n"
            f"    dir={self.dir},\n"
            f"    storage_file={self.storage_file},\n"
            f"    persistable={self.persistable},\n"
            f"    source={self.source},\n"
            f"    used_temp_file_path={self.used_temp_file_path},\n"
            f"    persistence_requested={self.persistence_requested}\n)"
        )
