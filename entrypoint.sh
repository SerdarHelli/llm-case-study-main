#!/bin/bash
set -e

echo "=== Starting Veridia RAG System ==="

pip install -q milvus-lite 2>/dev/null || true

if [ ! -f "milvus_lite.db" ]; then
    echo "Database not found. Preparing data..."
    python scripts/prepare_data.py
else
    echo "Database already exists. Skipping data preparation."
fi

echo "Starting FastAPI application..."
exec python app.py
