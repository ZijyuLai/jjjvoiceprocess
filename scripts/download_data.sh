#!/bin/bash
# Download LJSpeech-1.1 dataset

set -e

DATA_DIR="/Users/misuzu/General Workspace/jjjvoiceprocess/data"
mkdir -p "$DATA_DIR"

echo "Downloading LJSpeech-1.1 dataset..."
cd "$DATA_DIR"

if [ ! -d "LJSpeech-1.1" ]; then
    wget https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2
    echo "Extracting dataset..."
    tar xjf LJSpeech-1.1.tar.bz2
    rm LJSpeech-1.1.tar.bz2
    echo "Done! Dataset saved to $DATA_DIR/LJSpeech-1.1"
else
    echo "Dataset already exists at $DATA_DIR/LJSpeech-1.1"
fi

echo "Dataset structure:"
ls -la LJSpeech-1.1/
echo ""
echo "Number of audio files: $(ls LJSpeech-1.1/wavs/*.wav 2>/dev/null | wc -l)"
