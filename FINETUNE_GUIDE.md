# VCTK → LJSpeech 微调方案

## 环境配置

### 1. 创建 Conda 环境

```bash
conda create -n tts python=3.10 -y
conda activate tts
```

### 2. 安装 PyTorch (CUDA 12.x)

```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. 安装依赖

```bash
pip install TTS pesq pystoi librosa soundfile tensorboardX
```

### 4. 安装 espeak-ng (Windows)

```bash
# Windows: 下载安装 https://github.com/espeak-ng/espeak-ng/releases
# 或使用 scoop:
scoop install espeak-ng
```

### 5. 禁用遥测（避免网络错误）

```bash
# 设置环境变量
export TRAINER_TELEMETRY=0
export COQUI_TELEMETRY=0

# Windows PowerShell:
$env:TRAINER_TELEMETRY=0
$env:COQUI_TELEMETRY=0
```

---

## 项目结构

```
jjjvoiceprocess/
├── data/
│   └── LJSpeech-1.1/          # 数据集
│       ├── wavs/               # 音频文件
│       └── metadata.csv        # 元数据
├── scripts/
│   ├── download_data.sh        # 下载数据集
│   └── finetune_vctk_v2.py     # 微调脚本
├── models/
│   └── vctk_finetuned/         # 微调后的模型
├── outputs/                    # 生成的音频
└── requirements.txt            # 依赖列表
```

---

## 步骤1: 下载 LJSpeech 数据集

```bash
cd data
wget https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2
tar xjf LJSpeech-1.1.tar.bz2
rm LJSpeech-1.1.tar.bz2
```

或使用脚本:

```bash
chmod +x scripts/download_data.sh
./scripts/download_data.sh
```

---

## 步骤2: 下载 VCTK 预训练模型

```bash
python -c "
from TTS.api import TTS
print('Downloading VCTK model...')
tts = TTS('tts_models/en/vctk/vits')
print('Done!')
"
```

模型会自动下载到: `~/.local/share/tts/` (Linux) 或 `%LOCALAPPDATA%\tts\` (Windows)

---

## 步骤3: 微调训练

### 创建微调脚本 `scripts/finetune_vctk_v2.py`

```python
#!/usr/bin/env python3
"""
VITS Model Fine-tuning Script (VCTK -> LJSpeech)
"""

import os
import sys
import json
from pathlib import Path

# 禁用telemetry
os.environ['TRAINER_TELEMETRY'] = '0'
os.environ['COQUI_TELEMETRY'] = '0'

import torch
from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits
from TTS.tts.datasets import load_tts_samples
from TTS.tts.utils.speakers import SpeakerManager
from TTS.config.shared_configs import BaseDatasetConfig
from trainer import Trainer, TrainerArgs

# VCTK预训练模型路径 (根据实际路径修改)
VCTK_MODEL_DIR = Path.home() / ".local/share/tts/tts_models--en--vctk--vits"  # Linux
# VCTK_MODEL_DIR = Path.home() / "AppData/Local/tts/tts_models--en--vctk--vits"  # Windows


def check_device():
    if torch.cuda.is_available():
        print(f"Using CUDA: {torch.cuda.get_device_name(0)}")
        return "cuda"
    print("Using CPU")
    return "cpu"


def finetune_vctk_to_ljspeech(data_path, output_path, epochs=5, batch_size=8, learning_rate=0.00002):
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
    config.model_args.num_speakers = original_num_speakers  # 保持109个说话人
    config.model_args.init_discriminator = True  # 启用判别器

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
    print(f"Source model: VCTK ({original_num_speakers} speakers)")
    print(f"Target data: LJSpeech (1 speaker)")
    print(f"Device: {device}")
    print(f"Epochs: {epochs}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {learning_rate}")
    print(f"{'=' * 60}\n")

    # 初始化模型
    model = Vits.init_from_config(config)

    # 加载VCTK预训练权重
    print(f"Loading VCTK checkpoint: {vctk_checkpoint}")
    model.load_checkpoint(config, checkpoint_path=str(vctk_checkpoint), eval=False, strict=False)

    # 创建SpeakerManager
    print("Setting up speaker manager...")
    if vctk_speakers.exists():
        speaker_manager = SpeakerManager(speaker_id_file_path=str(vctk_speakers))
        print(f"Loaded {speaker_manager.num_speakers} speakers from VCTK")
    else:
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
    # 将LJSpeech映射到VCTK中的p225说话人
    vctk_speaker_name = "p225"
    print(f"Mapping LJSpeech to VCTK speaker: {vctk_speaker_name}")

    for sample in train_samples:
        sample["speaker_name"] = vctk_speaker_name
    for sample in eval_samples:
        sample["speaker_name"] = vctk_speaker_name

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VCTK -> LJSpeech Fine-tuning")
    parser.add_argument("--data_path", type=str, default="./data/LJSpeech-1.1")
    parser.add_argument("--output_path", type=str, default="./models/vctk_finetuned")
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
```

### 运行微调

```bash
# 设置环境变量
export TRAINER_TELEMETRY=0
export COQUI_TELEMETRY=0

