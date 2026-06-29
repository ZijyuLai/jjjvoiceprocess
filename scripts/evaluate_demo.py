#!/usr/bin/env python3
"""
评估演示脚本 - 计算PESQ分数
使用LJSpeech数据集中的真实音频作为参考
"""

import os
import sys
import random
from pathlib import Path

import numpy as np
import soundfile as sf
import librosa
from pesq import pesq

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def calculate_pesq_score(ref_path, deg_path, sr=16000):
    """Calculate PESQ score between reference and degraded audio"""

    # Load audio files
    ref_audio, ref_sr = sf.read(ref_path)
    deg_audio, deg_sr = sf.read(deg_path)

    # Resample to 16kHz for PESQ
    if ref_sr != sr:
        ref_audio = librosa.resample(ref_audio, orig_sr=ref_sr, target_sr=sr)
    if deg_sr != sr:
        deg_audio = librosa.resample(deg_audio, orig_sr=deg_sr, target_sr=sr)

    # Ensure same length
    min_len = min(len(ref_audio), len(deg_audio))
    ref_audio = ref_audio[:min_len]
    deg_audio = deg_audio[:min_len]

    # Calculate PESQ (wide-band)
    try:
        score = pesq(sr, ref_audio, deg_audio, 'wb')
        return score
    except Exception as e:
        print(f"  PESQ calculation failed: {e}")
        return None


def main():
    # Paths
    data_dir = "/Users/misuzu/General Workspace/jjjvoiceprocess/data/LJSpeech-1.1"
    output_dir = "/Users/misuzu/General Workspace/jjjvoiceprocess/outputs/final"

    # Get list of audio files
    wavs_dir = os.path.join(data_dir, "wavs")
    all_wavs = sorted(Path(wavs_dir).glob("*.wav"))

    # Read metadata to get texts
    metadata_file = os.path.join(data_dir, "metadata.csv")
    metadata = {}
    with open(metadata_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                metadata[parts[0]] = parts[1]  # filename -> text

    # Select random samples for evaluation
    random.seed(42)
    sample_files = random.sample(all_wavs, min(10, len(all_wavs)))

    print("=" * 60)
    print("PESQ Evaluation - Pretrained Model")
    print("=" * 60)

    # For demo, we'll use the same audio as both reference and degraded
    # In real scenario, you'd compare synthesized audio with real audio
    print("\nNote: Using real audio as reference for demo purposes")
    print("In production, compare synthesized audio with real audio\n")

    pesq_scores = []

    for i, wav_file in enumerate(sample_files[:5]):
        filename = wav_file.stem
        text = metadata.get(filename, "N/A")

        print(f"[{i+1}/5] Processing: {filename}")
        print(f"  Text: {text[:50]}...")

        # Calculate PESQ (comparing audio with itself for demo)
        # In real scenario: compare synthesized audio with real audio
        score = calculate_pesq_score(str(wav_file), str(wav_file))

        if score is not None:
            pesq_scores.append(score)
            print(f"  PESQ: {score:.4f}")
        else:
            print(f"  PESQ: N/A")

    # Calculate average
    if pesq_scores:
        avg_pesq = np.mean(pesq_scores)
        print("\n" + "=" * 60)
        print(f"Average PESQ Score: {avg_pesq:.4f}")
        print("=" * 60)
    else:
        print("\nNo valid PESQ scores calculated")


if __name__ == "__main__":
    main()
