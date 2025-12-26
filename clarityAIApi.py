from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor
import asyncio
import multiprocessing as mp
from scripts.img2dcmCreation import uploader
from dicomDownloader import download_study_by_uid
from scripts.logSetup import setup_logging
from scripts.measurementExtraction import processDicom

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

def yolo_detection_worker(folder_path, measurementFlag, organLabelFlag):
    """
    Worker function for YOLO detection - runs in separate process
    This function will be executed in its own process with its own Python interpreter
    """
    import sys
    import os
    
    # Set up logging in worker process
    print(f"[YOLO_WORKER] Starting YOLO worker in process {os.getpid()}", file=sys.stderr, flush=True)
    
    try:
        print(f"[YOLO_WORKER] Importing YOLODetector...", file=sys.stderr, flush=True)
        from scripts.measurementTableDetection import YOLODetector
        
        print(f"[YOLO_WORKER] Initializing detector...", file=sys.stderr, flush=True)
        detector = YOLODetector()
        
        print(f"[YOLO_WORKER] Processing DICOM at {folder_path}...", file=sys.stderr, flush=True)
        result1, result2 = processDicom(folder_path, detector, None, measurementFlag, organLabelFlag)
        
        print(f"[YOLO_WORKER] Processing complete successfully", file=sys.stderr, flush=True)
        return {"success": True, "result1": result1, "result2": result2}
    
    except Exception as e:
        import traceback
        error_msg = f"[YOLO_WORKER] Error: {str(e)}"
        print(error_msg, file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def whisper_transcription_worker(audio_path):
    """
    Worker function for Whisper transcription - runs in separate process
    """
    import sys
    import os
    
    print(f"[WHISPER_WORKER] Starting Whisper worker in process {os.getpid()}", file=sys.stderr, flush=True)
    
    try:
        print(f"[WHISPER_WORKER] Importing transcription modules...", file=sys.stderr, flush=True)
        from speech2Text.whisperTranscriber import WhisperTranscriberHandler
        from speech2Text.spellChecker import GrammarChecker
        
        print(f"[WHISPER_WORKER] Initializing models...", file=sys.stderr, flush=True)
        transcriber = WhisperTranscriberHandler()
        grammar_checker = GrammarChecker()
        
        print(f"[WHISPER_WORKER] Transcribing audio: {audio_path}", file=sys.stderr, flush=True)
        transcription, status1 = transcriber.transcribe(audio_path)
        
        print(f"[WHISPER_WORKER] Checking grammar...", file=sys.stderr, flush=True)
        corrected, status2 = grammar_checker.check_and_correct(transcription)
        
        print(f"[WHISPER_WORKER] Processing complete", file=sys.stderr, flush=True)
        return {
            "success": status1 and status2,
            "text": corrected,
            "transcription": transcription
        }
    
    except Exception as e:
        import traceback
        error_msg = f"[WHISPER_WORKER] Error: {str(e)}"
        print(error_msg, file=sys.stderr, flush=True)
        print(traceback.format_exc(), file=sys.stderr, flush=True)
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# ============================================================================
# LIFESPAN - Initialize/Cleanup Process Pools
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global yolo_executor, whisper_executor, study_type_processor

    logger.info("Starting process pools...")

    try:
        mp.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

    yolo_executor = ProcessPoolExecutor(max_workers=1)
    whisper_executor = ProcessPoolExecutor(max_workers=1)

    # 🔥 Load Study Type Model ONCE
    from scripts.reportStudyTypeIdentification import StudyTypeProcessor
    study_type_processor = StudyTypeProcessor()

    logger.info("All processors initialized and ready")

    yield

    if yolo_executor:
        yolo_executor.shutdown(wait=True)
    if whisper_executor:
        whisper_executor.shutdown(wait=True)


# Initialize FastAPI with lifespan
app = FastAPI(
    title="Unified Measurement and Speech API",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# API MODELS
# ============================================================================

class MeasurementExtractRequest(BaseModel):
    file_id: str

class FolderPathRequest(BaseModel):
    folder_path: str


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Unified DICOM Measurement & Speech API",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "API information",
            "POST /measurementsExtractionWithLabel": "Extract measurements with organ labels from DICOM",
            "POST /measurementsExtraction": "Extract measurements from DICOM",
            "POST /metaDataExtraction": "Extract metadata from DICOM",
            "POST /upload_dicom": "Upload DICOM folder for processing",
            "POST /speech2text": "Upload audio file for transcription",
            "POST /find_study_type": "Identify ultrasound study type from report text",
            "GET /speech/status": "Check service status",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "yolo_executor": "ready" if yolo_executor else "not initialized",
        "whisper_executor": "ready" if whisper_executor else "not initialized"
    }


@app.post("/measurementsExtractionWithLabel")
async def extract_measurements_with_label(request: MeasurementExtractRequest):
    """
    Extract measurements and patient info with organ labels from a PACS DICOM file.
    This endpoint runs YOLO detection in a separate process.
    """
    file_id = request.file_id
    
    try:
        output_filename = DOWNLOAD_DIR / f"{file_id}.dcm"
        logger.info(f"[WITH_LABEL] Downloading study for file_id: {file_id}")
        
        # Download DICOM files
        success, allFiles, folderPath = download_study_by_uid(file_id, str(output_filename))
        
        if not success:
            logger.error(f"[WITH_LABEL] Failed to download DICOM from PACS for file_id: {file_id}")
            raise HTTPException(status_code=404, detail="Failed to download DICOM from PACS")
        
        logger.info(f"[WITH_LABEL] Processing DICOM from folder: {folderPath}")
        logger.info(f"[WITH_LABEL] Submitting to YOLO worker process...")
        
        # Run YOLO detection in separate process with timeout
        loop = asyncio.get_event_loop()
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    yolo_executor, 
                    yolo_detection_worker, 
                    str(folderPath), True, True
                ),
                timeout=300  # 5 minutes timeout
            )
            logger.info(f"[WITH_LABEL] Received result from YOLO worker")
        except asyncio.TimeoutError:
            logger.error(f"[WITH_LABEL] YOLO worker process timed out after 300 seconds")
            raise HTTPException(status_code=504, detail="Processing timed out after 5 minutes")
        
        # Check if processing succeeded
        if not result["success"]:
            logger.error(f"[WITH_LABEL] YOLO processing failed: {result.get('error')}")
            logger.error(f"[WITH_LABEL] Traceback: {result.get('traceback')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing DICOM: {result.get('error')}"
            )
        
        logger.info(f"[WITH_LABEL] YOLO processing completed successfully")
        
        return [
            {"patientInformation": result["result1"]},
            {"measurements": result["result2"]}
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[WITH_LABEL] Measurement extraction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing DICOM: {str(e)}")


@app.post("/measurementsExtraction")
async def extract_measurements(request: MeasurementExtractRequest):
    """
    Extract measurements and patient info from a PACS DICOM file.
    This endpoint runs YOLO detection in a separate process.
    """
    file_id = request.file_id
    
    try:
        output_filename = DOWNLOAD_DIR / f"{file_id}.dcm"
        logger.info(f"[MEASUREMENTS] Downloading study for file_id: {file_id}")
        
        # Download DICOM files
        success, allFiles, folderPath = download_study_by_uid(file_id, str(output_filename))
        
        if not success:
            logger.error(f"[MEASUREMENTS] Failed to download DICOM from PACS for file_id: {file_id}")
            raise HTTPException(status_code=404, detail="Failed to download DICOM from PACS")
        
        logger.info(f"[MEASUREMENTS] Processing DICOM from folder: {folderPath}")
        logger.info(f"[MEASUREMENTS] Submitting to YOLO worker process...")
        
        # Run YOLO detection in separate process with timeout
        loop = asyncio.get_event_loop()
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    yolo_executor, 
                    yolo_detection_worker, 
                    str(folderPath), True, False
                ),
                timeout=300  # 5 minutes timeout
            )
            logger.info(f"[MEASUREMENTS] Received result from YOLO worker")
        except asyncio.TimeoutError:
            logger.error(f"[MEASUREMENTS] YOLO worker process timed out after 300 seconds")
            raise HTTPException(status_code=504, detail="Processing timed out after 5 minutes")
        
        # Check if processing succeeded
        if not result["success"]:
            logger.error(f"[MEASUREMENTS] YOLO processing failed: {result.get('error')}")
            logger.error(f"[MEASUREMENTS] Traceback: {result.get('traceback')}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing DICOM: {result.get('error')}"
            )
        
        logger.info(f"[MEASUREMENTS] YOLO processing completed successfully")
        
        return [
            {"patientInformation": result["result1"]},
            {"measurements": result["result2"]}
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MEASUREMENTS] Measurement extraction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing DICOM: {str(e)}")


