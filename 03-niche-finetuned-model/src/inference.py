"""
Inference Module for Fine-Tuned Model

Load and use the fine-tuned Llama 3 model for Python API questions.
"""
import os
from typing import Optional, List, Dict
import torch
from unsloth import FastLanguageModel
from dotenv import load_dotenv

load_dotenv()


class FineTunedModel:
    """Inference wrapper for fine-tuned model"""
    
    def __init__(
        self,
        model_path: str = "models/llama3-python-api",
        max_seq_length: int = 2048,
        load_in_4bit: bool = True,
        use_merged: bool = False
    ):
        """
        Initialize inference model
        
        Args:
            model_path: Path to fine-tuned model
            max_seq_length: Maximum sequence length
            load_in_4bit: Use 4-bit quantization
            use_merged: Use merged model (faster but larger)
        """
        self.model_path = model_path
        if use_merged:
            self.model_path = f"{model_path}/merged"
        
        self.max_seq_length = max_seq_length
        self.load_in_4bit = load_in_4bit
        
        self.model = None
        self.tokenizer = None
        
        self._load_model()
    
    def _load_model(self):
        """Load the fine-tuned model"""
        print(f"Loading model from: {self.model_path}")
        
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_path,
            max_seq_length=self.max_seq_length,
            dtype=None,
            load_in_4bit=self.load_in_4bit,
        )
        
        # Set to inference mode
        FastLanguageModel.for_inference(self.model)
        
        print("✓ Model loaded and ready for inference")
    
    def generate(
        self,
        instruction: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """
        Generate response for an instruction
        
        Args:
            instruction: User instruction/question
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            do_sample: Whether to use sampling
            
        Returns:
            Generated response
        """
        # Format prompt with Llama 3 template
        prompt = self._format_prompt(instruction)
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
        
        # Decode full response
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract assistant response
        response = self._extract_response(full_response)
        
        return response
    
    def _format_prompt(self, instruction: str) -> str:
        """Format instruction as Llama 3 prompt"""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful Python programming assistant specializing in library documentation and API usage.<|eot_id|><|start_header_id|>user<|end_header_id|>

{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    def _extract_response(self, full_response: str) -> str:
        """Extract assistant response from full output"""
        if "<|start_header_id|>assistant<|end_header_id|>" in full_response:
            response = full_response.split("<|start_header_id|>assistant<|end_header_id|>")[-1]
            response = response.replace("<|eot_id|>", "").strip()
        else:
            response = full_response
        
        return response
    
    def batch_generate(
        self,
        instructions: List[str],
        max_new_tokens: int = 512,
        temperature: float = 0.7
    ) -> List[str]:
        """
        Generate responses for multiple instructions
        
        Args:
            instructions: List of instructions
            max_new_tokens: Maximum tokens per response
            temperature: Sampling temperature
            
        Returns:
            List of generated responses
        """
        responses = []
        
        for instruction in instructions:
            response = self.generate(
                instruction,
                max_new_tokens=max_new_tokens,
                temperature=temperature
            )
            responses.append(response)
        
        return responses
    
    def chat(self):
        """Interactive chat mode"""
        print("="*70)
        print("Fine-Tuned Python API Assistant")
        print("="*70)
        print("Ask questions about Python libraries (requests, pandas, numpy)")
        print("Type 'exit' or 'quit' to stop")
        print("="*70 + "\n")
        
        while True:
            try:
                # Get user input
                instruction = input("You: ").strip()
                
                if instruction.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not instruction:
                    continue
                
                # Generate response
                print("\nAssistant: ", end="", flush=True)
                response = self.generate(instruction)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")


class ModelComparison:
    """Compare base model vs fine-tuned model"""
    
    def __init__(
        self,
        base_model_name: str = None,
        finetuned_model_path: str = "models/llama3-python-api"
    ):
        """
        Initialize comparison
        
        Args:
            base_model_name: Base model ID
            finetuned_model_path: Fine-tuned model path
        """
        self.base_model_name = base_model_name or os.getenv(
            'MODEL_NAME', 'meta-llama/Meta-Llama-3-8B'
        )
        
        print("Loading base model...")
        self.base_model, self.base_tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.base_model_name,
            max_seq_length=2048,
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(self.base_model)
        
        print("Loading fine-tuned model...")
        self.finetuned = FineTunedModel(finetuned_model_path)
        
        print("\n✓ Both models loaded\n")
    
    def compare(self, instruction: str) -> Dict[str, str]:
        """
        Compare responses from both models
        
        Args:
            instruction: User instruction
            
        Returns:
            Dictionary with both responses
        """
        print(f"Instruction: {instruction}\n")
        
        # Base model response
        print("Generating from base model...")
        base_prompt = self.finetuned._format_prompt(instruction)
        base_inputs = self.base_tokenizer(base_prompt, return_tensors="pt").to(self.base_model.device)
        
        with torch.no_grad():
            base_outputs = self.base_model.generate(
                **base_inputs,
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.base_tokenizer.eos_token_id
            )
        
        base_full = self.base_tokenizer.decode(base_outputs[0], skip_special_tokens=True)
        base_response = self.finetuned._extract_response(base_full)
        
        # Fine-tuned model response
        print("Generating from fine-tuned model...")
        finetuned_response = self.finetuned.generate(instruction)
        
        return {
            'instruction': instruction,
            'base_response': base_response,
            'finetuned_response': finetuned_response
        }
    
    def interactive_compare(self):
        """Interactive comparison mode"""
        print("="*70)
        print("Model Comparison: Base vs Fine-Tuned")
        print("="*70)
        print("Type 'exit' to quit")
        print("="*70 + "\n")
        
        while True:
            try:
                instruction = input("Question: ").strip()
                
                if instruction.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not instruction:
                    continue
                
                result = self.compare(instruction)
                
                print("\n" + "="*70)
                print("BASE MODEL")
                print("="*70)
                print(result['base_response'])
                
                print("\n" + "="*70)
                print("FINE-TUNED MODEL")
                print("="*70)
                print(result['finetuned_response'])
                print("\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")


def main():
    """Example usage"""
    # Single model inference
    model = FineTunedModel("models/llama3-python-api")
    
    # Example query
    response = model.generate(
        "How do I make a GET request with headers using the requests library?"
    )
    print(response)
    
    # Or start interactive chat
    # model.chat()


if __name__ == "__main__":
    main()
