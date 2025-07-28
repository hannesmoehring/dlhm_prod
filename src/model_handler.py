import subprocess
import uuid
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

TEACH_DIR = os.path.join(current_dir, "models", "teach" , "teach")
TEACH_PYTHON = os.path.join(TEACH_DIR, "..", "venv", "bin", "python")

stored_models = {}

class ModelHandler: 
    # python interact_teach.py folder=experiment/teach/ output=../output/outputyyy/ texts='[run, wave, walk]' durs='[5, 5,5]'
    def teach_handler(self, model_path, motion_desc):
        request_id = uuid.uuid4()
        script_name = "interact_teach.py"
        output_dir = f"../output/output_{request_id}"
        motion_input = [motion_desc, 5]
        command_str = f"cd {TEACH_DIR} && {TEACH_PYTHON} {script_name} folder=experiment/teach/ output={output_dir} texts='[{motion_desc}]' durs='[5]'"
        args = [
            TEACH_PYTHON,
            script_name,
            "folder=experiment/teach/",
            f"output={output_dir}",
            "texts='[a running person]'",
            "durs='[5]'"
        ]
        
        process = subprocess.Popen(
            command_str,
            cwd=TEACH_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            bufsize=1
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

    def store_model(self, model_input, model_id : uuid.UUID) -> bool:
        
        print(f"Storing model input: {model_input}")

    # teach_handler("path/to/model", "motion description")
