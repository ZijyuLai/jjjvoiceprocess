# TTS Speech Synthesis System

## 智能语音合成 - 课程大作业

基于 Coqui TTS 的 VITS 模型，实现文本到语音合成系统。

### 环境要求

- Python 3.10
- PyTorch 2.0+ (MPS 支持)
- macOS with Apple Silicon

### 环境配置

```bash
# 创建 conda 环境
conda create -n tts python=3.10 -y
conda activate tts

# 安装依赖
pip install -r requirements.txt
```

### 项目结构

```
jjjvoiceprocess/
├── configs/              # 模型配置文件
├── data/                 # 数据集目录
├── models/               # 训练好的模型
├── outputs/              # 生成的音频
├── scripts/              # 脚本文件
│   ├── download_data.sh  # 下载数据集
│   ├── train.py          # 训练脚本
│   ├── inference.py      # 推理脚本
│   ├── evaluate.py       # 评估脚本
│   └── quick_demo.py     # 快速演示
├── requirements.txt      # 依赖列表
└── README.md             # 本文件
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

#### 3. 训练模型

```bash
python scripts/train.py \
    --data_path data/LJSpeech-1.1 \
    --output_path models \
    --epochs 100 \
    --batch_size 16
```

#### 4. 使用训练好的模型生成语音

```bash
python scripts/inference.py \
    --model_path models/best_model.pth \
    --text "Your text here" \
    --output_dir outputs
```

#### 5. 评估模型 (计算 PESQ)

```bash
python scripts/evaluate.py \
    --ref_dir data/reference_audio \
    --deg_dir outputs \
    --output_file results.json
```

### 可用的预训练模型

```bash
python scripts/quick_demo.py --list_models
```

### 技术方案

1. **模型架构**: VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech)
2. **声码器**: HiFi-GAN (集成在 VITS 中)
3. **训练数据**: LJSpeech-1.1 (24小时英语语音)
4. **评估指标**: PESQ (感知语音质量评估)

### 评估指标

- **PESQ**: Perceptual Evaluation of Speech Quality (越大越好)
- **STOI**: Short-Time Objective Intelligibility
- **SNR**: Signal-to-Noise Ratio

### 参考文献

1. VITS: Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech
2. Coqui TTS: https://github.com/coqui-ai/TTS
3. LJSpeech Dataset: https://keithito.com/LJ-Speech-Dataset/

### 许可证

本项目仅供学术研究使用。
