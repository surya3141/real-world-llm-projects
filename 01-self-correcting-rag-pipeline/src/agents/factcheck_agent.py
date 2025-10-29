"""
Fact-Check Agent - Validates factual consistency of generated answers
"""
from typing import List, Dict
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import os
import json


class FactCheckAgent:
    """
    Evaluator Agent that scores the generated answer against source documents
    for factual consistency. This is the final safeguard against hallucination.
    """
    
    def __init__(self, model_name: str = None, temperature: float = 0.0):
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature = temperature
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature
        )
        
        self.system_prompt = """You are a fact-checking agent. Your job is to evaluate if a generated answer is factually consistent with the source documents.

You must respond with ONLY a JSON object in this exact format:
{
    "consistency_score": 0-10,
    "is_consistent": true/false,
    "factual_errors": ["list of any errors found"],
    "reasoning": "Detailed explanation of your evaluation"
}

Scoring guide:
- 10: Perfect consistency, all claims supported by sources
- 8-9: High consistency, minor unsupported details
- 6-7: Mostly consistent, some unsupported claims
- 4-5: Partially consistent, significant unsupported content
- 2-3: Low consistency, major factual errors
- 0-1: Completely inconsistent or fabricated

Check for:
1. Every claim in the answer is supported by the sources
2. No information added from outside sources
3. No misinterpretation of source material
4. Proper representation of any uncertainties"""

    def evaluate_answer(
        self, 
        query: str,
        answer: str, 
        source_documents: List[str]
    ) -> Dict:
        """
        Evaluate if the generated answer is factually consistent with sources.
        
        Args:
            query: Original user question
            answer: Generated answer to evaluate
            source_documents: Source documents used to generate the answer
            
        Returns:
            Dict with consistency_score, is_consistent, factual_errors, reasoning
        """
        # Format sources
        sources = "\n\n---\n\n".join([
            f"Source {i+1}:\n{doc}" 
            for i, doc in enumerate(source_documents)
        ])
        
        if not source_documents:
            return {
                "consistency_score": 0,
                "is_consistent": False,
                "factual_errors": ["No source documents provided"],
                "reasoning": "Cannot evaluate consistency without source documents"
            }
        
        prompt = f"""Question: {query}

Generated Answer:
{answer}

Source Documents:
{sources}

Evaluate if the answer is factually consistent with the source documents."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        try:
            result = json.loads(response.content)
            # Ensure score is in valid range
            result["consistency_score"] = max(0, min(10, result.get("consistency_score", 5)))
            return result
        except json.JSONDecodeError:
            # Fallback parsing
            content = response.content.lower()
            score = 5  # default middle score
            
            # Try to extract score
            import re
            score_match = re.search(r'score["\s:]+(\d+)', content)
            if score_match:
                score = int(score_match.group(1))
            
            return {
                "consistency_score": score,
                "is_consistent": score >= 7,
                "factual_errors": [],
                "reasoning": "Fallback parsing used: " + content[:200]
            }
    
    def detailed_evaluation(
        self, 
        query: str,
        answer: str, 
        source_documents: List[str]
    ) -> Dict:
        """
        Perform detailed evaluation with claim-by-claim analysis.
        
        Args:
            query: Original user question
            answer: Generated answer to evaluate
            source_documents: Source documents used
            
        Returns:
            Dict with detailed evaluation including claims analysis
        """
        # First get standard evaluation
        standard_eval = self.evaluate_answer(query, answer, source_documents)
        
        # Add detailed prompt for claim extraction
        claims_prompt = f"""Answer: {answer}

Break down this answer into individual factual claims (as a JSON list of strings)."""

        messages = [
            HumanMessage(content=claims_prompt)
        ]
        
        try:
            claims_response = self.llm.invoke(messages)
            claims = json.loads(claims_response.content)
            if isinstance(claims, dict) and "claims" in claims:
                claims = claims["claims"]
            standard_eval["claims"] = claims
        except:
            standard_eval["claims"] = ["Unable to extract individual claims"]
        
        return standard_eval
    
    def should_regenerate(
        self, 
        evaluation: Dict, 
        threshold: float = 7.0
    ) -> bool:
        """
        Determine if the answer should be regenerated based on evaluation.
        
        Args:
            evaluation: Result from evaluate_answer
            threshold: Minimum acceptable consistency score
            
        Returns:
            True if answer should be regenerated, False otherwise
        """
        return evaluation["consistency_score"] < threshold


if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv
    load_dotenv()
    
    agent = FactCheckAgent()
    
    query = "What is the capital of France?"
    answer = "Paris is the capital of France and is known for the Eiffel Tower. It has a population of about 2 million people in the city proper."
    sources = [
        "Paris is the capital and most populous city of France.",
        "The Eiffel Tower is a wrought-iron lattice tower in Paris."
    ]
    
    print("Testing Fact-Check Agent\n")
    print(f"Query: {query}\n")
    print(f"Answer: {answer}\n")
    
    evaluation = agent.evaluate_answer(query, answer, sources)
    
    print("Evaluation Results:")
    print(f"Consistency Score: {evaluation['consistency_score']}/10")
    print(f"Is Consistent: {evaluation['is_consistent']}")
    print(f"Factual Errors: {evaluation['factual_errors']}")
    print(f"Reasoning: {evaluation['reasoning']}\n")
    
    print(f"Should Regenerate: {agent.should_regenerate(evaluation)}")
    
    print("\n" + "="*50 + "\n")
    print("Testing with hallucinated content:\n")
    
    hallucinated_answer = "Paris is the capital of France. It was founded in 1776 and has a population of 50 million people."
    
    evaluation2 = agent.evaluate_answer(query, hallucinated_answer, sources)
    
    print("Evaluation Results:")
    print(f"Consistency Score: {evaluation2['consistency_score']}/10")
    print(f"Is Consistent: {evaluation2['is_consistent']}")
    print(f"Factual Errors: {evaluation2['factual_errors']}")
    print(f"Reasoning: {evaluation2['reasoning']}")
