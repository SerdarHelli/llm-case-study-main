# BlueCloud LLM Engineer/Scientist - Veridia RAG System

A Retrieval-Augmented Generation (RAG) system for answering questions about Dr. Elara Voss's research documents on the fictional world of Veridia. This project implements a complete pipeline for PDF processing, embedding generation, vector-based retrieval, and LLM-based question answering.

## 📋 Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Project Architecture](#project-architecture)
3. [Technical Discussion](#technical-discussion)
4. [Running the System](#running-the-system)
5. [API Documentation](#api-documentation)
6. [Evaluation Results](#evaluation-results)
7. [Bonus Features](#bonus-features)

---

## Installation & Setup

### Prerequisites

- **Python**: 3.9 or higher
- **Ollama**: For running LLM inference (download from [ollama.ai](https://ollama.ai))
- **Git**: For version control

### Step 1: Environment Setup

#### Using Virtual Environment (Recommended)

```bash
# Clone or navigate to the project directory
cd llm-case-study

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Using Conda

```bash
conda create -n veridia-rag python=3.9
conda activate veridia-rag
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies Overview:**
- **pymupdf**: PDF text extraction
- **sentence-transformers**: Embedding generation (Snowflake Arctic Embed)
- **milvus**: Vector database for similarity search
- **fastapi & uvicorn**: Web API framework
- **torch**: Deep learning backend for embeddings
- **scikit-learn**: Evaluation metrics

### Step 3: Download and Setup LLM

The system uses **Ollama** to run open-source LLMs locally.

```bash
# Download and install Ollama from https://ollama.ai

# After installation, pull the recommended LLM model
ollama pull llama2:7b

# Start Ollama server (runs on localhost:11434)
ollama serve
```

**Note**: The first model pull may take 10-15 minutes. You can also use other models:
```bash
ollama pull mistral  # Alternative: Mistral 7B
ollama pull neural-chat  # Alternative: Neural Chat
```

### Step 4: Start Milvus Vector Database

```bash
# Milvus Lite will be embedded and run automatically
# It creates a local database in './milvus_data' directory
# No separate installation needed - handled by pymilvus library
```

### Step 5: Prepare Data

Process the PDF and populate the vector database:

```bash
python scripts/prepare_data.py
```

This script will:
- Extract text from `data/dr_voss_diary.pdf`
- Split text into overlapping chunks (size: 500 chars, overlap: 100 chars)
- Generate embeddings using Snowflake Arctic Embed (384-dim)
- Store chunks and embeddings in Milvus
- Save metadata to `data/metadata.json`

**Expected Output:**
```
INFO:__main__:Loading embedding model...
INFO:__main__:Extracted X characters
INFO:__main__:Created Y chunks
INFO:__main__:Generating embeddings...
INFO:__main__:Storing chunks in Milvus...
INFO:__main__:PDF processing complete!
```

---

## Project Architecture

### System Components

```
┌─────────────────┐
│  PDF Document   │
│  (Veridia)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  Document Processing Layer  │
│  - PDF Extraction           │
│  - Text Chunking            │
│  - Metadata Generation      │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Embedding Generation       │
│  (Snowflake Arctic Embed-S) │
│  384-dimensional vectors    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Vector Database (Milvus)   │
│  - Storage                  │
│  - Indexing (IVF_FLAT)      │
│  - Similarity Search        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  FastAPI Server             │
│  - Query Endpoint           │
│  - Context Retrieval        │
│  - LLM Integration          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  LLM (Ollama/Llama2)        │
│  - Answer Generation        │
│  - Context Integration      │
└─────────────────────────────┘
```

### Directory Structure

```
llm_case_study/
├── data/
│   ├── dr_voss_diary.pdf      # Source document
│   ├── questions.txt          # 55 evaluation questions
│   ├── answers.txt            # Expected answers
│   ├── metadata.json          # Processing metadata
│   └── eval_results.json      # Evaluation output
├── scripts/
│   ├── prepare_data.py        # PDF processing pipeline
│   └── eval.py                # Evaluation pipeline
├── app.py                     # FastAPI server
├── requirements.txt           # Python dependencies
└── README.md                  # Documentation
```

---

## Technical Discussion

### 1. Model Selection

#### Embedding Model: Snowflake Arctic Embed-S
**Choice**: `Snowflake/snowflake-arctic-embed-s`
**Rationale**:
- **Efficiency**: Lightweight model (384-dim) ideal for similarity search
- **Quality**: Strong semantic representation of text
- **Speed**: Fast inference for both chunking and query processing
- **Open Source**: Freely available through HuggingFace
- **Scalability**: Suitable for large-scale document repositories

**Alternative Considered**: sentence-transformers/all-MiniLM-L6-v2 (smaller, faster)

#### LLM: Llama 2 7B
**Choice**: Llama 2 7B via Ollama
**Rationale**:
- **Open Source**: Fully accessible, no API costs
- **Performance**: Good balance between quality and speed
- **Local Execution**: Privacy-preserving, no data transmission
- **Community**: Extensive support and documentation
- **Hardware**: Runs on CPU/GPU, accessible hardware

**Alternative Considered**: Mistral 7B (slightly faster), Neural Chat (specialized)

### 2. Data Processing Strategy

#### Document Chunking
- **Strategy**: Sentence-based chunking with sliding window
- **Chunk Size**: 500 characters (approximately 80-100 words)
- **Overlap**: 100 characters (20% overlap)
- **Rationale**:
  - Preserves semantic units (complete sentences)
  - Overlap helps with context continuity
  - Size balances granularity with computational efficiency
  - Allows recovery of information split across chunk boundaries

#### Text Extraction
- **Method**: PyMuPDF (fitz) for PDF parsing
- **Approach**: Page-by-page extraction with error handling
- **Preservation**: Maintains text structure and content integrity

### 3. Vector Database Design

#### Milvus Configuration
- **Index Type**: IVF_FLAT (Inverted File Flat)
- **Metric**: L2 distance (Euclidean)
- **nlist**: 128 (number of quantization buckets)
- **nprobe**: 16 (number of buckets to search)

**Design Rationale**:
- **IVF_FLAT**: Good balance between speed and accuracy
- **L2 Distance**: Standard metric for embedding similarity
- **Lightweight**: Milvus Lite sufficient for document corpus
- **Scalability**: Can handle millions of vectors if needed

#### Storage Schema
```
id (INT64, auto-increment) → Unique document ID
chunk_id (INT64) → Chunk sequence number
text (VARCHAR) → Original chunk text
embedding (FLOAT_VECTOR, 384-dim) → Text embedding
```

### 4. Retrieval System

#### Context Retrieval Pipeline
1. **Query Embedding**: Convert user question to 384-dim vector
2. **Similarity Search**: Find top-5 most similar chunks using L2 distance
3. **Context Assembly**: Combine retrieved chunks with question
4. **LLM Prompt**: Format context + question for LLM processing

#### Retrieval Parameters
- **Top-K**: 5 chunks (balance between context size and relevance)
- **Similarity Metric**: L2 distance (normalized)
- **Filtering**: No keyword-based filtering (pure semantic search)

**Optimization Potential**:
- Hybrid search (semantic + BM25 keyword matching)
- Reranking with cross-encoders
- Query expansion/reformulation

### 5. Answer Generation

#### Prompt Engineering
```
Template: "Based on the following context about Veridia, answer the question.
Context: [Retrieved Chunks]
Question: [User Question]
Answer:"
```

#### LLM Parameters
- **Temperature**: 0.7 (balance between creativity and consistency)
- **Max Tokens**: Default (controlled by model)
- **Sampling Strategy**: Nucleus sampling (default)

---

## Running the System

### 1. Start Required Services

**Terminal 1 - Start Ollama**:
```bash
ollama serve
```

**Terminal 2 - Start Milvus** (if using standalone):
```bash
# Milvus Lite handles this automatically in pymilvus
# No separate step needed
```

### 2. Run Data Preparation

```bash
python scripts/prepare_data.py
```

Expected output:
```
INFO:__main__:Loading embedding model...
INFO:__main__:Processing page 1/XX...
INFO:__main__:Created YYY chunks
INFO:__main__:PDF processing complete!
```

### 3. Start FastAPI Server

**Terminal 3**:
```bash
python app.py
```

Server runs on `http://localhost:8000`

### 4. Query the API

**Using cURL**:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the official language of Veridia?"}'
```

**Using Python**:
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"question": "What is the currency of Veridia?"}
)
print(response.json())
```

**Using FastAPI Interactive Docs**:
- Open `http://localhost:8000/docs` in your browser
- Try the `/query` endpoint with sample questions

### 5. Run Evaluation

```bash
python scripts/eval.py
```

Output:
- Prints evaluation metrics to console
- Saves detailed results to `data/eval_results.json`
- Computes: exact match, semantic similarity, entity overlap scores

---

## API Documentation

### POST /query

**Request**:
```json
{
  "question": "string"
}
```

**Response**:
```json
{
  "question": "string",
  "answer": "string",
  "source_chunks": ["string", "string"]
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is Veridia'\''s most famous historical figure?"}'
```

Response:
```json
{
  "question": "Who is Veridia's most famous historical figure?",
  "answer": "Queen Seraphina is Veridia's most famous historical figure.",
  "source_chunks": [
    "Queen Seraphina ruled during a period of great expansion...",
    "The legacy of Queen Seraphina continues to influence..."
  ]
}
```

### GET /health

**Response**:
```json
{
  "status": "ok"
}
```

---

## Evaluation Results

### Evaluation Metrics

The system is evaluated using three complementary metrics:

1. **Exact Match (EM)**: 30% weight
   - Binary: 1.0 if answer matches exactly, 0.0 otherwise
   - Case-insensitive comparison

2. **Semantic Similarity**: 50% weight
   - Cosine similarity between embeddings (range: 0-1)
   - Captures semantic equivalence even with different wording

3. **Entity/Keyword Overlap**: 20% weight
   - Jaccard similarity of key entities
   - Measures information preservation

### Expected Performance

Based on the RAG architecture and Veridia-specific content:

| Metric | Expected Score |
|--------|-----------------|
| Avg Exact Match | 0.35-0.50 |
| Avg Semantic Similarity | 0.65-0.80 |
| Avg Entity Overlap | 0.40-0.60 |
| **Overall Score** | **0.55-0.70** |
| Retrieval Success Rate | 0.90+ |

### Limitations & Challenges

1. **Small Model Constraints**: Llama 2 7B may struggle with complex reasoning
2. **Context Window**: Limited context passed to LLM (top-5 chunks)
3. **Answer Specificity**: Generic answers for out-of-domain questions
4. **Hallucination**: LLM may generate plausible-sounding but incorrect answers
5. **Chunking Artifacts**: Information split across chunks may be missed

### Improvement Strategies

1. **Larger LLM**: Use 13B or larger models for better reasoning
2. **Hybrid Retrieval**: Combine semantic + keyword-based search (BM25)
3. **Reranking**: Use cross-encoders to rerank retrieved chunks
4. **Query Expansion**: Reformulate queries to improve retrieval
5. **Few-shot Examples**: Provide in-context examples for better LLM responses
6. **Fine-tuning**: Fine-tune embedding model on Veridia-specific queries
7. **Multi-hop Reasoning**: Handle questions requiring multiple document pieces

---

## Production Considerations

### Scalability

For production deployment with larger document collections:

1. **Vector Database**: Upgrade to full Milvus cluster
2. **LLM Serving**: Use vLLM or TGI for efficient inference
3. **Caching**: Cache embeddings and frequent queries
4. **Batching**: Process multiple queries in parallel
5. **Monitoring**: Track latency, accuracy, and system health

### Security

1. **Input Validation**: Sanitize user queries
2. **Rate Limiting**: Implement API rate limiting
3. **Authentication**: Add API key authentication
4. **Logging**: Maintain audit trails without logging sensitive data
5. **Content Filtering**: Filter inappropriate responses

### Deployment

- **Docker**: Containerize for easy deployment
- **CI/CD**: Automated testing and deployment pipeline
- **Monitoring**: Track system performance and errors
- **Backup**: Regular backup of vector database

---

## Bonus Features

### Image Extraction & Multi-Modal Understanding

(Optional - to be implemented)

PDF documents may contain images with valuable information. This feature:
1. Extracts images from the PDF using PyMuPDF
2. Uses a multi-modal LLM (e.g., LLaVA) to generate text descriptions
3. Embeds descriptions alongside text chunks
4. Enables answering questions about visual content

### Dockerization

(Optional - to be implemented)

Containerize the entire system for consistent deployment:
- `Dockerfile` for the FastAPI application
- `docker-compose.yml` for orchestrating all services
- Pre-configured Ollama container with model

---

## Troubleshooting

### Milvus Connection Error
```
Error: Connection to Milvus failed
```
**Solution**: Ensure Python environment is properly set up. Milvus Lite runs embedded.

### Ollama Connection Error
```
Error: Cannot connect to LLM at http://localhost:11434
```
**Solution**: 
- Verify Ollama is running: `ollama serve`
- Check if model is downloaded: `ollama list`
- Verify port 11434 is accessible

### Out of Memory
**Solution**:
- Use smaller embedding model: `all-MiniLM-L6-v2`
- Reduce batch size in processing
- Use CPU instead of GPU (slower but less memory)

### Slow Query Response
**Solution**:
- Verify Ollama server is running and responsive
- Reduce number of retrieved chunks (top_k)
- Use faster LLM model (neural-chat)
- Optimize embedding batch size

---

## References

- [Milvus Documentation](https://milvus.io/docs)
- [Sentence Transformers](https://www.sbert.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Llama 2 Paper](https://arxiv.org/abs/2307.09288)

---

## License & Attribution

This project is developed as part of the BlueCloud LLM Engineer/Scientist coding challenge.

**Key Technologies Used**:
- Open source LLM: Llama 2 (Meta)
- Embedding model: Snowflake Arctic Embed
- Vector database: Milvus (LF AI & Data)
- Web framework: FastAPI

---

## Author Notes

This RAG system demonstrates:
- End-to-end RAG pipeline from PDF to LLM
- Vector database design and optimization
- Prompt engineering and context management
- Comprehensive evaluation methodology
- Production-ready code structure

For questions or improvements, refer to the evaluation results and architectural decisions documented above.
