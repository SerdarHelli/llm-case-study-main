#!/usr/bin/env python3

import os
import json
import pymupdf
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "Snowflake/snowflake-arctic-embed-s"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = 19530
COLLECTION_NAME = "pdf_chunks"

class PDFProcessor:
    def __init__(self, embedding_model: str = EMBEDDING_MODEL):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Loaded embedding model with dimension: {self.embedding_dim}")
    
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
    
    def setup_milvus(self) -> Collection:
        """Setup Milvus collection."""
        logger.info(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        
        # Drop existing collection if it exists
        try:
            Collection.drop(COLLECTION_NAME)
            logger.info(f"Dropped existing collection {COLLECTION_NAME}")
        except:
            pass
        
        # Create new collection
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="chunk_id", dtype=DataType.INT64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
        ]
        
        schema = CollectionSchema(fields=fields, description="PDF chunks collection")
        collection = Collection(name=COLLECTION_NAME, schema=schema)
        
        # Create index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        logger.info(f"Created Milvus collection: {COLLECTION_NAME}")
        return collection
    
    def store_chunks_in_milvus(self, collection: Collection, chunks: List[str], 
                               embeddings: np.ndarray) -> None:
        """Store chunks and embeddings in Milvus."""
        logger.info(f"Storing {len(chunks)} chunks in Milvus")
        
        data = {
            "chunk_id": list(range(len(chunks))),
            "text": chunks,
            "embedding": embeddings.tolist()
        }
        
        collection.insert(data)
        collection.flush()
        logger.info("Chunks stored and flushed to Milvus")
    
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
    
    # Extract text
    text = processor.extract_text_from_pdf(pdf_path)
    logger.info(f"Extracted {len(text)} characters")
    
    # Chunk text
    chunks = processor.chunk_text(text)
    
    # Generate embeddings
    embeddings = processor.generate_embeddings(chunks)
    
    # Setup Milvus and store
    collection = processor.setup_milvus()
    processor.store_chunks_in_milvus(collection, chunks, embeddings)
    
    # Save metadata
    processor.save_metadata(chunks)
    
    logger.info("PDF processing complete!")

if __name__ == "__main__":
    main()
