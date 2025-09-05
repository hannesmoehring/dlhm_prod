#!/bin/bash
echo "starting t2m setup"
pwd
mkdir -p models/t2m && cd models/t2m

CURRENT_DIR="$(pwd)"

echo "sudo installs + wait"
sudo apt install -y wget && \
sudo wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
sudo /bin/bash ~/miniconda.sh -b -p /opt/conda && \
sudo rm -r ~/miniconda.sh
sudo mount -o remount,size=8G /dev/shm
sleep 10s
echo "starting copy"
rsync /mnt/projects/dlhm/mohringhannes/misc/local_conda.tar.gz .
echo "starting unpack"
mkdir unpacked_conda
tar -xzf local_conda.tar.gz -C unpacked_conda
rm local_conda.tar.gz
cd $CURRENT_DIR
echo "starting conda env"
source /opt/conda/bin/activate unpacked_conda/
sleep 10s
cd $CURRENT_DIR
python -m pip install torch==1.11.0+cu113 torchvision==0.12.0+cu113 torchaudio==0.11.0 --extra-index-url https://download.pytorch.org/whl/cu113
python -m pip install numpy==1.21
python -m pip install moviepy==1.0.3
printf "import ssl\nssl._create_default_https_context = ssl._create_unverified_context\n\n" | cat - $CURRENT_DIR/unpacked_conda/lib/python3.8/site-packages/clip/clip.py > temp && mv temp $CURRENT_DIR/unpacked_conda/lib/python3.8/site-packages/clip/clip.py
echo "getting everything."
rsync --progress /mnt/projects/dlhm/mohringhannes/dev/t2m/gpt_t2m_20250809-051810.zip .
unzip gpt_t2m_20250809-051810.zip
rm gpt_t2m_20250809-051810.zip
mkdir T2M-GPT/dataset
cd T2M-GPT/dataset
#python -m gdown 1rmnG-R8wTb1sRs0PYp4RRmLg8XH-qSGW
#unzip humanml3d.zip
#mv humanml3d HumanML3D
cd $CURRENT_DIR
cp /mnt/projects/dlhm/mohringhannes/dev/t2m/run_t2m.py T2M-GPT/
python -m pip install h5py
python -m pip install shapely pyrender trimesh mapbox_earcut
cd $CURRENT_DIR
cd T2M-GPT
sed -i '5d' render_final.py
mkdir body_models
cd body_models
rsync /mnt/projects/dlhm/mohringhannes/dev/t2m/smpl.zip .
unzip smpl.zip
rm smpl.zip
cd ..
echo "starting example run"
sed -i '183c\    import glob, os\n    filename_list = [f for f in sorted(glob.glob(os.path.join(args.filedir, "*"))) if f.endswith((".npy",".npz"))]' render_final.py
sed -i '188c\    \    motions = np.load(filedir + filename, allow_pickle=True)' render_final.py
sed -i '1i import os; os.environ.setdefault("PYRENDER_PLATFORM","egl"); os.environ.setdefault("PYOPENGL_PLATFORM","egl"); os.environ.pop("DISPLAY", None); os.environ["PYGLET_HEADLESS"]="1"' render_final.py
sed -i '193d' render_final.py
sed -i '193d' render_final.py
sed -i '193d' render_final.py
cd $CURRENT_DIR
cd T2M-GPT
python run_t2m.py "a man sprinting and jumping"
echo "example run over"
python render_final.py --filedir ../gen_output/ --motion-list 1
cd $CURRENT_DIR 
cd ../..
