"""
Multi-Agent Marketing Campaign Creator using CrewAI
"""
from typing import Dict, Optional
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
import os

load_dotenv()


class MarketingCampaignCrew:
    """
    A multi-agent system that creates complete marketing campaigns.
    
    Agents:
    - Research Agent: Analyzes market trends and competition
    - Copywriter Agent: Creates compelling ad copy
    - Art Director Agent: Generates visual concepts and image prompts
    - Manager Agent: Coordinates and assembles final brief
    """
    
    def __init__(self):
        # Initialize tools
        self.search_tool = SerperDevTool() if os.getenv("SERPER_API_KEY") else None
        
        # Create agents
        self.research_agent = self._create_research_agent()
        self.copywriter_agent = self._create_copywriter_agent()
        self.art_director_agent = self._create_art_director_agent()
        self.manager_agent = self._create_manager_agent()
    
    def _create_research_agent(self) -> Agent:
        """Create the Market Research Agent"""
        tools = [self.search_tool] if self.search_tool else []
        
        return Agent(
            role='Market Research Analyst',
            goal='Analyze market trends, competition, and target audience for {product} targeting {audience}',
            backstory="""You are an expert market researcher with 10 years of experience 
            in consumer behavior analysis. You excel at identifying trends, understanding 
            what motivates customers, and finding market gaps. You use data-driven insights 
            to inform marketing strategies.""",
            tools=tools,
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
    
    def _create_copywriter_agent(self) -> Agent:
        """Create the Copywriter Agent"""
        return Agent(
            role='Creative Copywriter',
            goal='Create compelling, emotionally resonant ad copy for {product} targeting {audience}',
            backstory="""You are an award-winning copywriter known for creating 
            campaigns that go viral. You understand how to translate features into 
            benefits, create urgency without being pushy, and write copy that converts. 
            You've worked with Fortune 500 brands and understand various tones from 
            professional to casual.""",
            tools=[],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def _create_art_director_agent(self) -> Agent:
        """Create the Art Director Agent"""
        return Agent(
            role='Art Director & Visual Strategist',
            goal='Create visual concepts and detailed image generation prompts for {product} campaign',
            backstory="""You are a creative director with expertise in visual 
            storytelling, product photography, and brand identity. You understand 
            composition, color theory, and how to create images that convert. You've 
            art directed campaigns for major brands and know how to create visuals 
            that align with copy and resonate with target audiences.""",
            tools=[],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def _create_manager_agent(self) -> Agent:
        """Create the Campaign Manager Agent"""
        return Agent(
            role='Campaign Manager',
            goal='Coordinate the team and assemble a comprehensive marketing brief for {product}',
            backstory="""You are a seasoned campaign manager with 15 years of 
            experience leading creative teams. You know how to extract the best work 
            from each team member, ensure coherence across all deliverables, and 
            create compelling presentations for clients. You're detail-oriented but 
            also see the big picture.""",
            tools=[],
            verbose=True,
            allow_delegation=True,
            max_iter=3
        )
    
    def create_campaign(
        self, 
        product: str, 
        audience: str,
        campaign_goal: Optional[str] = None
    ) -> Dict:
        """
        Create a complete marketing campaign.
        
        Args:
            product: Product or service to market
            audience: Target audience description
            campaign_goal: Optional specific campaign goal
            
        Returns:
            Dict with complete campaign brief
        """
        # Define tasks
        research_task = Task(
            description=f"""Conduct comprehensive market research for {product} targeting {audience}.
            
            Your research should include:
            1. Current market trends in this category
            2. Competitive analysis (key players, their positioning)
            3. Target audience insights (demographics, psychographics, pain points)
            4. Market gaps and opportunities
            5. Key messaging angles that would resonate
            
            Provide actionable insights that the copywriter and art director can use.
            """,
            agent=self.research_agent,
            expected_output="Comprehensive market research report with trends, competitor analysis, and target audience insights"
        )
        
        copywriting_task = Task(
            description=f"""Using the market research insights, create compelling ad copy for {product}.
            
            Your deliverables should include:
            1. Campaign name/tagline
            2. Main headline (attention-grabbing, benefit-focused)
            3. Body copy (2-3 short paragraphs, emotionally resonant)
            4. 3 alternative subheadlines
            5. Clear call-to-action
            6. Tone and voice guidelines
            
            Make it memorable, persuasive, and aligned with the target audience's values.
            """,
            agent=self.copywriter_agent,
            expected_output="Complete ad copy package with headlines, body copy, and CTAs",
            context=[research_task]
        )
        
        art_direction_task = Task(
            description=f"""Create visual concepts for the {product} campaign that align with the copy.
            
            Your deliverables should include:
            1. 3 distinct visual concepts with detailed image generation prompts
            2. Each prompt should specify: composition, lighting, style, mood, colors
            3. Color palette (hex codes)
            4. Typography recommendations
            5. Platform-specific considerations (Instagram, web, print)
            
            Ensure visuals support and enhance the messaging.
            """,
            agent=self.art_director_agent,
            expected_output="3 visual concepts with detailed image generation prompts and brand guidelines",
            context=[research_task, copywriting_task]
        )
        
        assembly_task = Task(
            description=f"""Assemble all deliverables into a comprehensive marketing campaign brief.
            
            Your brief should include:
            1. Executive summary
            2. Target audience profile
            3. Market positioning
            4. Creative strategy (copy + rationale)
            5. Visual direction (concepts + rationale)
            6. Recommended channels
            7. Budget estimate (for execution)
            8. Success metrics to track
            
            Make it client-ready and actionable.
            """,
            agent=self.manager_agent,
            expected_output="Complete marketing campaign brief ready for client presentation",
            context=[research_task, copywriting_task, art_direction_task]
        )
        
        # Create crew
        crew = Crew(
            agents=[
                self.research_agent,
                self.copywriter_agent,
                self.art_director_agent,
                self.manager_agent
            ],
            tasks=[
                research_task,
                copywriting_task,
                art_direction_task,
                assembly_task
            ],
            process=Process.sequential,
            verbose=2
        )
        
        # Execute
        inputs = {
            "product": product,
            "audience": audience
        }
        
        if campaign_goal:
            inputs["campaign_goal"] = campaign_goal
        
        result = crew.kickoff(inputs=inputs)
        
        return {
            "campaign_brief": result,
            "product": product,
            "audience": audience
        }


if __name__ == "__main__":
    # Example usage
    print("="*70)
    print("Multi-Agent Marketing Campaign Creator")
    print("="*70)
    
    crew = MarketingCampaignCrew()
    
    result = crew.create_campaign(
        product="Eco-Friendly Water Bottle made from recycled ocean plastic",
        audience="Environmentally conscious millennials aged 25-35",
        campaign_goal="Launch new product line and build brand awareness"
    )
    
    print("\n" + "="*70)
    print("CAMPAIGN BRIEF")
    print("="*70)
    print(result["campaign_brief"])
