from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.redis import redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_pool.aclose()


app = FastAPI(
    title="Matrix — Competency Matrix Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_handler(request: Request, exc):
    return JSONResponse(status_code=401, content={"detail": "Not authenticated"})


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_handler(request: Request, exc):
    return JSONResponse(status_code=403, content={"detail": "Forbidden"})
