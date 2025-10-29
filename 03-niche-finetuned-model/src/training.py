"""
Fine-tuning Pipeline for Llama 3 8B using LoRA/PEFT

Uses Unsloth for optimized training with 4-bit quantization.
"""
import os
from pathlib import Path
from typing import Optional
import torch
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTTrainer
from unsloth import FastLanguageModel
import wandb
from dotenv import load_dotenv

load_dotenv()


class FineTuningPipeline:
    """Llama 3 fine-tuning with LoRA"""
    
    def __init__(
        self,
        model_name: str = None,
        max_seq_length: int = 2048,
        load_in_4bit: bool = True,
        use_wandb: bool = False
    ):
        """
        Initialize fine-tuning pipeline
        
        Args:
            model_name: Hugging Face model ID
            max_seq_length: Maximum sequence length
            load_in_4bit: Use 4-bit quantization
            use_wandb: Enable Weights & Biases logging
        """
        self.model_name = model_name or os.getenv('MODEL_NAME', 'meta-llama/Meta-Llama-3-8B')
        self.max_seq_length = max_seq_length
        self.load_in_4bit = load_in_4bit
        self.use_wandb = use_wandb
        
        self.model = None
        self.tokenizer = None
        
        if self.use_wandb and os.getenv('WANDB_API_KEY'):
            wandb.init(
                project=os.getenv('WANDB_PROJECT', 'python-api-finetuning'),
                config={
                    'model': self.model_name,
                    'max_seq_length': self.max_seq_length,
                    'load_in_4bit': self.load_in_4bit
                }
            )
    
    def load_model(self, lora_rank: int = 16, lora_alpha: int = 32, 
                   lora_dropout: float = 0.1):
        """
        Load base model with LoRA configuration
        
        Args:
            lora_rank: LoRA rank (lower = fewer parameters)
            lora_alpha: LoRA alpha (scaling factor)
            lora_dropout: Dropout for LoRA layers
        """
        print(f"Loading model: {self.model_name}")
        print(f"LoRA config: rank={lora_rank}, alpha={lora_alpha}, dropout={lora_dropout}")
        
        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.model_name,
            max_seq_length=self.max_seq_length,
            dtype=None,  # Auto-detect
            load_in_4bit=self.load_in_4bit,
        )
        
        # Apply LoRA
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=lora_rank,
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_alpha=lora_alpha,
            lora_dropout=lora_dropout,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=42,
        )
        
        print("✓ Model loaded with LoRA adapters")
        print(f"✓ Trainable parameters: {self._count_trainable_params()}")
    
    def _count_trainable_params(self) -> str:
        """Count trainable parameters"""
        trainable = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.model.parameters())
        percentage = 100 * trainable / total
        return f"{trainable:,} / {total:,} ({percentage:.2f}%)"
    
    def load_dataset(self, data_path: str = "data/training_data.jsonl"):
        """
        Load training dataset
        
        Args:
            data_path: Path to JSONL training data
            
        Returns:
            Loaded dataset
        """
        print(f"Loading dataset: {data_path}")
        
        dataset = load_dataset('json', data_files=data_path, split='train')
        
        # Format dataset for instruction tuning
        def format_prompt(example):
            """Format as instruction-response pair"""
            instruction = example['instruction']
            response = example['response']
            
            # Llama 3 instruction format
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful Python programming assistant specializing in library documentation and API usage.<|eot_id|><|start_header_id|>user<|end_header_id|>

{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

{response}<|eot_id|>"""
            
            return {"text": prompt}
        
        dataset = dataset.map(format_prompt)
        
        print(f"✓ Loaded {len(dataset)} training examples")
        return dataset
    
    def train(
        self,
        dataset,
        output_dir: str = "models/llama3-python-api",
        num_epochs: int = 3,
        batch_size: int = 4,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 100,
        logging_steps: int = 10,
        save_steps: int = 500
    ):
        """
        Fine-tune the model
        
        Args:
            dataset: Training dataset
            output_dir: Directory to save model
            num_epochs: Number of training epochs
            batch_size: Training batch size
            gradient_accumulation_steps: Gradient accumulation steps
            learning_rate: Learning rate
            warmup_steps: Warmup steps
            logging_steps: Steps between logging
            save_steps: Steps between checkpoints
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        print("\n" + "="*70)
        print("Starting Training")
        print("="*70)
        print(f"Output directory: {output_dir}")
        print(f"Epochs: {num_epochs}")
        print(f"Batch size: {batch_size}")
        print(f"Gradient accumulation: {gradient_accumulation_steps}")
        print(f"Effective batch size: {batch_size * gradient_accumulation_steps}")
        print(f"Learning rate: {learning_rate}")
        print("="*70 + "\n")
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=42,
            report_to="wandb" if self.use_wandb else "none",
        )
        
        # Trainer
        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=self.max_seq_length,
            dataset_num_proc=2,
            packing=False,
            args=training_args,
        )
        
        # Train
        print("🚀 Training started...")
        trainer.train()
        
        # Save final model
        print(f"\n✓ Training complete!")
        print(f"✓ Saving model to {output_dir}")
        
        self.model.save_pretrained(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        # Save LoRA adapters separately
        self.model.save_pretrained_merged(
            f"{output_dir}/merged",
            self.tokenizer,
            save_method="merged_16bit"
        )
        
        print(f"✓ Model saved:")
        print(f"  - LoRA adapters: {output_dir}/")
        print(f"  - Merged model:  {output_dir}/merged/")
        
        if self.use_wandb:
            wandb.finish()


def main():
    """Example training pipeline"""
    # Configuration from environment
    lora_rank = int(os.getenv('LORA_RANK', 16))
    lora_alpha = int(os.getenv('LORA_ALPHA', 32))
    lora_dropout = float(os.getenv('LORA_DROPOUT', 0.1))
    num_epochs = int(os.getenv('NUM_EPOCHS', 3))
    batch_size = int(os.getenv('BATCH_SIZE', 4))
    learning_rate = float(os.getenv('LEARNING_RATE', 2e-4))
    
    # Initialize pipeline
    pipeline = FineTuningPipeline(
        max_seq_length=2048,
        load_in_4bit=True,
        use_wandb=bool(os.getenv('WANDB_API_KEY'))
    )
    
    # Load model with LoRA
    pipeline.load_model(
        lora_rank=lora_rank,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout
    )
    
    # Load dataset
    dataset = pipeline.load_dataset("data/training_data.jsonl")
    
    # Train
    pipeline.train(
        dataset=dataset,
        output_dir="models/llama3-python-api",
        num_epochs=num_epochs,
        batch_size=batch_size,
        learning_rate=learning_rate
    )


if __name__ == "__main__":
    main()
