"""
Evaluation System for Fine-Tuned Model

Compares base Llama 3 vs fine-tuned model on Python API questions.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple
import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from unsloth import FastLanguageModel
from tqdm import tqdm
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class ModelEvaluator:
    """Evaluate and compare models"""
    
    def __init__(
        self,
        base_model_name: str = None,
        finetuned_model_path: str = "models/llama3-python-api",
        max_seq_length: int = 2048
    ):
        """
        Initialize evaluator
        
        Args:
            base_model_name: Base model ID
            finetuned_model_path: Path to fine-tuned model
            max_seq_length: Maximum sequence length
        """
        self.base_model_name = base_model_name or os.getenv(
            'MODEL_NAME', 'meta-llama/Meta-Llama-3-8B'
        )
        self.finetuned_model_path = finetuned_model_path
        self.max_seq_length = max_seq_length
        
        self.base_model = None
        self.base_tokenizer = None
        self.finetuned_model = None
        self.finetuned_tokenizer = None
    
    def load_base_model(self):
        """Load base model"""
        print(f"Loading base model: {self.base_model_name}")
        
        self.base_model, self.base_tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.base_model_name,
            max_seq_length=self.max_seq_length,
            dtype=None,
            load_in_4bit=True,
        )
        
        FastLanguageModel.for_inference(self.base_model)
        print("✓ Base model loaded")
    
    def load_finetuned_model(self):
        """Load fine-tuned model"""
        print(f"Loading fine-tuned model: {self.finetuned_model_path}")
        
        self.finetuned_model, self.finetuned_tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.finetuned_model_path,
            max_seq_length=self.max_seq_length,
            dtype=None,
            load_in_4bit=True,
        )
        
        FastLanguageModel.for_inference(self.finetuned_model)
        print("✓ Fine-tuned model loaded")
    
    def load_test_data(self, test_path: str = "data/test_data.jsonl") -> List[Dict]:
        """
        Load test dataset
        
        Args:
            test_path: Path to test data
            
        Returns:
            List of test examples
        """
        print(f"Loading test data: {test_path}")
        
        dataset = load_dataset('json', data_files=test_path, split='train')
        test_examples = [example for example in dataset]
        
        print(f"✓ Loaded {len(test_examples)} test examples")
        return test_examples
    
    def generate_response(
        self,
        model,
        tokenizer,
        instruction: str,
        max_new_tokens: int = 512
    ) -> str:
        """
        Generate response from model
        
        Args:
            model: Language model
            tokenizer: Tokenizer
            instruction: User instruction
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        # Format prompt
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful Python programming assistant specializing in library documentation and API usage.<|eot_id|><|start_header_id|>user<|end_header_id|>