@app.post("/metaDataExtraction")
async def MetaDataExtraction(request: MeasurementExtractRequest):
    """
    Extract measurements and patient info from a PACS DICOM file.
    This endpoint runs YOLO detection in a separate process.
    """
    file_id = request.file_id
    
    try:
        output_filename = "API"/DOWNLOAD_DIR / f"{file_id}.dcm"
        logger.info(f"Downloading study for file_id: {file_id}")
        
        # Download DICOM files
        success, allFiles, folderPath = download_study_by_uid(file_id, str(output_filename))
        
        if not success:
            raise HTTPException(status_code=404, detail="Failed to download DICOM from PACS")
        
        logger.info(f"Processing DICOM from folder: {folderPath}")
        result = processDicom(folderPath,None,True,False,False)
        # Check if processing succeeded
        # if not result["success"]:
        #     logger.error(f"YOLO processing failed: {result.get('error')}")
        #     logger.error(f"Traceback: {result.get('traceback')}")
        #     raise HTTPException(
        #         status_code=500, 
        #         detail=f"Error processing DICOM: {result.get('error')}"
        #     )
        
        logger.info("YOLO processing completed successfully")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Measurement extraction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing DICOM: {str(e)}")

# Add this to your API MODELS section
class StudyTypeRequest(BaseModel):
    report_text: str

