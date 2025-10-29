"""
Streamlit Web Interface for Multi-Agent Workflow Automator
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from workflow_automator import MarketingCampaignCrew
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="Multi-Agent Campaign Creator",
    page_icon="🎨",
    layout="wide"
)

# Initialize session state
if "campaign_history" not in st.session_state:
    st.session_state.campaign_history = []

# Title and description
st.title("🎨 Multi-Agent Marketing Campaign Creator")
st.markdown("""
This system uses four specialized AI agents to create complete marketing campaigns:
- **Research Agent**: Analyzes market trends and competition
- **Copywriter Agent**: Crafts compelling ad copy
- **Art Director Agent**: Creates visual concepts
- **Manager Agent**: Assembles comprehensive brief
""")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.info("""
    **How it works:**
    1. Enter product details
    2. Define target audience
    3. Let agents collaborate
    4. Get complete campaign brief
    """)
    
    st.divider()
    
    st.subheader("About")
    st.markdown("""
    **Part of 50 Days AI Challenge**
    
    Built by:
    - **Surya Arul** (Implementation)
    - Based on roadmap by **Sri Nithya Thimmaraju**
    
    [Medium](https://medium.com/@arulsurya05) | [LinkedIn](https://www.linkedin.com/in/surya-arul/)
    """)

# Main interface
st.subheader("📝 Campaign Details")

col1, col2 = st.columns(2)

with col1:
    product = st.text_area(
        "Product/Service",
        placeholder="e.g., Eco-Friendly Water Bottle made from recycled ocean plastic",
        height=100
    )

with col2:
    audience = st.text_area(
        "Target Audience",
        placeholder="e.g., Environmentally conscious millennials aged 25-35",
        height=100
    )

campaign_goal = st.text_input(
    "Campaign Goal (Optional)",
    placeholder="e.g., Launch new product line and build brand awareness"
)

# Generate button
if st.button("🚀 Generate Campaign", type="primary"):
    if not product or not audience:
        st.error("Please fill in both Product and Target Audience fields.")
    else:
        with st.spinner("🤖 Agents are collaborating to create your campaign..."):
            try:
                # Create crew and generate campaign
                crew = MarketingCampaignCrew()
                result = crew.create_campaign(
                    product=product,
                    audience=audience,
                    campaign_goal=campaign_goal if campaign_goal else None
                )
                
                # Store in history
                st.session_state.campaign_history.append(result)
                
                # Display results
                st.success("✅ Campaign created successfully!")
                
                st.divider()
                
                st.subheader("📋 Campaign Brief")
                
                # Display the brief in a nice format
                brief_text = result["campaign_brief"]
                
                # Try to parse sections if possible
                st.markdown(brief_text)
                
                # Download button
                st.download_button(
                    label="📥 Download Campaign Brief",
                    data=brief_text,
                    file_name=f"campaign_brief_{product[:30].replace(' ', '_')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error generating campaign: {str(e)}")
                st.info("Make sure your API keys are set in the .env file.")

# Campaign history
if st.session_state.campaign_history:
    st.divider()
    st.subheader("📚 Campaign History")
    
    for i, campaign in enumerate(reversed(st.session_state.campaign_history), 1):
        with st.expander(f"Campaign {len(st.session_state.campaign_history) - i + 1}: {campaign['product'][:50]}..."):
            st.write(f"**Product**: {campaign['product']}")
            st.write(f"**Audience**: {campaign['audience']}")
            st.divider()
            st.markdown(campaign['campaign_brief'])

# Clear history button
if st.session_state.campaign_history:
    if st.button("🗑️ Clear History"):
        st.session_state.campaign_history = []
        st.rerun()
