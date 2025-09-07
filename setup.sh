#!/bin/bash

echo "starting setup"
python -m pip install --upgrade "pip==21.3"
python -m pip install -r requirements.txt
sudo apt install uvicorn

paths=(
  "models/teach/teach_venv"
  "models/teach/teach"
  "models/t2m/unpacked_conda"
  "models/t2m/T2M-GPT"
)

for p in "${paths[@]}"; do
    if [ -d "$p" ]; then
        echo "✅ Exists: $p"
    else
        echo "❌ Missing: $p"
    fi
done

