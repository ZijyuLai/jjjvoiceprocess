#!/usr/bin/env python3
"""
TTS Inference Script
Generate speech from text using trained VITS model
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import torch
import soundfile as sf

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits
from TTS.tts.utils.synthesis import synthesis
from TTS.utils.audio import AudioProcessor

def check_device():
    """Check available device"""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"

def load_model(model_path, config_path=None):
    """Load trained TTS model"""

    # Try to find config
    if config_path is None:
        # Look for config in model directory
        model_dir = Path(model_path).parent
        possible_configs = [
            model_dir / "config.json",
            model_dir.parent / "config.json"
        ]
        for cfg in possible_configs:
            if cfg.exists():
                config_path = str(cfg)
                break

    if config_path and Path(config_path).exists():
        config = VitsConfig()
        config.load_json(config_path)
    else:
        # Use default LJSpeech config
        from TTS.tts.configs.vits_config import VitsConfig
        config = VitsConfig()

    # Load model
    model = Vits.init_from_config(config)
    model.load_checkpoint(config, model_path)

    # Move to device
    device = check_device()
    model = model.to(device)
    model.eval()

    return model, config, device

def synthesize_speech(model, config, text, device, speaker_id=None):
    """Synthesize speech from text"""

    # Setup audio processor
    ap = AudioProcessor.init_from_config(config)

    # Synthesize
    outputs = synthesis(
        model=model,
        text=text,
        CONFIG=config,
        use_cuda=device == "cuda",
        speaker_id=speaker_id,
        d_vector=None,
        style_wav=None,
        enable_eos_b=config.use_eos_b,
        use_griffin_lim=False,
    )

    # Get waveform
    waveform = outputs["wav"]

    # Convert to numpy if tensor
    if isinstance(waveform, torch.Tensor):
        waveform = waveform.cpu().numpy()

    return waveform

def main():
    parser = argparse.ArgumentParser(description="TTS Inference Script")
    parser.add_argument(
        "--model_path",
        type=str,
        required=True,
        help="Path to trained model checkpoint"
    )
    parser.add_argument(
        "--config_path",
        type=str,
        default=None,
        help="Path to model config JSON"
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Text to synthesize (single sentence)"
    )
    parser.add_argument(
        "--text_file",
        type=str,
        default=None,
        help="Path to text file with sentences (one per line)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(project_root / "outputs"),
        help="Output directory for generated audio"
    )
    parser.add_argument(
        "--speaker_id",
        type=int,
        default=None,
        help="Speaker ID for multi-speaker models"
    )

    args = parser.parse_args()

    # Validate inputs
    if args.text is None and args.text_file is None:
        parser.error("Either --text or --text_file must be provided")

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load model
    print("Loading model...")
    model, config, device = load_model(args.model_path, args.config_path)
    print(f"Model loaded on {device}")

    # Prepare texts
    texts = []
    if args.text:
        texts.append(args.text)
    if args.text_file:
        with open(args.text_file, 'r', encoding='utf-8') as f:
            texts.extend([line.strip() for line in f if line.strip()])

    # Generate speech for each text
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for i, text in enumerate(texts):
        print(f"\n[{i+1}/{len(texts)}] Synthesizing: {text[:50]}...")

        # Generate waveform
        waveform = synthesize_speech(model, config, text, device, args.speaker_id)

        # Save audio
        output_filename = f"tts_output_{timestamp}_{i+1}.wav"
        output_path = os.path.join(args.output_dir, output_filename)

        sf.write(output_path, waveform, config.audio.sample_rate)
        print(f"  Saved to: {output_path}")

    print(f"\n{'='*60}")
    print("Synthesis completed!")
    print(f"Generated {len(texts)} audio files in: {args.output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
