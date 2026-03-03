"""Cliente assíncrono para a API Siconfi — RGF, RREO e DCA."""
import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

logger = logging.getLogger(__name__)

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
ENDPOINTS = {
    "rgf":  f"{BASE_URL}/rgf",
    "rreo": f"{BASE_URL}/rreo",
    "dca":  f"{BASE_URL}/dca",
}


class SiconfiClient:
    """
    Sessão HTTP compartilhada para todas as requisições da pipeline.

    Uso:
        async with SiconfiClient(max_concurrent=12) as client:
            items = await client.get("rgf", params)
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        request_delay: float = 1.0,
    ):
        self.max_concurrent = max_concurrent
        self.timeout = ClientTimeout(total=timeout_seconds)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: aiohttp.ClientSession | None = None
        self._semaphore: asyncio.Semaphore | None = None

    async def __aenter__(self) -> "SiconfiClient":
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={"Accept": "application/json"},
        )
        return self

    async def __aexit__(self, *_) -> None:
        if self._session:
            await self._session.close()

    async def get(self, relatorio: str, params: dict[str, Any]) -> list[dict]:
        """GET com retry exponencial. Retorna [] em caso de falha definitiva."""
        url = ENDPOINTS[relatorio]
        for attempt in range(1, self.max_retries + 1):
            try:
                async with self._semaphore:
                    async with self._session.get(url, params=params) as resp:
                        resp.raise_for_status()
                        data = await resp.json(content_type=None)
                        return data.get("items", [])
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning("Tentativa %d/%d | %s %s: %s",
                               attempt, self.max_retries, relatorio, params, exc)
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * attempt)
                else:
                    logger.error("Falha definitiva | %s %s", relatorio, params)
                    return []