{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        
        # Tokenize
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract assistant response
        if "<|start_header_id|>assistant<|end_header_id|>" in full_response:
            response = full_response.split("<|start_header_id|>assistant<|end_header_id|>")[-1]
            response = response.replace("<|eot_id|>", "").strip()
        else:
            response = full_response
        
        return response
    
    def evaluate_quality(self, response: str, reference: str) -> Dict[str, float]:
        """
        Simple quality metrics
        
        Args:
            response: Generated response
            reference: Reference response
            
        Returns:
            Quality scores
        """
        # Code block presence
        has_code = "```python" in response or "```\n" in response
        
        # Length similarity (normalized)
        len_ratio = min(len(response), len(reference)) / max(len(response), len(reference))
        
        # Keyword overlap (simple metric)
        response_words = set(response.lower().split())
        reference_words = set(reference.lower().split())
        overlap = len(response_words & reference_words) / len(reference_words | response_words)
        
        return {
            'has_code': 1.0 if has_code else 0.0,
            'length_similarity': len_ratio,
            'keyword_overlap': overlap,
            'completeness': (len_ratio + overlap) / 2
        }
    
    def run_evaluation(
        self,
        test_examples: List[Dict],
        num_samples: int = None
    ) -> Tuple[List[Dict], pd.DataFrame]:
        """
        Run evaluation on test set
        
        Args:
            test_examples: Test examples
            num_samples: Number of samples to evaluate (None = all)
            
        Returns:
            Tuple of (results, summary_df)
        """
        if num_samples:
            test_examples = test_examples[:num_samples]
        
        print("\n" + "="*70)
        print(f"Evaluating on {len(test_examples)} examples")
        print("="*70 + "\n")
        
        results = []
        
        for example in tqdm(test_examples, desc="Evaluating"):
            instruction = example['instruction']
            reference = example['response']
            
            # Generate from base model
            base_response = self.generate_response(
                self.base_model,
                self.base_tokenizer,
                instruction
            )
            
            # Generate from fine-tuned model
            finetuned_response = self.generate_response(
                self.finetuned_model,
                self.finetuned_tokenizer,
                instruction
            )
            
            # Evaluate both
            base_scores = self.evaluate_quality(base_response, reference)
            finetuned_scores = self.evaluate_quality(finetuned_response, reference)
            
            results.append({
                'instruction': instruction,
                'reference': reference,
                'base_response': base_response,
                'finetuned_response': finetuned_response,
                'base_scores': base_scores,
                'finetuned_scores': finetuned_scores
            })
        
        # Calculate summary statistics
        summary = self._create_summary(results)
        
        return results, summary
    
    def _create_summary(self, results: List[Dict]) -> pd.DataFrame:
        """Create summary DataFrame"""
        base_metrics = {
            'has_code': [],
            'length_similarity': [],
            'keyword_overlap': [],
            'completeness': []
        }
        
        finetuned_metrics = {
            'has_code': [],
            'length_similarity': [],
            'keyword_overlap': [],
            'completeness': []
        }
        
        for result in results:
            for metric in base_metrics.keys():
                base_metrics[metric].append(result['base_scores'][metric])
                finetuned_metrics[metric].append(result['finetuned_scores'][metric])
        
        # Calculate averages
        summary_data = []
        for metric in base_metrics.keys():
            base_avg = sum(base_metrics[metric]) / len(base_metrics[metric])
            finetuned_avg = sum(finetuned_metrics[metric]) / len(finetuned_metrics[metric])
            improvement = ((finetuned_avg - base_avg) / base_avg * 100) if base_avg > 0 else 0
            
            summary_data.append({
                'Metric': metric,
                'Base Model': f"{base_avg:.3f}",
                'Fine-Tuned': f"{finetuned_avg:.3f}",
                'Improvement': f"{improvement:+.1f}%"
            })
        
        return pd.DataFrame(summary_data)
    
    def save_results(
        self,
        results: List[Dict],
        summary: pd.DataFrame,
        output_dir: str = "evaluation_results"
    ):
        """
        Save evaluation results
        
        Args:
            results: Detailed results
            summary: Summary DataFrame
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save detailed results
        with open(output_path / "detailed_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Save summary
        summary.to_csv(output_path / "summary.csv", index=False)
        
        # Save markdown report
        with open(output_path / "report.md", 'w', encoding='utf-8') as f:
            f.write("# Evaluation Report\n\n")
            f.write("## Summary Statistics\n\n")
            f.write(summary.to_markdown(index=False))
            f.write("\n\n## Key Findings\n\n")
            
            # Calculate overall improvement
            completeness_improvement = float(summary[summary['Metric'] == 'completeness']['Improvement'].values[0].rstrip('%'))
            
            f.write(f"- Overall completeness improvement: **{completeness_improvement:+.1f}%**\n")
            f.write(f"- Evaluated on {len(results)} test examples\n")
            f.write(f"- Base model: {self.base_model_name}\n")
            f.write(f"- Fine-tuned model: {self.finetuned_model_path}\n")
        
        print(f"\n✓ Results saved to {output_dir}/")


def main():
    """Run evaluation"""
    evaluator = ModelEvaluator()
    
    # Load models
    evaluator.load_base_model()
    evaluator.load_finetuned_model()
    
    # Load test data
    test_examples = evaluator.load_test_data()
    
    # Run evaluation (limit to 50 samples for speed)
    results, summary = evaluator.run_evaluation(test_examples, num_samples=50)
    
    # Print summary
    print("\n" + "="*70)
    print("EVALUATION SUMMARY")
    print("="*70)
    print(summary.to_string(index=False))
    print("="*70)
    
    # Save results
    evaluator.save_results(results, summary)


if __name__ == "__main__":
    main()
