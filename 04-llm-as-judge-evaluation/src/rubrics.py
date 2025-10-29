"""
Evaluation Rubrics for LLM-as-Judge

Defines structured criteria and scoring guidelines for different domains.
"""
from typing import Dict, List
from pydantic import BaseModel, Field


class Criterion(BaseModel):
    """Single evaluation criterion"""
    name: str
    weight: float = Field(ge=0, le=1)
    description: str
    scoring_guide: Dict[str, str] = Field(default_factory=dict)


class Rubric(BaseModel):
    """Complete evaluation rubric"""
    name: str
    description: str
    criteria: List[Criterion]
    
    def validate_weights(self) -> bool:
        """Ensure weights sum to 1.0"""
        total = sum(c.weight for c in self.criteria)
        return abs(total - 1.0) < 0.01


# Marketing Content Rubric
MARKETING_RUBRIC = Rubric(
    name="marketing",
    description="Evaluate marketing and advertising content",
    criteria=[
        Criterion(
            name="clarity",
            weight=0.20,
            description="Message is clear, easy to understand, and unambiguous",
            scoring_guide={
                "9-10": "Crystal clear message, instantly understandable",
                "7-8": "Clear message with minor ambiguities",
                "5-6": "Somewhat clear but requires effort to understand",
                "3-4": "Confusing or unclear in multiple areas",
                "1-2": "Very unclear, message is lost"
            }
        ),
        Criterion(
            name="persuasiveness",
            weight=0.25,
            description="Content is compelling, motivating, and drives action",
            scoring_guide={
                "9-10": "Highly compelling, strong motivation to act",
                "7-8": "Persuasive with good value proposition",
                "5-6": "Somewhat persuasive but lacks impact",
                "3-4": "Weak persuasion, unconvincing",
                "1-2": "Not persuasive, fails to motivate"
            }
        ),
        Criterion(
            name="brand_alignment",
            weight=0.20,
            description="Consistent with brand voice, tone, and values",
            scoring_guide={
                "9-10": "Perfect brand alignment, exemplifies brand voice",
                "7-8": "Good brand fit, minor inconsistencies",
                "5-6": "Acceptable but noticeable misalignment",
                "3-4": "Poor brand fit, inconsistent voice",
                "1-2": "Completely off-brand"
            }
        ),
        Criterion(
            name="creativity",
            weight=0.20,
            description="Original, engaging, and stands out",
            scoring_guide={
                "9-10": "Highly original and memorable",
                "7-8": "Creative with fresh approach",
                "5-6": "Somewhat creative but formulaic",
                "3-4": "Generic, lacks originality",
                "1-2": "Cliché and unoriginal"
            }
        ),
        Criterion(
            name="call_to_action",
            weight=0.15,
            description="Clear next steps and strong CTA",
            scoring_guide={
                "9-10": "Compelling CTA, crystal clear next steps",
                "7-8": "Good CTA, clear action",
                "5-6": "Acceptable CTA but could be stronger",
                "3-4": "Weak or vague CTA",
                "1-2": "No clear CTA or action"
            }
        )
    ]
)


# Technical Writing Rubric
TECHNICAL_RUBRIC = Rubric(
    name="technical",
    description="Evaluate technical documentation and explanations",
    criteria=[
        Criterion(
            name="accuracy",
            weight=0.30,
            description="Information is technically correct and precise",
            scoring_guide={
                "9-10": "Completely accurate, no errors",
                "7-8": "Accurate with minor imprecisions",
                "5-6": "Mostly accurate but has some errors",
                "3-4": "Multiple inaccuracies",
                "1-2": "Fundamentally incorrect"
            }
        ),
        Criterion(
            name="clarity",
            weight=0.25,
            description="Easy to understand for target audience",
            scoring_guide={
                "9-10": "Exceptionally clear, perfect for audience",
                "7-8": "Clear and understandable",
                "5-6": "Understandable but requires effort",
                "3-4": "Confusing or hard to follow",
                "1-2": "Very unclear, incomprehensible"
            }
        ),
        Criterion(
            name="completeness",
            weight=0.20,
            description="Covers all necessary aspects and details",
            scoring_guide={
                "9-10": "Comprehensive, covers everything needed",
                "7-8": "Complete with minor gaps",
                "5-6": "Adequate but missing some details",
                "3-4": "Incomplete, significant gaps",
                "1-2": "Very incomplete, major omissions"
            }
        ),
        Criterion(
            name="structure",
            weight=0.15,
            description="Well-organized and logically structured",
            scoring_guide={
                "9-10": "Perfectly organized, excellent flow",
                "7-8": "Well-structured, good organization",
                "5-6": "Acceptable structure but could improve",
                "3-4": "Poor organization, hard to follow",
                "1-2": "Chaotic, no clear structure"
            }
        ),
        Criterion(
            name="examples",
            weight=0.10,
            description="Includes helpful, relevant examples",
            scoring_guide={
                "9-10": "Excellent examples, highly illustrative",
                "7-8": "Good examples that help understanding",
                "5-6": "Some examples but could be better",
                "3-4": "Few or poor examples",
                "1-2": "No examples or irrelevant ones"
            }
        )
    ]
)


