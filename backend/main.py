import os
from dotenv import load_dotenv

# Load .env before importing routes — route modules evaluate SECRET_KEY and
# other env vars at import time, so load_dotenv must run first.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.conversations import router as conversations_router
from routes.projects import router as projects_router
from routes.articles import router as articles_router

load_dotenv()

app = FastAPI(title="RAG Article API")

# Allow the React dev server (port 5173) and production frontend to hit this API.
# In production, Nginx handles routing so the frontend and API share the same origin —
# but during local dev the React server runs on a different port, so CORS is needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Production-like local test
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(chat_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(articles_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
