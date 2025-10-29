"""
Streamlit Interface for LLM-as-Judge Evaluation

Interactive UI for evaluating content and comparing outputs.
"""
import streamlit as st
import json
from judge import LLMJudge
from rubrics import get_rubric, list_rubrics
from evaluator import BatchEvaluator
from dotenv import load_dotenv

load_dotenv()


def initialize_session_state():
    """Initialize Streamlit session state"""
    if 'judge' not in st.session_state:
        st.session_state.judge = None
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'current_rubric' not in st.session_state:
        st.session_state.current_rubric = 'marketing'


def load_judge():
    """Load LLM judge"""
    if st.session_state.judge is None:
        with st.spinner("Loading LLM Judge..."):
            st.session_state.judge = LLMJudge()


def main():
    st.set_page_config(
        page_title="LLM-as-Judge Evaluator",
        page_icon="⚖️",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Header
    st.title("⚖️ LLM-as-Judge Evaluation Framework")
    st.markdown("Evaluate content quality using AI judges with structured rubrics")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Rubric selection
        rubric_name = st.selectbox(
            "Evaluation Rubric",
            options=list_rubrics(),
            index=list_rubrics().index(st.session_state.current_rubric)
        )
        
        if rubric_name != st.session_state.current_rubric:
            st.session_state.current_rubric = rubric_name
        
        rubric = get_rubric(rubric_name)
        
        st.markdown("---")
        
        # Show rubric details
        with st.expander("📋 Rubric Details", expanded=False):
            st.markdown(f"**{rubric.name}**")
            st.caption(rubric.description)
            
            for criterion in rubric.criteria:
                st.markdown(f"**{criterion.name}** ({criterion.weight*100:.0f}%)")
                st.caption(criterion.description)
        
        st.markdown("---")
        
        # Mode selection
        st.header("🎯 Mode")
        mode = st.radio(
            "Select evaluation mode:",
            options=["Single Evaluation", "Compare Two", "Batch Evaluation"],
            index=0
        )
        
        st.markdown("---")
        
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.rerun()
    
    # Load judge
    load_judge()
    
    # Main content based on mode
    if mode == "Single Evaluation":
        single_evaluation_mode(rubric)
    elif mode == "Compare Two":
        comparison_mode(rubric)
    else:
        batch_evaluation_mode(rubric)
    
    # Show history
    if st.session_state.history:
        st.markdown("---")
        with st.expander("📜 Evaluation History", expanded=False):
            for idx, item in enumerate(reversed(st.session_state.history)):
                st.markdown(f"**{len(st.session_state.history) - idx}. {item['type']}** - Score: {item.get('score', 'N/A')}")
                st.caption(f"Rubric: {item['rubric']} | Time: {item.get('timestamp', 'N/A')}")
                st.markdown("---")


def single_evaluation_mode(rubric):
    """Single content evaluation"""
    st.header("📝 Single Content Evaluation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        text = st.text_area(
            "Content to Evaluate",
            height=200,
            placeholder="Enter the content you want to evaluate..."
        )
    
    with col2:
        context = st.text_area(
            "Context (Optional)",
            height=200,
            placeholder="E.g., 'Instagram ad for millennials'"
        )
    
    if st.button("🔍 Evaluate", type="primary"):
        if not text:
            st.error("Please enter content to evaluate")
            return
        
        with st.spinner("Evaluating..."):
            try:
                result = st.session_state.judge.evaluate(
                    text,
                    rubric,
                    context if context else None
                )
                
                # Display results
                display_evaluation_result(result, text)
                
                # Add to history
                st.session_state.history.append({
                    'type': 'Single Evaluation',
                    'rubric': rubric.name,
                    'score': result.overall_score,
                    'text': text[:100] + "...",
                    'timestamp': st.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
            except Exception as e:
                st.error(f"Error during evaluation: {e}")


def comparison_mode(rubric):
    """Compare two content versions"""
    st.header("🔄 Compare Two Versions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Version A")
        text1 = st.text_area(
            "Content A",
            height=200,
            placeholder="Enter first version...",
            key="text1"
        )
    
    with col2:
        st.subheader("Version B")
        text2 = st.text_area(
            "Content B",
            height=200,
            placeholder="Enter second version...",
            key="text2"
        )
    
    context = st.text_input(
        "Context (Optional)",
        placeholder="E.g., 'Email subject line for product launch'"
    )
    
    if st.button("⚖️ Compare", type="primary"):
        if not text1 or not text2:
            st.error("Please enter both versions to compare")
            return
        
        with st.spinner("Comparing..."):
            try:
                comparison = st.session_state.judge.compare(
                    text1,
                    text2,
                    rubric,
                    context if context else None
                )
                
                # Display comparison
                display_comparison_result(comparison, text1, text2)
                
                # Add to history
                st.session_state.history.append({
                    'type': 'Comparison',
                    'rubric': rubric.name,
                    'score': f"A: {comparison['text1_evaluation'].overall_score}, B: {comparison['text2_evaluation'].overall_score}",
                    'winner': comparison['winner'],
                    'timestamp': st.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
            except Exception as e:
                st.error(f"Error during comparison: {e}")


def batch_evaluation_mode(rubric):
    """Batch evaluation from file"""
    st.header("📊 Batch Evaluation")
    
    st.markdown("""
    Upload a JSONL file with content to evaluate. Each line should be:
    ```json
    {"id": "item_1", "text": "Content here", "context": "Optional context"}
    ```
    """)
    
    uploaded_file = st.file_uploader(
        "Upload JSONL file",
        type=['jsonl', 'json']
    )
    
    if uploaded_file:
        # Save temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        if st.button("🚀 Start Batch Evaluation", type="primary"):
            with st.spinner("Evaluating batch..."):
                try:
                    evaluator = BatchEvaluator(rubric_name=rubric.name)
                    results = evaluator.evaluate_from_file(tmp_path, save_results=True)
                    
                    # Display summary
                    st.success(f"✓ Evaluated {len(results)} items")
                    
                    # Statistics
                    scores = [
                        r['evaluation']['overall_score']
                        for r in results if 'evaluation' in r
                    ]
                    
                    if scores:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Mean Score", f"{sum(scores)/len(scores):.2f}")
                        with col2:
                            st.metric("Min Score", f"{min(scores):.2f}")
                        with col3:
                            st.metric("Max Score", f"{max(scores):.2f}")
                        
                        # Generate report
                        st.markdown("### 📄 Generate Report")
                        report_format = st.radio(
                            "Report Format",
                            options=["markdown", "html"],
                            horizontal=True
                        )
                        
                        if st.button("Generate Report"):
                            report = evaluator.generate_report(results, report_format)
                            st.download_button(
                                label="📥 Download Report",
                                data=report,
                                file_name=f"evaluation_report.{report_format}",
                                mime="text/markdown" if report_format == "markdown" else "text/html"
                            )
                
                except Exception as e:
                    st.error(f"Error during batch evaluation: {e}")


def display_evaluation_result(result, text):
    """Display evaluation result"""
    st.markdown("---")
    st.header("📊 Evaluation Results")
    
    # Overall score
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.metric(
            "Overall Score",
            f"{result.overall_score}/10",
            delta=f"{result.overall_score - 7.0:+.1f} vs baseline"
        )
    
    # Criteria scores
    st.subheader("Criteria Breakdown")
    
    cols = st.columns(len(result.criteria_scores))
    
    for idx, (criterion, score) in enumerate(result.criteria_scores.items()):
        with cols[idx]:
            st.metric(criterion.replace('_', ' ').title(), f"{score}/10")
    
    # Detailed reasoning
    st.subheader("Detailed Reasoning")
    
    for criterion, reasoning in result.reasoning.items():
        with st.expander(f"📌 {criterion.replace('_', ' ').title()}"):
            st.write(reasoning)
    
    # Strengths and improvements
    col_s, col_i = st.columns(2)
    
    with col_s:
        st.subheader("✅ Strengths")
        for strength in result.strengths:
            st.success(strength)
    
    with col_i:
        st.subheader("💡 Improvements")
        for improvement in result.improvements:
            st.info(improvement)


def display_comparison_result(comparison, text1, text2):
    """Display comparison result"""
    st.markdown("---")
    st.header("⚖️ Comparison Results")
    
    # Winner
    winner = comparison['winner']
    margin = comparison['margin']
    
    if winner == "tie":
        st.info("🤝 It's a tie! Both versions scored equally.")
    else:
        winner_label = "Version A" if winner == "text1" else "Version B"
        st.success(f"🏆 Winner: **{winner_label}** (by {margin:.2f} points)")
    
    # Side-by-side scores
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Version A")
        st.metric("Score", f"{comparison['text1_evaluation'].overall_score}/10")
        
        with st.expander("Details"):
            for criterion, score in comparison['text1_evaluation'].criteria_scores.items():
                st.write(f"**{criterion}**: {score}/10")
    
    with col2:
        st.subheader("Version B")
        st.metric("Score", f"{comparison['text2_evaluation'].overall_score}/10")
        
        with st.expander("Details"):
            for criterion, score in comparison['text2_evaluation'].criteria_scores.items():
                st.write(f"**{criterion}**: {score}/10")
    
    # Comparison analysis
    st.subheader("🔍 Comparative Analysis")
    st.write(comparison['comparison'])


if __name__ == "__main__":
    main()
