# Development Guide - Veridia RAG System

This guide is for developers who want to contribute to or extend the Veridia RAG system.

---

## Development Environment Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd llm-case-study-main
```

### 2. Create Development Environment
```bash
# Python environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies with dev tools
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

### 3. Configure IDE

#### VSCode Settings (.vscode/settings.json)
```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "[python]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "ms-python.python"
    }
}
```

---

## Project Architecture Overview

### Module Organization

```
llm-case-study/
├── core/                      # Core functionality (future)
│   ├── __init__.py
│   ├── embedding.py          # Embedding operations
│   ├── retrieval.py          # Retrieval logic
│   └── generation.py         # LLM generation
├── models/                    # Data models (future)
│   └── schemas.py            # Request/response schemas
├── utils/                     # Utilities (future)
│   ├── logger.py            # Logging configuration
│   └── metrics.py           # Evaluation metrics
└── tests/                     # Test suite
    ├── test_prepare_data.py
    ├── test_app.py
    └── test_eval.py
```

### Current Dependencies Map

```
requests → LLM Service (Ollama)
              ↓
FastAPI ← ← ← app.py → Milvus (Vector DB)
                ↓
         SentenceTransformers → Embeddings
                ↓
         PyMuPDF → PDF Processing
```

---

## Code Style Guidelines

### Python Style (PEP 8)

```python
# Good
class DocumentProcessor:
    """Process documents and generate embeddings."""
    
    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name)
    
    def process(self, text: str) -> numpy.ndarray:
        """Process text and return embeddings."""
        return self.model.encode([text])

# Bad
def process(txt):  # Unclear parameter name
    return model.encode(txt)  # No type hints
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `PDFProcessor`)
- **Functions/Methods**: `snake_case` (e.g., `extract_text`)
- **Constants**: `UPPER_CASE` (e.g., `CHUNK_SIZE`)
- **Private**: Leading underscore (e.g., `_internal_method`)

### Documentation Standards

```python
def retrieve_context(question: str, top_k: int = 5) -> tuple[List[str], List[float]]:
    """Retrieve relevant chunks from vector database.
    
    Args:
        question: The user's query string
        top_k: Number of chunks to retrieve
    
    Returns:
        Tuple of (chunk_texts, similarity_scores)
    
    Raises:
        ConnectionError: If Milvus connection fails
    """
```

---

## Adding New Features

### Example: Adding a New Chunking Strategy

#### 1. Create Feature Branch
```bash
git checkout -b feature/recursive-chunking
```

#### 2. Implement Feature
```python
# In scripts/prepare_data.py
class RecursiveChunker:
    """Recursively chunk text while respecting paragraph boundaries."""
    
    def __init__(self, max_size: int = 500, min_size: int = 100):
        self.max_size = max_size
        self.min_size = min_size
    
    def chunk(self, text: str) -> List[str]:
        """Split text recursively."""
        # Implementation here
        pass
```

#### 3. Add Tests
```python
# In tests/test_chunking.py
def test_recursive_chunker():
    chunker = RecursiveChunker(max_size=500)
    text = "..." # Sample text
    chunks = chunker.chunk(text)
    
    assert len(chunks) > 0
    assert all(len(c) <= 500 for c in chunks)
