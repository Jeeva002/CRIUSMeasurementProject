import os
import io
import numpy as np
from PIL import Image
import pydicom
from pydicom import dcmread
from pydicom.dataset import FileDataset, Dataset
from pydicom.uid import generate_uid
from datetime import datetime
import requests
import string
import random




class FolderToDicomPacsUploader:
    def __init__(self, pacs_url):
        self.pacs_url = pacs_url
        self.valid_image_extensions = {'.jpg', '.jpeg', '.png'}

    # ---------------------------
    # Helpers
    # ---------------------------
    def is_dicom(self, file):
        try:
            with open(file, "rb") as f:
                header = f.read(132)
                if header[128:132] == b"DICM":
                    return True
            dcmread(file, stop_before_pixels=True)
            return True
        except:
            return False

    def is_image(self, file):
        ext = os.path.splitext(file)[1].lower()
        if ext not in self.valid_image_extensions:
            return False
        try:
            Image.open(file).verify()
            return True
        except:
            return False

    def get_study_uid(self, file):
        try:
            ds = dcmread(file, stop_before_pixels=True)
            return ds.get("StudyInstanceUID")
        except:
            return None

    # ---------------------------
    # Convert image → DICOM
    # ---------------------------
    def create_dicom_from_image(self, img_path, study_uid, series_uid, instance, patient_name, patient_id):
        img = Image.open(img_path)
        if img.mode not in ["L", "RGB"]:
            img = img.convert("RGB")

        arr = np.array(img)

        file_meta = Dataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"

        ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)

        # ------------------------------------
        # Patient & Study Info (shared per study)
        # ------------------------------------
        ds.PatientName = patient_name
        ds.PatientID = patient_id

        ds.StudyID = "1"
        ds.AccessionNumber = "ACC001"
        ds.StudyDescription = "ABDOMEN/US"
        ds.SeriesDescription = "Converted Series"
        ds.PatientBirthDate = ""
        ds.PatientSex = ""

        now = datetime.now()
        ds.StudyDate = now.strftime('%Y%m%d')
        ds.StudyTime = now.strftime('%H%M%S')

        ds.StudyInstanceUID = study_uid
        ds.SeriesInstanceUID = series_uid
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

        ds.Modality = "US"
        ds.SeriesNumber = 1
        ds.InstanceNumber = instance

        if arr.ndim == 2:
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
        else:
            ds.SamplesPerPixel = 3
            ds.PhotometricInterpretation = "RGB"
            ds.PlanarConfiguration = 0

        ds.Rows, ds.Columns = arr.shape[0], arr.shape[1]
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.PixelData = arr.tobytes()

        buffer = io.BytesIO()
        ds.save_as(buffer, write_like_original=False)
        buffer.seek(0)

        return buffer

    # ---------------------------
    # Upload DICOM
    # ---------------------------
    def upload_dicom(self, buffer):
        resp = requests.post(
            self.pacs_url,
            data=buffer.read(),
            headers={"Content-Type": "application/dicom"}
        )
        return resp.status_code in [200, 201]

    # ---------------------------
    # Main Process
    # ---------------------------
    def process_folder(self, folder_path):
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return {
                "status": False,
                "message": f"Folder not found: {folder_path}",
                "study_instance_uids": [],
                "uploaded": 0,
                "failed": 0
            }

        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]

        dicoms = [f for f in files if self.is_dicom(f)]
        images = [f for f in files if self.is_image(f)]

        uploaded = 0
        failed = 0
        study_uids = set()

        # -----------------------------
        # Case 1: DICOM files exist
        # -----------------------------
        if dicoms:
            for dcm in dicoms:
                try:
                    study_uid = self.get_study_uid(dcm)
                    if study_uid:
                        study_uids.add(study_uid)

                    with open(dcm, "rb") as f:
                        buf = io.BytesIO(f.read())
                        buf.seek(0)

                    if self.upload_dicom(buf):
                        uploaded += 1
                    else:
                        failed += 1

                except:
                    failed += 1

        # -----------------------------
        # Case 2: No DICOM → convert images
        # -----------------------------
        elif images:
            study_uid = generate_uid()
            series_uid = generate_uid()
            instance = 1

            # Generate NAME + ID ONCE per study
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_str = ''.join(random.choices(string.ascii_uppercase, k=4))

            patient_name = f"Anonymous_{timestamp}_{random_str}"
            patient_id = f"ID{int(datetime.now().timestamp())}{random.randint(100,999)}"

            for img in images:
                try:
                    buf = self.create_dicom_from_image(
                        img, study_uid, series_uid, instance,
                        patient_name, patient_id
                    )
                    instance += 1

                    if self.upload_dicom(buf):
                        uploaded += 1
                    else:
                        failed += 1
                except:
                    failed += 1

            study_uids.add(study_uid)

        else:
            return {
                "status": False,
                "message": "No valid DICOM or image file found",
                "study_instance_uids": [],
                "uploaded": 0,
                "failed": 0
            }

        # -----------------------------
        # Final Output Formatting
        # -----------------------------
        status = uploaded > 0
        message = "success" if status else "All uploads failed"

        return {
            "status": status,
            "message": message,
            "study_instance_uids": sorted(list(study_uids)),
            "uploaded": uploaded,
            "failed": failed
        }

# Example Usage
uploader = FolderToDicomPacsUploader(
    pacs_url="https://genai.asthramedtech.com/instances"
)

# folder_path = r"c:\Users\Welcome\Documents\dicmom2img"
# result = uploader.process_folder(folder_path)
# print(result)