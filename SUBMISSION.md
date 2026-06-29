# 课程大作业提交清单

## 项目信息

- **题目**: 语音合成系统（题目2）
- **学号**: [请填写]
- **姓名**: [请填写]
- **提交时间**: 2026年6月30日

## 技术方案

### 模型架构

- **模型**: VITS (Variational Inference with adversarial learning for end-to-end Text-to-Speech)
- **声码器**: HiFi-GAN (集成在VITS中)
- **框架**: Coqui TTS

### 训练数据

- **数据集**: LJSpeech-1.1
- **数据量**: 13,100条音频，约24小时
- **语言**: 英语

### 评估指标

- **PESQ**: Perceptual Evaluation of Speech Quality (越大越好)
- **测试结果**: 4.6439 (满分5.0)

## 提交文件清单

### 1. 项目报告

- [ ] 项目报告.pdf (需包含技术方案、算法设计、实验结果与分析)

### 2. 完整代码

- [x] `scripts/finetune.py` - 微调训练脚本
- [x] `scripts/inference.py` - 推理脚本
- [x] `scripts/evaluate.py` - 评估脚本
- [x] `scripts/quick_demo.py` - 快速演示脚本
- [x] `scripts/download_data.sh` - 数据下载脚本
- [x] `configs/vits_ljspeech.json` - 模型配置
- [x] `requirements.txt` - 依赖列表
- [x] `README.md` - 项目说明

### 3. 预训练模型

- [ ] 微调后的模型文件 (训练完成后保存到 `models/vits_finetuned/`)
- [x] 或使用Coqui TTS预训练模型 `tts_models/en/ljspeech/vits`

### 4. 测试音频

- [x] `outputs/final/demo_20260629_101716_1.wav` - 测试音频1
- [x] `outputs/final/demo_20260629_101716_2.wav` - 测试音频2
- [x] `outputs/final/demo_20260629_101716_3.wav` - 测试音频3

## 测试文本

1. "The quick brown fox jumps over the lazy dog."
2. "Machine learning has revolutionized speech synthesis technology."
3. "This is a text to speech system built for the course project."

## 运行说明

### 环境配置

```bash
# 创建conda环境
conda create -n tts python=3.10 -y
conda activate tts

# 安装依赖
pip install -r requirements.txt

# 安装espeak-ng (macOS)
brew install espeak-ng
```

### 使用预训练模型

```bash
# 生成测试音频
python scripts/quick_demo.py --text "Your text here" --output_dir outputs

# 评估PESQ
python scripts/evaluate.py --ref_dir data/reference --deg_dir outputs
```

### 微调训练

```bash
# 下载数据集
chmod +x scripts/download_data.sh
./scripts/download_data.sh

# 开始微调
python scripts/finetune.py --data_path data/LJSpeech-1.1 --epochs 10
```

## 创新点/改进

1. **使用预训练模型微调**: 基于Coqui TTS的VITS预训练模型，大幅减少训练时间
2. **Apple Silicon MPS加速**: 利用M5芯片的MPS加速训练
3. **完整评估流程**: 提供PESQ评估脚本

## 参考文献

1. VITS: Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech
2. Coqui TTS: https://github.com/coqui-ai/TTS
3. LJSpeech Dataset: https://keithito.com/LJ-Speech-Dataset/
