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

TEACH_DIR = os.path.join(current_dir, "models", "teach", "teach")
TEACH_PYTHON = os.path.join(TEACH_DIR, "..", "venv", "bin", "python")

MODEL_STORAGE_DIR = os.path.join(current_dir, "model_store")
stored_models: list[uuid.UUID] = []


class ModelHandler:
    async def generate(
        self, motion_desc: str, request_id: uuid.UUID, status_store, model_id=None, durations: list[float] = []
    ):
        status_store[request_id] = dlhm_types.RequestStatus.GENERATION_STARTED
        self.teach_handler(motion_desc=motion_desc, request_id=request_id, model_id=model_id, durations=durations)

        status_store[request_id] = dlhm_types.RequestStatus.GENERATION_FINISHED

        status_store[request_id] = dlhm_types.RequestStatus.SUCCESS

    # python interact_teach.py folder=experiment/teach/ output=../output/outputyyy/ texts='[run, wave, walk]' durs='[5, 5,5]'
    def teach_handler(self, motion_desc: str, request_id: uuid.UUID, model_id=None, durations: list[float] = []):
        script_name = "interact_teach.py"
        output_dir = f"{OUTPUT_DIR}/teach_{request_id}"
        motion_input = [motion_desc, 5]
        command_str = f"cd {TEACH_DIR} && {TEACH_PYTHON} {script_name} folder=experiment/teach/ output={output_dir} texts='[{motion_desc}]' durs='[5]'"
        args = [
            TEACH_PYTHON,
            script_name,
            "folder=experiment/teach/",
            f"output={output_dir}",
            "texts='[a running person]'",
            "durs='[5]'",
        ]

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

    def store_model(self, model: UploadFile, model_id: uuid.UUID) -> bool:
        save_path = os.path.join(MODEL_STORAGE_DIR, "model_" + str(model_id))
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
