# Motion Generation from Textual Descriptions

This project enables **motion generation** from textual descriptions using two models: **T2M** and **TEACH**.  
Given a text input, the system generates a corresponding 3D motion and provides a downloadable archive with the results.

---

## 📂 Project Structure

```
.
|-- models
|   |-- t2m
|   `-- teach
|-- scripts
`-- src
    |-- model
    |-- model_store
    `-- output
        |-- <request_id>
            |-- t2m
            `-- teach
```

- `models/` – Pretrained environments and model dependencies
- `scripts/` – Utility scripts
- `src/model/` – Core model code
- `src/model_store/` – Model management
- `src/output/` – Generated motions, organized by request IDs

---

## ⚙️ Setup

1. **Download & Unpack**  
   First, download and unpack the provided project folder.

2. **Install Requirements**

   ```bash
   python -m pip install -r requirements.txt
   sudo apt install uvicorn
   ```

3. **Model Environments**  
   Each model requires its own environment:

   - **T2M** → `/models/t2m/unpacked_conda`
   - **TEACH** → `/models/teach/teach_venv`

   Both must use:

   - Python **3.9**
   - Pip **21.3**

   ⚠️ Dependencies for these projects are fragile. It is **highly recommended** to use the **provided environments** instead of recreating them manually. Simply place the provided environment folders at the paths above.

---

## 🚀 Running the API

Start the server with:

```bash
./start_api.sh
```

The API will be available at:

```
http://127.0.0.1:8000
```

## ![API Start](assets/media/step0.png)

## 🖥️ Usage

### 1. Generate a Motion

Send a description to the API:

```bash
curl "http://127.0.0.1:8000/generate/?motion_description=<DESCRIPTION>"
```

➡️ Returns a `request_id`.

![Step 1](assets/media/step1.png)

### Process started on the server

![Step 2](assets/media/step2.png)

---

### 2. Check Status

Query the status of your generation:

```bash
curl "http://127.0.0.1:8000/status/<request_id>"
```

---

### 3. Download the Motion

Once completed, download the ZIP folder with the rendered motions:

```bash
curl "http://127.0.0.1:8000/download/<request_id>" --output result.zip
```

This archive will contain both **T2M** and **TEACH** outputs under the corresponding request ID.

![Step 3](assets/media/step3.png)

---

## 📊 Output

Each run creates a folder under `src/output/<request_id>/` with the following structure:

```
src/output/<request_id>/
|-- t2m
`-- teach
```

---

## ⚠️ Notes

- Ensure you have **Python 3.9** and **pip 21.3** for the environments.
- Provided environments are recommended due to fragile dependencies.
- Server defaults to **port 8000**.

## Caveats

- Model Upload is supported for SMPL Models via the model_upload endpoint
  - `curl -X POST "http://localhost:8000/upload_model/" \
-F "model=@SMPL_NEUTRAL.pkl"
`
  - But due to the complex structure of TEACH and other projects, this is fragile.
- Unfortunately, there was no reliable way found to quantitavely measure the quality of single outputs.

---

## 📜 License

This project utilizes other projects, please repect the applying licenses.
