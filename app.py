#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-s")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_chunks")
DB_FILE = os.getenv("DB_FILE", "milvus_lite.db")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:8001/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Llama-2-7b-hf")
TOP_K = int(os.getenv("TOP_K", "5"))

app = FastAPI(title="Veridia RAG API", description="RAG system for Dr. Voss's Veridia research")

embedding_model = None
client = None

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question: str
    answer: str
    source_chunks: Optional[List[str]] = None

def initialize_models():
    """Initialize embedding model and Milvus Lite client."""
    global embedding_model, client
    
    logger.info("Initializing models and database connections...")
    
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")
    
    client = MilvusClient(DB_FILE)
    logger.info(f"Initialized MilvusClient with db file: {DB_FILE}")

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    initialize_models()

def retrieve_context(question: str, top_k: int = TOP_K) -> tuple[List[str], List[float]]:
    """Retrieve relevant chunks from Milvus Lite."""
    logger.info(f"Retrieving context for question: {question}")
    
    question_embedding = embedding_model.encode([question])[0]
    
    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[question_embedding.tolist()],
        limit=top_k,
        output_fields=["text"]
    )
    
    chunks = []
    distances = []
    
    if results and len(results) > 0:
        for hit in results[0]:
            chunks.append(hit["entity"]["text"])
            distances.append(hit["distance"])
    
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
        client = OpenAI(api_key="not-needed", base_url=LLM_BASE_URL)
        response = client.completions.create(
            model=LLM_MODEL,
            prompt=prompt,
            temperature=0.7,
            max_tokens=512,
            timeout=60
        )
        answer = response.choices[0].text.strip()
        logger.info("Answer generated successfully")
        return answer
    
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
