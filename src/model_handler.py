# model_handler.py
# This file handles the interaction with the models TEACH and T2M
# It manages model storage, generation requests and output retrieval
# It uses subprocess to call the respective model scripts
# and manages the output files accordingly as well as makes them available for download


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

# Paths for python interpreters/exeutables and model directories.
TEACH_DIR = os.path.join(current_dir, "..", "models", "teach", "teach")
TEACH_PYTHON = os.path.join(TEACH_DIR, "..", "teach_venv", "bin", "python")
TEACH_MODEL = os.path.join(TEACH_DIR, "", "data", "smpl_models", "smpl")

T2M_DIR = os.path.join(current_dir, "..", "models", "t2m", "T2M-GPT")
T2M_PYTHON = os.path.join(T2M_DIR, "..", "unpacked_conda", "bin", "python")
T2M_MODEL = os.path.join(T2M_DIR, "body_models", "smpl")

MODEL_STORAGE_DIR = os.path.join(current_dir, "model_store")
stored_models: list[uuid.UUID] = []

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_STORAGE_DIR, exist_ok=True)


class ModelHandler:
    async def generate(self, motion_desc: str, request_id: uuid.UUID, status_store, model_id=None, durations: list[float] = [5]):
        if durations == []:
            durations = [5]
        motion_desc = motion_desc.replace("_", " ")
        status_store[request_id] = dlhm_types.RequestStatus.GENERATION_STARTED
        req_output_dir = OUTPUT_DIR + f"/{request_id}"
        os.makedirs(req_output_dir)
        teach_output_dir = req_output_dir + f"/teach"
        t2m_output_dir = req_output_dir + f"/t2m"
        os.makedirs(teach_output_dir, exist_ok=True)
        os.makedirs(t2m_output_dir, exist_ok=True)

        # custom smpl model handling. replaces the new model with the existing one. Backup is created on service start.
        if model_id is not None:
            print(f"Using custom model {model_id}")
            os.remove(TEACH_MODEL + "/SMPL_MALE.pkl")
            os.remove(T2M_MODEL + "/SMPL_NEUTRAL.pkl")
            shutil.copyfile(MODEL_STORAGE_DIR + f"/{model_id}/SMPL_MALE.pkl", TEACH_MODEL + "/SMPL_MALE.pkl")
            shutil.copyfile(MODEL_STORAGE_DIR + f"/{model_id}/SMPL_MALE.pkl", T2M_MODEL + "/SMPL_NEUTRAL.pkl")

        # fallbacks if something goes wrong with a custom model
        try:
            self.teach_handler(motion_desc=motion_desc, directory=teach_output_dir, request_id=request_id, durations=durations)
        except Exception as e:
            print("Error during teach generation, attempting default model...")
            if model_id is not None:
                os.remove(TEACH_MODEL + "SMPL_MALE.pkl")
                shutil.copyfile(TEACH_MODEL + "SMPL_MALE_backup.pkl", TEACH_MODEL + "SMPL_MALE.pkl")

        try:
            self.t2m_handler(motion_desc=motion_desc, directory=t2m_output_dir, request_id=request_id)
        except Exception as e:
            print("Error during t2m generation, attempting default model...")
            if model_id is not None:
                os.remove(T2M_MODEL + "SMPL_NEUTRAL.pkl")
                shutil.copyfile(T2M_MODEL + "SMPL_NEUTRAL_backup.pkl", T2M_MODEL + "SMPL_NEUTRAL.pkl")

        status_store[request_id] = dlhm_types.RequestStatus.GENERATION_FINISHED

        status_store[request_id] = dlhm_types.RequestStatus.SUCCESS

    # TEACH handler, calls the interact_teach.py script with subprocess
    # and streams the output to the console
    def teach_handler(self, motion_desc: str, directory: str, request_id: uuid.UUID, durations: list[float] = [5]):
        script_name = "interact_teach.py"
        output_dir = f"{directory}/teach_{request_id}"
        motion_duration = 2  # default duration per motion segment

        # print(motion_desc)
        motion_info = f"[{motion_desc}]"
        # print(motion_info)

        # check if durations match the number of motion assignments
        if len(durations) != (motion_info.count(",") + 1):
            print(
                f"[teach subprocess] Warning: Number of durations {len(durations)} does not match number of motion segments {len(motion_info)}. Using default duration {motion_duration}s for all segments."
            )
            durations = [motion_duration] * (motion_info.count(",") + 1)

        print(f"[teach subprocess] using motion description: {motion_info}")
        print(f"[teach subprocess] using duration: {durations}")

        command_str = (
            f"cd {TEACH_DIR} && {TEACH_PYTHON} {script_name} folder=../baseline/17l8a1tq output={output_dir} texts='{motion_info}' durs='{durations}'"
        )

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

    # T2M handler, calls the run_t2m.py script with subprocess as well as a rendering script
    # and streams the output to the console
    def t2m_handler(self, motion_desc: str, directory: str, request_id: uuid.UUID):
        output_dir = f"{directory}/t2m_{request_id}"

        # Adding "then" to separate multiple commands for better results
        motion_desc = motion_desc.replace(",", " then ")
        print(f"[t2m subprocess] using motion description: {motion_desc}")
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

    # store the uploaded model in the model storage directory
    # and keep track of the stored models in memory
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

    # checks model storage if the required model is available
    def check_model_storage(self, model_id: uuid.UUID) -> bool:
        return model_id in stored_models

    # retrieves the generated video file for a request_id
    def retrieve_video(self, request_id) -> FileResponse:
        selected_model = "teach"
        filename = f"{selected_model}_{request_id}.mp4"
        filepath = os.path.join(OUTPUT_DIR, filename)
        if not os.path.isfile(filepath):
            HTTPException(500, "File not found for this request_id")

        return FileResponse(path=filepath, media_type="video/mp4", filename=filename)
