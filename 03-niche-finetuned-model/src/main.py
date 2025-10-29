"""
Command-line Interface for Fine-Tuning Pipeline

Provides commands for data preparation, training, evaluation, and inference.
"""
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def prepare_data(args):
    """Prepare training data"""
    from data_curation import PythonAPICurator
    
    print("="*70)
    print("Data Preparation")
    print("="*70)
    
    libraries = args.libraries if args.libraries else ['requests', 'pandas', 'numpy']
    output_dir = args.output_dir or "data"
    
    curator = PythonAPICurator(output_dir=output_dir)
    curator.curate(libraries=libraries)


def train_model(args):
    """Train the model"""
    from training import FineTuningPipeline
    
    print("="*70)
    print("Model Training")
    print("="*70)
    
    # Initialize pipeline
    pipeline = FineTuningPipeline(
        model_name=args.model_name,
        max_seq_length=args.max_seq_length,
        load_in_4bit=not args.no_quantization,
        use_wandb=args.use_wandb
    )
    
    # Load model with LoRA
    pipeline.load_model(
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout
    )
    
    # Load dataset
    dataset = pipeline.load_dataset(args.data_path)
    
    # Train
    pipeline.train(
        dataset=dataset,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps
    )


def evaluate_model(args):
    """Evaluate the model"""
    from evaluation import ModelEvaluator
    
    print("="*70)
    print("Model Evaluation")
    print("="*70)
    
    evaluator = ModelEvaluator(
        base_model_name=args.base_model,
        finetuned_model_path=args.model_path,
        max_seq_length=args.max_seq_length
    )
    
    # Load models
    evaluator.load_base_model()
    evaluator.load_finetuned_model()
    
    # Load test data
    test_examples = evaluator.load_test_data(args.test_data)
    
    # Run evaluation
    results, summary = evaluator.run_evaluation(
        test_examples,
        num_samples=args.num_samples
    )
    
    # Print summary
    print("\n" + "="*70)
    print("EVALUATION RESULTS")
    print("="*70)
    print(summary.to_string(index=False))
    print("="*70)
    
    # Save results
    if args.save_results:
        evaluator.save_results(results, summary, args.output_dir)


def interactive_mode(args):
    """Interactive inference mode"""
    from inference import FineTunedModel, ModelComparison
    
    if args.compare:
        # Comparison mode
        comparison = ModelComparison(
            base_model_name=args.base_model,
            finetuned_model_path=args.model_path
        )
        comparison.interactive_compare()
    else:
        # Single model mode
        model = FineTunedModel(
            model_path=args.model_path,
            load_in_4bit=not args.no_quantization
        )
        model.chat()


