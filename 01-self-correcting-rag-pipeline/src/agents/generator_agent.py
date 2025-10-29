"""
Generator Agent - Creates answers from filtered context
"""
from typing import List, Dict
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import os


class GeneratorAgent:
    """
    Agent that generates answers based on the filtered relevant documents.
    Uses the context provided to create accurate, grounded responses.
    """
    
    def __init__(self, model_name: str = None, temperature: float = 0.0):
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature
        )
        
        self.system_prompt = """You are an expert answer generation agent. Your job is to answer questions based ONLY on the provided context documents.

CRITICAL RULES:
1. Base your answer STRICTLY on the provided context
2. If the context doesn't contain enough information, say so explicitly
3. Do NOT add information from your training data
4. Quote or reference specific parts of the context when possible
5. Be concise but complete
6. If multiple documents provide conflicting information, mention this

Your response should be factual, well-structured, and directly answer the question."""

    def generate_answer(
        self, 
        query: str, 
        context_documents: List[str]
    ) -> Dict[str, str]:
        """
        Generate an answer based on the query and context documents.
        
        Args:
            query: User's question
            context_documents: List of relevant document chunks
            
        Returns:
            Dict with keys: answer, sources_used
        """
        # Format context
        context = "\n\n---\n\n".join([
            f"Document {i+1}:\n{doc}" 
            for i, doc in enumerate(context_documents)
        ])
        
        if not context_documents:
            return {
                "answer": "I don't have enough context to answer this question. No relevant documents were found.",
                "sources_used": 0
            }
        
        prompt = f"""Question: {query}

Context Documents:
{context}

Please answer the question based on the provided context."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "answer": response.content,
            "sources_used": len(context_documents)
        }
    
    def generate_with_metadata(
        self, 
        query: str, 
        context_documents: List[Dict]
    ) -> Dict:
        """
        Generate answer with additional metadata from filtered documents.
        
        Args:
            query: User's question
            context_documents: List of dicts with document and metadata
            
        Returns:
            Dict with answer and metadata
        """
        # Extract just the document texts
        doc_texts = [doc.get("document", doc) if isinstance(doc, dict) else doc 
                     for doc in context_documents]
        
        result = self.generate_answer(query, doc_texts)
        
        # Add metadata
        result["context_metadata"] = [
            {
                "confidence": doc.get("confidence", 1.0),
                "reasoning": doc.get("reasoning", "N/A")
            }
            for doc in context_documents
            if isinstance(doc, dict)
        ]
        
        return result
    
    def generate_with_citations(
        self, 
        query: str, 
        context_documents: List[str]
    ) -> Dict[str, str]:
        """
        Generate answer with inline citations [1], [2], etc.
        
        Args:
            query: User's question
            context_documents: List of relevant document chunks
            
        Returns:
            Dict with keys: answer, citations
        """
        # Format context with numbers
        context = "\n\n".join([
            f"[{i+1}] {doc}" 
            for i, doc in enumerate(context_documents)
        ])
        
        if not context_documents:
            return {
                "answer": "I don't have enough context to answer this question.",
                "citations": []
            }
        
        system_prompt = self.system_prompt + "\n\nWhen referencing information, include citation numbers like [1], [2], etc."
        
        prompt = f"""Question: {query}

Context Documents:
{context}

Please answer the question and include citation numbers when referencing specific information."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "answer": response.content,
            "citations": context_documents
        }


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = GeneratorAgent()
    
    query = "What is the capital of France and what is it known for?"
    documents = [
        "Paris is the capital and most populous city of France.",
        "The Eiffel Tower is a wrought-iron lattice tower in Paris, named after engineer Gustave Eiffel.",
        "Paris is known for its art, fashion, and culture. It's home to world-famous museums like the Louvre."
    ]
    
    print("Testing Generator Agent\n")
    print(f"Query: {query}\n")
    
    result = agent.generate_answer(query, documents)
    
    print(f"Answer:\n{result['answer']}\n")
    print(f"Sources used: {result['sources_used']}\n")
    
    print("\n" + "="*50 + "\n")
    print("Testing with citations:\n")
    
    result_citations = agent.generate_with_citations(query, documents)
    print(f"Answer with citations:\n{result_citations['answer']}\n")
