#!/usr/bin/env python3

import os
import sys
import json
import logging
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "Snowflake/snowflake-arctic-embed-s"
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = 19530
COLLECTION_NAME = "pdf_chunks"
TOP_K = 5

class RAGEvaluator:
    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self._connect_milvus()
    
    def _connect_milvus(self):
        """Connect to Milvus."""
        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            self.collection = Collection(COLLECTION_NAME)
            self.collection.load()
            logger.info(f"Connected to Milvus collection: {COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error connecting to Milvus: {e}")
            raise
    
    def retrieve_context(self, question: str, top_k: int = TOP_K) -> List[str]:
        """Retrieve relevant chunks from Milvus."""
        question_embedding = self.embedding_model.encode([question])[0]
        
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 16}
        }
        
        results = self.collection.search(
            data=[question_embedding.tolist()],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )
        
        chunks = []
        for hits in results:
            for hit in hits:
                chunks.append(hit.entity.get("text"))
        
        return chunks
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        emb1 = self.embedding_model.encode([text1])
        emb2 = self.embedding_model.encode([text2])
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return similarity
    
    def extract_key_entities(self, text: str) -> set:
        """Extract key entities (simple word-based approach)."""
        words = set(text.lower().split())
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'of', 'to', 'in', 'and', 'or', 'but', 'as', 'by', 'for', 'with', 'on', 'at', 'from', 'up', 'about', 'into', 'through', 'during'}
        return words - stop_words
    
    def calculate_entity_overlap(self, text1: str, text2: str) -> float:
        """Calculate entity/word overlap between two texts."""
        entities1 = self.extract_key_entities(text1)
        entities2 = self.extract_key_entities(text2)
        
        if not entities1 or not entities2:
            return 0.0
        
        overlap = len(entities1 & entities2)
        total = len(entities1 | entities2)
        
        return overlap / total if total > 0 else 0.0
    
    def evaluate_answer(self, question: str, generated_answer: str, 
                       expected_answer: str) -> Dict:
        """Evaluate a generated answer against expected answer."""
        
        metrics = {
            "question": question,
            "generated_answer": generated_answer[:100] + "..." if len(generated_answer) > 100 else generated_answer,
            "expected_answer": expected_answer[:100] + "..." if len(expected_answer) > 100 else expected_answer,
            "exact_match": 0.0,
            "semantic_similarity": 0.0,
            "entity_overlap": 0.0,
            "overall_score": 0.0
        }
        
        # Exact match (case-insensitive, trimmed)
        if generated_answer.lower().strip() == expected_answer.lower().strip():
            metrics["exact_match"] = 1.0
        
        # Semantic similarity
        metrics["semantic_similarity"] = self.calculate_semantic_similarity(
            generated_answer, expected_answer
        )
        
        # Entity overlap
        metrics["entity_overlap"] = self.calculate_entity_overlap(
            generated_answer, expected_answer
        )
        
        # Overall score (weighted average)
        metrics["overall_score"] = (
            0.3 * metrics["exact_match"] +
            0.5 * metrics["semantic_similarity"] +
            0.2 * metrics["entity_overlap"]
        )
        
        return metrics
    
    def run_evaluation(self, questions_file: str = "data/questions.txt",
                      answers_file: str = "data/answers.txt") -> Dict:
        """Run evaluation on all questions."""
        
        if not os.path.exists(questions_file):
            logger.error(f"Questions file not found: {questions_file}")
            return {}
        
        if not os.path.exists(answers_file):
            logger.error(f"Answers file not found: {answers_file}")
            return {}
        
        with open(questions_file, 'r') as f:
            questions = [line.strip() for line in f if line.strip()]
        
        with open(answers_file, 'r') as f:
            answers = [line.strip() for line in f if line.strip()]
        
        if len(questions) != len(answers):
            logger.warning(f"Number of questions ({len(questions)}) != number of answers ({len(answers)})")
        
        results = {
            "total_questions": len(questions),
            "evaluations": [],
            "summary": {
                "avg_exact_match": 0.0,
                "avg_semantic_similarity": 0.0,
                "avg_entity_overlap": 0.0,
                "avg_overall_score": 0.0,
                "retrieval_success_rate": 0.0
            }
        }
        
        retrieval_successes = 0
        
        for i, question in enumerate(questions[:len(answers)]):
            logger.info(f"Evaluating question {i+1}/{len(questions)}: {question[:50]}...")
            
            try:
                # Retrieve context
                context_chunks = self.retrieve_context(question)
                
                if not context_chunks:
                    logger.warning(f"No context retrieved for question {i+1}")
                    generated_answer = "No relevant information found."
                else:
                    retrieval_successes += 1
                    # For evaluation, create a simple answer from context
                    generated_answer = self._generate_simple_answer(question, context_chunks)
                
                expected_answer = answers[i] if i < len(answers) else "Unknown"
                
                # Evaluate
                eval_result = self.evaluate_answer(question, generated_answer, expected_answer)
                results["evaluations"].append(eval_result)
            
            except Exception as e:
                logger.error(f"Error evaluating question {i+1}: {e}")
        
        # Calculate summary statistics
        if results["evaluations"]:
            exact_matches = [e["exact_match"] for e in results["evaluations"]]
            semantic_sims = [e["semantic_similarity"] for e in results["evaluations"]]
            entity_overlaps = [e["entity_overlap"] for e in results["evaluations"]]
            overall_scores = [e["overall_score"] for e in results["evaluations"]]
            
            results["summary"]["avg_exact_match"] = np.mean(exact_matches)
            results["summary"]["avg_semantic_similarity"] = np.mean(semantic_sims)
            results["summary"]["avg_entity_overlap"] = np.mean(entity_overlaps)
            results["summary"]["avg_overall_score"] = np.mean(overall_scores)
            results["summary"]["retrieval_success_rate"] = retrieval_successes / len(questions)
        
        return results
    
    def _generate_simple_answer(self, question: str, context_chunks: List[str]) -> str:
        """Generate a simple answer from context chunks."""
        if not context_chunks:
            return "No context available."
        
        # Find the chunk most similar to the question
        best_chunk = context_chunks[0]
        best_score = 0
        
        for chunk in context_chunks:
            score = self.calculate_semantic_similarity(question, chunk)
            if score > best_score:
                best_score = score
                best_chunk = chunk
        
        # Extract a sentence from the chunk
        sentences = best_chunk.split('.')
        if sentences:
            return sentences[0].strip() + "."
        return best_chunk[:100]

