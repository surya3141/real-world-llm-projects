"""
Self-Correcting RAG Pipeline - Main orchestrator
"""
from typing import Dict, List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

from retriever import VectorRetriever
from agents.relevance_agent import RelevanceAgent
from agents.generator_agent import GeneratorAgent
from agents.factcheck_agent import FactCheckAgent


class SelfCorrectingRAG:
    """
    Main pipeline that orchestrates the self-correcting RAG system.
    
    Flow:
    1. Retrieve documents using vector similarity
    2. Filter for relevance using Relevance Agent
    3. Generate answer using Generator Agent
    4. Fact-check using Fact-Check Agent
    5. (Optional) Self-correct if confidence is low
    """
    
    def __init__(
        self,
        documents_path: Optional[str] = None,
        persist_directory: Optional[str] = None,
        load_existing: bool = True,
        top_k: int = 5,
        relevance_threshold: float = 0.7,
        factcheck_threshold: float = 7.0,
        max_correction_loops: int = 2
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            documents_path: Path to documents directory (for creating new vectorstore)
            persist_directory: Path to save/load vectorstore
            load_existing: Whether to load existing vectorstore
            top_k: Number of documents to retrieve
            relevance_threshold: Minimum relevance confidence
            factcheck_threshold: Minimum fact-check score
            max_correction_loops: Maximum self-correction attempts
        """
        load_dotenv()
        
        self.top_k = int(os.getenv("TOP_K", top_k))
        self.relevance_threshold = float(os.getenv("RELEVANCE_THRESHOLD", relevance_threshold))
        self.factcheck_threshold = float(os.getenv("FACTCHECK_THRESHOLD", factcheck_threshold))
        self.max_correction_loops = int(os.getenv("MAX_CORRECTION_LOOPS", max_correction_loops))
        
        # Initialize components
        self.retriever = VectorRetriever()
        self.relevance_agent = RelevanceAgent()
        self.generator_agent = GeneratorAgent()
        self.factcheck_agent = FactCheckAgent()
        
        # Setup vectorstore
        if load_existing and persist_directory and Path(persist_directory).exists():
            print("Loading existing vectorstore...")
            self.retriever.load_vectorstore(persist_directory)
        elif documents_path:
            print("Creating new vectorstore from documents...")
            documents = self.retriever.load_documents(documents_path)
            self.retriever.create_vectorstore(documents, persist_directory)
        else:
            print("Warning: No vectorstore loaded. Call setup_vectorstore() before querying.")
    
    def setup_vectorstore(
        self, 
        documents_path: str, 
        persist_directory: Optional[str] = None
    ):
        """
        Setup vectorstore from documents.
        
        Args:
            documents_path: Path to documents directory
            persist_directory: Optional path to save vectorstore
        """
        documents = self.retriever.load_documents(documents_path)
        self.retriever.create_vectorstore(documents, persist_directory)
    
    def query(
        self,
        question: str,
        enable_self_correction: bool = True,
        return_intermediate: bool = False
    ) -> Dict:
        """
        Query the RAG system with self-correction.
        
        Args:
            question: User's question
            enable_self_correction: Whether to enable self-correction loop
            return_intermediate: Whether to return intermediate results
            
        Returns:
            Dict with answer, confidence_score, and optionally intermediate results
        """
        intermediate_results = {
            "attempts": [],
            "correction_loops": 0
        }
        
        attempt_num = 0
        
        while attempt_num <= self.max_correction_loops:
            attempt_num += 1
            
            # Step 1: Retrieve documents
            print(f"\n{'='*60}")
            print(f"Attempt {attempt_num}")
            print(f"{'='*60}")
            print(f"Step 1: Retrieving documents...")
            
            retrieved_docs = self.retriever.retrieve(question, top_k=self.top_k)
            retrieved_texts = [doc["document"] for doc in retrieved_docs]
            
            print(f"Retrieved {len(retrieved_texts)} documents")
            
            # Step 2: Filter for relevance
            print(f"\nStep 2: Filtering for relevance...")
            
            filtered_docs = self.relevance_agent.filter_documents(
                question, 
                retrieved_texts, 
                threshold=self.relevance_threshold
            )
            
            print(f"Filtered to {len(filtered_docs)} relevant documents")
            
            if not filtered_docs:
                return {
                    "answer": "No relevant documents found to answer your question.",
                    "confidence_score": 0,
                    "reasoning": "Relevance filtering removed all documents",
                    "intermediate_results": intermediate_results if return_intermediate else None
                }
            
            # Step 3: Generate answer
            print(f"\nStep 3: Generating answer...")
            
            generation_result = self.generator_agent.generate_with_metadata(
                question,
                filtered_docs
            )
            
            answer = generation_result["answer"]
            print(f"Answer generated ({len(answer)} characters)")
            
            # Step 4: Fact-check
            print(f"\nStep 4: Fact-checking answer...")
            
            filtered_texts = [doc["document"] for doc in filtered_docs]
            evaluation = self.factcheck_agent.evaluate_answer(
                question,
                answer,
                filtered_texts
            )
            
            print(f"Consistency Score: {evaluation['consistency_score']}/10")
            
            # Record attempt
            attempt_data = {
                "attempt_number": attempt_num,
                "retrieved_count": len(retrieved_texts),
                "filtered_count": len(filtered_docs),
                "answer": answer,
                "evaluation": evaluation
            }
            intermediate_results["attempts"].append(attempt_data)
            
            # Check if we should self-correct
            if evaluation["consistency_score"] >= self.factcheck_threshold:
                print(f"\n✓ Answer passed fact-check!")
                
                result = {
                    "answer": answer,
                    "confidence_score": evaluation["consistency_score"],
                    "is_consistent": evaluation["is_consistent"],
                    "reasoning": evaluation["reasoning"],
                    "factual_errors": evaluation.get("factual_errors", []),
                    "sources_used": len(filtered_docs),
                    "correction_loops": attempt_num - 1
                }
                
                if return_intermediate:
                    result["intermediate_results"] = intermediate_results
                
                return result
            
            elif not enable_self_correction or attempt_num > self.max_correction_loops:
                print(f"\n⚠ Answer failed fact-check. Returning anyway (self-correction disabled or max loops reached).")
                
                result = {
                    "answer": answer,
                    "confidence_score": evaluation["consistency_score"],
                    "is_consistent": evaluation["is_consistent"],
                    "reasoning": evaluation["reasoning"],
                    "factual_errors": evaluation.get("factual_errors", []),
                    "sources_used": len(filtered_docs),
                    "correction_loops": attempt_num - 1,
                    "warning": "Answer did not pass fact-check threshold"
                }
                
                if return_intermediate:
                    result["intermediate_results"] = intermediate_results
                
                return result
            
            else:
                print(f"\n↻ Score below threshold. Attempting self-correction...")
                intermediate_results["correction_loops"] += 1
                # Loop will retry with same documents but regenerate answer
    
    def query_simple(self, question: str) -> str:
        """
        Simple query interface that returns just the answer string.
        
        Args:
            question: User's question
            
        Returns:
            Answer string
        """
        result = self.query(question, enable_self_correction=False)
        return result["answer"]


if __name__ == "__main__":
    # Example usage
    print("="*60)
    print("Self-Correcting RAG Pipeline")
    print("="*60)
    
    # Initialize pipeline
    rag = SelfCorrectingRAG(
        documents_path="data/sample_docs",
        persist_directory="data/vectorstore",
        load_existing=True
    )
    
    # Test query
    question = "What is the Eiffel Tower and when was it built?"
    
    print(f"\nQuestion: {question}\n")
    
    result = rag.query(
        question,
        enable_self_correction=True,
        return_intermediate=True
    )
    
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    print(f"\nAnswer:\n{result['answer']}\n")
    print(f"Confidence Score: {result['confidence_score']}/10")
    print(f"Correction Loops: {result['correction_loops']}")
    print(f"Sources Used: {result['sources_used']}")
    
    if result.get('factual_errors'):
        print(f"\nFactual Errors: {result['factual_errors']}")
    
    print(f"\nReasoning:\n{result['reasoning']}")
