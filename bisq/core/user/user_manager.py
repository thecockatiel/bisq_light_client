from threading import RLock
from bisq.common.config.config import Config
from bisq.common.file.corrupted_storage_file_handler import CorruptedStorageFileHandler
from bisq.common.file.file_util import delete_directory
from bisq.common.persistence.persistence_orchestrator import PersistenceOrchestrator
from bisq.common.protocol.network.network_proto_resolver import NetworkProtoResolver
from bisq.common.util.utilities import get_random_id
from bisq.core.exceptions.illegal_state_exception import IllegalStateException

from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.crypto.encryption import Encryption
from bisq.common.crypto.key_ring import KeyRing
from bisq.common.crypto.key_storage import KeyStorage
from bisq.common.persistence.persistence_manager import PersistenceManager
from bisq.common.persistence.persistence_manager_source import PersistenceManagerSource
from bisq.common.protocol.persistable.persistable_data_host import PersistedDataHost
from bisq.common.setup.log_setup import (
    destory_user_logger,
    get_ctx_logger,
    get_user_logger,
    logger_context,
)
from bisq.common.user_thread import UserThread
from bisq.core.user.preferences import Preferences
from bisq.core.user.user import User
from bisq.core.user.user_context import UserContext
from bisq.core.user.user_manager_payload import UserManagerPayload
from utils.aio import as_future
from utils.concurrency import AtomicInt
from utils.data import SimpleProperty
from utils.preconditions import check_argument
from bisq.core.provider.fee.fee_service import FeeService
from bisq.core.protocol.persistable.core_persistence_proto_resolver import (
    CorePersistenceProtoResolver,
)
from utils.clock import Clock
from twisted.internet.defer import Deferred
import asyncio

if TYPE_CHECKING:
    from global_container import GlobalContainer
    from shared_container import SharedContainer


