"""
Command-line Interface for LLM-as-Judge Evaluation

Provides commands for single evaluation, comparison, and batch processing.
"""
import argparse
import sys
import json
from pathlib import Path
from judge import LLMJudge
from evaluator import BatchEvaluator
from rubrics import get_rubric, list_rubrics, create_custom_rubric
from dotenv import load_dotenv

load_dotenv()


def evaluate_single(args):
    """Single content evaluation"""
    print("="*70)
    print("LLM-as-Judge Evaluation")
    print("="*70)
    
    rubric = get_rubric(args.rubric)
    judge = LLMJudge()
    
    text = args.text
    context = args.context
    
    print(f"\nRubric: {rubric.name}")
    print(f"Text: {text[:100]}..." if len(text) > 100 else f"Text: {text}")
    if context:
        print(f"Context: {context}")
    
    print("\nEvaluating...")
    
    result = judge.evaluate(text, rubric, context)
    
    print("\n" + "="*70)
    print("EVALUATION RESULTS")
    print("="*70)
    print(f"\nOverall Score: {result.overall_score}/10")
    
    print("\nCriteria Scores:")
    for criterion, score in result.criteria_scores.items():
        print(f"  {criterion}: {score}/10")
    
    print("\nStrengths:")
    for strength in result.strengths:
        print(f"  ✓ {strength}")
    
    print("\nImprovements:")
    for improvement in result.improvements:
        print(f"  → {improvement}")
    
    print("\nDetailed Reasoning:")
    for criterion, reasoning in result.reasoning.items():
        print(f"\n  {criterion}:")
        print(f"    {reasoning}")
    
    # Save if requested
    if args.output:
        output = {
            "text": text,
            "context": context,
            "rubric": rubric.name,
            "evaluation": result.dict()
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n✓ Results saved to: {args.output}")


def compare_texts(args):
    """Compare two texts"""
    print("="*70)
    print("LLM-as-Judge Comparison")
    print("="*70)
    
    rubric = get_rubric(args.rubric)
    judge = LLMJudge()
    
    text1 = args.text1
    text2 = args.text2
    context = args.context
    
    print(f"\nRubric: {rubric.name}")
    print(f"\nVersion A: {text1[:100]}..." if len(text1) > 100 else f"\nVersion A: {text1}")
    print(f"Version B: {text2[:100]}..." if len(text2) > 100 else f"Version B: {text2}")
    if context:
        print(f"Context: {context}")
    
    print("\nComparing...")
    
    comparison = judge.compare(text1, text2, rubric, context)
    
    print("\n" + "="*70)
    print("COMPARISON RESULTS")
    print("="*70)
    
    # Scores
    print("\nScores:")
    print(f"  Version A: {comparison['text1_evaluation'].overall_score}/10")
    print(f"  Version B: {comparison['text2_evaluation'].overall_score}/10")
    
    # Winner
    winner = comparison['winner']
    margin = comparison['margin']
    
    print("\nWinner:")
    if winner == "tie":
        print("  🤝 It's a tie!")
    elif winner == "text1":
        print(f"  🏆 Version A wins by {margin:.2f} points")
    else:
        print(f"  🏆 Version B wins by {margin:.2f} points")
    
    # Comparison
    print("\nComparative Analysis:")
    print(f"  {comparison['comparison']}")
    
    # Save if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({
                "text1": text1,
                "text2": text2,
                "context": context,
                "rubric": rubric.name,
                "comparison": {
                    "text1_score": comparison['text1_evaluation'].overall_score,
                    "text2_score": comparison['text2_evaluation'].overall_score,
                    "winner": winner,
                    "margin": margin,
                    "analysis": comparison['comparison']
                }
            }, f, indent=2)
        
        print(f"\n✓ Results saved to: {args.output}")


def batch_evaluate(args):
    """Batch evaluation"""
    print("="*70)
    print("Batch Evaluation")
    print("="*70)
    
    evaluator = BatchEvaluator(
        rubric_name=args.rubric,
        output_dir=args.output_dir
    )
    
    print(f"\nInput file: {args.input}")
    print(f"Rubric: {args.rubric}")
    print(f"Output directory: {args.output_dir}")
    
    # Evaluate
    results = evaluator.evaluate_from_file(args.input, save_results=True)
    
    # Generate report
    if args.generate_report:
        report = evaluator.generate_report(results, output_format=args.report_format)
        print("\n" + "="*70)
        print("REPORT GENERATED")
        print("="*70)


