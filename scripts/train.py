#!/usr/bin/env python3
"""
TTS Training Script using Coqui TTS
VITS model fine-tuning on LJSpeech dataset
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits, VitsArgs
from TTS.utils.audio import AudioProcessor
from TTS.tts.datasets import load_samples
from TTS.config.shared_configs import BaseDatasetConfig

import torch

def check_device():
    """Check available device (MPS for Apple Silicon)"""
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

def setup_ljspeech_config(data_path, output_path):
    """Setup VITS configuration for LJSpeech"""

    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="ljspeech",
        path=data_path,
        meta_file_train="metadata.csv",
        meta_file_val="metadata.csv",
        language="en"
    )

    config = VitsConfig(
        batch_size=16,
        eval_batch_size=4,
        num_loader_workers=4,
        num_eval_loader_workers=2,
        run_eval=True,
        test_delay_epochs=2,
        epochs=100,
        text_cleaner="english_cleaners",
        use_phonemes=True,
        phoneme_language="en-us",
        phonemizer="gruut",
        audio={
            "fft_size": 1024,
            "sample_rate": 22050,
            "win_length": 1024,
            "hop_length": 256,
            "num_mels": 80,
            "mel_fmin": 0,
            "mel_fmax": None
        },
        datasets=[dataset_config],
        output_path=output_path,
        save_step=1000,
        print_step=50,
        log_model_step=1000,
        save_n_checkpoints=5,
        save_checkpoints=True,
        target_loss="loss_0",
        test_sentences=[
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning is transforming the way we interact with technology.",
            "This is a text to speech synthesis system built for the course project."
        ],
    )

    return config

def train_from_scratch(config, device):
    """Train VITS model from scratch"""

    # Initialize model
    model = Vits(config)

    # Load samples for training
    train_samples, eval_samples = load_samples(config.datasets)

    # Initialize trainer
    from TTS.tts.utils.synthesis import synthesis
    from TTS.trainer import Trainer, TrainerArgs

    trainer_args = TrainerArgs()
    trainer_args.continue_path = None
    trainer_args.find_unused_parameters = False

    trainer = Trainer(
        trainer_args,
        config,
        output_path=config.output_path,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples,
    )

    # Start training
    trainer.fit()

def finetune_pretrained(config, pretrained_model, output_path, device):
    """Fine-tune from pretrained VITS model"""

    from TTS.tts.models.vits import Vits

    # Load pretrained model
    model = Vits.init_from_config(config)
    model.load_checkpoint(config, pretrained_model)

    # Load samples
    train_samples, eval_samples = load_samples(config.datasets)

    # Initialize trainer
    from TTS.trainer import Trainer, TrainerArgs

    trainer_args = TrainerArgs()
    trainer_args.continue_path = None

    trainer = Trainer(
        trainer_args,
        config,
        output_path=output_path,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples,
    )

    # Start fine-tuning
    trainer.fit()

def main():
    parser = argparse.ArgumentParser(description="TTS Training Script")
    parser.add_argument(
        "--data_path",
        type=str,
        default="/Users/misuzu/General Workspace/jjjvoiceprocess/data/LJSpeech-1.1",
        help="Path to LJSpeech dataset"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="/Users/misuzu/General Workspace/jjjvoiceprocess/models",
        help="Output directory for model checkpoints"
    )
    parser.add_argument(
        "--pretrained",
        type=str,
        default=None,
        help="Path to pretrained model checkpoint for fine-tuning"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="Training batch size"
    )

    args = parser.parse_args()

    # Check device
    device = check_device()

    # Create output directory
    os.makedirs(args.output_path, exist_ok=True)

    # Setup configuration
    config = setup_ljspeech_config(args.data_path, args.output_path)
    config.epochs = args.epochs
    config.batch_size = args.batch_size

    print(f"\n{'='*60}")
    print("TTS Training Configuration")
    print(f"{'='*60}")
    print(f"Data path: {args.data_path}")
    print(f"Output path: {args.output_path}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Device: {device}")
    if args.pretrained:
        print(f"Pretrained model: {args.pretrained}")
    print(f"{'='*60}\n")

    # Start training
    if args.pretrained:
        print("Starting fine-tuning from pretrained model...")
        finetune_pretrained(config, args.pretrained, args.output_path, device)
    else:
        print("Starting training from scratch...")
        train_from_scratch(config, device)

    print("\nTraining completed!")
    print(f"Model checkpoints saved to: {args.output_path}")

if __name__ == "__main__":
    main()
