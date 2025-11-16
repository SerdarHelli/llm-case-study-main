# Bonus Features Documentation

This document describes the optional bonus features implemented in the Veridia RAG system.

## 1. Image Extraction & Multi-Modal Understanding

### Overview

PDF documents often contain images, diagrams, and charts with valuable information. This feature extracts images from the PDF and integrates them into the knowledge base through text descriptions.

### Implementation

#### Image Extraction Script

Located in: `scripts/extract_images.py`

**Features**:
- Extracts all images from the PDF document
- Saves images to `data/images/` directory
- Preserves color information and handles transparency
- Generates metadata about image locations and properties

**Usage**:
```bash
python scripts/extract_images.py
```

**Output**:
- Extracted images: `data/images/page_X_image_Y.png`
- Metadata: `data/images_metadata.json`

#### Image Metadata Structure

```json
{
  "page": 1,
  "image_index": 1,
  "file_path": "data/images/page_1_image_1.png",
  "description": ""
}
```

### Generating Image Descriptions

To generate text descriptions for images using a multi-modal LLM, integrate with models like:

#### Option 1: LLaVA (LLaMA Vision Assistant)

```bash
# Pull LLaVA model from Ollama
ollama pull llava:7b

# Use in Python
import requests
import base64

def describe_image(image_path):
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llava:7b",
            "prompt": "Describe this image in detail:",
            "images": [image_base64],
            "stream": False
        }
    )
    
    return response.json()["response"]
```

#### Option 2: GPT-4V (if API access available)

```python
import openai
import base64

def describe_image_gpt4v(image_path):
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode()
    
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail:"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    )
    
    return response.choices[0].message["content"]
```

### Integration into RAG Pipeline

After generating descriptions, integrate them into the knowledge base:

```python
# 1. Generate descriptions for all images
for image_info in images_metadata:
    image_path = image_info["file_path"]
    description = describe_image(image_path)
    image_info["description"] = description

# 2. Create text chunks from descriptions
description_chunks = [info["description"] for info in images_metadata]

# 3. Generate embeddings and store in Milvus
# Same process as document chunks
embeddings = embedding_model.encode(description_chunks)
collection.insert({
    "chunk_id": chunk_ids,
    "text": description_chunks,
    "embedding": embeddings.tolist(),
    "source_type": "image"
})
```

### Benefits

- **Visual Information**: Capture information from diagrams, charts, maps
- **Multi-modal Context**: Combine text and visual understanding
- **Enhanced Retrieval**: Image descriptions improve semantic search
- **Accessibility**: Make visual content searchable and accessible

---

## 2. Dockerization

### Overview

Containerize the entire RAG system for consistent deployment across environments.

### Components

#### Dockerfile

Located in: `Dockerfile`

**Features**:
- Python 3.9 slim base image
- All dependencies pre-installed
- Health check included
- Optimized for production

**Build**:
```bash
docker build -t veridia-rag:latest .
```

**Run**:
```bash
docker run -p 8000:8000 veridia-rag:latest
```

#### Docker Compose

Located in: `docker-compose.yml`

**Services**:
1. **api**: FastAPI application
2. **milvus**: Vector database
3. **ollama**: LLM inference service

**Features**:
- Complete system orchestration
- Service networking
- Volume persistence
- Environment configuration

### Quick Start with Docker Compose

#### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)

#### Setup

1. **Build and start all services**:
```bash
docker-compose up -d
```

2. **Download LLM model** (first time only):
```bash
docker exec veridia-ollama ollama pull llama2:7b
```

3. **Prepare data**:
```bash
docker exec veridia-rag-api python scripts/prepare_data.py
```