def single_query(args):
    """Single query inference"""
    from inference import FineTunedModel
    
    model = FineTunedModel(
        model_path=args.model_path,
        load_in_4bit=not args.no_quantization
    )
    
    response = model.generate(
        args.query,
        max_new_tokens=args.max_tokens,
        temperature=args.temperature
    )
    
    print("\n" + "="*70)
    print("Response:")
    print("="*70)
    print(response)
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description="Fine-Tuning Pipeline for Python API Documentation"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Prepare data command
    prepare_parser = subparsers.add_parser('prepare', help='Prepare training data')
    prepare_parser.add_argument(
        '--libraries',
        nargs='+',
        help='Python libraries to scrape (default: requests pandas numpy)'
    )
    prepare_parser.add_argument(
        '--output-dir',
        default='data',
        help='Output directory (default: data)'
    )
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train the model')
    train_parser.add_argument(
        '--model-name',
        default='meta-llama/Meta-Llama-3-8B',
        help='Base model name'
    )
    train_parser.add_argument(
        '--data-path',
        default='data/training_data.jsonl',
        help='Path to training data'
    )
    train_parser.add_argument(
        '--output-dir',
        default='models/llama3-python-api',
        help='Output directory for model'
    )
    train_parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Number of training epochs'
    )
    train_parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Training batch size'
    )
    train_parser.add_argument(
        '--gradient-accumulation',
        type=int,
        default=4,
        help='Gradient accumulation steps'
    )
    train_parser.add_argument(
        '--learning-rate',
        type=float,
        default=2e-4,
        help='Learning rate'
    )
    train_parser.add_argument(
        '--lora-rank',
        type=int,
        default=16,
        help='LoRA rank'
    )
    train_parser.add_argument(
        '--lora-alpha',
        type=int,
        default=32,
        help='LoRA alpha'
    )
    train_parser.add_argument(
        '--lora-dropout',
        type=float,
        default=0.1,
        help='LoRA dropout'
    )
    train_parser.add_argument(
        '--max-seq-length',
        type=int,
        default=2048,
        help='Maximum sequence length'
    )
    train_parser.add_argument(
        '--warmup-steps',
        type=int,
        default=100,
        help='Warmup steps'
    )
    train_parser.add_argument(
        '--no-quantization',
        action='store_true',
        help='Disable 4-bit quantization'
    )
    train_parser.add_argument(
        '--use-wandb',
        action='store_true',
        help='Enable Weights & Biases logging'
    )
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate the model')
    eval_parser.add_argument(
        '--base-model',
        default='meta-llama/Meta-Llama-3-8B',
        help='Base model name'
    )
    eval_parser.add_argument(
        '--model-path',
        default='models/llama3-python-api',
        help='Path to fine-tuned model'
    )
    eval_parser.add_argument(
        '--test-data',
        default='data/test_data.jsonl',
        help='Path to test data'
    )
    eval_parser.add_argument(
        '--num-samples',
        type=int,
        help='Number of test samples (default: all)'
    )
    eval_parser.add_argument(
        '--max-seq-length',
        type=int,
        default=2048,
        help='Maximum sequence length'
    )
    eval_parser.add_argument(
        '--save-results',
        action='store_true',
        help='Save evaluation results'
    )
    eval_parser.add_argument(
        '--output-dir',
        default='evaluation_results',
        help='Output directory for results'
    )
    
    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Interactive inference')
    interactive_parser.add_argument(
        '--model-path',
        default='models/llama3-python-api',
        help='Path to fine-tuned model'
    )
    interactive_parser.add_argument(
        '--base-model',
        default='meta-llama/Meta-Llama-3-8B',
        help='Base model name (for comparison)'
    )
    interactive_parser.add_argument(
        '--compare',
        action='store_true',
        help='Compare with base model'
    )
    interactive_parser.add_argument(
        '--no-quantization',
        action='store_true',
        help='Disable 4-bit quantization'
    )
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Single query inference')
    query_parser.add_argument(
        'query',
        help='Question to ask the model'
    )
    query_parser.add_argument(
        '--model-path',
        default='models/llama3-python-api',
        help='Path to fine-tuned model'
    )
    query_parser.add_argument(
        '--max-tokens',
        type=int,
        default=512,
        help='Maximum tokens to generate'
    )
    query_parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Sampling temperature'
    )
    query_parser.add_argument(
        '--no-quantization',
        action='store_true',
        help='Disable 4-bit quantization'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\nExamples:")
        print("  Prepare data:  python src/main.py prepare --libraries requests pandas")
        print("  Train model:   python src/main.py train --epochs 3 --batch-size 4")
        print("  Evaluate:      python src/main.py evaluate --num-samples 50")
        print("  Interactive:   python src/main.py interactive")
        print("  Compare:       python src/main.py interactive --compare")
        print("  Single query:  python src/main.py query \"How to use pandas DataFrame?\"")
        sys.exit(0)
    
    # Execute command
    if args.command == 'prepare':
        prepare_data(args)
    elif args.command == 'train':
        train_model(args)
    elif args.command == 'evaluate':
        evaluate_model(args)
    elif args.command == 'interactive':
        interactive_mode(args)
    elif args.command == 'query':
        single_query(args)


if __name__ == "__main__":
    main()
