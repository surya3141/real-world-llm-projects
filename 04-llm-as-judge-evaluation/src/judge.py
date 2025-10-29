"""
LLM Judge Implementation

Uses GPT-4 to evaluate content based on structured rubrics.
"""
import os
from typing import Dict, List, Optional
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from rubrics import Rubric, get_rubric
from dotenv import load_dotenv
import json

load_dotenv()


class CriterionEvaluation(BaseModel):
    """Evaluation for a single criterion"""
    criterion: str
    score: float
    reasoning: str


class EvaluationResult(BaseModel):
    """Complete evaluation result"""
    overall_score: float
    criteria_scores: Dict[str, float]
    reasoning: Dict[str, str]
    strengths: List[str]
    improvements: List[str]


class LLMJudge:
    """LLM-based evaluator using structured rubrics"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = 0.2
    ):
        """
        Initialize LLM judge
        
        Args:
            model_name: OpenAI model to use (default: gpt-4o)
            temperature: Sampling temperature (lower = more consistent)
        """
        self.model_name = model_name or os.getenv('JUDGE_MODEL', 'gpt-4o')
        self.temperature = temperature
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=os.getenv('OPENAI_API_KEY')
        )
    
    def evaluate(
        self,
        text: str,
        rubric: Rubric,
        context: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate text using rubric
        
        Args:
            text: Content to evaluate
            rubric: Evaluation rubric
            context: Optional context for evaluation
            
        Returns:
            EvaluationResult with scores and reasoning
        """
        # Build prompt
        prompt = self._build_evaluation_prompt(text, rubric, context)
        
        # Get LLM response
        response = self.llm.invoke(prompt)
        
        # Parse response
        result = self._parse_evaluation_response(response.content, rubric)
        
        return result
    
    def _build_evaluation_prompt(
        self,
        text: str,
        rubric: Rubric,
        context: Optional[str] = None
    ) -> str:
        """Build evaluation prompt"""
        
        # Build criteria section
        criteria_text = ""
        for criterion in rubric.criteria:
            criteria_text += f"\n**{criterion.name.upper()}** (Weight: {criterion.weight*100:.0f}%)\n"
            criteria_text += f"Description: {criterion.description}\n"
            
            if criterion.scoring_guide:
                criteria_text += "Scoring Guide:\n"
                for range_desc, guide in criterion.scoring_guide.items():
                    criteria_text += f"  {range_desc}: {guide}\n"
            
            criteria_text += "\n"
        
        context_section = ""
        if context:
            context_section = f"\n**Context**: {context}\n"
        
        prompt = f"""You are an expert evaluator. Assess the following content using the provided rubric.

**Rubric**: {rubric.name}
{rubric.description}
{context_section}
**Content to Evaluate**:
{text}

**Evaluation Criteria**:
{criteria_text}

**Instructions**:
1. Evaluate the content on each criterion using a 1-10 scale
2. Provide detailed reasoning for each score
3. Identify key strengths (3-5 points)
4. Suggest specific improvements (3-5 points)
5. Calculate overall weighted score

**Output Format** (valid JSON):
{{
  "evaluations": [
    {{
      "criterion": "criterion_name",
      "score": 8.5,
      "reasoning": "Detailed explanation..."
    }},
    ...
  ],
  "strengths": [
    "Strength 1",
    "Strength 2",
    ...
  ],
  "improvements": [
    "Improvement 1",
    "Improvement 2",
    ...
  ]
}}

Provide your evaluation:"""
        
        return prompt
    
    def _parse_evaluation_response(
        self,
        response: str,
        rubric: Rubric
    ) -> EvaluationResult:
        """Parse LLM response into structured result"""
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            # Extract scores and reasoning
            criteria_scores = {}
            reasoning = {}
            
            for eval_item in data.get('evaluations', []):
                criterion = eval_item['criterion']
                score = float(eval_item['score'])
                reason = eval_item['reasoning']
                
                criteria_scores[criterion] = score
                reasoning[criterion] = reason
            
            # Calculate overall weighted score
            overall_score = 0.0
            for criterion in rubric.criteria:
                if criterion.name in criteria_scores:
                    overall_score += criteria_scores[criterion.name] * criterion.weight
            
            # Extract strengths and improvements
            strengths = data.get('strengths', [])
            improvements = data.get('improvements', [])
            
            return EvaluationResult(
                overall_score=round(overall_score, 2),
                criteria_scores=criteria_scores,
                reasoning=reasoning,
                strengths=strengths,
                improvements=improvements
            )
            
        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Response: {response}")
            
            # Fallback: return empty result
            return EvaluationResult(
                overall_score=0.0,
                criteria_scores={},
                reasoning={"error": f"Failed to parse evaluation: {e}"},
                strengths=[],
                improvements=[]
            )
    
    def compare(
        self,
        text1: str,
        text2: str,
        rubric: Rubric,
        context: Optional[str] = None
    ) -> Dict:
        """
        Compare two texts using rubric
        
        Args:
            text1: First text
            text2: Second text
            rubric: Evaluation rubric
            context: Optional context
            
        Returns:
            Comparison with evaluations and winner
        """
        # Evaluate both
        eval1 = self.evaluate(text1, rubric, context)
        eval2 = self.evaluate(text2, rubric, context)
        
        # Determine winner
        if eval1.overall_score > eval2.overall_score:
            winner = "text1"
            margin = eval1.overall_score - eval2.overall_score
        elif eval2.overall_score > eval1.overall_score:
            winner = "text2"
            margin = eval2.overall_score - eval1.overall_score
        else:
            winner = "tie"
            margin = 0.0
        
        # Get comparative reasoning
        comparison_prompt = f"""Compare these two versions and explain which is better and why:

**Version 1**:
{text1}

**Version 2**:
{text2}

**Scores**:
- Version 1: {eval1.overall_score}/10
- Version 2: {eval2.overall_score}/10

Provide a brief comparison focusing on key differences:"""
        
        comparison_response = self.llm.invoke(comparison_prompt)
        
        return {
            "text1_evaluation": eval1,
            "text2_evaluation": eval2,
            "winner": winner,
            "margin": round(margin, 2),
            "comparison": comparison_response.content
        }


