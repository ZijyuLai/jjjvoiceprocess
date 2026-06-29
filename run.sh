#!/bin/bash
# TTS 课程大作业 - 一键运行脚本

set -e

PROJECT_DIR="/Users/misuzu/General Workspace/jjjvoiceprocess"
DATA_DIR="$PROJECT_DIR/data"
OUTPUT_DIR="$PROJECT_DIR/models/vits_finetuned"

echo "=========================================="
echo "智能语音合成 - VITS 模型微调"
echo "=========================================="

# 激活 conda 环境
source activate tts

# Step 1: 下载 LJSpeech 数据集
echo ""
echo "[Step 1/4] 下载 LJSpeech 数据集..."
echo "=========================================="

cd "$DATA_DIR"

if [ ! -d "LJSpeech-1.1" ]; then
    echo "正在下载 LJSpeech-1.1 数据集..."
    wget https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2
    echo "解压数据集..."
    tar xjf LJSpeech-1.1.tar.bz2
    rm LJSpeech-1.1.tar.bz2
    echo "数据集下载完成!"
else
    echo "数据集已存在，跳过下载"
fi

echo "音频文件数量: $(ls LJSpeech-1.1/wavs/*.wav | wc -l)"

# Step 2: 数据预处理检查
echo ""
echo "[Step 2/4] 检查数据集..."
echo "=========================================="

cd "$PROJECT_DIR"

# 检查 metadata.csv
if [ -f "$DATA_DIR/LJSpeech-1.1/metadata.csv" ]; then
    echo "✓ metadata.csv 存在"
    echo "数据条数: $(wc -l < $DATA_DIR/LJSpeech-1.1/metadata.csv)"
else
    echo "✗ metadata.csv 不存在!"
    exit 1
fi

# Step 3: 微调训练
echo ""
echo "[Step 3/4] 开始 VITS 模型微调..."
echo "=========================================="

python scripts/finetune.py \
    --data_path "$DATA_DIR/LJSpeech-1.1" \
    --output_path "$OUTPUT_DIR" \
    --pretrained_model "tts_models/en/ljspeech/vits" \
    --epochs 50 \
    --batch_size 8 \
    --learning_rate 0.00002

# Step 4: 生成测试音频
echo ""
echo "[Step 4/4] 生成测试音频..."
echo "=========================================="

# 使用微调后的模型生成音频
python scripts/inference.py \
    --model_path "$OUTPUT_DIR/best_model.pth" \
    --text "Hello, this is a text to speech synthesis system." \
    --text "The quick brown fox jumps over the lazy dog." \
    --text "Machine learning has revolutionized speech synthesis." \
    --output_dir "$PROJECT_DIR/outputs"

echo ""
echo "=========================================="
echo "完成! 所有文件已生成"
echo "=========================================="
echo "微调模型: $OUTPUT_DIR"
echo "测试音频: $PROJECT_DIR/outputs"
echo ""
