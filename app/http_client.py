import httpx

from app.config import settings

client: httpx.AsyncClient | None = None


async def open_http_client() -> None:
    global client
    client = httpx.AsyncClient(
        base_url=settings.WORK_URL.rstrip("/"),
        timeout=settings.HTTP_TIMEOUT,
    )


async def close_http_client() -> None:
    if client is not None:
        await client.aclose()


def get_http_client() -> httpx.AsyncClient:
    if client is None:
        raise RuntimeError("HTTP client is not initiated. Did the app startup run?")
    return client