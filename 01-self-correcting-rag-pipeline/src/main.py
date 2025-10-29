"""
Command-line interface for the Self-Correcting RAG Pipeline
"""
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

from rag_pipeline import SelfCorrectingRAG
from prepare_data import create_sample_documents

load_dotenv()


def setup_pipeline(args):
    """Setup the pipeline with sample data"""
    print("Setting up Self-Correcting RAG Pipeline...\n")
    
    # Create sample documents
    print("Step 1: Creating sample documents...")
    create_sample_documents()
    
    # Create vectorstore
    print("\nStep 2: Creating vectorstore...")
    rag = SelfCorrectingRAG(
        documents_path=args.documents_path,
        persist_directory=args.vectorstore_path,
        load_existing=False
    )
    
    print("\n✓ Setup complete!")
    print(f"Vectorstore saved to: {args.vectorstore_path}")
    
    return rag


def query_pipeline(args):
    """Query the RAG pipeline"""
    # Load pipeline
    print("Loading RAG Pipeline...\n")
    
    try:
        rag = SelfCorrectingRAG(
            persist_directory=args.vectorstore_path,
            load_existing=True,
            top_k=args.top_k,
            relevance_threshold=args.relevance_threshold,
            factcheck_threshold=args.factcheck_threshold,
            max_correction_loops=args.max_corrections
        )
    except Exception as e:
        print(f"Error loading vectorstore: {e}")
        print("\nTry running setup first: python src/main.py --setup")
        return
    
    # Process query
    print(f"Question: {args.query}\n")
    
    result = rag.query(
        args.query,
        enable_self_correction=args.enable_correction,
        return_intermediate=args.verbose
    )
    
    # Display results
    print("="*70)
    print("ANSWER")
    print("="*70)
    print(f"\n{result['answer']}\n")
    
    print("="*70)
    print("METADATA")
    print("="*70)
    print(f"Confidence Score:   {result['confidence_score']}/10")
    print(f"Is Consistent:      {result['is_consistent']}")
    print(f"Sources Used:       {result['sources_used']}")
    print(f"Correction Loops:   {result['correction_loops']}")
    
    if result.get('warning'):
        print(f"\n⚠️  Warning: {result['warning']}")
    
    if result.get('factual_errors') and len(result['factual_errors']) > 0:
        print(f"\nFactual Errors Found:")
        for error in result['factual_errors']:
            print(f"  - {error}")
    
    print(f"\nReasoning:\n{result['reasoning']}")
    
    if args.verbose and result.get('intermediate_results'):
        print("\n" + "="*70)
        print("INTERMEDIATE RESULTS")
        print("="*70)
        import json
        print(json.dumps(result['intermediate_results'], indent=2))


def interactive_mode(args):
    """Interactive query mode"""
    print("="*70)
    print("Self-Correcting RAG Pipeline - Interactive Mode")
    print("="*70)
    print("\nLoading pipeline...")
    
    try:
        rag = SelfCorrectingRAG(
            persist_directory=args.vectorstore_path,
            load_existing=True,
            top_k=args.top_k,
            relevance_threshold=args.relevance_threshold,
            factcheck_threshold=args.factcheck_threshold,
            max_correction_loops=args.max_corrections
        )
    except Exception as e:
        print(f"Error loading vectorstore: {e}")
        print("\nTry running setup first: python src/main.py --setup")
        return
    
    print("✓ Pipeline loaded!\n")
    print("Type your questions (or 'quit' to exit):\n")
    
    while True:
        try:
            question = input("❓ Question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not question:
                continue
            
            print("\n🤔 Processing...\n")
            
            result = rag.query(
                question,
                enable_self_correction=args.enable_correction,
                return_intermediate=False
            )
            
            print(f"💡 Answer: {result['answer']}\n")
            print(f"   Confidence: {result['confidence_score']}/10 | Sources: {result['sources_used']}\n")
            print("-"*70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Self-Correcting RAG Pipeline CLI"
    )
    
    # Modes
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup pipeline with sample documents"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query the pipeline"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode"
    )
    
    # Paths
    parser.add_argument(
        "--documents-path",
        type=str,
        default="data/sample_docs",
        help="Path to documents directory"
    )
    
    parser.add_argument(
        "--vectorstore-path",
        type=str,
        default="data/vectorstore",
        help="Path to vectorstore directory"
    )
    
    # Parameters
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of documents to retrieve"
    )
    
    parser.add_argument(
        "--relevance-threshold",
        type=float,
        default=0.7,
        help="Relevance filtering threshold"
    )
    
    parser.add_argument(
        "--factcheck-threshold",
        type=float,
        default=7.0,
        help="Fact-check score threshold"
    )
    
    parser.add_argument(
        "--max-corrections",
        type=int,
        default=2,
        help="Maximum correction loops"
    )
    
    parser.add_argument(
        "--no-correction",
        dest="enable_correction",
        action="store_false",
        help="Disable self-correction"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show intermediate results"
    )
    
    args = parser.parse_args()
    
    # Execute mode
    if args.setup:
        setup_pipeline(args)
    elif args.query:
        query_pipeline(args)
    elif args.interactive:
        interactive_mode(args)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  Setup:       python src/main.py --setup")
        print("  Query:       python src/main.py --query 'What is the Eiffel Tower?'")
        print("  Interactive: python src/main.py --interactive")


if __name__ == "__main__":
    main()
