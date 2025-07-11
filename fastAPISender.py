from fastapi import FastAPI,File,UploadFile,HTTPException
from fastapi.responses import FileResponse
import os 
import shutil
from pathlib import Path
import zipfile
import uvicorn
import requests

app=FastAPI(title="Zip File Transfer",version="1.0.0")

@app.get("/")
async def root():
    "API Information"

    return {
        "message": "Zip File Server API",
        "endpoints":{"download":"POST /upload-zip/ - upload a zip file"}

    }


@app.post("/upload-zip")
async def uploadZip(file: UploadFile =File(...)):
    return "zip file uploaded succesfully"


@app.get("/list-zips")
async def listAvailableFilesinServer():
  try:
    response=requests.get('http://127.0.0.1:8000')
    status=response.raise_for_status()
    data=response.json
    print(f"found {data['total_files']}")
  except Exception as e:
     print(e)

@app.get("/download-zip")
async def downloadZip(filename: str):
    listAvailableFilesinServer()
   # return FileResponse(path=file_path,filename=filena me,me)
if __name__ =="__main__":
    uvicorn.run(app,host="0.0.0.0",port=8000)