from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
import shutil
import tempfile


from dicomDownloader import download_study_by_uid



from scripts.logSetup import setup_logging
from speech2Text.whisperTranscriber import WhisperTranscriberHandler
from speech2Text.spellChecker import GrammarChecker


app = FastAPI(title="Unified Measurement and Speech API", version="1.0.0")

# Logging and globals for speech
logger = setup_logging()
transcriber = None
grammar_checker = None

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

AUDIO_TEMP_DIR = Path("temp_audio")
AUDIO_TEMP_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global transcriber, grammar_checker
    # Initialize components for speech-to-text
    logger.info("Loading Speech-to-Text components...")
    grammar_checker = GrammarChecker()
    transcriber = WhisperTranscriberHandler()
    yield
    logger.info("Shutdown complete.")

app.router.lifespan_context = lifespan



class MeasurementExtractRequest(BaseModel):
    file_id: str



@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Unified DICOM Measurement & Speech API",
        "endpoints": {
            "POST /extract-measurements": "Extract info & measurements from DICOM",
            "POST /speech2text": "Upload audio file for transcription"
        }
    }

@app.post("/extract-measurements")
async def extract_measurements(request: MeasurementExtractRequest):
    """
    Extract measurements and patient info from a PACS DICOM file.
    """
    file_id = request.file_id
    try:
        from scripts.measurementExtraction import processDicom

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




@app.post("/speech2text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Upload an audio file and receive transcription.
    Supports common audio formats (wav, mp3, m4a, flac, ogg, etc.)
    """
    if not transcriber:
        raise HTTPException(status_code=503, detail="Transcription service not initialized")
    
    try:
        # Create a temporary file to save the uploaded audio
        suffix = Path(audio_file.filename).suffix if audio_file.filename else ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=AUDIO_TEMP_DIR) as temp_file:
            # Copy uploaded file content to temporary file
            shutil.copyfileobj(audio_file.file, temp_file)
            temp_path = temp_file.name
        
        logger.info(f"Processing audio file: {audio_file.filename}")
        
        # Transcribe the audio file
        transcription,status1 = transcriber.transcribe(temp_path)
        
        # Apply grammar correction
        corrected,status2 = grammar_checker.check_and_correct(transcription)
        
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)
        if status1 and status2:
            return {
                "status": "success",
                "text": corrected,
            
            }
        else:
            return {
                "status": "Failed",
                "text": corrected,
                
            }
        
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}", exc_info=True)
        # Clean up temporary file in case of error
        if 'temp_path' in locals():
            Path(temp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error during transcription: {str(e)}")


@app.get("/speech/status")
async def speech_status():
    """Check if the transcription model is loaded and ready"""
    model_loaded = transcriber is not None
    return {
        "model_loaded": model_loaded,
        "status": "ready" if model_loaded else "not initialized"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=9001, reload=True)