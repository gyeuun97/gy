"""표준 라이브러리만 쓰는 얇은 HTTP 헬퍼."""

import json
import urllib.error
import urllib.request
from typing import Dict, Optional

DEFAULT_TIMEOUT = 15


class FetchError(RuntimeError):
    """HTTP 요청이 실패했을 때. status 로 원인을 구분한다."""

    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


def get_json(url: str, headers: Dict[str, str], timeout: int = DEFAULT_TIMEOUT) -> dict:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        raise FetchError(f"HTTP {exc.code} - {body}", status=exc.code) from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"연결 실패: {exc.reason}") from exc
