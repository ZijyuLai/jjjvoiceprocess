# TTS Speech Synthesis System

## 智能语音合成 - 课程大作业

基于 Coqui TTS 的 VITS 模型，实现文本到语音合成系统。

### 环境要求

- Python 3.10
- PyTorch 2.0+ (MPS/CUDA 支持)
- macOS with Apple Silicon 或 Linux/Windows with NVIDIA GPU

### 环境配置

```bash
# 创建 conda 环境
conda create -n tts python=3.10 -y
conda activate tts

# 安装 PyTorch (Apple Silicon)
pip install torch torchaudio

# 安装 PyTorch (NVIDIA GPU)
# pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安装依赖
pip install -r requirements.txt

# 安装 espeak-ng (macOS)
brew install espeak-ng

# 安装 espeak-ng (Linux)
# sudo apt-get install espeak-ng

# 禁用遥测（避免网络错误）
export TRAINER_TELEMETRY=0
export COQUI_TELEMETRY=0
```

### 项目结构

```
jjjvoiceprocess/
├── configs/                    # 模型配置文件
├── data/                       # 数据集目录
├── figures/                    # 报告图表
├── models/                     # 训练好的模型
├── outputs/                    # 生成的音频
│   ├── final/                  # 预训练模型测试音频
│   ├── vctk_checkpoint5000/    # VCTK微调检查点5000音频
│   ├── vctk_checkpoint6000/    # VCTK微调检查点6000音频
│   └── vctk_checkpoint6500/    # VCTK微调检查点6500音频
├── scripts/                    # 脚本文件
│   ├── download_data.sh        # 下载数据集
│   ├── train.py                # 训练脚本
│   ├── finetune.py             # LJSpeech微调脚本
│   ├── finetune_vctk_v2.py     # VCTK迁移学习微调脚本
│   ├── inference.py            # 推理脚本
│   ├── evaluate.py             # 评估脚本
│   ├── evaluate_comparison.py  # 对比评估脚本
│   ├── quick_demo.py           # 快速演示
│   └── generate_figures.py     # 生成图表
├── requirements.txt            # 依赖列表
├── FINETUNE_GUIDE.md           # 微调指南
└── README.md                   # 本文件
```

### 快速开始

#### 1. 使用预训练模型快速演示

```bash
python scripts/quick_demo.py --text "Hello, this is a text to speech synthesis system."
```

#### 2. 下载 LJSpeech 数据集

```bash
chmod +x scripts/download_data.sh
./scripts/download_data.sh
```

#### 3. 使用预训练模型生成语音

```bash
python scripts/quick_demo.py \
    --text "Your text here" \
    --output_dir outputs
```

### VCTK 迁移学习微调

本项目尝试了跨数据集迁移学习：使用 VCTK 多说话人模型在 LJSpeech 单说话人数据集上进行微调。

#### 微调训练

```bash
# 禁用遥测
export TRAINER_TELEMETRY=0
export COQUI_TELEMETRY=0

# 运行VCTK微调
python scripts/finetune_vctk_v2.py \
    --data_path data/LJSpeech-1.1 \
    --output_path models/vctk_finetuned \
    --epochs 5 \
    --batch_size 8

# 从检查点继续训练
python scripts/finetune_vctk_v2.py \
    --data_path data/LJSpeech-1.1 \
    --output_path models/vctk_finetuned \
    --epochs 5 \
    --batch_size 8 \
    --continue_path models/vctk_finetuned/-June-29-2026_02+32PM-7f2a2e4
```

#### 评估微调效果

```bash
# 对比预训练模型和微调模型
python scripts/evaluate_comparison.py
```

#### 微调实验结果

| 检查点 | PESQ | STOI | 时长准确性 | 训练Epoch |
|--------|------|------|------------|-----------|
| Checkpoint 2000 | 1.0488 | 0.0821 | 差 | 1 |
| Checkpoint 5000 | 1.0795 | 0.1961 | 好 | 2 |
| Checkpoint 6500 | 1.0729 | 0.2185 | 好 | 3 |

**主要发现：**
- STOI 从 0.0821 提升到 0.2185（+166%）
- 时长预测误差从 6 秒降低到 1 秒以内
- 证明了跨数据集迁移学习的可行性

### 评估指标

- **PESQ**: Perceptual Evaluation of Speech Quality (越大越好)
- **STOI**: Short-Time Objective Intelligibility (越大越好)
- **MCD**: Mel Cepstral Distortion (越小越好)

### 技术方案

1. **模型架构**: VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech)
2. **声码器**: HiFi-GAN (集成在 VITS 中)
3. **训练数据**: LJSpeech-1.1 (24小时英语语音)
4. **迁移学习**: VCTK (109个说话人) → LJSpeech (单说话人)
5. **评估指标**: PESQ, STOI

### 参考文献

1. Kim, J., Kong, S., & Son, J. (2021). Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech. ICML 2021.
2. Kong, J., Kim, J., & Bae, J. (2020). HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis. NeurIPS 2020.
3. Coqui TTS: https://github.com/coqui-ai/TTS
4. LJSpeech Dataset: https://keithito.com/LJ-Speech-Dataset/
5. VCTK Dataset: https://datashare.ed.ac.uk/handle/10283/3443

### 许可证

本项目仅供学术研究使用。
