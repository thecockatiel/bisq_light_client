from typing import Any


class HttpResponseError(Exception):
    def __init__(
        self,
        error: Any,
        status: int,
        response_text: str,
        url: str,
        duration_ms: int,
        request_params: Any,
    ):
        super().__init__(error)
        self.status = status
        self.response_text = response_text
        self.url = url
        self.duration_ms = duration_ms
        self.request_params = request_params

    def __str__(self):
        return f"Received errorMsg '{self.response_text}' with responseCode {self.status} from {self.url}. Response took: {self.duration_ms} ms. params: {self.request_params}"
