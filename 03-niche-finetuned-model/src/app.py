"""
Streamlit Interface for Model Comparison

Interactive UI to compare base Llama 3 vs fine-tuned model responses.
"""
import streamlit as st
import os
from pathlib import Path
from inference import FineTunedModel, ModelComparison
from dotenv import load_dotenv

load_dotenv()


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'comparison' not in st.session_state:
        st.session_state.comparison = None
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False


def load_models():
    """Load both models"""
    if not st.session_state.model_loaded:
        with st.spinner("Loading models... This may take a minute..."):
            try:
                st.session_state.comparison = ModelComparison(
                    finetuned_model_path="models/llama3-python-api"
                )
                st.session_state.model_loaded = True
                st.success("✓ Models loaded successfully!")
            except Exception as e:
                st.error(f"Error loading models: {e}")
                st.stop()


def main():
    st.set_page_config(
        page_title="Fine-Tuned Model Comparison",
        page_icon="🤖",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Header
    st.title("🤖 Fine-Tuned Python API Assistant")
    st.markdown("Compare **Base Llama 3 8B** vs **Fine-Tuned** on Python library questions")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        model_path = st.text_input(
            "Fine-tuned Model Path",
            value="models/llama3-python-api",
            help="Path to your fine-tuned model"
        )
        
        st.markdown("---")
        
        st.header("📊 Model Info")
        st.info("""
        **Base Model**: Llama 3 8B
        
        **Fine-Tuned On**: Python API docs
        - requests
        - pandas
        - numpy
        
        **Training**: LoRA/PEFT (16 rank)
        """)
        
        st.markdown("---")
        
        if st.button("🔄 Load/Reload Models"):
            st.session_state.model_loaded = False
            load_models()
        
        st.markdown("---")
        
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()
    
    # Load models on startup
    load_models()
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🔷 Base Llama 3 8B")
    
    with col2:
        st.header("🔶 Fine-Tuned Model")
    
    # Input area
    st.markdown("---")
    
    with st.form("query_form"):
        instruction = st.text_area(
            "Ask a Python API question:",
            height=100,
            placeholder="How do I make a POST request with JSON data using the requests library?"
        )
        
        col_gen1, col_gen2 = st.columns([1, 4])
        with col_gen1:
            submitted = st.form_submit_button("Generate Responses", type="primary")
    
    # Generate responses
    if submitted and instruction:
        with st.spinner("Generating responses..."):
            try:
                result = st.session_state.comparison.compare(instruction)
                st.session_state.history.append(result)
            except Exception as e:
                st.error(f"Error generating responses: {e}")
    
    # Display latest result
    if st.session_state.history:
        latest = st.session_state.history[-1]
        
        st.markdown("### Question:")
        st.info(latest['instruction'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Base Model Response")
            with st.container():
                st.markdown(latest['base_response'])
        
        with col2:
            st.markdown("#### Fine-Tuned Model Response")
            with st.container():
                st.markdown(latest['finetuned_response'])
        
        # Quality indicators
        st.markdown("---")
        st.markdown("### 📊 Quick Analysis")
        
        col_q1, col_q2, col_q3 = st.columns(3)
        
        base_has_code = "```" in latest['base_response']
        fine_has_code = "```" in latest['finetuned_response']
        
        with col_q1:
            st.metric(
                "Base Model - Has Code",
                "✓" if base_has_code else "✗",
                delta=None
            )
        
        with col_q2:
            st.metric(
                "Fine-Tuned - Has Code",
                "✓" if fine_has_code else "✗",
                delta=None
            )
        
        with col_q3:
            base_len = len(latest['base_response'])
            fine_len = len(latest['finetuned_response'])
            diff = fine_len - base_len
            st.metric(
                "Response Length Diff",
                f"{diff:+d} chars",
                delta=f"{(diff/base_len*100):+.1f}%" if base_len > 0 else "N/A"
            )
    
    # History
    if len(st.session_state.history) > 1:
        st.markdown("---")
        with st.expander("📜 History", expanded=False):
            for idx, item in enumerate(reversed(st.session_state.history[:-1])):
                st.markdown(f"**{len(st.session_state.history) - idx - 1}. {item['instruction'][:100]}...**")
                
                col_h1, col_h2 = st.columns(2)
                
                with col_h1:
                    with st.container():
                        st.caption("Base Model")
                        st.text(item['base_response'][:200] + "...")
                
                with col_h2:
                    with st.container():
                        st.caption("Fine-Tuned Model")
                        st.text(item['finetuned_response'][:200] + "...")
                
                st.markdown("---")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <p><strong>Project 3: Niche Fine-Tuned Model</strong></p>
        <p>Part of the 50-Day AI Challenge</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
