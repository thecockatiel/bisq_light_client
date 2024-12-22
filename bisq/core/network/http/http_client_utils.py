from typing import Optional
from urllib.parse import ParseResult, urlparse


def parse_and_validate_url(url: Optional[str]) -> Optional[ParseResult]:
    """returns the parsed url if it is valid http url, otherwise returns None"""
    if not url:
        return None

    parsed = urlparse(url)
    if not all([parsed.scheme, parsed.netloc]):
        return None

    if parsed.scheme not in ["http", "https"]:
        return None

    return parsed
