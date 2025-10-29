"""
Batch Evaluator and Report Generator

Handles batch evaluations and generates comprehensive reports.
"""
import json
import jsonlines
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from judge import LLMJudge, EvaluationResult
from rubrics import get_rubric, Rubric
from tqdm import tqdm


class BatchEvaluator:
    """Batch evaluation system"""
    
    def __init__(
        self,
        rubric_name: str = "marketing",
        output_dir: str = "evaluations"
    ):
        """
        Initialize batch evaluator
        
        Args:
            rubric_name: Name of rubric to use
            output_dir: Directory for evaluation results
        """
        self.rubric = get_rubric(rubric_name)
        self.judge = LLMJudge()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def evaluate_batch(
        self,
        items: List[Dict],
        save_results: bool = True
    ) -> List[Dict]:
        """
        Evaluate multiple items
        
        Args:
            items: List of dicts with 'text' and optional 'context', 'id'
            save_results: Whether to save results to file
            
        Returns:
            List of evaluation results
        """
        results = []
        
        print(f"Evaluating {len(items)} items...")
        
        for item in tqdm(items, desc="Evaluating"):
            text = item.get('text', '')
            context = item.get('context')
            item_id = item.get('id', f"item_{len(results)}")
            
            try:
                evaluation = self.judge.evaluate(text, self.rubric, context)
                
                result = {
                    'id': item_id,
                    'text': text,
                    'context': context,
                    'evaluation': evaluation.dict(),
                    'rubric': self.rubric.name,
                    'timestamp': datetime.now().isoformat()
                }
                
                results.append(result)
                
            except Exception as e:
                print(f"Error evaluating item {item_id}: {e}")
                results.append({
                    'id': item_id,
                    'text': text,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        if save_results:
            self._save_results(results)
        
        return results
    
    def evaluate_from_file(
        self,
        filepath: str,
        save_results: bool = True
    ) -> List[Dict]:
        """
        Evaluate items from JSONL file
        
        Args:
            filepath: Path to JSONL file
            save_results: Whether to save results
            
        Returns:
            List of evaluation results
        """
        items = []
        
        with jsonlines.open(filepath) as reader:
            for item in reader:
                items.append(item)
        
        return self.evaluate_batch(items, save_results)
    
    def _save_results(self, results: List[Dict]):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eval_{self.rubric.name}_{timestamp}.jsonl"
        filepath = self.output_dir / filename
        
        with jsonlines.open(filepath, mode='w') as writer:
            for result in results:
                writer.write(result)
        
        print(f"\n✓ Results saved to: {filepath}")
    
    def generate_report(
        self,
        results: List[Dict],
        output_format: str = "markdown"
    ) -> str:
        """
        Generate evaluation report
        
        Args:
            results: Evaluation results
            output_format: 'markdown' or 'html'
            
        Returns:
            Report content
        """
        # Extract scores
        scores_data = []
        
        for result in results:
            if 'evaluation' in result:
                eval_data = result['evaluation']
                row = {
                    'id': result['id'],
                    'overall_score': eval_data['overall_score']
                }
                
                # Add criteria scores
                for criterion, score in eval_data['criteria_scores'].items():
                    row[f'{criterion}_score'] = score
                
                scores_data.append(row)
        
        df = pd.DataFrame(scores_data)
        
        # Calculate statistics
        stats = {
            'total_evaluated': len(results),
            'mean_score': df['overall_score'].mean() if not df.empty else 0,
            'median_score': df['overall_score'].median() if not df.empty else 0,
            'std_score': df['overall_score'].std() if not df.empty else 0,
            'min_score': df['overall_score'].min() if not df.empty else 0,
            'max_score': df['overall_score'].max() if not df.empty else 0
        }
        
        # Generate report
        if output_format == "markdown":
            report = self._generate_markdown_report(df, stats, results)
        else:
            report = self._generate_html_report(df, stats, results)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "md" if output_format == "markdown" else "html"
        filename = f"report_{self.rubric.name}_{timestamp}.{ext}"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✓ Report saved to: {filepath}")
        
        return report
    
    def _generate_markdown_report(
        self,
        df: pd.DataFrame,
        stats: Dict,
        results: List[Dict]
    ) -> str:
        """Generate markdown report"""
        
        report = f"""# Evaluation Report

**Rubric**: {self.rubric.name}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Evaluated**: {stats['total_evaluated']}

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Mean Score | {stats['mean_score']:.2f} |
| Median Score | {stats['median_score']:.2f} |
| Std Deviation | {stats['std_score']:.2f} |
| Min Score | {stats['min_score']:.2f} |
| Max Score | {stats['max_score']:.2f} |

---

## Score Distribution

"""
        
        # Add histogram (text-based)
        if not df.empty:
            bins = [0, 2, 4, 6, 8, 10]
            hist, _ = pd.cut(df['overall_score'], bins=bins, retbins=True)
            counts = hist.value_counts().sort_index()
            
            report += "```\n"
            for interval, count in counts.items():
                bar = "█" * int(count)
                report += f"{interval}: {bar} ({count})\n"
            report += "```\n\n"
        
        # Criteria breakdown
        report += "## Criteria Breakdown\n\n"
        
        criteria_cols = [col for col in df.columns if col.endswith('_score') and col != 'overall_score']
        
        if criteria_cols:
            criteria_stats = []
            for col in criteria_cols:
                criterion_name = col.replace('_score', '')
                criteria_stats.append({
                    'Criterion': criterion_name,
                    'Mean': f"{df[col].mean():.2f}",
                    'Std': f"{df[col].std():.2f}"
                })
            
            criteria_df = pd.DataFrame(criteria_stats)
            report += criteria_df.to_markdown(index=False)
            report += "\n\n"
        
        # Top performers
        report += "## Top Performers\n\n"
        
        if not df.empty:
            top_5 = df.nlargest(5, 'overall_score')
            
            for idx, row in top_5.iterrows():
                result = next(r for r in results if r['id'] == row['id'])
                
                report += f"### {row['id']} (Score: {row['overall_score']:.2f})\n\n"
                report += f"**Text**: {result['text'][:200]}...\n\n"
                
                if 'evaluation' in result:
                    strengths = result['evaluation'].get('strengths', [])
                    if strengths:
                        report += "**Strengths**:\n"
                        for strength in strengths[:3]:
                            report += f"- {strength}\n"
                        report += "\n"
        
        # Bottom performers
        report += "## Areas for Improvement\n\n"
        
        if not df.empty:
            bottom_5 = df.nsmallest(5, 'overall_score')
            
            for idx, row in bottom_5.iterrows():
                result = next(r for r in results if r['id'] == row['id'])
                
                report += f"### {row['id']} (Score: {row['overall_score']:.2f})\n\n"
                
                if 'evaluation' in result:
                    improvements = result['evaluation'].get('improvements', [])
                    if improvements:
                        report += "**Suggested Improvements**:\n"
                        for improvement in improvements[:3]:
                            report += f"- {improvement}\n"
                        report += "\n"
        
        report += "---\n\n"
        report += "*Generated by LLM-as-Judge Evaluation Framework*\n"
        
        return report
    
    def _generate_html_report(
        self,
        df: pd.DataFrame,
        stats: Dict,
        results: List[Dict]
    ) -> str:
        """Generate HTML report"""
        
        # Simple HTML template
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Evaluation Report - {self.rubric.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .score {{ font-weight: bold; color: #4CAF50; }}
    </style>
</head>
<body>
    <h1>Evaluation Report</h1>
    <p><strong>Rubric:</strong> {self.rubric.name}</p>
    <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p><strong>Total Evaluated:</strong> {stats['total_evaluated']}</p>
    
    <h2>Summary Statistics</h2>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Mean Score</td><td class="score">{stats['mean_score']:.2f}</td></tr>
        <tr><td>Median Score</td><td class="score">{stats['median_score']:.2f}</td></tr>
        <tr><td>Std Deviation</td><td>{stats['std_score']:.2f}</td></tr>
        <tr><td>Min Score</td><td>{stats['min_score']:.2f}</td></tr>
        <tr><td>Max Score</td><td>{stats['max_score']:.2f}</td></tr>
    </table>
    
    <h2>All Results</h2>
    {df.to_html(index=False) if not df.empty else '<p>No data</p>'}
    
</body>
</html>"""
        
        return html


if __name__ == "__main__":
    # Example usage
    evaluator = BatchEvaluator(rubric_name="marketing")
    
    # Sample items
    items = [
        {
            "id": "ad_1",
            "text": "Introducing EcoBottle - sustainable hydration!",
            "context": "Instagram ad for eco-friendly water bottle"
        },
        {
            "id": "ad_2",
            "text": "Buy our water bottle. It's good.",
            "context": "Facebook ad"
        }
    ]
    
    # Evaluate
    results = evaluator.evaluate_batch(items)
    
    # Generate report
    report = evaluator.generate_report(results)
    print("\n" + report)
