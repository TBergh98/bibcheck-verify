import time
from typing import Any

import httpx


class RequestBudgetExceeded(RuntimeError):
    pass


class ApiClient:
    def __init__(self, max_requests: int = 2000, mailto: str | None = None, timeout: float = 20.0,
                 client: httpx.Client | None = None):
        self.max_requests = max_requests
        self.requests = 0
        self.mailto = mailto
        self.client = client or httpx.Client(timeout=timeout)

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.requests >= self.max_requests:
            raise RequestBudgetExceeded("maximum request budget exceeded")
        headers = {"User-Agent": f"bibcheck-verify/0.1.0 ({self.mailto})" if self.mailto else "bibcheck-verify/0.1.0"}
        for attempt in range(4):
            self.requests += 1
            response = self.client.get(url, params=params, headers=headers)
            if response.status_code != 429:
                response.raise_for_status()
                return response.json()
            if attempt == 3:
                response.raise_for_status()
            time.sleep(2**attempt)
        raise RuntimeError("unreachable")
