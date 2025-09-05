#!/bin/bash
echo "starting teach setup"
pwd
mkdir -p models/teach && cd models/teach

CURRENT_DIR="$(pwd)"

rsync --progress /mnt/projects/dlhm/mohringhannes/dev/teach/teach_gpu_ready.tar.gz .
echo "unpacking gpu ready"
tar -xzf teach_gpu_ready.tar.gz
rm teach_gpu_ready.tar.gz

rsync --progress /mnt/projects/dlhm/mohringhannes/dev/teach/teach_finished_full_epoch.tar.gz .
echo "unpacking trained"
tar -xf teach_finished_full_epoch.tar.gz
rm teach_finished_full_epoch.tar.gz

cd $CURRENT_DIR
source teach_venv/bin/activate
mkdir compress_output
echo "starting generation..."
cd teach
python interact_teach.py folder=../baseline/17l8a1tq output=../compress_output/v1-seed-1234 texts='[run, turn, hands over the head, walk]' durs='[2, 1, 2, 1]' seed=1234
cd $CURRENT_DIR
cd ../..