# 运行微调 (5个epoch)
python scripts/finetune_vctk_v2.py \
    --data_path data/LJSpeech-1.1 \
    --output_path models/vctk_finetuned \
    --epochs 5 \
    --batch_size 16 \
    --learning_rate 0.00002
```

### 预计时间 (4070 Super)

| Epochs | Batch Size | 预计时间 |
|--------|------------|----------|
| 5 | 8 | ~6小时 |
| 5 | 16 | ~4小时 |
| 10 | 8 | ~12小时 |
| 10 | 16 | ~8小时 |

---

## 步骤4: 生成测试音频

```python
# scripts/generate_test.py
import os
import torch
from TTS.tts.configs.vits_config import VitsConfig
from TTS.tts.models.vits import Vits
from TTS.utils.audio import AudioProcessor
from TTS.tts.utils.synthesis import synthesis
import soundfile as sf

# 加载微调后的模型
config_path = "models/vctk_finetuned/config.json"
checkpoint_path = "models/vctk_finetuned/best_model.pth"  # 或 checkpoint_XXXX.pth

config = VitsConfig()
config.load_json(config_path)

model = Vits.init_from_config(config)
model.load_checkpoint(config, checkpoint_path=checkpoint_path, eval=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

ap = AudioProcessor.init_from_config(config)

# 测试文本
test_texts = [
    "The quick brown fox jumps over the lazy dog.",
    "Machine learning has revolutionized speech synthesis technology.",
    "This is a text to speech system built for the course project.",
]

output_dir = "outputs/finetuned"
os.makedirs(output_dir, exist_ok=True)

for i, text in enumerate(test_texts):
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

    output_path = os.path.join(output_dir, f"finetuned_{i+1}.wav")
    sf.write(output_path, waveform, config.audio.sample_rate)
    print(f"Generated: {output_path}")
```

---

## 步骤5: 评估模型

```bash
python scripts/evaluate_comparison.py
```

### 评估指标

| 指标 | 说明 | 期望 |
|------|------|------|
| PESQ | 感知语音质量 | > 4.0 |
| STOI | 语音可懂度 | > 0.9 |
| MCD | 梅尔倒谱失真 | < 5.0 |

---

## 预期结果

### 损失函数变化 (5个Epoch)

| Epoch | loss_1 (生成器) | loss_mel | loss_kl |
|-------|----------------|----------|---------|
| 0 | 47.78 → 25.38 | 29.50 → 19.05 | 11.11 → 2.36 |
| 1 | ~23 | ~18 | ~2 |
| 2 | ~22 | ~17 | ~1.8 |
| 3 | ~21 | ~17 | ~1.6 |
| 4 | ~20 | ~16 | ~1.5 |

### 微调效果评判

1. **损失下降**: loss_1 和 loss_mel 持续下降
2. **PESQ提升**: 微调后PESQ应高于预训练模型
3. **主观听感**: 音频更自然、清晰

---

## 常见问题

### 1. SSL连接错误

```bash
export TRAINER_TELEMETRY=0
export COQUI_TELEMETRY=0
```

### 2. 内存不足

减小batch_size:

```bash
python scripts/finetune_vctk_v2.py --batch_size 4
```

### 3. 找不到VCTK模型

手动下载:

```python
from TTS.api import TTS
tts = TTS("tts_models/en/vctk/vits")
```

### 4. Windows路径问题

使用正斜杠或原始字符串:

```python
data_path = "C:/Users/username/data/LJSpeech-1.1"
# 或
data_path = r"C:\Users\username\data\LJSpeech-1.1"
```

---

## 4070 Super 优化建议

1. **增大batch_size**: 4070S有12GB显存，可以用batch_size=16或32
2. **启用混合精度**: 在config中设置 `mixed_precision=True`
3. **增加workers**: `num_loader_workers=8`

```bash
python scripts/finetune_vctk_v2.py \
    --batch_size 16 \
    --epochs 10
```
