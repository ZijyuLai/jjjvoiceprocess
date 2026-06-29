#!/usr/bin/env python3
"""
TTS Evaluation Script
Calculate PESQ and other metrics for synthesized speech
"""

import os
import sys
import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from pesq import pesq
from pystoi import stoi
import librosa

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

def calculate_stoi_score(ref_path, deg_path, sr=16000):
    """Calculate STOI score"""

    ref_audio, ref_sr = sf.read(ref_path)
    deg_audio, deg_sr = sf.read(deg_path)

    # Resample
    if ref_sr != sr:
        ref_audio = librosa.resample(ref_audio, orig_sr=ref_sr, target_sr=sr)
    if deg_sr != sr:
        deg_audio = librosa.resample(deg_audio, orig_sr=deg_sr, target_sr=sr)

    # Ensure same length
    min_len = min(len(ref_audio), len(deg_audio))
    ref_audio = ref_audio[:min_len]
    deg_audio = deg_audio[:min_len]

    # Calculate STOI
    try:
        score = stoi(ref_audio, deg_audio, sr, extended=False)
        return score
    except Exception as e:
        print(f"  STOI calculation failed: {e}")
        return None

def calculate_snr(ref_path, deg_path):
    """Calculate Signal-to-Noise Ratio"""

    ref_audio, _ = sf.read(ref_path)
    deg_audio, _ = sf.read(deg_path)

    # Ensure same length
    min_len = min(len(ref_audio), len(deg_audio))
    ref_audio = ref_audio[:min_len]
    deg_audio = deg_audio[:min_len]

    # Calculate noise
    noise = ref_audio - deg_audio

    # Calculate SNR
    signal_power = np.mean(ref_audio ** 2)
    noise_power = np.mean(noise ** 2)

    if noise_power == 0:
        return float('inf')

    snr = 10 * np.log10(signal_power / noise_power)
    return snr

def evaluate_directory(ref_dir, deg_dir, output_file=None):
    """Evaluate all audio pairs in directories"""

    # Find matching audio pairs
    ref_files = sorted(Path(ref_dir).glob("*.wav"))
    deg_files = sorted(Path(deg_dir).glob("*.wav"))

    results = []
    pesq_scores = []
    stoi_scores = []
    snr_scores = []

    print(f"\n{'='*60}")
    print("TTS Evaluation Results")
    print(f"{'='*60}\n")

    # Try to match files by name or index
    for i, ref_file in enumerate(ref_files):
        # Try to find matching degraded file
        deg_file = None

        # Try exact match first
        deg_candidate = Path(deg_dir) / ref_file.name
        if deg_candidate.exists():
            deg_file = deg_candidate
        else:
            # Try index match
            if i < len(deg_files):
                deg_file = deg_files[i]

        if deg_file is None:
            print(f"  Warning: No matching file found for {ref_file.name}")
            continue

        print(f"  Processing: {ref_file.name}")

        # Calculate metrics
        pesq_score = calculate_pesq_score(str(ref_file), str(deg_file))
        stoi_score = calculate_stoi_score(str(ref_file), str(deg_file))
        snr_score = calculate_snr(str(ref_file), str(deg_file))

        result = {
            "reference": ref_file.name,
            "degraded": deg_file.name,
            "pesq": pesq_score,
            "stoi": stoi_score,
            "snr": snr_score
        }
        results.append(result)

        if pesq_score is not None:
            pesq_scores.append(pesq_score)
        if stoi_score is not None:
            stoi_scores.append(stoi_score)
        if snr_score is not None:
            snr_scores.append(snr_score)

        print(f"    PESQ: {pesq_score:.4f}" if pesq_score else "    PESQ: N/A")
        print(f"    STOI: {stoi_score:.4f}" if stoi_score else "    STOI: N/A")
        print(f"    SNR:  {snr_score:.2f} dB" if snr_score else "    SNR: N/A")

    # Calculate averages
    print(f"\n{'='*60}")
    print("Average Scores:")
    print(f"{'='*60}")

    if pesq_scores:
        avg_pesq = np.mean(pesq_scores)
        print(f"  PESQ: {avg_pesq:.4f}")
    else:
        avg_pesq = None
        print("  PESQ: N/A")

    if stoi_scores:
        avg_stoi = np.mean(stoi_scores)
        print(f"  STOI: {avg_stoi:.4f}")
    else:
        avg_stoi = None
        print("  STOI: N/A")

    if snr_scores:
        avg_snr = np.mean(snr_scores)
        print(f"  SNR:  {avg_snr:.2f} dB")
    else:
        avg_snr = None
        print("  SNR: N/A")

    print(f"{'='*60}\n")

    # Save results to JSON
    if output_file:
        output_data = {
            "summary": {
                "avg_pesq": avg_pesq,
                "avg_stoi": avg_stoi,
                "avg_snr": avg_snr,
                "num_samples": len(results)
            },
            "details": results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {output_file}")

    return {
        "avg_pesq": avg_pesq,
        "avg_stoi": avg_stoi,
        "avg_snr": avg_snr,
        "details": results
    }

def main():
    parser = argparse.ArgumentParser(description="TTS Evaluation Script")
    parser.add_argument(
        "--ref_dir",
        type=str,
        required=True,
        help="Directory containing reference audio files"
    )
    parser.add_argument(
        "--deg_dir",
        type=str,
        required=True,
        help="Directory containing degraded/synthesized audio files"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Output JSON file for evaluation results"
    )

    args = parser.parse_args()

    # Validate directories
    if not Path(args.ref_dir).exists():
        parser.error(f"Reference directory not found: {args.ref_dir}")
    if not Path(args.deg_dir).exists():
        parser.error(f"Degraded directory not found: {args.deg_dir}")

    # Run evaluation
    results = evaluate_directory(args.ref_dir, args.deg_dir, args.output_file)

    return results

if __name__ == "__main__":
    main()
