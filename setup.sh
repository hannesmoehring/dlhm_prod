#!/bin/bash

echo "starting setup"
python -m pip install --upgrade "pip==21.3"
python -m pip install -r requirements.txt
python -m pip install gdown
sudo apt install uvicorn

echo "attempting to retrieve files..."
mkdir temp
cd temp
rsync --progress /mnt/projects/dlhm/mohringhannes/final/dlhm_final.tar.gz .
tar -xzf dlhm_prod.tar.gz
rm dlhm_prod.tar.gz
# install project with models
# unpack

cd ..
mkdir -p models/t2m
mkdir -p models/teach
cd models/t2m
# install unpacked_conda
rsync --progress /mnt/projects/dlhm/mohringhannes/final/unpacked_conda.tar.gz .
tar -xzf unpacked_conda.tar.gz
rm unpacked_conda.tar.gz
# unpack
cd ..
cd teach
# install teach_venv
rsync --progress /mnt/projects/dlhm/mohringhannes/final/teach_venv.tar.gz .
tar -xzf teach_venv.tar.gz
rm teach_venv.tar.gz
# unpack
cd ../..

mv temp/dlhm_prod/models/t2m/T2M-GPT models/t2m/
mv temp/dlhm_prod/models/teach/teach models/teach/
mv temp/dlhm_prod/models/teach/baseline models/baseline/


echo "checking model paths"

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