class BatchJudge:
    """Batch evaluation with multiple judges"""
    
    def __init__(self, num_judges: int = 1):
        """
        Initialize batch judge
        
        Args:
            num_judges: Number of judges for consensus (default: 1)
        """
        self.judges = [LLMJudge() for _ in range(num_judges)]
    
    def evaluate_with_consensus(
        self,
        text: str,
        rubric: Rubric,
        context: Optional[str] = None
    ) -> Dict:
        """
        Evaluate with multiple judges and aggregate
        
        Args:
            text: Content to evaluate
            rubric: Evaluation rubric
            context: Optional context
            
        Returns:
            Aggregated evaluation with consensus scores
        """
        evaluations = []
        
        for judge in self.judges:
            result = judge.evaluate(text, rubric, context)
            evaluations.append(result)
        
        # Aggregate scores
        aggregated_scores = {}
        for criterion in rubric.criteria:
            scores = [
                e.criteria_scores.get(criterion.name, 0.0)
                for e in evaluations
            ]
            aggregated_scores[criterion.name] = sum(scores) / len(scores)
        
        # Calculate overall
        overall = sum(
            aggregated_scores[c.name] * c.weight
            for c in rubric.criteria
        )
        
        # Aggregate strengths and improvements
        all_strengths = []
        all_improvements = []
        
        for e in evaluations:
            all_strengths.extend(e.strengths)
            all_improvements.extend(e.improvements)
        
        # Deduplicate
        unique_strengths = list(set(all_strengths))[:5]
        unique_improvements = list(set(all_improvements))[:5]
        
        return {
            "consensus_score": round(overall, 2),
            "criteria_scores": aggregated_scores,
            "individual_evaluations": evaluations,
            "num_judges": len(self.judges),
            "strengths": unique_strengths,
            "improvements": unique_improvements
        }


if __name__ == "__main__":
    # Example usage
    judge = LLMJudge()
    
    # Sample marketing content
    content = """Introducing EcoBottle - the water bottle that loves the planet 
as much as you do! Made from 100% recycled materials, keeps drinks cold 
for 24 hours. Join the sustainability revolution today!"""
    
    # Evaluate
    rubric = get_rubric("marketing")
    result = judge.evaluate(content, rubric)
    
    print("="*70)
    print("EVALUATION RESULT")
    print("="*70)
    print(f"Overall Score: {result.overall_score}/10")
    print("\nCriteria Scores:")
    for criterion, score in result.criteria_scores.items():
        print(f"  {criterion}: {score}/10")
    
    print("\nStrengths:")
    for strength in result.strengths:
        print(f"  + {strength}")
    
    print("\nImprovements:")
    for improvement in result.improvements:
        print(f"  - {improvement}")