# Creative Content Rubric
CREATIVE_RUBRIC = Rubric(
    name="creative",
    description="Evaluate creative writing and artistic content",
    criteria=[
        Criterion(
            name="originality",
            weight=0.30,
            description="Unique, innovative, and fresh perspective",
            scoring_guide={
                "9-10": "Highly original and groundbreaking",
                "7-8": "Original with fresh ideas",
                "5-6": "Some originality but familiar",
                "3-4": "Derivative, little originality",
                "1-2": "Completely unoriginal, cliché"
            }
        ),
        Criterion(
            name="engagement",
            weight=0.25,
            description="Captures and holds attention",
            scoring_guide={
                "9-10": "Highly engaging, captivating",
                "7-8": "Engaging and interesting",
                "5-6": "Moderately engaging",
                "3-4": "Somewhat boring or dull",
                "1-2": "Very boring, fails to engage"
            }
        ),
        Criterion(
            name="emotion",
            weight=0.20,
            description="Evokes appropriate emotional response",
            scoring_guide={
                "9-10": "Powerful emotional impact",
                "7-8": "Strong emotional connection",
                "5-6": "Some emotional resonance",
                "3-4": "Weak emotional impact",
                "1-2": "No emotional connection"
            }
        ),
        Criterion(
            name="style",
            weight=0.15,
            description="Consistent, polished writing style",
            scoring_guide={
                "9-10": "Masterful style, perfectly executed",
                "7-8": "Strong style, well-crafted",
                "5-6": "Acceptable style, some inconsistencies",
                "3-4": "Weak style, inconsistent",
                "1-2": "Poor style, unprofessional"
            }
        ),
        Criterion(
            name="impact",
            weight=0.10,
            description="Memorable and leaves lasting impression",
            scoring_guide={
                "9-10": "Highly memorable, lasting impact",
                "7-8": "Memorable and effective",
                "5-6": "Some impact but forgettable",
                "3-4": "Little lasting impact",
                "1-2": "No impact, instantly forgettable"
            }
        )
    ]
)


# Customer Service Rubric
CUSTOMER_SERVICE_RUBRIC = Rubric(
    name="customer_service",
    description="Evaluate customer support and service responses",
    criteria=[
        Criterion(
            name="helpfulness",
            weight=0.30,
            description="Provides useful, actionable information",
            scoring_guide={
                "9-10": "Extremely helpful, solves problem completely",
                "7-8": "Very helpful, addresses key concerns",
                "5-6": "Somewhat helpful but incomplete",
                "3-4": "Not very helpful, vague",
                "1-2": "Unhelpful or misleading"
            }
        ),
        Criterion(
            name="empathy",
            weight=0.25,
            description="Shows understanding and care for customer",
            scoring_guide={
                "9-10": "Highly empathetic, shows genuine care",
                "7-8": "Empathetic and understanding",
                "5-6": "Some empathy but could be warmer",
                "3-4": "Little empathy, cold",
                "1-2": "No empathy, dismissive"
            }
        ),
        Criterion(
            name="professionalism",
            weight=0.20,
            description="Professional tone and appropriate language",
            scoring_guide={
                "9-10": "Perfectly professional",
                "7-8": "Professional and courteous",
                "5-6": "Acceptable professionalism",
                "3-4": "Somewhat unprofessional",
                "1-2": "Very unprofessional"
            }
        ),
        Criterion(
            name="clarity",
            weight=0.15,
            description="Clear instructions and explanations",
            scoring_guide={
                "9-10": "Crystal clear, easy to follow",
                "7-8": "Clear and understandable",
                "5-6": "Mostly clear but some confusion",
                "3-4": "Unclear or confusing",
                "1-2": "Very unclear"
            }
        ),
        Criterion(
            name="response_time_appropriateness",
            weight=0.10,
            description="Thoroughness appropriate for query complexity",
            scoring_guide={
                "9-10": "Perfect balance of detail and brevity",
                "7-8": "Good balance, appropriate length",
                "5-6": "Acceptable but could be better",
                "3-4": "Too brief or too lengthy",
                "1-2": "Inappropriate length"
            }
        )
    ]
)


# Rubric Registry
RUBRICS = {
    "marketing": MARKETING_RUBRIC,
    "technical": TECHNICAL_RUBRIC,
    "creative": CREATIVE_RUBRIC,
    "customer_service": CUSTOMER_SERVICE_RUBRIC,
}


def get_rubric(name: str) -> Rubric:
    """
    Get rubric by name
    
    Args:
        name: Rubric name
        
    Returns:
        Rubric instance
        
    Raises:
        ValueError: If rubric not found
    """
    if name not in RUBRICS:
        raise ValueError(
            f"Rubric '{name}' not found. Available: {list(RUBRICS.keys())}"
        )
    return RUBRICS[name]


def list_rubrics() -> List[str]:
    """List available rubric names"""
    return list(RUBRICS.keys())


def create_custom_rubric(
    name: str,
    description: str,
    criteria: List[Dict]
) -> Rubric:
    """
    Create a custom rubric
    
    Args:
        name: Rubric name
        description: Rubric description
        criteria: List of criterion dictionaries
        
    Returns:
        Custom Rubric instance
    """
    criterion_objects = []
    
    for crit in criteria:
        criterion_objects.append(
            Criterion(
                name=crit['name'],
                weight=crit.get('weight', 1.0 / len(criteria)),
                description=crit['description'],
                scoring_guide=crit.get('scoring_guide', {})
            )
        )
    
    rubric = Rubric(
        name=name,
        description=description,
        criteria=criterion_objects
    )
    
    # Validate weights
    if not rubric.validate_weights():
        # Normalize weights
        total = sum(c.weight for c in rubric.criteria)
        for c in rubric.criteria:
            c.weight = c.weight / total
    
    return rubric


if __name__ == "__main__":
    # Example: Print all rubrics
    print("Available Evaluation Rubrics:")
    print("="*70)
    
    for rubric_name in list_rubrics():
        rubric = get_rubric(rubric_name)
        print(f"\n{rubric.name.upper()}: {rubric.description}")
        print(f"Criteria ({len(rubric.criteria)}):")
        
        for criterion in rubric.criteria:
            print(f"  - {criterion.name}: {criterion.weight*100:.0f}% - {criterion.description}")