def list_rubrics_cmd(args):
    """List available rubrics"""
    print("="*70)
    print("Available Evaluation Rubrics")
    print("="*70)
    
    for rubric_name in list_rubrics():
        rubric = get_rubric(rubric_name)
        print(f"\n{rubric.name.upper()}")
        print(f"  Description: {rubric.description}")
        print(f"  Criteria ({len(rubric.criteria)}):")
        
        for criterion in rubric.criteria:
            print(f"    - {criterion.name} ({criterion.weight*100:.0f}%): {criterion.description}")


def create_rubric_cmd(args):
    """Create custom rubric"""
    print("="*70)
    print("Create Custom Rubric")
    print("="*70)
    
    print(f"\nName: {args.name}")
    print(f"Description: {args.description}")
    print(f"Criteria: {', '.join(args.criteria)}")
    
    # Build criteria
    criteria = []
    weight = 1.0 / len(args.criteria)
    
    for criterion_name in args.criteria:
        criteria.append({
            'name': criterion_name,
            'weight': weight,
            'description': f"Evaluate {criterion_name}",
            'scoring_guide': {
                "9-10": "Excellent",
                "7-8": "Good",
                "5-6": "Adequate",
                "3-4": "Weak",
                "1-2": "Poor"
            }
        })
    
    rubric = create_custom_rubric(args.name, args.description, criteria)
    
    # Save to file
    output_dir = Path("rubrics/custom")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{args.name}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'name': rubric.name,
            'description': rubric.description,
            'criteria': [c.dict() for c in rubric.criteria]
        }, f, indent=2)
    
    print(f"\n✓ Custom rubric created: {output_file}")
    print("\nYou can now use it with: --rubric custom/{args.name}")


def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-Judge Evaluation Framework CLI"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate single content')
    eval_parser.add_argument(
        '--text', '-t',
        required=True,
        help='Content to evaluate'
    )
    eval_parser.add_argument(
        '--rubric', '-r',
        default='marketing',
        choices=list_rubrics(),
        help='Evaluation rubric'
    )
    eval_parser.add_argument(
        '--context', '-c',
        help='Optional context'
    )
    eval_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare two texts')
    compare_parser.add_argument(
        '--text1',
        required=True,
        help='First text'
    )
    compare_parser.add_argument(
        '--text2',
        required=True,
        help='Second text'
    )
    compare_parser.add_argument(
        '--rubric', '-r',
        default='marketing',
        choices=list_rubrics(),
        help='Evaluation rubric'
    )
    compare_parser.add_argument(
        '--context', '-c',
        help='Optional context'
    )
    compare_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch evaluation from file')
    batch_parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input JSONL file'
    )
    batch_parser.add_argument(
        '--rubric', '-r',
        default='marketing',
        choices=list_rubrics(),
        help='Evaluation rubric'
    )
    batch_parser.add_argument(
        '--output-dir',
        default='evaluations',
        help='Output directory'
    )
    batch_parser.add_argument(
        '--generate-report',
        action='store_true',
        help='Generate evaluation report'
    )
    batch_parser.add_argument(
        '--report-format',
        choices=['markdown', 'html'],
        default='markdown',
        help='Report format'
    )
    
    # List rubrics command
    list_parser = subparsers.add_parser('list-rubrics', help='List available rubrics')
    
    # Create rubric command
    create_parser = subparsers.add_parser('create-rubric', help='Create custom rubric')
    create_parser.add_argument(
        '--name',
        required=True,
        help='Rubric name'
    )
    create_parser.add_argument(
        '--description',
        required=True,
        help='Rubric description'
    )
    create_parser.add_argument(
        '--criteria',
        nargs='+',
        required=True,
        help='Criterion names'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print("\nExamples:")
        print('  Evaluate:      python src/main.py evaluate --text "Your content" --rubric marketing')
        print('  Compare:       python src/main.py compare --text1 "Version A" --text2 "Version B"')
        print('  Batch:         python src/main.py batch --input data.jsonl --generate-report')
        print('  List rubrics:  python src/main.py list-rubrics')
        print('  Create rubric: python src/main.py create-rubric --name custom --description "Custom" --criteria clarity accuracy')
        sys.exit(0)
    
    # Execute command
    if args.command == 'evaluate':
        evaluate_single(args)
    elif args.command == 'compare':
        compare_texts(args)
    elif args.command == 'batch':
        batch_evaluate(args)
    elif args.command == 'list-rubrics':
        list_rubrics_cmd(args)
    elif args.command == 'create-rubric':
        create_rubric_cmd(args)


if __name__ == "__main__":
    main()
