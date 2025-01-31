import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional
from bisq.common.setup.log_setup import get_logger
from bisq.common.user_thread import UserThread
from utils.preconditions import check_argument
from bisq.core.notifications.mobile_message_type import MobileMessageType
from bisq.core.notifications.mobile_model_os import MobileModelOS
from bisq.core.util.json_util import JsonUtil
from utils.data import SimpleProperty
import uuid
from bisq.common.version import Version

if TYPE_CHECKING:
    from bisq.core.notifications.mobile_message import MobileMessage
    from bisq.core.network.http.async_http_client import AsyncHttpClient
    from bisq.core.notifications.mobile_message_encryption import (
        MobileMessageEncryption,
    )
    from bisq.core.notifications.mobile_model import MobileModel
    from bisq.core.notifications.mobile_notification_validator import (
        MobileNotificationValidator,
    )
    from bisq.core.user.preferences import Preferences


logger = get_logger(__name__)


class MobileNotificationService:
    # Used in Relay app to response of a success state. We won't want a code dependency just for that string so we keep it
    # duplicated in relay and here. Must not be changed.
    SUCCESS = "success"
    DEV_URL_LOCALHOST = "http://localhost:8080/"
    DEV_URL = "http://172.105.9.31:8080/"
    URL = "http://bisqpushv56wo32w2dv7xacvvcrnow6gud5vkvftwsgevczmspzvqgad.onion/"
    BISQ_MESSAGE_IOS_MAGIC = "BisqMessageiOS"
    BISQ_MESSAGE_ANDROID_MAGIC = "BisqMessageAndroid"

    def __init__(
        self,
        preferences: "Preferences",
        mobile_message_encryption: "MobileMessageEncryption",
        mobile_notification_validator: "MobileNotificationValidator",
        mobile_model: "MobileModel",
        http_client: "AsyncHttpClient",
        use_localhost: bool = False,
    ):
        self.preferences = preferences
        self.mobile_message_encryption = mobile_message_encryption
        self.mobile_notification_validator = mobile_notification_validator
        self.http_client = http_client
        self.mobile_model = mobile_model

        self.setup_confirmation_sent = False
        self.use_sound_property = SimpleProperty(False)
        self.use_trade_notifications_property = SimpleProperty(False)
        self.use_market_notifications_property = SimpleProperty(False)
        self.use_price_notifications_property = SimpleProperty(False)

        base_url = (
            MobileNotificationService.DEV_URL
            if use_localhost
            else MobileNotificationService.URL
        )
        http_client.base_url = base_url
        http_client.ignore_socks5_proxy = False

    def on_all_services_initialized(self):
        key_and_token = self.preferences.get_phone_key_and_token()
        if self.mobile_notification_validator.is_valid(key_and_token):
            self.setup_confirmation_sent = True
            self.mobile_model.apply_key_and_token(key_and_token)
            self.mobile_message_encryption.set_key(self.mobile_model.key)

        self.use_trade_notifications_property.set(
            self.preferences.is_use_trade_notifications()
        )
        self.use_market_notifications_property.set(
            self.preferences.is_use_market_notifications()
        )
        self.use_price_notifications_property.set(
            self.preferences.is_use_price_notifications()
        )
        self.use_sound_property.set(
            self.preferences.is_use_sound_for_mobile_notifications()
        )

    def apply_key_and_token(self, key_and_token: str) -> bool:
        if self.mobile_notification_validator.is_valid(key_and_token):
            self.mobile_model.apply_key_and_token(key_and_token)
            self.mobile_message_encryption.set_key(self.mobile_model.key)
            self.preferences.set_phone_key_and_token(key_and_token)
            if not self.setup_confirmation_sent:
                try:
                    self.send_confirmation_message()
                    self.setup_confirmation_sent = True
                except Exception as e:
                    logger.error(e)
            return True
        return False

    def send_message(
        self,
        message: "MobileMessage",
        use_sound: Optional[bool] = None,
        result_handler: Callable[[str], None] = None,
        error_handler: Callable[[Exception], None] = None,
    ) -> bool:
        if use_sound is None:
            use_sound = self.use_sound_property.get()

        if result_handler is None:
            result_handler = lambda result: logger.debug(f"sendMessage result={result}")

        if error_handler is None:
            error_handler = lambda e: logger.error(f"sendMessage failed. throwable={e}")

        if not self.mobile_model.key:
            return False

        do_send = False
        message_type = message.mobile_message_type
        if message_type == MobileMessageType.SETUP_CONFIRMATION:
            do_send = True
        elif message_type in (MobileMessageType.OFFER, MobileMessageType.TRADE, MobileMessageType.DISPUTE):
            do_send = self.use_trade_notifications_property.get()
        elif message_type == MobileMessageType.PRICE:
            do_send = self.use_price_notifications_property.get()
        elif message_type == MobileMessageType.MARKET:
            do_send = self.use_market_notifications_property.get()
        elif message_type == MobileMessageType.ERASE:
            do_send = True

        if not do_send:
            return False

        logger.info(f"Send message: '{message.message}'")
        logger.info(f"sendMessage message={message}")
        json = JsonUtil.object_to_json(message)
        logger.info(f"sendMessage json={json}")

        # Pad JSON string to multiple of 16 bytes for encryption
        json = json + " " * (16 - (len(json) % 16) if len(json) % 16 != 0 else 0)

        # Generate 16 random characters for iv
        # TODO: probably not secure? investigate later
        iv = uuid.uuid4().hex[:16]

        # Encrypt the JSON with the IV
        cipher = self.mobile_message_encryption.encrypt(json, iv)
        logger.info(f"key = {self.mobile_model.key}")
        logger.info(f"iv = {iv}")
        logger.info(f"encryptedJson = {cipher}")

        # Send the encrypted message
        self._do_send_message(iv, cipher, use_sound, result_handler, error_handler)
        return True

    def send_erase_message(self):
        message = MobileMessage("", "", MobileMessageType.ERASE)
        self.send_message(message, False)

    def reset(self):
        self.mobile_model.reset()
        self.preferences.set_phone_key_and_token(None)
        self.setup_confirmation_sent = False

    def send_confirmation_message(self):
        logger.info("send_confirmation_message")
        message = MobileMessage("", "", MobileMessageType.SETUP_CONFIRMATION)
        self.send_message(message, True)

    def _do_send_message(
        self,
        iv: str,
        cipher: str,
        use_sound: bool,
        result_handler: Optional[Callable[[str], None]] = None,
        error_handler: Optional[Callable[[Exception], None]] = None,
    ):
        if self.http_client.has_pending_request:
            logger.warning(
                f"We have a pending request open. We ignore that request. httpClient {self.http_client}"
            )
            return

        msg: Optional[str] = None
        if self.mobile_model.os in (MobileModelOS.IOS, MobileModelOS.IOS_DEV):
            msg = MobileNotificationService.BISQ_MESSAGE_IOS_MAGIC
        elif self.mobile_model.os == MobileModelOS.ANDROID:
            msg = MobileNotificationService.BISQ_MESSAGE_ANDROID_MAGIC
        else:
            raise RuntimeError("No mobileModel OS set")

        msg += (
            MobileModel.PHONE_SEPARATOR_WRITING
            + iv
            + MobileModel.PHONE_SEPARATOR_WRITING
            + cipher
        )
        is_android = self.mobile_model.os == MobileModelOS.ANDROID
        is_production = self.mobile_model.os == MobileModelOS.IOS

        if not self.mobile_model.token:
            raise ValueError("mobile_model.token must be set")

        token_as_hex = self.mobile_model.token.encode("utf-8").hex()
        msg_as_hex = msg.encode("utf-8").hex()
        param = (
            f"/relay?isAndroid={str(is_android).lower()}&"
            f"isProduction={str(is_production).lower()}&"
            f"isContentAvailable={str(self.mobile_model.is_content_available).lower()}&"
            f"snd={str(use_sound).lower()}&"
            f"token={token_as_hex}&"
            f"msg={msg_as_hex}"
        )

        logger.info(f"Send: token={self.mobile_model.token}")
        logger.info(f"Send: msg={msg}")
        logger.info(
            f"Send: isAndroid={is_android}\nuseSound={use_sound}\n"
            f"tokenAsHex={token_as_hex}\nmsgAsHex={msg_as_hex}"
        )

        future = self.http_client.get(
            param,
            headers={
                "User-Agent": f"bisq/{Version.VERSION}, uid: {self.http_client.uid}"
            },
        )

        def on_done(t: asyncio.Task[str]):
            try:
                result = t.result()
                logger.info(f"sendMobileNotification result={result}")
                check_argument(result == MobileNotificationService.SUCCESS, f"Result was not 'success'. result={result}")
                UserThread.execute(lambda: result_handler(result))
            except Exception as e:
                UserThread.execute(lambda: error_handler(e))

        future.add_done_callback(on_done)
