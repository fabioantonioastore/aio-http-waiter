import asyncio
from typing import Any, Self

import aiohttp
import aiohttp_retry


RETRY_STATUS_CODE = {408, 429, 503, 504}


class WaiterClient:
    def __init__(
        self,
        base_url: str | None = None,
        attempts: int = 0,
        statuses: set[int] = RETRY_STATUS_CODE,
    ) -> None:
        self.__session: aiohttp.ClientSession | None = None
        self._base_url = base_url
        self._retry_options = aiohttp_retry.ExponentialRetry(
            attempts=attempts, statuses=statuses
        )
        self._retry_client: aiohttp_retry.RetryClient | None = None
        self.__lock = asyncio.Lock()

    @property
    def base_url(self) -> str | None:
        return self._base_url

    async def __aenter__(self) -> Self:
        await self._create_session()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self.__session is not None and not self.__session.closed:
            await self.__session.close()
        if self._retry_client is not None:
            await self._retry_client.close()

    async def _create_session(self) -> aiohttp.ClientSession:
        async with self.__lock:
            if self.__session is None or self.__session.closed:
                self.__session = aiohttp.ClientSession(base_url=self._base_url)
        return self.__session

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.__session is not None and not self.__session.closed:
            return self.__session
        return await self._create_session()

    async def _create_retry_client(self) -> aiohttp_retry.RetryClient:
        async with self.__lock:
            if self._retry_client is None:
                session = await self._get_session()
                self._retry_client = aiohttp_retry.RetryClient(
                    client_session=session, retry_options=self._retry_options
                )
        return self._retry_client

    async def _get_retry_client(self) -> aiohttp_retry.RetryClient:
        if self._retry_client is not None:
            return self._retry_client
        return await self._create_retry_client()

    async def request(
        self, method: str, url: str, **kwargs: Any
    ) -> aiohttp.ClientResponse:
        retry_client = await self._get_retry_client()
        return await retry_client.request(method=method, url=url, **kwargs)

    async def get(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.request(method="GET", url=url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.request(method="POST", url=url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.request(method="PUT", url=url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.request(method="PATCH", url=url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self.request(method="DELETE", url=url, **kwargs)
