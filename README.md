# BlueCloud 

A complete Retrieval-Augmented Generation (RAG) pipeline for processing and querying Dr. Elara Voss's research documents using LLMs.

## System Architecture

The Veridia RAG system combines:
- **PDF Processing**: PyMuPDF for document extraction
- **Embeddings**: Sentence Transformers (Snowflake Arctic Embed)
- **Vector Database**: Milvus Lite for semantic search
- **LLM**: vLLM with Llama-2-7b-hf for inference
- **API**: FastAPI for REST endpoints

## Prerequisites

- Docker & Docker Compose
- GPU with CUDA support (RTX series recommended)
- 16GB+ VRAM for optimal performance
- Valid HuggingFace token (for Llama-2 access)

## Quick Setup

### 1. Configure Environment Variables

Edit `.env` file with your HuggingFace token:

```bash
HUGGING_FACE_HUB_TOKEN="hf_your_token_here"
```

To get a token:
1. Visit https://huggingface.co/settings/tokens
2. Create a new token with read permissions
3. Accept the Llama-2-7b-hf license at https://huggingface.co/meta-llama/Llama-2-7b-hf

### 2. Build Docker Images

```bash
cd /root/llm-case-study-main
DOCKER_BUILDKIT=0 docker build -t llm-case-study-main_api .
```

### 3. Start Services

```bash
docker-compose up -d
```

This starts:
- **vLLM API** (port 8001): LLM inference server
- **Veridia API** (port 8000): RAG backend

### 4. Wait for Initialization

The vLLM container will take 5-15 minutes to download and load the model. Monitor progress:

```bash
docker logs veridia-vllm -f
docker logs veridia-rag-api -f
```

Check API health:

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

## Usage

### Health Check

```bash
curl http://localhost:8000/health
```

### Query the RAG System

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Veridia?"}'
```

Response format:
```json
{
  "answer": "...",
  "source_chunks": [
    {"text": "...", "similarity": 0.95}
  ]
}
```

## Evaluation

### Run Evaluation Tests

```bash
python scripts/prepare_data.py
python scripts/eval.py
```

This runs:
- BLEU score evaluation
- ROUGE metrics
- Retrieval similarity scores
- Custom metrics on known Q&A pairs

Evaluation data located in:
- `data/questions.txt` - Test questions
- `data/answers.txt` - Expected answers



## Project Structure

```
├── app.py                 # FastAPI application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image definition
├── docker-compose.yml    # Multi-container orchestration
├── entrypoint.sh         # Container startup script
├── scripts/
│   ├── prepare_data.py   # Data preparation & chunking
│   ├── eval.py           # Evaluation metrics
│   └── extract_images.py # Image extraction from PDFs
└── data/
    ├── dr_voss_diary.pdf # Research document
    ├── questions.txt     # Evaluation questions
    └── answers.txt       # Expected answers
```

## Configuration

Key settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | Snowflake/snowflake-arctic-embed-s | Embedding model |
| `LLM_BASE_URL` | http://vllm:8000/v1 | vLLM API endpoint |
| `LLM_MODEL` | meta-llama/Llama-2-7b-hf | LLM model |
| `TOP_K` | 5 | Retrieval results count |
| `CHUNK_SIZE` | 500 | Document chunk size |
| `CHUNK_OVERLAP` | 100 | Chunk overlap for context |
| `GPU_MEMORY_UTILIZATION` | 0.7 | GPU memory allocation |

## Troubleshooting

### vLLM Container Fails to Start

**Error**: `ValueError: Free memory on device is less than desired GPU memory utilization`

**Solution**: Reduce `gpu_memory_utilization` in `docker-compose.yml`:
```yaml
--gpu-memory-utilization 0.5
```

### milvus-lite Module Not Found

**Solution**: Rebuild the API container:
```bash
docker-compose down
DOCKER_BUILDKIT=0 docker build -t llm-case-study-main_api .
docker-compose up -d
```

### CUDA Compatibility Warning

**Warning**: `sm_120 is not compatible with current PyTorch installation`

**Note**: This is a compatibility warning for RTX 5070 GPUs. The system will still work but with reduced performance. To suppress, use a PyTorch build with sm_120 support.

### Slow Model Loading

**Expected**: First-time model load takes 10-15 minutes. Subsequent starts use cached weights (~1-2 minutes).

Monitor progress:
```bash
docker logs veridia-vllm -f | grep "Loading"
```

## API Endpoints

### Health Check
- **GET** `/health` - System health status

### Query
- **POST** `/query` - Query the RAG system
  - Body: `{"question": "string"}`
  - Response: `{"answer": "string", "source_chunks": [...]}`

## Development

### Install Locally

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```


## Performance Notes

- **Embedding**: ~50ms per document
- **Retrieval**: ~10ms for vector search
- **LLM Inference**: ~2-5s per query depending on response length
- **Total Query Latency**: ~2-6 seconds

## Known Limitations

1. **Model Size**: Llama-2-7b requires ~16GB VRAM
2. **Network**: Requires internet for initial model download from HuggingFace
3. **Chunk Size**: Fixed 500 tokens
4. **Batch Size**: Single query processing; implement queue for production


## Support

For issues or questions, check:
1. Docker container logs: `docker logs veridia-rag-api`
2. System requirements: GPU with CUDA, 16GB+ VRAM
3. Network connectivity: HuggingFace token validity
