from collections.abc import Iterable
import ssl

import httpx
import truststore

from app.core.config import get_settings
from app.core.exceptions import (
    PublishAuthenticationError,
    PublishPermissionError,
    PublishTargetConfigurationError,
    PublishTimeoutError,
    PublishUploadError,
)


class RemoteHttpPublisher:
    retry_statuses = {429, 500, 502, 503, 504}

    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self.transport = transport

    def client(self) -> httpx.Client:
        settings = get_settings()
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return httpx.Client(
            timeout=httpx.Timeout(
                settings.publish_operation_timeout_seconds,
                connect=settings.publish_connection_timeout_seconds,
            ),
            verify=ssl_context,
            transport=self.transport,
            follow_redirects=True,
        )

    def request(
        self, client: httpx.Client, method: str, url: str, *, expected: Iterable[int] = (200,),
        operation: str = "远程请求", **kwargs: object,
    ) -> httpx.Response:
        expected_codes = set(expected)
        response: httpx.Response | None = None
        for attempt in range(3):
            try:
                response = client.request(method, url, **kwargs)
            except httpx.TimeoutException as exc:
                if attempt == 2:
                    raise PublishTimeoutError(f"{operation}超时") from exc
                continue
            except httpx.HTTPError as exc:
                if attempt == 2:
                    raise PublishUploadError(f"{operation}失败") from exc
                continue
            if response.status_code in expected_codes:
                return response
            if response.status_code in self.retry_statuses and attempt < 2:
                continue
            break
        assert response is not None
        if response.status_code == 401:
            raise PublishAuthenticationError(f"{operation}认证失败")
        if response.status_code == 403:
            raise PublishPermissionError(f"{operation}没有权限")
        if response.status_code == 404:
            raise PublishTargetConfigurationError(f"{operation}目标不存在")
        raise PublishUploadError(f"{operation}失败（HTTP {response.status_code}）")
