from bisq.common.setup.log_setup import get_ctx_logger
from typing import Optional
from bisq.core.notifications.mobile_model_os import MobileModelOS

 

class MobileModel:
    PHONE_SEPARATOR = "|"
    PHONE_SEPARATOR_WRITING = "|"
    
    def __init__(self,):
        self.logger = get_ctx_logger(__name__)
        self.os: Optional[MobileModelOS] = None
        self.descriptor: Optional[str] = None
        self.key: Optional[str] = None
        self.token: Optional[str] = None
        self.is_content_available = True
        
    def reset(self):
        self.os = None
        self.key = None
        self.token = None
    
    def apply_key_and_token(self, key_and_token: str):
        self.logger.info(f"apply_key_and_token: key_and_token={key_and_token[:20]}...(truncated in log for privacy reasons)")
        tokens = key_and_token.split(MobileModel.PHONE_SEPARATOR)
        magic = tokens[0]
        self.descriptor = tokens[1]
        self.key = tokens[2]
        self.token = tokens[3]
        
        if magic == MobileModelOS.IOS.magic_string:
            self.os = MobileModelOS.IOS
        elif magic == MobileModelOS.IOS_DEV.magic_string:
            self.os = MobileModelOS.IOS_DEV
        elif magic == MobileModelOS.ANDROID.magic_string:
            self.os = MobileModelOS.ANDROID
            
        self.is_content_available = self.parse_descriptor(self.descriptor)
        
        
    def parse_descriptor(self, descriptor: str) -> bool:
        # phone descriptors
        # iPod Touch 5
        # iPod Touch 6
        # iPhone 4
        # iPhone 4s
        # iPhone 5
        # iPhone 5c
        # iPhone 5s
        # iPhone 6
        # iPhone 6 Plus
        # iPhone 6s
        # iPhone 6s Plus
        # iPhone 7
        # iPhone 7 Plus
        # iPhone SE
        # iPhone 8
        # iPhone 8 Plus
        # iPhone X
        # iPhone XS
        # iPhone XS Max
        # iPhone XR
        # iPhone 11
        # iPhone 11 Pro
        # iPhone 11 Pro Max
        # iPad 2
        # iPad 3
        # iPad 4
        # iPad Air
        # iPad Air 2
        # iPad 5
        # iPad 6
        # iPad Mini
        # iPad Mini 2
        # iPad Mini 3
        # iPad Mini 4
        # iPad Pro 9.7 Inch
        # iPad Pro 12.9 Inch
        # iPad Pro 12.9 Inch 2. Generation
        # iPad Pro 10.5 Inch
        # iPhone 6 does not support isContentAvailable, iPhone 6s and 7 does.
        # We don't know about other versions, but let's assume all above iPhone 6 are ok.
        if descriptor:
            tokens = descriptor.split(" ")
            if len(tokens) >= 1:
                model = tokens[0]
                if model == "iPhone":
                    version_string = tokens[1]
                    valid_versions = ["X", "XS", "XR"]
                    if version_string in valid_versions:
                        return True
                    version_suffix = ""
                    if len(version_string) == 2 and version_string[0].isdigit() and not version_string[1].isdigit():
                        version_suffix = version_string[1:]
                        version_string = version_string[0]
                    elif len(version_string) == 3 and version_string[0:2].isdigit() and not version_string[2].isdigit():
                        version_suffix = version_string[2:]
                        version_string = version_string[0:2]
                    try:
                        version = int(version_string)
                        return version > 6 or (version == 6 and version_suffix.lower() == "s")
                    except (ValueError, TypeError):
                        pass
                else:
                    return model == "iPad" and len(tokens) > 1 and tokens[1] == "Pro"
        return False
