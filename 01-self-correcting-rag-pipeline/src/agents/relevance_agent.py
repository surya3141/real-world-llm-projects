"""
Relevance Agent - Filters retrieved documents for relevance to the query
"""
from typing import List, Dict
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import os


class RelevanceAgent:
    """
    Guardrail Agent that evaluates if retrieved documents are relevant to the user's query.
    This helps reduce noise and prevents hallucination from irrelevant context.
    """
    
    def __init__(self, model_name: str = None, temperature: float = 0.0):
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature
        )
        
        self.system_prompt = """You are a relevance evaluation agent. Your job is to determine if a retrieved document chunk is relevant to answering the user's question.

You must respond with ONLY a JSON object in this exact format:
{
    "is_relevant": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}

A document is relevant if it contains information that could help answer the question, even partially.
Be strict but fair - err on the side of inclusion if there's any potential relevance."""

    def evaluate_relevance(self, query: str, document: str) -> Dict:
        """
        Evaluate if a document is relevant to the query.
        
        Args:
            query: User's question
            document: Retrieved document chunk
            
        Returns:
            Dict with keys: is_relevant (bool), confidence (float), reasoning (str)
        """
        prompt = f"""Question: {query}

Document:
{document}

Evaluate if this document is relevant to answering the question."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        try:
            import json
            result = json.loads(response.content)
            return result
        except json.JSONDecodeError:
            # Fallback parsing
            content = response.content.lower()
            is_relevant = "true" in content or "relevant" in content
            return {
                "is_relevant": is_relevant,
                "confidence": 0.5,
                "reasoning": "Fallback parsing used"
            }
    
    def filter_documents(
        self, 
        query: str, 
        documents: List[str], 
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Filter a list of documents, keeping only relevant ones.
        
        Args:
            query: User's question
            documents: List of retrieved document chunks
            threshold: Minimum confidence threshold for relevance
            
        Returns:
            List of dicts with keys: document, is_relevant, confidence, reasoning
        """
        results = []
        
        for doc in documents:
            evaluation = self.evaluate_relevance(query, doc)
            
            # Add document to results with evaluation
            result = {
                "document": doc,
                **evaluation
            }
            
            # Keep only documents above threshold
            if evaluation["is_relevant"] and evaluation["confidence"] >= threshold:
                results.append(result)
        
        return results
    
    def get_filtered_documents_only(
        self, 
        query: str, 
        documents: List[str], 
        threshold: float = 0.7
    ) -> List[str]:
        """
        Convenience method to get only the filtered document texts.
        
        Args:
            query: User's question
            documents: List of retrieved document chunks
            threshold: Minimum confidence threshold
            
        Returns:
            List of relevant document strings
        """
        filtered = self.filter_documents(query, documents, threshold)
        return [item["document"] for item in filtered]


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = RelevanceAgent()
    
    query = "What is the capital of France?"
    documents = [
        "Paris is the capital and most populous city of France.",
        "The Eiffel Tower is a wrought-iron lattice tower in Paris.",
        "Tokyo is the capital of Japan and one of the most populous cities.",
        "France is known for its wine and cheese production."
    ]
    
    print("Testing Relevance Agent\n")
    print(f"Query: {query}\n")
    
    filtered = agent.filter_documents(query, documents, threshold=0.6)
    
    print(f"Filtered {len(filtered)} out of {len(documents)} documents:\n")
    for i, result in enumerate(filtered, 1):
        print(f"{i}. Confidence: {result['confidence']:.2f}")
        print(f"   Document: {result['document'][:100]}...")
        print(f"   Reasoning: {result['reasoning']}\n")
