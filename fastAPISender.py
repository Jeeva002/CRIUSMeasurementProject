from fastapi import FastAPI, File, UploadFile, HTTPException
import os
import zipfile
import uvicorn
import subprocess
from pathlib import Path
from scripts.measurementExtraction import processDicom
import signal
import sys
app = FastAPI(title="ML Processing App", version="1.0.0")

# Create directories
UPLOAD_DIR = Path("API/uploads")
EXTRACT_DIR = Path("API/extracted")
UPLOAD_DIR.mkdir(exist_ok=True)
EXTRACT_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": " ML Processing API"}

@app.post("/upload-zip")
async def upload_zip(file: UploadFile = File(...)):

    
    # Check if it's a zip file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")
    
    try:
        # 1. Save uploaded zip file
        zip_path = UPLOAD_DIR / file.filename
        with open(zip_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 2. Extract zip file
        extract_path = EXTRACT_DIR / file.filename.replace('.zip', '')
        extract_path.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 3. Pass location to another program
        result1,result2 = call_other_program(str(extract_path))
        
        # 4. Return simple JSON response
        return result1,result2
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def call_other_program(extract_location):
    """Call another program with the extracted files location"""
    try:
        # Option 1: Call external program via subprocess
        # Replace 'your_program.py' with your actual program
        result1,result2=processDicom(extract_location)
            
        return result1,result2
    except Exception as e:
        return {"output": None, "error": str(e)}

if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=9001)


