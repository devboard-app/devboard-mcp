import app.tools.tickets  # noqa
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.exception_handlers import register_exception_handlers
from app.http_client import close_http_client, open_http_client
from app.mcp_server import mcp
from app.redis_client import close_redis, open_redis

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
mcp_app = mcp.streamable_http_app(stateless_http=True, json_response=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_http_client()
    await open_redis()
    async with mcp.session_manager.run():
        yield
    await close_redis()
    await close_http_client()


app = FastAPI(title="Devboard MCP Service", lifespan=lifespan)
register_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "ok"}


app.mount("/", mcp_app)
