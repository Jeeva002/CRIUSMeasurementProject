from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor
import asyncio
from functools import partial

from dicomDownloader import download_study_by_uid
from scripts.logSetup import setup_logging

app = FastAPI(title="Unified Measurement and Speech API", version="1.0.0")

# Logging
logger = setup_logging()

# Global executors - separate process pools for each task type
yolo_executor = None
whisper_executor = None

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

AUDIO_TEMP_DIR = Path("temp_audio")
AUDIO_TEMP_DIR.mkdir(exist_ok=True)


# ============================================================================
# WORKER FUNCTIONS - These run in separate processes
# ============================================================================

def yolo_detection_worker(folder_path):
    """
    Worker function for YOLO detection - runs in separate process
    This function will be executed in its own process with its own Python interpreter
    """
    try:
        # Import here so each process has its own instance
        from scripts.measurementTableDetection import YOLODetector
        from scripts.measurementExtraction import processDicom
        
        # Initialize detector in this process
        detector = YOLODetector()
        
        # Process DICOM
        result1, result2 = processDicom(folder_path, detector)
        
        return {"success": True, "result1": result1, "result2": result2}
    
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def whisper_transcription_worker(audio_path):
    """
    Worker function for Whisper transcription - runs in separate process
    """
    try:
        # Import here so each process has its own instance
        from speech2Text.whisperTranscriber import WhisperTranscriberHandler
        from speech2Text.spellChecker import GrammarChecker
        
        # Initialize models in this process
        transcriber = WhisperTranscriberHandler()
        grammar_checker = GrammarChecker()
        
        # Transcribe
        transcription, status1 = transcriber.transcribe(audio_path)
        
        # Grammar check
        corrected, status2 = grammar_checker.check_and_correct(transcription)
        
        return {
            "success": status1 and status2,
            "text": corrected,
            "transcription": transcription
        }
    
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# ============================================================================
# LIFESPAN - Initialize/Cleanup Process Pools
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global yolo_executor, whisper_executor
    
    logger.info("Starting process pools...")
    
    # Create separate process pools for each task type
    # max_workers=1 means one process per pool (can increase if needed)
    yolo_executor = ProcessPoolExecutor(max_workers=1, mp_context=None)
    whisper_executor = ProcessPoolExecutor(max_workers=1, mp_context=None)
    
    logger.info("Process pools initialized successfully")
    logger.info("- YOLO executor ready")
    logger.info("- Whisper executor ready")
    
    yield
    
    # Cleanup
    logger.info("Shutting down process pools...")
    yolo_executor.shutdown(wait=True)
    whisper_executor.shutdown(wait=True)
    logger.info("Shutdown complete.")

app.router.lifespan_context = lifespan


# ============================================================================
# API MODELS
# ============================================================================

class MeasurementExtractRequest(BaseModel):
    file_id: str


# ============================================================================
# API ENDPOINTS
# ============================================================================

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
    This endpoint runs YOLO detection in a separate process.
    """
    file_id = request.file_id
    
    try:
        output_filename = DOWNLOAD_DIR / f"{file_id}.dcm"
        logger.info(f"Downloading study for file_id: {file_id}")
        
        # Download DICOM files
        success, allFiles, folderPath = download_study_by_uid(file_id, str(output_filename))
        
        if not success:
            raise HTTPException(status_code=404, detail="Failed to download DICOM from PACS")
        
        logger.info(f"Processing DICOM from folder: {folderPath}")
        logger.info("Submitting to YOLO worker process...")
        
        # Run YOLO detection in separate process
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            yolo_executor, 
            yolo_detection_worker, 
            str(folderPath)
        )
        
        # Check if processing succeeded
        if not result["success"]:
            logger.error(f"YOLO processing failed: {result.get('error')}")
            logger.error(f"Traceback: {result.get('traceback')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing DICOM: {result.get('error')}"
            )
        
        logger.info("YOLO processing completed successfully")
        
        return [
            {"patientInformation": result["result1"]},
            {"measurements": result["result2"]}
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Measurement extraction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing DICOM: {str(e)}")


@app.post("/speech2text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Upload an audio file and receive transcription.
    This endpoint runs Whisper transcription in a separate process.
    Supports common audio formats (wav, mp3, m4a, flac, ogg, etc.)
    """
    temp_path = None
    
    try:
        # Create a temporary file to save the uploaded audio
        suffix = Path(audio_file.filename).suffix if audio_file.filename else ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=AUDIO_TEMP_DIR) as temp_file:
            shutil.copyfileobj(audio_file.file, temp_file)
            temp_path = temp_file.name
        
        logger.info(f"Processing audio file: {audio_file.filename}")
        logger.info("Submitting to Whisper worker process...")
        
        # Run Whisper transcription in separate process
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            whisper_executor,
            whisper_transcription_worker,
            temp_path
        )
        
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)
        
        # Check if processing succeeded
        if result["success"]:
            logger.info("Transcription completed successfully")
            return {
                "status": "success",
                "text": result["text"]
            }
        else:
            logger.error(f"Transcription failed: {result.get('error')}")
            logger.error(f"Traceback: {result.get('traceback')}")
            return {
                "status": "failed",
                "text": result.get("text", ""),
                "error": result.get("error")
            }
    
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}", exc_info=True)
        # Clean up temporary file in case of error
        if temp_path and Path(temp_path).exists():
            Path(temp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error during transcription: {str(e)}")


@app.get("/speech/status")
async def speech_status():
    """Check if the transcription service is ready"""
    return {
        "whisper_executor": "ready" if whisper_executor else "not initialized",
        "yolo_executor": "ready" if yolo_executor else "not initialized",
        "status": "ready" if (whisper_executor and yolo_executor) else "not initialized"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=9001, reload=True)