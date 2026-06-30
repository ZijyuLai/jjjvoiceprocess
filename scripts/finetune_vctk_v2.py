#!/usr/bin/env python3
"""
VITS Model Fine-tuning Script (VCTK -> LJSpeech)
使用VCTK预训练模型在LJSpeech上微调，处理多说话人到单说话人的转换
"""

import os
import sys
import json
from pathlib import Path

# 禁用telemetry
os.environ['TRAINER_TELEMETRY'] = '0'
os.environ['COQUI_TELEMETRY'] = '0'

import torch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits
from TTS.tts.datasets import load_tts_samples
from TTS.tts.utils.speakers import SpeakerManager
from TTS.config.shared_configs import BaseDatasetConfig
from trainer import Trainer, TrainerArgs

# VCTK预训练模型路径 (自动适配平台)
if sys.platform == "darwin":
    VCTK_MODEL_DIR = Path.home() / "Library/Application Support/tts/tts_models--en--vctk--vits"
elif sys.platform == "win32":
    VCTK_MODEL_DIR = Path.home() / "AppData/Local/tts/tts_models--en--vctk--vits"
else:
    VCTK_MODEL_DIR = Path.home() / ".local/share/tts/tts_models--en--vctk--vits"


def check_device():
    if torch.cuda.is_available():
        print(f"Using CUDA: {torch.cuda.get_device_name(0)}")
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("Using Apple Silicon MPS acceleration")
        return "mps"
    print("Using CPU")
    return "cpu"


def finetune_vctk_to_ljspeech(data_path, output_path, epochs=5, batch_size=8, learning_rate=0.00002, continue_path=None):
    """Fine-tune VCTK model on LJSpeech dataset"""

    device = check_device()

    # 查找VCTK模型文件
    vctk_config_path = VCTK_MODEL_DIR / "config.json"
    vctk_checkpoint = VCTK_MODEL_DIR / "model_file.pth"
    vctk_speakers = VCTK_MODEL_DIR / "speaker_ids.json"

    if not vctk_config_path.exists() or not vctk_checkpoint.exists():
        print(f"VCTK model not found at {VCTK_MODEL_DIR}")
        print("Downloading VCTK model...")
        from TTS.api import TTS
        tts = TTS("tts_models/en/vctk/vits")
        del tts

    print(f"Loading VCTK config from: {vctk_config_path}")

    # 加载VCTK配置
    config = VitsConfig()
    config.load_json(str(vctk_config_path))

    # 保存原始说话人数量
    original_num_speakers = config.model_args.num_speakers
    print(f"Original VCTK speakers: {original_num_speakers}")

    # 修改配置用于LJSpeech微调
    # 保持多说话人结构，但只使用一个说话人
    config.model_args.num_speakers = original_num_speakers  # 保持109个说话人
    config.model_args.init_discriminator = True

    # 批次和训练配置
    config.batch_size = batch_size
    config.eval_batch_size = 4
    config.num_loader_workers = 4
    config.num_eval_loader_workers = 2
    config.run_eval = True
    config.test_delay_epochs = 1
    config.epochs = epochs
    config.output_path = output_path
    config.save_step = 500
    config.print_step = 50
    config.save_n_checkpoints = 3
    config.save_checkpoints = True

    # 微调学习率
    config.learning_rate = learning_rate
    config.lr_scheduler = "NoamLR"
    config.lr_scheduler_params = {"warmup_steps": 500}

    # 数据集配置 - 使用LJSpeech
    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="ljspeech",
        path=data_path,
        meta_file_train="metadata.csv",
        meta_file_val="metadata.csv",
        language="en"
    )
    config.datasets = [dataset_config]

    # 音素缓存
    config.phoneme_cache_path = os.path.join(output_path, "phoneme_cache")
    os.makedirs(config.phoneme_cache_path, exist_ok=True)

    # 测试句子
    config.test_sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is transforming speech synthesis technology.",
        "This is a text to speech system built for the course project.",
    ]

    print(f"\n{'=' * 60}")
    print("VCTK -> LJSpeech Fine-tuning (Multi-speaker to Single-speaker)")
    print(f"{'=' * 60}")
    print(f"Source model: VCTK ({original_num_speakers} speakers)")
    print(f"Target data: LJSpeech (1 speaker)")
    print(f"Data path: {data_path}")
    print(f"Output path: {output_path}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {learning_rate}")
    print(f"Device: {device}")
    print(f"{'=' * 60}\n")

    # 初始化模型
    model = Vits.init_from_config(config)

    # 加载VCTK预训练权重
    print(f"Loading VCTK checkpoint: {vctk_checkpoint}")
    model.load_checkpoint(config, checkpoint_path=str(vctk_checkpoint), eval=False, strict=False)

    # 创建SpeakerManager并加载VCTK说话人
    print("Setting up speaker manager...")
    if vctk_speakers.exists():
        speaker_manager = SpeakerManager(speaker_id_file_path=str(vctk_speakers))
        print(f"Loaded {speaker_manager.num_speakers} speakers from VCTK")
    else:
        # 如果没有speaker_ids.json，创建一个默认的
        speaker_manager = SpeakerManager()
        speaker_manager.name_to_id = {"ljspeech": 0}

    # 设置模型的speaker_manager
    model.speaker_manager = speaker_manager

    # 加载数据集
    print("Loading LJSpeech dataset...")
    train_samples, eval_samples = load_tts_samples(config.datasets, eval_split=True)
    print(f"Training samples: {len(train_samples)}")
    print(f"Eval samples: {len(eval_samples)}")

    # 为所有样本添加speaker_name字段
    # 将LJSpeech映射到VCTK中的一个说话人（使用p225，id=1）
    vctk_speaker_name = "p225"  # 使用VCTK中的一个说话人
    print(f"Mapping LJSpeech to VCTK speaker: {vctk_speaker_name}")

    for sample in train_samples:
        sample["speaker_name"] = vctk_speaker_name
    for sample in eval_samples:
        sample["speaker_name"] = vctk_speaker_name

    # 初始化训练器
    trainer_args = TrainerArgs()
    trainer_args.find_unused_parameters = False

    # 从检查点继续训练
    if continue_path:
        trainer_args.continue_path = continue_path
        print(f"\nContinuing training from: {continue_path}")

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

    parser = argparse.ArgumentParser(description="VCTK -> LJSpeech Fine-tuning")
    parser.add_argument("--data_path", type=str,
                        default=str(project_root / "data" / "LJSpeech-1.1"))
    parser.add_argument("--output_path", type=str,
                        default=str(project_root / "models" / "vctk_finetuned"))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=0.00002)
    parser.add_argument("--continue_path", type=str, default=None,
                        help="Path to checkpoint directory to continue training from")
    args = parser.parse_args()

    os.makedirs(args.output_path, exist_ok=True)

    finetune_vctk_to_ljspeech(
        data_path=args.data_path,
        output_path=args.output_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        continue_path=args.continue_path,
    )


if __name__ == "__main__":
    main()
