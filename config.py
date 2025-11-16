#!/usr/bin/env python3

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration for the Veridia RAG system."""
    
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-s")
    EMBEDDING_DIM = 384
    
    MILVUS_HOST = os.getenv("MILVUS_HOST", "127.0.0.1")
    MILVUS_PORT = int(os.getenv("MILVUS_PORT", 19530))
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_chunks")
    
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama2:7b")
    LLM_TEMPERATURE = 0.7
    LLM_TIMEOUT = 60
    
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
    TOP_K = int(os.getenv("TOP_K", 5))
    
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    API_DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    DATA_DIR = "data"
    PDF_PATH = os.path.join(DATA_DIR, "dr_voss_diary.pdf")
    QUESTIONS_PATH = os.path.join(DATA_DIR, "questions.txt")
    ANSWERS_PATH = os.path.join(DATA_DIR, "answers.txt")
    METADATA_PATH = os.path.join(DATA_DIR, "metadata.json")
    IMAGES_DIR = os.path.join(DATA_DIR, "images")
    
    @classmethod
    def get_config_dict(cls):
        """Return configuration as dictionary."""
        return {
            "embedding_model": cls.EMBEDDING_MODEL,
            "embedding_dim": cls.EMBEDDING_DIM,
            "milvus_host": cls.MILVUS_HOST,
            "milvus_port": cls.MILVUS_PORT,
            "collection_name": cls.COLLECTION_NAME,
            "llm_base_url": cls.LLM_BASE_URL,
            "llm_model": cls.LLM_MODEL,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "top_k": cls.TOP_K,
        }
    
    @classmethod
    def print_config(cls):
        """Print current configuration."""
        print("\n" + "="*60)
        print("VERIDIA RAG SYSTEM CONFIGURATION")
        print("="*60)
        for key, value in cls.get_config_dict().items():
            print(f"{key:<20} : {value}")
        print("="*60 + "\n")
