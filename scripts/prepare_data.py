#!/usr/bin/env python3

import os
import json
import pymupdf
import numpy as np
from pathlib import Path
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-s")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_chunks")
DB_FILE = os.getenv("DB_FILE", "milvus_lite.db")

class PDFProcessor:
    def __init__(self, embedding_model: str = EMBEDDING_MODEL, db_file: str = DB_FILE):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.client = MilvusClient(db_file)
        logger.info(f"Loaded embedding model with dimension: {self.embedding_dim}")
        logger.info(f"Initialized MilvusClient with db file: {db_file}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        logger.info(f"Extracting text from {pdf_path}")
        doc = pymupdf.open(pdf_path)
        text = ""
        for page_num, page in enumerate(doc):
            logger.info(f"Processing page {page_num + 1}/{len(doc)}")
            text += page.get_text()
        doc.close()
        return text
    
    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, 
                   overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks."""
        logger.info(f"Chunking text with size={chunk_size}, overlap={overlap}")
        sentences = text.split('.')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts."""
        logger.info(f"Generating embeddings for {len(texts)} chunks")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings
    
    def setup_collection(self) -> None:
        """Setup Milvus Lite collection."""
        logger.info(f"Setting up collection: {COLLECTION_NAME}")
        
        if self.client.has_collection(COLLECTION_NAME):
            logger.info(f"Dropping existing collection {COLLECTION_NAME}")
            self.client.drop_collection(COLLECTION_NAME)
        
        logger.info(f"Creating collection {COLLECTION_NAME}")
        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            dimension=self.embedding_dim,
            metric_type="L2"
        )
        logger.info(f"Collection {COLLECTION_NAME} created successfully")
    
    def store_chunks_in_milvus(self, chunks: List[str], embeddings: np.ndarray) -> None:
        """Store chunks and embeddings in Milvus Lite."""
        logger.info(f"Storing {len(chunks)} chunks in Milvus Lite")
        
        data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            data.append({
                "id": i,
                "vector": embedding.tolist(),
                "text": chunk
            })
        
        res = self.client.insert(
            collection_name=COLLECTION_NAME,
            data=data
        )
        logger.info(f"Inserted {len(data)} documents. Response: {res}")
    
    def save_metadata(self, chunks: List[str], output_path: str = "data/metadata.json") -> None:
        """Save metadata about chunks."""
        logger.info(f"Saving metadata to {output_path}")
        metadata = {
            "total_chunks": len(chunks),
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": self.embedding_dim,
            "collection_name": COLLECTION_NAME,
            "db_file": DB_FILE,
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Metadata saved")

def main():
    pdf_path = "data/dr_voss_diary.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF not found at {pdf_path}")
        return
    
    processor = PDFProcessor()
    
    text = processor.extract_text_from_pdf(pdf_path)
    logger.info(f"Extracted {len(text)} characters")
    
    chunks = processor.chunk_text(text)
    
    embeddings = processor.generate_embeddings(chunks)
    
    processor.setup_collection()
    processor.store_chunks_in_milvus(chunks, embeddings)
    
    processor.save_metadata(chunks)
    
    logger.info("PDF processing complete!")

if __name__ == "__main__":
    main()