# Add this to your API ENDPOINTS section
@app.post("/find_study_type")
async def find_study_type(request: StudyTypeRequest):
    try:
        logger.info("[STUDY_TYPE] Processing report")

        status, study_type = study_type_processor.identify(
            request.report_text
        )

        return {
            "status": status,
            "study_type": study_type
        }

    except Exception as e:
        logger.error("[STUDY_TYPE] Error", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/upload_dicom")
async def upload_dicom(request: FolderPathRequest):
    """
    Process DICOM files from a local folder path.
    """
    folder_path = request.folder_path
    
    try:
        folder = Path(folder_path)
        
        if not folder.exists():
            logger.error(f"[UPLOAD] Folder does not exist: {folder_path}")
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")
        
        if not folder.is_dir():
            logger.error(f"[UPLOAD] Path is not a directory: {folder_path}")
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
       
        logger.info(f"[UPLOAD] Processing DICOM from folder: {folder_path}")
        
        # Call your function
        result = uploader.process_folder(folder_path)
        
        logger.info(f"[UPLOAD] Processing completed successfully")
        
        # Return the result directly
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UPLOAD] Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/speech2text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Upload an audio file and receive transcription.
    This endpoint runs Whisper transcription in a separate process.
    Supports common audio formats (wav, mp3, m4a, flac, ogg, etc.)
    """
    temp_path = None
    
    try:
        # Validate file
        if not audio_file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Create a temporary file to save the uploaded audio
        suffix = Path(audio_file.filename).suffix if audio_file.filename else ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=AUDIO_TEMP_DIR) as temp_file:
            shutil.copyfileobj(audio_file.file, temp_file)
            temp_path = temp_file.name
        
        logger.info(f"[SPEECH2TEXT] Processing audio file: {audio_file.filename}")
        logger.info(f"[SPEECH2TEXT] Submitting to Whisper worker process...")
        
        # Run Whisper transcription in separate process with timeout
        loop = asyncio.get_event_loop()
        
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    whisper_executor,
                    whisper_transcription_worker,
                    temp_path
                ),
                timeout=300  # 5 minutes timeout
            )
            logger.info(f"[SPEECH2TEXT] Received result from Whisper worker")
        except asyncio.TimeoutError:
            logger.error(f"[SPEECH2TEXT] Whisper worker process timed out after 300 seconds")
            raise HTTPException(status_code=504, detail="Transcription timed out after 5 minutes")
        
        # Clean up temporary file
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        
        # Check if processing succeeded
        if result["success"]:
            logger.info(f"[SPEECH2TEXT] Transcription completed successfully")
            return {
                "status": "success",
                "text": result["text"],
                "original_transcription": result.get("transcription", "")
            }
        else:
            logger.error(f"[SPEECH2TEXT] Transcription failed: {result.get('error')}")
            logger.error(f"[SPEECH2TEXT] Traceback: {result.get('traceback')}")
            return {
                "status": "failed",
                "text": result.get("text", ""),
                "error": result.get("error")
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SPEECH2TEXT] Error during transcription: {str(e)}", exc_info=True)
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


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # For production, use:
    # uvicorn.run("main:app", host="0.0.0.0", port=9001, workers=1)
    
    # For development:
    uvicorn.run("main:app", host="127.0.0.1", port=9001, reload=True)