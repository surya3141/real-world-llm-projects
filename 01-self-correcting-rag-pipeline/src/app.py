"""
Streamlit Web Interface for Self-Correcting RAG Pipeline
"""
import streamlit as st
import sys
from pathlib import Path
import os

# Add src to path
sys.path.append(str(Path(__file__).parent))

from rag_pipeline import SelfCorrectingRAG
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="Self-Correcting RAG",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Title and description
st.title("🔍 Self-Correcting RAG Pipeline")
st.markdown("""
This system addresses hallucination in RAG systems through a multi-agent architecture:
- **Relevance Agent**: Filters retrieved documents for relevance
- **Generator Agent**: Creates answers from filtered context
- **Fact-Check Agent**: Validates factual consistency
""")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Vectorstore setup
    st.subheader("1. Vectorstore")
    vectorstore_path = st.text_input(
        "Vectorstore Path",
        value="data/vectorstore"
    )
    
    documents_path = st.text_input(
        "Documents Path (for new vectorstore)",
        value="data/documents"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Load Vectorstore"):
            with st.spinner("Loading vectorstore..."):
                try:
                    st.session_state.rag_pipeline = SelfCorrectingRAG(
                        persist_directory=vectorstore_path,
                        load_existing=True
                    )
                    st.success("✓ Vectorstore loaded!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("Create New"):
            with st.spinner("Creating vectorstore..."):
                try:
                    st.session_state.rag_pipeline = SelfCorrectingRAG(
                        documents_path=documents_path,
                        persist_directory=vectorstore_path,
                        load_existing=False
                    )
                    st.success("✓ Vectorstore created!")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.divider()
    
    # Pipeline parameters
    st.subheader("2. Pipeline Parameters")
    
    top_k = st.slider("Documents to Retrieve", 1, 10, 5)
    relevance_threshold = st.slider("Relevance Threshold", 0.0, 1.0, 0.7, 0.1)
    factcheck_threshold = st.slider("Fact-Check Threshold", 0.0, 10.0, 7.0, 0.5)
    
    enable_self_correction = st.checkbox("Enable Self-Correction", value=True)
    max_correction_loops = st.slider("Max Correction Loops", 1, 5, 2)
    
    show_intermediate = st.checkbox("Show Intermediate Results", value=False)
    
    st.divider()
    
    # About
    st.subheader("About")
    st.markdown("""
    **Part of 50 Days AI Challenge**
    
    Created by:
    - Sri Nithya Thimmaraju
    - Surya Arul
    
    [Medium Articles](https://medium.com/@nithya-thimmaraju)
    """)

# Main interface
if st.session_state.rag_pipeline is None:
    st.info("👈 Please load or create a vectorstore from the sidebar to get started.")
else:
    # Chat interface
    st.subheader("💬 Ask a Question")
    
    # Display chat history
    for i, chat in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(chat["question"])
        
        with st.chat_message("assistant"):
            st.write(chat["answer"])
            
            # Show metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Confidence", f"{chat['confidence_score']}/10")
            col2.metric("Sources", chat['sources_used'])
            col3.metric("Corrections", chat['correction_loops'])
            
            # Show details in expander
            with st.expander("View Details"):
                st.write("**Reasoning:**")
                st.write(chat['reasoning'])
                
                if chat.get('factual_errors'):
                    st.write("**Factual Errors:**")
                    for error in chat['factual_errors']:
                        st.write(f"- {error}")
    
    # Input
    question = st.chat_input("Enter your question...")
    
    if question:
        # Update pipeline parameters
        st.session_state.rag_pipeline.top_k = top_k
        st.session_state.rag_pipeline.relevance_threshold = relevance_threshold
        st.session_state.rag_pipeline.factcheck_threshold = factcheck_threshold
        st.session_state.rag_pipeline.max_correction_loops = max_correction_loops
        
        # Display user message
        with st.chat_message("user"):
            st.write(question)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                result = st.session_state.rag_pipeline.query(
                    question,
                    enable_self_correction=enable_self_correction,
                    return_intermediate=show_intermediate
                )
                
                # Display answer
                st.write(result['answer'])
                
                # Show metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Confidence", f"{result['confidence_score']}/10")
                col2.metric("Sources", result['sources_used'])
                col3.metric("Corrections", result['correction_loops'])
                
                # Show details in expander
                with st.expander("View Details"):
                    st.write("**Reasoning:**")
                    st.write(result['reasoning'])
                    
                    if result.get('factual_errors'):
                        st.write("**Factual Errors:**")
                        for error in result['factual_errors']:
                            st.write(f"- {error}")
                    
                    # Show intermediate results if enabled
                    if show_intermediate and result.get('intermediate_results'):
                        st.write("**Intermediate Results:**")
                        st.json(result['intermediate_results'])
        
        # Add to chat history
        st.session_state.chat_history.append({
            "question": question,
            "answer": result['answer'],
            "confidence_score": result['confidence_score'],
            "sources_used": result['sources_used'],
            "correction_loops": result['correction_loops'],
            "reasoning": result['reasoning'],
            "factual_errors": result.get('factual_errors', [])
        })
        
        st.rerun()
    
    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
