#!/usr/bin/env python3
"""
Quick Demo Script - Use pretrained TTS model for synthesis
This script uses Coqui TTS's built-in pretrained models
"""

import os
import sys
from pathlib import Path
from datetime import datetime

import torch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from TTS.api import TTS

def check_device():
    """Check available device"""
    if torch.cuda.is_available():
        print(f"Using CUDA: {torch.cuda.get_device_name(0)}")
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("Using Apple Silicon MPS acceleration")
        return "mps"
    print("Using CPU")
    return "cpu"

def list_available_models():
    """List all available pretrained TTS models"""
    print("\nAvailable pretrained TTS models:")
    print("=" * 60)

    # Get all models
    models = TTS().list_models()

    # Group by type
    tts_models = [m for m in models if 'tts_models' in m]
    vocoder_models = [m for m in models if 'vocoder_models' in m]

    print("\nTTS Models:")
    for model in tts_models[:10]:  # Show first 10
        print(f"  - {model}")

    print(f"\n  ... and {len(tts_models) - 10} more TTS models")

    print("\nVocoder Models:")
    for model in vocoder_models[:5]:
        print(f"  - {model}")

    print(f"\n  ... and {len(vocoder_models) - 5} more vocoder models")

    return models

def synthesize_with_pretrained(texts, output_dir, model_name=None):
    """Synthesize speech using pretrained model"""

    device = check_device()

    # Default to a good English model
    if model_name is None:
        model_name = "tts_models/en/ljspeech/vits"

    print(f"\nUsing model: {model_name}")
    print(f"Device: {device}")
    print("=" * 60)

    # Initialize TTS
    tts = TTS(model_name).to(device)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Synthesize each text
    output_files = []
    for i, text in enumerate(texts):
        print(f"\n[{i+1}/{len(texts)}] Synthesizing: {text[:50]}...")

        # Output path
        output_path = os.path.join(output_dir, f"demo_{timestamp}_{i+1}.wav")

        # Synthesize
        tts.tts_to_file(text=text, file_path=output_path)

        print(f"  Saved to: {output_path}")
        output_files.append(output_path)

    print("\n" + "=" * 60)
    print("Demo synthesis completed!")
    print(f"Generated {len(output_files)} audio files in: {output_dir}")
    print("=" * 60)

    return output_files

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Quick TTS Demo")
    parser.add_argument(
        "--text",
        type=str,
        nargs="+",
        help="Text(s) to synthesize"
    )
    parser.add_argument(
        "--text_file",
        type=str,
        help="Path to text file (one sentence per line)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(project_root / "outputs" / "demo"),
        help="Output directory"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="tts_models/en/ljspeech/vits",
        help="Pretrained model name"
    )
    parser.add_argument(
        "--list_models",
        action="store_true",
        help="List all available models"
    )

    args = parser.parse_args()

    # List models if requested
    if args.list_models:
        list_available_models()
        return

    # Get texts
    texts = []
    if args.text:
        texts.extend(args.text)
    if args.text_file:
        with open(args.text_file, 'r', encoding='utf-8') as f:
            texts.extend([line.strip() for line in f if line.strip()])

    if not texts:
        # Use default demo texts
        texts = [
            "Hello, this is a text to speech synthesis system.",
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning has revolutionized many fields including speech synthesis."
        ]
        print("No text provided, using default demo texts")

    # Run synthesis
    output_files = synthesize_with_pretrained(texts, args.output_dir, args.model)

    return output_files

if __name__ == "__main__":
    main()
