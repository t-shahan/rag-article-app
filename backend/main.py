import os
from dotenv import load_dotenv

# Load .env before importing routes — route modules evaluate SECRET_KEY and
# other env vars at import time, so load_dotenv must run first.
load_dotenv()

# Fail fast if required secrets are missing — better a clear startup error than
# a silent security hole (e.g. JWT signing with a default key).
if not os.getenv("JWT_SECRET_KEY"):
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is required but not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from limiter import limiter
from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.conversations import router as conversations_router
from routes.projects import router as projects_router
from routes.articles import router as articles_router

app = FastAPI(title="RAG Article API")

# Attach the rate limiter state so slowapi can find it on the app instance
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Allow the React dev server (port 5173) and production-like local test.
# In production, Nginx proxies everything so frontend and API share an origin —
# CORS is only needed for local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(articles_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
