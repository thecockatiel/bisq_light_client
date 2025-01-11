from bisq.common.setup.log_setup import get_logger
from bisq.core.notifications.mobile_model import MobileModel
from bisq.core.notifications.mobile_model_os import MobileModelOS


logger = get_logger(__name__)


class MobileNotificationValidator:

    def is_valid(self, key_and_token: str) -> bool:
        if not key_and_token:
            return False

        tokens = key_and_token.split(MobileModel.PHONE_SEPARATOR)
        if len(tokens) != 4:
            logger.error(
                f"invalid pairing ID format: not 4 sections separated by {MobileModel.PHONE_SEPARATOR_WRITING}"
            )
            return False

        magic = tokens[0]
        key = tokens[2]
        phone_id = tokens[3]

        if len(key) != 32:
            logger.error("invalid pairing ID format: key not 32 bytes")
            return False

        if magic in [
            MobileModelOS.IOS.magic_string,
            MobileModelOS.IOS_DEV.magic_string,
        ]:
            if len(phone_id) != 64:
                logger.error(
                    "invalid Bisq MobileModel ID format: iOS token not 64 bytes"
                )
                return False
        elif magic == MobileModelOS.ANDROID.magic_string:
            if len(phone_id) < 32:
                logger.error(
                    "invalid Bisq MobileModel ID format: Android token too short (<32 bytes)"
                )
                return False
        else:
            logger.error("invalid Bisq MobileModel ID format")
            return False

        return True
