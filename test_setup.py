#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def check_python_version():
    """Check Python version."""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 9:
        print("[OK] Python version OK")
        return True
    else:
        print("[FAIL] Python 3.9+ required")
        return False

def check_dependencies():
    """Check if all required packages are installed."""
    print_header("Checking Dependencies")
    
    required = [
        "pymupdf",
        "sentence_transformers",
        "milvus",
        "fastapi",
        "uvicorn",
        "pydantic",
        "numpy",
        "torch",
        "sklearn",
    ]
    
    all_ok = True
    for package in required:
        try:
            __import__(package)
            print(f"[OK] {package}")
        except ImportError:
            print(f"[FAIL] {package} (not installed)")
            all_ok = False
    
    return all_ok

def check_files():
    """Check if required files exist."""
    print_header("Checking Required Files")
    
    required_files = [
        "data/dr_voss_diary.pdf",
        "data/questions.txt",
        "data/answers.txt",
        "scripts/prepare_data.py",
        "scripts/eval.py",
        "app.py",
        "requirements.txt",
        "config.py",
    ]
    
    all_ok = True
    for file in required_files:
        if os.path.exists(file):
            print(f"[OK] {file}")
        else:
            print(f"[FAIL] {file} (not found)")
            all_ok = False
    
    return all_ok

def check_ollama():
    """Check if Ollama is accessible."""
    print_header("Checking Ollama Service")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("[OK] Ollama service is running")
            models = response.json().get("models", [])
            if models:
                print(f"[OK] Found {len(models)} model(s)")
                for model in models:
                    print(f"  - {model.get('name', 'unknown')}")
            else:
                print("[WARN] No models found - run: ollama pull llama2:7b")
            return True
        else:
            print("[FAIL] Ollama service returned error")
            return False
    except requests.exceptions.ConnectionError:
        print("[FAIL] Ollama service not running")
        print("  Start with: ollama serve")
        return False
    except Exception as e:
        print(f"[FAIL] Error checking Ollama: {e}")
        return False

def check_embedding_model():
    """Check if embedding model can be loaded."""
    print_header("Checking Embedding Model")
    
    try:
        from sentence_transformers import SentenceTransformer
        print("Loading embedding model: Snowflake/snowflake-arctic-embed-s")
        model = SentenceTransformer("Snowflake/snowflake-arctic-embed-s")
        dim = model.get_sentence_embedding_dimension()
        print(f"[OK] Embedding model loaded successfully")
        print(f"  Dimension: {dim}")
        return True
    except Exception as e:
        print(f"[FAIL] Error loading embedding model: {e}")
        print("  This is expected on first run - model will be downloaded on first use")
        return False

def check_pdf():
    """Check if PDF can be read."""
    print_header("Checking PDF Document")
    
    try:
        import pymupdf
        pdf_path = "data/dr_voss_diary.pdf"
        if os.path.exists(pdf_path):
            doc = pymupdf.open(pdf_path)
            pages = len(doc)
            doc.close()
            print(f"[OK] PDF document readable")
            print(f"  Pages: {pages}")
            return True
        else:
            print(f"[FAIL] PDF not found at {pdf_path}")
            return False
    except Exception as e:
        print(f"[FAIL] Error reading PDF: {e}")
        return False

def run_diagnostic():
    """Run all checks."""
    print("\n" + "="*60)
    print("  VERIDIA RAG SYSTEM - SETUP DIAGNOSTIC")
    print("="*60)
    
    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Required Files": check_files(),
        "PDF Document": check_pdf(),
        "Embedding Model": check_embedding_model(),
        "Ollama Service": check_ollama(),
    }
    
    print("\n" + "="*60)
    print("  DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for check, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{check:<25} : {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("  [OK] ALL CHECKS PASSED - System is ready!")
        print("  Next steps:")
        print("    1. Run: python scripts/prepare_data.py")
        print("    2. Run: python app.py (in another terminal)")
        print("    3. Test: curl http://localhost:8000/health")
    else:
        print("  [WARN] SOME CHECKS FAILED")
        print("  Fix the issues above and try again.")
    print("="*60 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = run_diagnostic()
    sys.exit(0 if success else 1)
