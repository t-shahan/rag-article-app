# Build context is the project root (set in docker-compose.yml) so we can
# reach both backend/ and src/ in a single COPY.

FROM python:3.11-slim

WORKDIR /app

# Dependencies first — cached layer, only rebuilds when requirements change
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Copy rag_chain.py — the backend routes add /src to sys.path at runtime.
# In the container that resolves to this location.
COPY src/ /src

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
