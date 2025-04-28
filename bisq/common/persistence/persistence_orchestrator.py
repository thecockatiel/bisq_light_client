from typing import TYPE_CHECKING

from bisq.common.handlers.result_handler import ResultHandler
from bisq.common.setup.log_setup import get_ctx_logger
from bisq.common.user_thread import UserThread
from utils.concurrency import AtomicBoolean, AtomicInt


if TYPE_CHECKING:
    from bisq.common.persistence.persistence_manager import PersistenceManager


class PersistenceOrchestrator:
    """Responsible for managing the PersistenceManagers for a single user"""

    def __init__(self):
        self.all_persistence_managers = dict[str, "PersistenceManager"]()
        self.all_services_initialized = AtomicBoolean(False)
        self.flush_at_shutdown_called = AtomicBoolean(False)
        self.logger = get_ctx_logger(__name__)

    def on_all_services_initialized(self):
        self.all_services_initialized.set(True)
        for manager in self.all_persistence_managers.values():
            # In case we got a requestPersistence call before we got initialized we trigger the timer for the
            # persist call
            if manager.persistence_requested.get():
                manager.maybe_start_timer_for_persistence()

    def flush_all_data_to_disk_at_backup(self, complete_handler: "ResultHandler"):
        self.flush_all_data_to_disk(complete_handler, False)

    def flush_all_data_to_disk_at_shutdown(self, complete_handler: "ResultHandler"):
        self.flush_all_data_to_disk(complete_handler, True)

    # We require being called only once from the global shutdown routine. As the shutdown routine has a timeout
    # and error condition where we call the method as well beside the standard path and it could be that those
    # alternative code paths call our method after it was called already, so it is a valid but rare case.
    # We add a guard to prevent repeated calls.
    def flush_all_data_to_disk(
        self, complete_handler: "ResultHandler", do_shutdown: bool
    ):
        if not self.all_services_initialized.get():
            self.logger.warning(
                "Application has not completed start up yet so we do not flush data to disk."
            )
            complete_handler()
            return

        def flush():
            if do_shutdown:
                if self.flush_at_shutdown_called:
                    self.logger.warning("Flush called again. Ignoring repeated call.")
                    return
                else:
                    self.flush_at_shutdown_called = True

            self.logger.info("Start flushAllDataToDisk")
            open_instances = AtomicInt(len(self.all_persistence_managers))

            if open_instances.get() == 0:
                self.logger.info(
                    "No PersistenceManager instances have been created yet."
                )
                complete_handler()
                return

            for persistence_manager in list(self.all_persistence_managers.values()):
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
                        lambda pm=persistence_manager: self._on_write_completed(
                            complete_handler,
                            open_instances,
                            pm,
                            do_shutdown,
                        )
                    )
                else:
                    self._on_write_completed(
                        complete_handler,
                        open_instances,
                        persistence_manager,
                        do_shutdown,
                    )

        UserThread.execute(flush)

    def _on_write_completed(
        self,
        complete_handler: "ResultHandler",
        open_instances: "AtomicInt",
        persistence_manager: "PersistenceManager",
        do_shutdown: bool,
    ):
        if do_shutdown:
            persistence_manager.shutdown()
        if open_instances.decrement_and_get() == 0:
            self.logger.info("flushAllDataToDisk completed")
            complete_handler()
