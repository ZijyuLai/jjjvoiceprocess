#!/usr/bin/env python3
"""
VITS Model Fine-tuning Script
基于 Coqui TTS 预训练模型在 LJSpeech 上微调
"""

import os
import sys
import json
from pathlib import Path

import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits
from TTS.tts.datasets import load_tts_samples
from TTS.config.shared_configs import BaseDatasetConfig
from trainer import Trainer, TrainerArgs

# Pretrained model paths (downloaded by Coqui TTS)
PRETRAINED_MODEL_DIR = Path.home() / "Library/Application Support/tts/tts_models--en--ljspeech--vits"
PRETRAINED_CHECKPOINT = PRETRAINED_MODEL_DIR / "model_file.pth"
PRETRAINED_CONFIG = PRETRAINED_MODEL_DIR / "config.json"


def check_device():
    if torch.backends.mps.is_available():
        device = "mps"
        print("Using Apple Silicon MPS acceleration")
    elif torch.cuda.is_available():
        device = "cuda"
        print("Using CUDA acceleration")
    else:
        device = "cpu"
        print("Using CPU (training will be slow)")
    return device


def finetune_vits(data_path, output_path, epochs=50, batch_size=8, learning_rate=0.00002):
    """Fine-tune VITS model on LJSpeech dataset"""

    device = check_device()

    # Load pretrained config and modify for fine-tuning
    print(f"Loading pretrained config from: {PRETRAINED_CONFIG}")
    config = VitsConfig()
    config.load_json(str(PRETRAINED_CONFIG))

    # Enable discriminator for training
    config.model_args.init_discriminator = True

    # Override training settings for fine-tuning
    config.batch_size = batch_size
    config.eval_batch_size = 4
    config.num_loader_workers = 4
    config.num_eval_loader_workers = 2
    config.run_eval = True
    config.test_delay_epochs = 2
    config.epochs = epochs
    config.output_path = output_path
    config.save_step = 500
    config.print_step = 50
    config.log_model_step = 500
    config.save_n_checkpoints = 3
    config.save_checkpoints = True

    # Fine-tuning: lower learning rate
    config.learning_rate = learning_rate
    config.lr_scheduler = "NoamLR"
    config.lr_scheduler_params = {"warmup_steps": 1000}

    # Dataset path
    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="ljspeech",
        path=data_path,
        meta_file_train="metadata.csv",
        meta_file_val="metadata.csv",
        language="en"
    )
    config.datasets = [dataset_config]

    # Phoneme cache path
    config.phoneme_cache_path = os.path.join(output_path, "phoneme_cache")
    os.makedirs(config.phoneme_cache_path, exist_ok=True)

    # Test sentences
    config.test_sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is transforming speech synthesis technology.",
        "This is a text to speech system built for the course project.",
    ]

    print(f"\n{'=' * 60}")
    print("VITS Fine-tuning Configuration")
    print(f"{'=' * 60}")
    print(f"Pretrained checkpoint: {PRETRAINED_CHECKPOINT}")
    print(f"Data path: {data_path}")
    print(f"Output path: {output_path}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {learning_rate}")
    print(f"Device: {device}")
    print(f"{'=' * 60}\n")

    # Initialize model from pretrained config
    model = Vits.init_from_config(config)

    # Load pretrained checkpoint (strict=False because pretrained has no discriminator weights)
    print(f"Loading pretrained checkpoint: {PRETRAINED_CHECKPOINT}")
    model.load_checkpoint(config, checkpoint_path=str(PRETRAINED_CHECKPOINT), eval=False, strict=False)

    # Load training samples
    print("Loading dataset samples...")
    train_samples, eval_samples = load_tts_samples(config.datasets, eval_split=True)
    print(f"Training samples: {len(train_samples)}")
    print(f"Eval samples: {len(eval_samples)}")

    # Initialize trainer
    trainer_args = TrainerArgs()
    trainer_args.find_unused_parameters = False

    print("\nStarting fine-tuning...\n")
    trainer = Trainer(
        trainer_args,
        config,
        output_path=output_path,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples,
    )

    trainer.fit()

    print(f"\nFine-tuning completed! Model saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="VITS Fine-tuning Script")
    parser.add_argument("--data_path", type=str,
                        default="/Users/misuzu/General Workspace/jjjvoiceprocess/data/LJSpeech-1.1")
    parser.add_argument("--output_path", type=str,
                        default="/Users/misuzu/General Workspace/jjjvoiceprocess/models/vits_finetuned")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=0.00002)
    args = parser.parse_args()

    os.makedirs(args.output_path, exist_ok=True)

    finetune_vits(
        data_path=args.data_path,
        output_path=args.output_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )


if __name__ == "__main__":
    main()
