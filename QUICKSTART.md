# Quick Start Guide - Veridia RAG System

Get the Veridia RAG system up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Ollama (for LLM inference)
- Git

## Installation (5 minutes)

### 1. Clone/Navigate to Project
```bash
cd llm-case-study-main
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Ollama (First Time)
```bash
# Download Ollama from https://ollama.ai
# After installation, in a separate terminal:
ollama pull llama2:7b
ollama serve
```

### 4. Prepare Data
In another terminal:
```bash
python scripts/prepare_data.py
```

Expected output:
```
INFO:__main__:Extracted X characters from PDF
INFO:__main__:Created Y chunks
INFO:__main__:Storing chunks in Milvus...
INFO:__main__:PDF processing complete!
```

## Running the System

### Terminal 1: Start Ollama
```bash
ollama serve
```

### Terminal 2: Start API Server
```bash
# Make sure you're in the venv
python app.py
```

Server starts on: `http://localhost:8000`

### Terminal 3: Query the API
```bash
# Test the API
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the official language of Veridia?"}'
```

Or open `http://localhost:8000/docs` in your browser for interactive API testing.

## Quick Testing

### Test 1: Health Check
```bash
curl http://localhost:8000/health
# Response: {"status":"ok"}
```

### Test 2: Sample Question
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is Veridia'\''s most famous historical figure?"}'
```

### Test 3: Run Evaluation
```bash
python scripts/eval.py
```

## Using Docker (Alternative)

```bash
# Build and start all services
docker-compose up -d

# Download LLM model
docker exec veridia-ollama ollama pull llama2:7b

# Prepare data
docker exec veridia-rag-api python scripts/prepare_data.py

# Test API
curl http://localhost:8000/health
```

## Troubleshooting

### Issue: "Cannot connect to Ollama"
**Solution**: 
```bash
# Make sure Ollama is running in another terminal
ollama serve
```

### Issue: "Milvus connection failed"
**Solution**: 
- Milvus runs embedded, no separate setup needed
- Check if port 19530 is available

### Issue: "API won't start"
**Solution**: 
- Check Python version: `python --version` (need 3.9+)
- Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

## Common Questions

**Q: Do I need a GPU?**
A: No, everything runs on CPU. GPU will make it faster but is not required.

**Q: How long does preparation take?**
A: Typically 5-15 minutes depending on document size.

**Q: Can I use different models?**
A: Yes! See README.md for alternatives.

**Q: How do I stop the system?**
A: Press Ctrl+C in each terminal to stop services.

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Check [BONUS_FEATURES.md](BONUS_FEATURES.md) for advanced features
3. Explore the codebase to understand the architecture
4. Run evaluation: `python scripts/eval.py`

## Support

For detailed information, refer to:
- **Setup Instructions**: [README.md - Installation & Setup](README.md#installation--setup)
- **Architecture Details**: [README.md - Project Architecture](README.md#project-architecture)
- **Technical Discussion**: [README.md - Technical Discussion](README.md#technical-discussion)
- **Bonus Features**: [BONUS_FEATURES.md](BONUS_FEATURES.md)

---

**Happy querying! 🚀**
