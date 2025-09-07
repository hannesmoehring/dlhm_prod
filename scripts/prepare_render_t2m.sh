cd models/t2m/T2M-GPT
sed -i '183c\   import glob, os\n    filename_list = [f for f in sorted(glob.glob(os.path.join(args.filedir, "*"))) if f.endswith((".npy",".npz"))]' render_final.py
sed -i '188c\   \   motions = np.load(filedir + filename, allow_pickle=True)' render_final.py
sed -i '1i import os; os.environ.setdefault("PYRENDER_PLATFORM","egl"); os.environ.setdefault("PYOPENGL_PLATFORM","egl"); os.environ.pop("DISPLAY", None); os.environ["PYGLET_HEADLESS"]="1"' render_final.py
sed -i '193d' render_final.py
sed -i '193d' render_final.py
sed -i '193d' render_final.py