from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn

# --- DICOM Imports ---
# Replace with your actual modules
from dicomDownloader import download_study_by_uid


# --- Speech Imports ---
from scripts.logSetup import setup_logging
from speech2Text.audioRecorder import AudioRecorderHandler
from speech2Text.whisperTranscriber import WhisperTranscriberHandler
from speech2Text.spellChecker import GrammarChecker

# --- Setup ---
app = FastAPI(title="Unified Measurement and Speech API", version="1.0.0")

# Logging and globals for speech
logger = setup_logging()
recorder = None
transcriber = None
grammar_checker = None

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global recorder, transcriber, grammar_checker
    # Initialize components for speech-to-text
    logger.info("Loading Speech-to-Text components...")
    recorder = AudioRecorderHandler(output_dir="recordings")
    grammar_checker = GrammarChecker()
    transcriber = WhisperTranscriberHandler()
    yield
    # Cleanup: stop any still-running audio recording
    if recorder and recorder.is_recording():
        recorder.stop_recording()
    logger.info("Shutdown complete.")

app.router.lifespan_context = lifespan

# ------------- MODELS -------------

class MeasurementExtractRequest(BaseModel):
    file_id: str

class SpeechRequest(BaseModel):
    message: str

# ------------- API ENDPOINTS -------------

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Unified DICOM Measurement & Speech API",
        "endpoints": {
            "POST /extract-measurements": "Extract info & measurements from DICOM",
            "POST /speech/start": "Start audio recording",
            "POST /speech/stop": "Stop and transcribe audio"
        }
    }

@app.post("/extract-measurements")
async def extract_measurements(request: MeasurementExtractRequest):
    """
    Extract measurements and patient info from a PACS DICOM file.
    """
    file_id = request.file_id
    try:
        from scripts.measurementExtraction import processDicom  # 👈 moved here!

        output_filename = DOWNLOAD_DIR / f"{file_id}.dcm"
        logger.info(f"Downloading study for file_id: {file_id}")
        success, allFiles, folderPath = download_study_by_uid(file_id, str(output_filename))

        if not success:
            raise HTTPException(status_code=404, detail="Failed to download DICOM from PACS")

        logger.info(f"Processing DICOM from folder: {folderPath}")
        result1, result2 = processDicom(str(folderPath))

        return [
            {"patientInformation": result1},
            {"measurements": result2}
        ]

    except Exception as e:
        logger.error(f"Measurement extraction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing DICOM: {str(e)}")


# ---- Speech-to-Text ----

@app.post("/speech/start")
async def speech_start(request: SpeechRequest):
    message = request.message.strip().lower()
    if message != "start recording":
        raise HTTPException(status_code=400, detail="Request 'message' must be 'start recording'")
    if recorder.is_recording():
        raise HTTPException(status_code=400, detail="Recording already in progress")
    try:
        status=recorder.start_recording()
        return {
            "status": status,
            "message": "Recording has been started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {str(e)}")

@app.post("/speech/stop")
async def speech_stop(request: SpeechRequest):
    message = request.message.strip().lower()
    if message != "end recording":
        raise HTTPException(status_code=400, detail="Request 'message' must be 'end recording'")
    if not recorder.is_recording():
        raise HTTPException(status_code=400, detail="No recording is in progress")
    try:
        audio_path,status = recorder.stop_recording()
        if not audio_path:
            raise HTTPException(status_code=500, detail="Failed to save recording")
        transcription = transcriber.transcribe(audio_path)
        corrected = grammar_checker.check_and_correct(transcription)
      
        return {
                "status": status,
                "transcription": corrected
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during transcription: {str(e)}")
    

@app.get("/speech/status")
async def speech_status():
    is_recording = recorder.is_recording() if recorder else False
    model_loaded = transcriber is not None
    return {
        "is_recording": is_recording,
        "model_loaded": model_loaded
    }

# --- MAIN ENTRYPOINT ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