```

#### 4. Update Configuration
```python
# In config.py
CHUNKING_STRATEGY = "recursive"  # or "sentence"
```

#### 5. Commit and Push
```bash
git add .
git commit -m "feat: add recursive chunking strategy"
git push origin feature/recursive-chunking
```

---

## Testing Guidelines

### Unit Testing

```python
# tests/test_app.py
import pytest
from app import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_query_endpoint():
    response = client.post(
        "/query",
        json={"question": "What is Veridia?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()

def test_empty_question():
    response = client.post(
        "/query",
        json={"question": ""}
    )
    assert response.status_code == 400
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_app.py -v
```

---

## Performance Optimization

### Profiling

```python
# Find bottlenecks
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
process_pdf("data/dr_voss_diary.pdf")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(10)
```

### Optimization Techniques

1. **Embedding Caching**
```python
cache = {}
def get_embedding(text):
    if text not in cache:
        cache[text] = model.encode([text])
    return cache[text]
```

2. **Batch Processing**
```python
# Process embeddings in batches
def encode_batch(texts, batch_size=32):
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings.extend(model.encode(batch))
    return embeddings
```

3. **Connection Pooling**
```python
# Reuse Milvus connection
connection_pool = {}
def get_connection(alias):
    if alias not in connection_pool:
        connections.connect(alias, host="localhost", port=19530)
    return connection_pool[alias]
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In config.py
DEBUG = True

# In scripts
if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
```

### Print Debugging

```python
# Use logger instead of print
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Processing: {question}")
logger.info(f"Retrieved {len(chunks)} chunks")
logger.warning(f"Slow query: {query_time}s")
logger.error(f"Failed to connect: {error}")
```

### Interactive Debugging with pdb

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use newer syntax (Python 3.7+)
breakpoint()
```

---

## API Development

### Adding New Endpoints

```python
# In app.py
@app.post("/custom-endpoint", response_model=CustomResponse)
async def custom_endpoint(request: CustomRequest):
    """Handle custom request."""
    try:
        result = process_request(request)
        return CustomResponse(result=result)
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Request/Response Schemas

```python
from pydantic import BaseModel, Field
from typing import Optional

class CustomRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[dict] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query": "example query",
                "filters": {"source": "pdf"}
            }
        }

class CustomResponse(BaseModel):
    result: str
    confidence: float = Field(..., ge=0.0, le=1.0)
```

---

## Database Management

### Milvus Operations

```python
from milvus import connections, Collection

# Connect
connections.connect("default", host="127.0.0.1", port=19530)

# List collections
from milvus import list_collections
collections = list_collections()

# Delete collection
Collection.drop("pdf_chunks")

# Backup
collection.flush()
```

### Data Migrations

```python
# Template for schema changes
def migrate_to_v2():
    """Migrate existing data to new schema."""
    old_collection = Collection("pdf_chunks")
    new_collection = Collection("pdf_chunks_v2")
    
    # Transfer data
    results = old_collection.query(expr="", output_fields=["*"])
    new_collection.insert(results)
    
    # Swap collections
    old_collection.drop()
    # Rename not directly supported, but use new_collection
```

---

## Continuous Integration Setup

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest --cov
    
    - name: Check code style
      run: |
        pip install flake8 black
        black --check .
        flake8 .
```

---

## Documentation Updates

### When to Update Docs

- [ ] Adding new feature
- [ ] Changing API endpoint
- [ ] Updating configuration
- [ ] Fixing bug with non-obvious solution
- [ ] Performance improvement

### Documentation Checklist

- [ ] README.md updated
- [ ] Code comments added
- [ ] Docstrings written
- [ ] Examples provided
- [ ] Type hints included

---

## Release Process

### Version Management

```bash
# Current version in setup or __version__
__version__ = "1.0.0"  # MAJOR.MINOR.PATCH

# Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Release Checklist

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Version bumped
- [ ] Changelog updated
- [ ] Tag created

---

## Troubleshooting Development Issues

### Common Problems

**Issue**: Import errors after adding new module
```bash
# Solution: Reinstall in development mode
pip install -e .
```

**Issue**: Milvus connection fails during tests
```bash
# Solution: Mock Milvus for unit tests
from unittest.mock import Mock
collection = Mock()
```

**Issue**: Tests pass locally but fail in CI
```bash
# Solution: Check Python version, dependencies versions
python --version
pip list
```

---

## Contributing Guidelines

### Code Review Checklist

- [ ] Follows PEP 8 style guide
- [ ] Has docstrings and comments
- [ ] Includes tests
- [ ] Doesn't break existing tests
- [ ] Performance acceptable
- [ ] Handles errors gracefully
- [ ] Updates documentation

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] README updated
- [ ] Docstrings added
- [ ] Examples provided
```

---

## Resources

### Learning Resources
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Milvus Documentation](https://milvus.io/docs)
- [Sentence Transformers Guide](https://www.sbert.net/)
- [Python Best Practices](https://pep8.org/)

### Tools
- **Code Quality**: `black`, `flake8`, `mypy`
- **Testing**: `pytest`, `pytest-cov`
- **Debugging**: `pdb`, `ipdb`
- **Profiling**: `cProfile`, `line_profiler`

---

## Questions or Issues?

- Check existing documentation
- Review similar implementations
- Test in isolation
- Use logging to trace execution
- Ask team members for guidance

---

*Last Updated: 2024*
*Maintained by: Veridia RAG Development Team*
