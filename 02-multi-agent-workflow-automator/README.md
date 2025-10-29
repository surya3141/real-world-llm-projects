# Multi-Agent Workflow Automator

## Overview
A production-ready multi-agent system using CrewAI that automates complex workflows through specialized AI agents collaborating together. This project demonstrates how to build a "Marketing Campaign Creator" team that researches, writes, designs, and assembles complete marketing briefs.

## Architecture

### Agents

1. **Research Agent**
   - Role: Market and trend analyst
   - Tools: Web search, data analysis
   - Output: Market research and trend insights

2. **Copywriter Agent**
   - Role: Creative writer
   - Tools: None (pure LLM generation)
   - Output: Engaging ad copy and headlines

3. **Art Director Agent**
   - Role: Visual concept creator
   - Tools: Image generation prompt creation
   - Output: Detailed image prompts for DALL-E/Stable Diffusion

4. **Manager Agent**
   - Role: Project coordinator
   - Tools: None (orchestration)
   - Output: Assembled final marketing brief

## Features
- 🤖 Specialized AI agents with distinct roles
- 🔄 Collaborative workflow with information passing
- 🎯 Context-aware agent interactions
- 📊 Progress tracking and logging
- 🎨 Multi-modal output (text + image prompts)
- 🔧 Customizable agent behaviors

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_for_search (optional)
```

## Usage

### Basic Usage

```python
from workflow_automator import MarketingCampaignCrew

# Initialize the crew
crew = MarketingCampaignCrew()

# Run campaign creation
result = crew.create_campaign(
    product="Eco-Friendly Water Bottle",
    target_audience="Environmentally conscious millennials",
    campaign_goal="Launch new product line"
)

print(result)
```

### Running the Demo

```bash
# CLI interface
python src/main.py --product "Your Product" --audience "Target Audience"

# Web interface
streamlit run src/app.py
```

## Project Structure

```
02-multi-agent-workflow-automator/
├── src/
│   ├── agents/
│   │   ├── research_agent.py
│   │   ├── copywriter_agent.py
│   │   ├── art_director_agent.py
│   │   └── manager_agent.py
│   ├── tools/
│   │   ├── search_tool.py
│   │   └── analysis_tool.py
│   ├── workflow_automator.py
│   ├── main.py
│   └── app.py
├── examples/
│   └── sample_campaigns.json
├── requirements.txt
├── .env.example
└── README.md
```

## How It Works

1. **Manager Agent** receives the brief and creates tasks
2. **Research Agent** analyzes market trends and competition
3. **Copywriter Agent** creates compelling ad copy based on research
4. **Art Director Agent** generates image prompts aligned with copy
5. **Manager Agent** assembles everything into final deliverable

## Example Output

```json
{
  "campaign_name": "Pure Earth Hydration",
  "market_research": {
    "trends": ["Sustainability", "Minimalism", "Health-conscious"],
    "target_insights": "Millennials value authenticity and eco-impact"
  },
  "ad_copy": {
    "headline": "Drink Pure. Live Green. Stay Hydrated.",
    "body": "Our bottles aren't just eco-friendly—they're a statement...",
    "cta": "Join the Revolution"
  },
  "visual_concepts": [
    {
      "prompt": "Minimalist eco-friendly water bottle on moss...",
      "style": "Clean, natural lighting, product photography"
    }
  ],
  "brief": "Complete assembled marketing brief..."
}
```

## Configuration

Edit `config.yaml`:

```yaml
agents:
  research:
    model: gpt-4o-mini
    temperature: 0.3
  copywriter:
    model: gpt-4o
    temperature: 0.9
  art_director:
    model: gpt-4o
    temperature: 0.8
  manager:
    model: gpt-4o-mini
    temperature: 0.2

workflow:
  max_iterations: 5
  allow_delegation: true
```

## Testing

```bash
pytest tests/ --cov=src
```

## Use Cases

- Marketing campaign creation
- Content production workflows
- Product launch planning
- Social media strategy
- Brand development

## License

MIT License

## Authors

**Sri Nithya Thimmaraju** & **Surya Arul**

Part of the **50 Days AI Challenge** 🚀
