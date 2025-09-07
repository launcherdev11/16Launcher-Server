from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import versions
from .dependencies import get_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    mongodb = await get_database()
    yield
    await mongodb.disconnect()


app = FastAPI(
    title="16Launcher",
    version="1.0.2",
    lifespan=lifespan
)

app.include_router(versions.router, prefix="/minecraft", tags=["Items"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"version": "1.0.2"}
