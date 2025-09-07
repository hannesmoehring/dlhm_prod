import os
import shutil
import subprocess
import uuid

from anyio import sleep
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse

import dlhm_types

current_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(current_dir, "output")

TEACH_DIR = os.path.join(current_dir, "..", "models", "teach", "teach")
TEACH_PYTHON = os.path.join(TEACH_DIR, "..", "teach_venv", "bin", "python")
TEACH_MODEL = os.path.join(TEACH_DIR, "", "data", "smpl_model", "smpl")

T2M_DIR = os.path.join(current_dir, "..", "models", "t2m", "T2M-GPT")
# ../unpacked_conda/bin/python run_t2m.py "a person sprinting and jumping"
T2M_PYTHON = os.path.join(T2M_DIR, "..", "unpacked_conda", "bin", "python")

MODEL_STORAGE_DIR = os.path.join(current_dir, "model_store")
stored_models: list[uuid.UUID] = []

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_STORAGE_DIR, exist_ok=True)


class ModelHandler:
    async def generate(self, motion_desc: str, request_id: uuid.UUID, status_store, model_id=None, durations: list[float] = []):
        status_store[request_id] = dlhm_types.RequestStatus.GENERATION_STARTED
        req_output_dir = OUTPUT_DIR + f"/{request_id}"
        os.makedirs(req_output_dir)
        teach_output_dir = req_output_dir + f"/teach"
        t2m_output_dir = req_output_dir + f"/t2m"
        os.makedirs(teach_output_dir, exist_ok=True)
        os.makedirs(t2m_output_dir, exist_ok=True)
        if model_id is not None:
            print(f"Using custom model {model_id}")
            os.remove(TEACH_MODEL + "SMPL_MALE.pkl")
            shutil.copyfile(MODEL_STORAGE_DIR + f"/{model_id}/SMPL_MALE.pkl", TEACH_MODEL + "SMPL_MALE.pkl")

        try:
            self.teach_handler(motion_desc=motion_desc, directory=teach_output_dir, request_id=request_id, model_id=model_id, durations=durations)
        except Exception as e:
            print("Error during teach generation, attempting default model...")
            os.remove(TEACH_MODEL + "SMPL_MALE.pkl")
            shutil.copyfile(TEACH_MODEL + "SMPL_MALE_backup.pkl", TEACH_MODEL + "SMPL_MALE.pkl")

        self.t2m_handler(motion_desc=motion_desc, directory=t2m_output_dir, request_id=request_id, model_id=model_id)

        status_store[request_id] = dlhm_types.RequestStatus.GENERATION_FINISHED

        status_store[request_id] = dlhm_types.RequestStatus.SUCCESS

    # python interact_teach.py folder=experiment/teach/ output=../output/outputyyy/ texts='[run, wave, walk]' durs='[5, 5,5]'
    def teach_handler(self, motion_desc: str, directory: str, request_id: uuid.UUID, model_id=None, durations: list[float] = []):
        script_name = "interact_teach.py"
        output_dir = f"{directory}/teach_{request_id}"
        motion_duration = 5
        command_str = f"cd {TEACH_DIR} && {TEACH_PYTHON} {script_name} folder=../baseline/17l8a1tq output={output_dir} texts='[{motion_desc}]' durs='[{motion_duration}]'"

        process = subprocess.Popen(
            command_str,
            cwd=TEACH_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            bufsize=1,
        )

        print("[teach subprocess] starting...\n")

        try:
            if process.stdout is not None:
                for line in process.stdout:
                    print(line, end="")
            else:
                print("[teach subprocess] No stdout to read from.")
        except KeyboardInterrupt:
            print("\n[teach subprocess] interrupted. Terminating.")
            process.terminate()

        exit_code = process.wait()
        if exit_code == 0:
            print("\n[teach subprocess] finished successfully.")
        else:
            print(f"\n[teach subprocess] exited with code {exit_code}")

    def t2m_handler(self, motion_desc: str, directory: str, request_id: uuid.UUID, model_id=None):
        output_dir = f"{directory}/t2m_{request_id}"
        command_str = f'cd {T2M_DIR} && {T2M_PYTHON} run_t2m.py "{motion_desc}" {output_dir}'
        final_render_command = f"cd {T2M_DIR} && {T2M_PYTHON} render_final.py --filedir {directory} --motion-list 1"
        process = subprocess.Popen(
            command_str,
            cwd=T2M_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            bufsize=1,
        )

        print("[t2m subprocess] starting...\n")

        try:
            if process.stdout is not None:
                for line in process.stdout:
                    print(line, end="")
            else:
                print("[t2m subprocess] No stdout to read from.")
        except KeyboardInterrupt:
            print("\n[t2m subprocess] interrupted. Terminating.")
            process.terminate()

        exit_code = process.wait()
        if exit_code == 0:
            print("\n[t2m subprocess] finished successfully.")
        else:
            print(f"\n[t2m subprocess] exited with code {exit_code}")

        print("\n[t2m subprocess] starting final rendering for SMPL rendering...\n")

        process = subprocess.Popen(
            final_render_command,
            cwd=T2M_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            bufsize=1,
        )

        print("[t2m subprocess] rendering...\n")

        try:
            if process.stdout is not None:
                for line in process.stdout:
                    print(line, end="")
            else:
                print("[t2m subprocess] No stdout to read from.")
        except KeyboardInterrupt:
            print("\n[t2m subprocess] interrupted. Terminating.")
            process.terminate()

        exit_code = process.wait()
        if exit_code == 0:
            print("\n[t2m subprocess] finished rendering.")
        else:
            print(f"\n[t2m subprocess] exited with code {exit_code}")

    def store_model(self, model: UploadFile, model_id: uuid.UUID) -> bool:
        os.makedirs(MODEL_STORAGE_DIR + f"/{model_id}", exist_ok=True)
        save_path = os.path.join(MODEL_STORAGE_DIR, f"{model_id}", "SMPL_MALE.pkl")
        if model is None:
            return False

        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(model.file, buffer)
            stored_models.append(model_id)
            return True
        except:
            return False

    def check_model_storage(self, model_id: uuid.UUID) -> bool:
        return model_id in stored_models

    def retrieve_video(self, request_id) -> FileResponse:
        selected_model = "teach"
        filename = f"{selected_model}_{request_id}.mp4"
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.isfile(filepath):
            HTTPException(500, "File not found for this request_id")

        return FileResponse(path=filepath, media_type="video/mp4", filename=filename)