def print_results(results: Dict) -> None:
    """Print evaluation results."""
    if not results:
        print("No results to display.")
        return
    
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    
    summary = results.get("summary", {})
    print(f"\nTotal Questions: {results.get('total_questions', 0)}")
    print(f"Retrieval Success Rate: {summary.get('retrieval_success_rate', 0):.2%}")
    print(f"\nMetrics:")
    print(f"  Avg Exact Match: {summary.get('avg_exact_match', 0):.4f}")
    print(f"  Avg Semantic Similarity: {summary.get('avg_semantic_similarity', 0):.4f}")
    print(f"  Avg Entity Overlap: {summary.get('avg_entity_overlap', 0):.4f}")
    print(f"  Avg Overall Score: {summary.get('avg_overall_score', 0):.4f}")
    
    print("\n" + "-"*80)
    print("DETAILED RESULTS")
    print("-"*80)
    
    for i, eval_result in enumerate(results.get("evaluations", [])[:10]):
        print(f"\nQuestion {i+1}: {eval_result.get('question', 'N/A')}")
        print(f"  Generated: {eval_result.get('generated_answer', 'N/A')}")
        print(f"  Expected: {eval_result.get('expected_answer', 'N/A')}")
        print(f"  Overall Score: {eval_result.get('overall_score', 0):.4f}")

def main():
    """Main evaluation function."""
    logger.info("Starting RAG evaluation...")
    
    try:
        evaluator = RAGEvaluator()
        results = evaluator.run_evaluation()
        
        # Save results
        output_file = "data/eval_results.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_file}")
        
        # Print results
        print_results(results)
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