class UserManager(PersistedDataHost):
    """Holds information about what users we have and which user is currently active"""

    def __init__(
        self,
        config: "Config",
        network_proto_resolver: "NetworkProtoResolver",
        corrupted_storage_file_handler: "CorruptedStorageFileHandler",
        shared_persistence_orchestrator: "PersistenceOrchestrator",
    ):
        super().__init__()
        self.logger = get_ctx_logger(__name__)
        self._persistence_proto_resolver = CorePersistenceProtoResolver(
            Clock(), None, network_proto_resolver
        )
        self._corrupted_storage_file_handler = corrupted_storage_file_handler
        self._data_dir = config.app_data_dir.joinpath("user_manager")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._persistence_manager = PersistenceManager(
            self._data_dir,
            self._persistence_proto_resolver,
            self._corrupted_storage_file_handler,
            shared_persistence_orchestrator,
        )
        self._config = config
        self._user_manager_payload = UserManagerPayload()
        self._user_contexts = dict[str, UserContext]()  # user_id -> UserContext
        self._user_containers = dict[
            str, "GlobalContainer"
        ]()  # user_id -> GlobalContainer
        self.active_user_context_property = SimpleProperty[Optional[UserContext]]()
        self._lock = RLock()

    def read_persisted(self, complete_handler: Callable[[], None]):
        assert self._persistence_manager is not None
        self._persistence_manager.read_persisted(
            lambda persisted: (
                setattr(self, "_user_manager_payload", persisted),
                self._init(complete_handler),
            ),
            lambda: (self._init(complete_handler, True),),
            file_name="UserManagerPayload",
        )

    def force_persist_now(self):
        if self._persistence_manager is not None:
            self._persistence_manager.force_persist_now()

    def _init(self, complete_handler: Callable[[], None], first_time=False):
        assert self._persistence_manager is not None
        self._persistence_manager.initialize(
            self._user_manager_payload, PersistenceManagerSource.PRIVATE
        )

        if first_time:
            # we want to save users asap first time to not create files unnecessarily
            self._persistence_manager.force_persist_now()

        # user manager payload will create a user entry if empty
        for user_id in self._user_manager_payload.user_alias_entries.keys():
            self._load_user_context(user_id)

        remaining = AtomicInt(len(self._user_contexts))

        def _on_data_read():
            if remaining.decrement_and_get() == 0:
                UserThread.execute(complete_handler)

        for user_id in self._user_contexts.keys():
            self._read_persisted_user_and_preference(user_id, _on_data_read)

    def _load_user_context(self, user_id: str):
        alias = self._user_manager_payload.user_alias_entries[user_id]
        user_data_dir = self._config.app_data_dir.joinpath("users", user_id)
        user_data_dir.mkdir(parents=True, exist_ok=True)
        storage_dir = user_data_dir.joinpath(
            self._config.base_currency_network.name.lower()
        ).joinpath("db")
        storage_dir.mkdir(parents=True, exist_ok=True)
        key_storage_dir = user_data_dir.joinpath("keys")
        key_storage_dir.mkdir(parents=True, exist_ok=True)
        logger = get_user_logger(user_id, user_data_dir)

        with logger_context(logger):
            key_storage = KeyStorage(key_storage_dir)
            key_ring = KeyRing(key_storage)
            persistence_orchestrator = PersistenceOrchestrator()
            user = User(
                user_data_dir,
                PersistenceManager(
                    storage_dir,
                    self._persistence_proto_resolver,
                    self._corrupted_storage_file_handler,
                    persistence_orchestrator,
                ),
                key_ring,
            )
            user_preferences = Preferences(
                PersistenceManager(
                    storage_dir,
                    self._persistence_proto_resolver,
                    self._corrupted_storage_file_handler,
                    persistence_orchestrator,
                ),
                self._config,
                FeeService(
                    None,
                ),  # create a temporary fee service, later replaced by each user's own fee service
            )

        self._user_contexts[user_id] = UserContext(
            user_id=user_id,
            alias=alias,
            user=user,
            preferences=user_preferences,
            persistence_orchestrator=persistence_orchestrator,
            logger=logger,
        )

    def _read_persisted_user_and_preference(
        self, user_id: str, complete_handler: Callable[[], None]
    ):
        ctx = self.get_user_context(user_id)
        remaining = AtomicInt(2)

        def _on_data_read():
            if remaining.decrement_and_get() == 0:
                UserThread.execute(complete_handler)

        ctx.user.read_persisted(_on_data_read)
        ctx.preferences.read_persisted(_on_data_read)

    @property
    def active_user_id(self):
        return self._user_manager_payload.active_user_id

    @property
    def active_context(self):
        if not self.active_user_context_property.value:
            raise IllegalStateException(
                "no user initialized yet, there's no active context"
            )
        return self.active_user_context_property.value

    def set_user_alias(self, user_id: str, alias: str):
        with self._lock:
            alias = alias.strip().replace(" ", "")
            check_argument(alias != "", "alias cannot be empty string")
            check_argument(
                user_id in self._user_manager_payload.user_alias_entries,
                "provided user id is not found",
            )
            check_argument(
                alias not in self._user_manager_payload.user_alias_entries,
                "new alias cannot be same as an existing user id",
            )
            check_argument(
                alias not in self._user_manager_payload.user_alias_entries.values(),
                "new alias cannot be same as an existing alias",
            )
            check_argument(
                alias.isalnum(),
                "new alias must be alpha numerical and contain at least one character",
            )
            self._user_manager_payload.user_alias_entries[user_id] = alias
            if user_id in self._user_contexts:
                self._user_contexts[user_id].alias = alias
            self.force_persist_now()

    async def create_user(self, user_id: Optional[str] = None):
        with self._lock:
            if user_id is None:
                user_id = str(get_random_id(8))
            else:
                exists = False
                try:
                    if self.get_user_context(user_id):
                        exists = True
                except:
                    pass
                if exists:
                    raise IllegalStateException("user id already exists in user list")
            self._user_manager_payload.user_alias_entries[user_id] = ""
            self.force_persist_now()
            self._load_user_context(user_id)
            d = Deferred()

            def _on_data_read():
                d.callback(True)

            try:
                self._read_persisted_user_and_preference(user_id, _on_data_read)
            except Exception as e:
                d.errback(e)
            await as_future(d)
            return user_id

    def find_user_context_for_sig_pub_key(self, pub_key_bytes: bytes):
        return next(
            (
                context
                for context in self._user_contexts.copy().values()
                if Encryption.is_pubkeys_equal(
                    pub_key_bytes,
                    context.key_ring.pub_key_ring.signature_pub_key_bytes,
                )
            ),
            None,
        )

    def get_user_context(self, user_id_or_alias: str):
        user_id_or_alias = user_id_or_alias.strip().replace(" ", "")
        check_argument(
            user_id_or_alias != "", "user_id or alias cannot be empty string"
        )
        if user_id_or_alias in self._user_manager_payload.user_alias_entries.values():
            user_id = next(
                (
                    k
                    for k, v in self._user_manager_payload.user_alias_entries.items()
                    if v == user_id_or_alias
                ),
                user_id_or_alias,
            )
        else:
            user_id = user_id_or_alias

        check_argument(
            user_id in self._user_contexts,
            f"user-id or alias `{user_id}` does not exist or is not loaded",
        )
        return self._user_contexts[user_id]

    def get_all_contexts(self):
        return self._user_contexts.values()

    async def switch_user(self, to_user_id: str, shared_container: "SharedContainer"):
        with self._lock:
            if to_user_id is None:
                to_user_id = next(iter(self._user_contexts.keys()))
            ctx = self.get_user_context(to_user_id)
            self._user_manager_payload.active_user_id = to_user_id
            self.force_persist_now()
            await ctx.start(shared_container, True)
            self.active_user_context_property.value = ctx

    async def delete_user(
        self, user_id: str, remove_user_data: bool, shared_container: "SharedContainer"
    ):
        with self._lock:
            created_new_user = False
            new_user_id = None
            ctx = self.get_user_context(user_id)
            await ctx.shut_down()
            destory_user_logger(ctx.user_id)
            ctx.logger = None
            del self._user_contexts[ctx.user_id]
            del self._user_manager_payload.user_alias_entries[ctx.user_id]
            if remove_user_data:
                try:
                    delete_directory(ctx.user.data_dir)
                except:
                    self.logger.warning(
                        f"Failed to unlink user `{ctx.user_id}` directory: {ctx.user.data_dir}"
                    )
            if len(self._user_contexts) > 0:
                if ctx.user_id == self.active_user_id:
                    new_user_id = next(iter(self._user_contexts.keys()), None)
                    if new_user_id is None:
                        # this should not ever happen, but just in case:
                        new_user_id = await self.create_user()
                        created_new_user = True
            else:
                new_user_id = await self.create_user()
                created_new_user = True

            if new_user_id:
                await self.switch_user(new_user_id, shared_container)

            return (new_user_id, created_new_user)

    def shut_down_all_users(self, result_handler: Callable[[int], None]):
        with self._lock:
            ids = self._user_contexts.keys()
            remaining = AtomicInt(len(ids))
            ecode = 0

            def on_finished(f: asyncio.Future[int], user_id: str):
                nonlocal ecode
                try:
                    result = f.result()
                    if result > 0:
                        ecode = result
                except BaseException as e:
                    self.logger.error(
                        f"Error while shutting down user_id `{user_id}`", exc_info=e
                    )
                    ecode = 1
                if remaining.decrement_and_get() == 0:
                    result_handler(ecode)

            # no need to use FutureCallback here as we are shutting down and dont need to pass contextvar
            for ctx in self.get_all_contexts():
                as_future(ctx.shut_down()).add_done_callback(
                    lambda f, user_id=ctx.user_id: on_finished(f, user_id)
                )
