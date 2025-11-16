#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import json
import os
import requests
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "Snowflake/snowflake-arctic-embed-s"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = 19530
COLLECTION_NAME = "pdf_chunks"
LLM_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama2:7b"
TOP_K = 5

app = FastAPI(title="Veridia RAG API", description="RAG system for Dr. Voss's Veridia research")

embedding_model = None
collection = None

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    source_chunks: Optional[List[str]] = None

def initialize_models():
    """Initialize embedding model and Milvus connection."""
    global embedding_model, collection
    
    logger.info("Initializing models and database connections...")
    
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
    
    try:
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        collection = Collection(COLLECTION_NAME)
        collection.load()
        logger.info(f"Connected to Milvus collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Error connecting to Milvus: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    initialize_models()

def retrieve_context(question: str, top_k: int = TOP_K) -> tuple[List[str], List[float]]:
    """Retrieve relevant chunks from Milvus."""
    logger.info(f"Retrieving context for question: {question}")
    
    question_embedding = embedding_model.encode([question])[0]
    
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 16}
    }
    
    results = collection.search(
        data=[question_embedding.tolist()],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["text"]
    )
    
    chunks = []
    distances = []
    
    for hits in results:
        for hit in hits:
            chunks.append(hit.entity.get("text"))
            distances.append(hit.distance)
    
    logger.info(f"Retrieved {len(chunks)} relevant chunks")
    return chunks, distances

def generate_answer(question: str, context: List[str]) -> str:
    """Generate answer using LLM with retrieved context."""
    logger.info("Generating answer using LLM...")
    
    context_text = "\n\n".join(context)
    
    prompt = f"""Based on the following context about Veridia, answer the question.

Context:
{context_text}

Question: {question}

Answer:"""
    
    try:
        response = requests.post(
            f"{LLM_BASE_URL}/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("response", "").strip()
            logger.info("Answer generated successfully")
            return answer
        else:
            logger.error(f"LLM API error: {response.status_code}")
            return "Unable to generate answer at this time."
    
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to LLM at {LLM_BASE_URL}")
        return "LLM service is not available. Make sure Ollama is running."
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return f"Error generating answer: {str(e)}"

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Process a query and return an answer based on retrieved context."""
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        chunks, distances = retrieve_context(request.question)
        
        if not chunks:
            return QueryResponse(
                question=request.question,
                answer="No relevant information found in the knowledge base.",
                source_chunks=[]
            )
        
        answer = generate_answer(request.question, chunks)
        
        return QueryResponse(
            question=request.question,
            answer=answer,
            source_chunks=chunks[:2]
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
