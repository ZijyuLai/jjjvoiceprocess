#!/usr/bin/env python3
"""
VITS Model Fine-tuning Script (VCTK -> LJSpeech)
使用VCTK预训练模型在LJSpeech上微调
"""

import os
import sys
import json
from pathlib import Path

import torch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits
from TTS.tts.datasets import load_tts_samples
from TTS.config.shared_configs import BaseDatasetConfig
from trainer import Trainer, TrainerArgs

# VCTK预训练模型路径
VCTK_MODEL_DIR = Path.home() / "Library/Application Support/tts/tts_models--en--vctk--vits"


def check_device():
    if torch.backends.mps.is_available():
        print("Using Apple Silicon MPS acceleration")
        return "mps"
    elif torch.cuda.is_available():
        print("Using CUDA acceleration")
        return "cuda"
    print("Using CPU")
    return "cpu"


def finetune_vctk_to_ljspeech(data_path, output_path, epochs=10, batch_size=8, learning_rate=0.00002):
    """Fine-tune VCTK model on LJSpeech dataset"""

    device = check_device()

    # 查找VCTK模型文件
    vctk_config = VCTK_MODEL_DIR / "config.json"
    vctk_checkpoint = VCTK_MODEL_DIR / "model_file.pth"

    if not vctk_config.exists() or not vctk_checkpoint.exists():
        print(f"VCTK model not found at {VCTK_MODEL_DIR}")
        print("Downloading VCTK model...")
        from TTS.api import TTS
        tts = TTS("tts_models/en/vctk/vits")
        del tts

    print(f"Loading VCTK config from: {vctk_config}")
    config = VitsConfig()
    config.load_json(str(vctk_config))

    # 修改配置用于LJSpeech微调
    # 注意：VCTK是多说话人，LJSpeech是单说话人
    config.model_args.num_speakers = 1  # 单说话人
    config.model_args.init_discriminator = True  # 启用判别器
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

    # 数据集配置
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
    print("VCTK -> LJSpeech Fine-tuning")
    print(f"{'=' * 60}")
    print(f"Source model: VCTK (multi-speaker)")
    print(f"Target data: LJSpeech (single-speaker)")
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

    # 加载数据集
    print("Loading LJSpeech dataset...")
    train_samples, eval_samples = load_tts_samples(config.datasets, eval_split=True)
    print(f"Training samples: {len(train_samples)}")
    print(f"Eval samples: {len(eval_samples)}")

    # 初始化训练器
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

    parser = argparse.ArgumentParser(description="VCTK -> LJSpeech Fine-tuning")
    parser.add_argument("--data_path", type=str,
                        default="/Users/misuzu/General Workspace/jjjvoiceprocess/data/LJSpeech-1.1")
    parser.add_argument("--output_path", type=str,
                        default="/Users/misuzu/General Workspace/jjjvoiceprocess/models/vctk_finetuned")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=0.00002)
    args = parser.parse_args()

    os.makedirs(args.output_path, exist_ok=True)

    finetune_vctk_to_ljspeech(
        data_path=args.data_path,
        output_path=args.output_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )


if __name__ == "__main__":
    main()
