#!/usr/bin/env python3
"""
评估对比脚本 - 对比预训练模型和微调模型的效果
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

import torch
import soundfile as sf
import librosa
from pesq import pesq
from pystoi import stoi

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits
from TTS.utils.audio import AudioProcessor
from TTS.tts.utils.synthesis import synthesis


def check_device():
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_model(config_path, checkpoint_path):
    """加载TTS模型"""
    config = VitsConfig()
    config.load_json(config_path)

    model = Vits.init_from_config(config)
    model.load_checkpoint(config, checkpoint_path=checkpoint_path, eval=True)

    device = check_device()
    model = model.to(device)

    return model, config, device


def generate_audio(model, config, text, device):
    """生成语音"""
    outputs = synthesis(
        model=model,
        text=text,
        CONFIG=config,
        use_cuda=device == "cuda",
        speaker_id=None,
        d_vector=None,
        style_wav=None,
    )
    waveform = outputs["wav"]
    if isinstance(waveform, torch.Tensor):
        waveform = waveform.cpu().numpy()
    return waveform


def calculate_metrics(ref_path, deg_path, sr=16000):
    """计算客观评估指标"""
    ref_audio, ref_sr = sf.read(ref_path)
    deg_audio, deg_sr = sf.read(deg_path)

    # 重采样到16kHz
    if ref_sr != sr:
        ref_audio = librosa.resample(ref_audio, orig_sr=ref_sr, target_sr=sr)
    if deg_sr != sr:
        deg_audio = librosa.resample(deg_audio, orig_sr=deg_sr, target_sr=sr)

    # 确保长度一致
    min_len = min(len(ref_audio), len(deg_audio))
    ref_audio = ref_audio[:min_len]
    deg_audio = deg_audio[:min_len]

    results = {}

    # PESQ
    try:
        results["pesq"] = pesq(sr, ref_audio, deg_audio, "wb")
    except Exception as e:
        results["pesq"] = None
        print(f"  PESQ failed: {e}")

    # STOI
    try:
        results["stoi"] = stoi(ref_audio, deg_audio, sr, extended=False)
    except Exception as e:
        results["stoi"] = None
        print(f"  STOI failed: {e}")

    # SNR
    try:
        noise = ref_audio - deg_audio
        signal_power = np.mean(ref_audio ** 2)
        noise_power = np.mean(noise ** 2)
        if noise_power > 0:
            results["snr"] = 10 * np.log10(signal_power / noise_power)
        else:
            results["snr"] = float("inf")
    except:
        results["snr"] = None

    # MCD (Mel Cepstral Distortion)
    try:
        ref_mel = librosa.feature.melspectrogram(y=ref_audio, sr=sr, n_mels=13)
        deg_mel = librosa.feature.melspectrogram(y=deg_audio, sr=sr, n_mels=13)
        ref_mfcc = librosa.feature.mfcc(S=librosa.power_to_db(ref_mel))
        deg_mfcc = librosa.feature.mfcc(S=librosa.power_to_db(deg_mel))
        min_frames = min(ref_mfcc.shape[1], deg_mfcc.shape[1])
        mcd = np.mean(np.sqrt(np.sum((ref_mfcc[:, :min_frames] - deg_mfcc[:, :min_frames]) ** 2, axis=0)))
        results["mcd"] = mcd
    except:
        results["mcd"] = None

    return results


def compare_models():
    """对比预训练模型和微调模型"""

    # 测试文本
    test_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning has revolutionized speech synthesis technology.",
        "This is a text to speech system built for the course project.",
    ]

    # 模型路径 (自动适配平台)
    import sys
    if sys.platform == "darwin":
        vctk_model_dir = Path.home() / "Library/Application Support/tts/tts_models--en--vctk--vits"
    elif sys.platform == "win32":
        vctk_model_dir = Path.home() / "AppData/Local/tts/tts_models--en--vctk--vits"
    else:
        vctk_model_dir = Path.home() / ".local/share/tts/tts_models--en--vctk--vits"

    pretrained_config = vctk_model_dir / "config.json"
    pretrained_checkpoint = vctk_model_dir / "model_file.pth"

    finetuned_config = str(project_root / "models" / "vctk_finetuned" / "config.json")
    finetuned_checkpoint = None  # 将在训练完成后设置

    # 查找最新的微调检查点
    finetuned_dir = project_root / "models" / "vctk_finetuned"
    if finetuned_dir.exists():
        checkpoints = sorted(finetuned_dir.glob("checkpoint_*.pth"))
        if checkpoints:
            finetuned_checkpoint = checkpoints[-1]

    output_dir = str(project_root / "outputs" / "comparison")
    os.makedirs(output_dir, exist_ok=True)

    device = check_device()
    print(f"Using device: {device}")

    results = {
        "pretrained": {"audio_files": [], "metrics": []},
        "finetuned": {"audio_files": [], "metrics": []},
    }

    # 生成预训练模型音频
    print("\n" + "=" * 60)
    print("Generating audio with PRETRAINED model (VCTK)")
    print("=" * 60)

    if pretrained_config.exists() and pretrained_checkpoint.exists():
        model_pre, config_pre, _ = load_model(str(pretrained_config), str(pretrained_checkpoint))

        for i, text in enumerate(test_texts):
            print(f"  [{i+1}/{len(test_texts)}] {text[:50]}...")
            waveform = generate_audio(model_pre, config_pre, text, device)
            output_path = os.path.join(output_dir, f"pretrained_{i+1}.wav")
            sf.write(output_path, waveform, config_pre.audio.sample_rate)
            results["pretrained"]["audio_files"].append(output_path)

        del model_pre  # 释放内存
    else:
        print("Pretrained model not found!")

    # 生成微调模型音频
    if finetuned_checkpoint and Path(finetuned_config).exists():
        print("\n" + "=" * 60)
        print("Generating audio with FINETUNED model")
        print("=" * 60)

        model_ft, config_ft, _ = load_model(finetuned_config, str(finetuned_checkpoint))

        for i, text in enumerate(test_texts):
            print(f"  [{i+1}/{len(test_texts)}] {text[:50]}...")
            waveform = generate_audio(model_ft, config_ft, text, device)
            output_path = os.path.join(output_dir, f"finetuned_{i+1}.wav")
            sf.write(output_path, waveform, config_ft.audio.sample_rate)
            results["finetuned"]["audio_files"].append(output_path)

        del model_ft
    else:
        print("Finetuned model not found! Please run finetune_vctk.py first.")

    # 计算指标对比
    print("\n" + "=" * 60)
    print("Calculating comparison metrics")
    print("=" * 60)

    # 使用LJSpeech的真实音频作为参考
    ljspeech_dir = str(project_root / "data" / "LJSpeech-1.1" / "wavs")
    ref_files = sorted(Path(ljspeech_dir).glob("*.wav"))[:3]

    for i, ref_file in enumerate(ref_files):
        print(f"\nSample {i+1}:")
        print(f"  Reference: {ref_file.name}")

        # 预训练模型指标
        if i < len(results["pretrained"]["audio_files"]):
            metrics = calculate_metrics(str(ref_file), results["pretrained"]["audio_files"][i])
            results["pretrained"]["metrics"].append(metrics)
            print(f"  Pretrained - PESQ: {metrics.get('pesq', 'N/A'):.4f}, STOI: {metrics.get('stoi', 'N/A'):.4f}")

        # 微调模型指标
        if i < len(results["finetuned"]["audio_files"]):
            metrics = calculate_metrics(str(ref_file), results["finetuned"]["audio_files"][i])
            results["finetuned"]["metrics"].append(metrics)
            print(f"  Finetuned  - PESQ: {metrics.get('pesq', 'N/A'):.4f}, STOI: {metrics.get('stoi', 'N/A'):.4f}")

    # 保存结果
    results_file = os.path.join(output_dir, "comparison_results.json")
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {results_file}")

    # 打印总结
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)

    if results["pretrained"]["metrics"] and results["finetuned"]["metrics"]:
        pre_pesq = np.mean([m["pesq"] for m in results["pretrained"]["metrics"] if m["pesq"]])
        ft_pesq = np.mean([m["pesq"] for m in results["finetuned"]["metrics"] if m["pesq"]])
        pre_stoi = np.mean([m["stoi"] for m in results["pretrained"]["metrics"] if m["stoi"]])
        ft_stoi = np.mean([m["stoi"] for m in results["finetuned"]["metrics"] if m["stoi"]])

        print(f"\nAverage PESQ:")
        print(f"  Pretrained: {pre_pesq:.4f}")
        print(f"  Finetuned:  {ft_pesq:.4f}")
        print(f"  Improvement: {ft_pesq - pre_pesq:+.4f}")

        print(f"\nAverage STOI:")
        print(f"  Pretrained: {pre_stoi:.4f}")
        print(f"  Finetuned:  {ft_stoi:.4f}")
        print(f"  Improvement: {ft_stoi - pre_stoi:+.4f}")

    return results


if __name__ == "__main__":
    compare_models()