4. **Query the API**:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the official language of Veridia?"}'
```

### Docker Networking

```
┌─────────────────┐
│   Host System   │
│  (port 8000)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│   Docker Network            │
│   veridia-network           │
├─────────────┬───────────────┤
│             │               │
▼             ▼               ▼
api      milvus            ollama
8000     19530             11434
```

### Data Persistence

```
Host System         Docker Containers
───────────────────────────────────────
data/        ────→ /app/data (api)
logs/        ────→ /app/logs (api)
milvus_data/ ────→ /var/lib/milvus (milvus)
ollama_data/ ────→ /root/.ollama (ollama)
```

### Useful Docker Commands

#### View logs
```bash
docker-compose logs api
docker-compose logs milvus
docker-compose logs ollama
docker-compose logs -f api  # Follow logs
```

#### Access container
```bash
docker exec -it veridia-rag-api bash
docker exec -it veridia-milvus bash
```

#### Stop services
```bash
docker-compose down
```

#### Stop and remove volumes
```bash
docker-compose down -v
```

#### Rebuild after code changes
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Kubernetes Deployment (Advanced)

For production-grade deployment, convert to Kubernetes manifests:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: veridia-rag-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: veridia-rag-api
  template:
    metadata:
      labels:
        app: veridia-rag-api
    spec:
      containers:
      - name: api
        image: veridia-rag:latest
        ports:
        - containerPort: 8000
        env:
        - name: MILVUS_HOST
          value: "milvus-service"
        - name: LLM_BASE_URL
          value: "http://ollama-service:11434"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

### Performance Optimization

#### For Docker
- Use multi-stage builds to reduce image size
- Implement caching strategies for dependencies
- Use Alpine-based images for smaller footprint
- Monitor resource usage and set appropriate limits

#### For Production
```dockerfile
FROM python:3.9-slim as builder
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.9-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
# ... rest of Dockerfile
```

---

## Implementation Roadmap

### Phase 1: Current Implementation ✅
- [x] Image extraction from PDF
- [x] Basic Dockerization
- [x] Docker Compose setup

### Phase 2: Recommended Enhancements
- [ ] Multi-modal LLM integration (LLaVA)
- [ ] Automatic image description generation
- [ ] Image metadata enrichment
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline integration

### Phase 3: Advanced Features (Future)
- [ ] OCR for text in images
- [ ] Diagram/flowchart understanding
- [ ] Table extraction from images
- [ ] Multi-modal hybrid search
- [ ] Custom model fine-tuning

---

## Testing Bonus Features

### Image Extraction Test

```python
# Test script: test_image_extraction.py
from scripts.extract_images import ImageExtractor
import os

extractor = ImageExtractor()
images = extractor.extract_images_from_pdf("data/dr_voss_diary.pdf")

assert len(images) > 0, "No images extracted"
assert all(os.path.exists(img["file_path"]) for img in images), "Some image files not found"
print(f"✓ Successfully extracted {len(images)} images")
```

### Docker Build Test

```bash
# Build image
docker build -t veridia-rag:test .

# Test image runs
docker run --rm veridia-rag:test python -c "print('Image works!')"

# Test health check
docker run -d -p 8000:8000 --name test-api veridia-rag:test
sleep 5
curl http://localhost:8000/health
docker stop test-api
```

---

## Troubleshooting Bonus Features

### Image Extraction Issues

**Problem**: No images extracted
- **Solution**: Verify PDF contains images (some PDFs have images as part of text)
- Check file permissions on output directory

**Problem**: Image quality is poor
- **Solution**: Increase resolution in pymupdf (default is 72 DPI)

### Docker Issues

**Problem**: Container won't start
- **Solution**: Check logs: `docker-compose logs api`
- Verify port 8000 is not in use

**Problem**: Milvus connection timeout
- **Solution**: Ensure Milvus container is running: `docker-compose ps`
- Wait for Milvus to initialize (30-60 seconds)

**Problem**: Out of memory
- **Solution**: Increase Docker desktop memory allocation
- Reduce model size (use 7B instead of 13B)

---

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [LLaVA GitHub Repository](https://github.com/haotian-liu/LLaVA)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
