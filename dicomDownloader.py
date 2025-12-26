import requests
import urllib3
from pathlib import Path
import zipfile
import shutil

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Server configuration
ORTHANC_URL = "https://genai.asthramedtech.com"
USERNAME = "admin"
PASSWORD = "1KfN0cnVL7C3XVbg"

def download_study_by_uid(study_instance_uid, download_dir="API/downloads", extract_dir="API/extracted"):
    """
    Download DICOM study from Orthanc and extract to separate directory.
    Deletes existing files in both directories before downloading.
    
    Args:
        study_instance_uid: The DICOM Study Instance UID
        download_dir: Directory to save ZIP files (default: "API/downloads")
        extract_dir: Directory to extract DICOM files (default: "API/extracted")
    
    Returns:
        tuple: (success: bool, files_list: list, folder_path: str)
    """
    try:
        # Normalize paths to ensure we're using base directories
        download_path = Path(download_dir)
        extract_path_base = Path(extract_dir)
        
        # If download_dir contains a file extension, get parent directory
        if download_path.suffix:  # Has file extension like .dcm
            download_path = download_path.parent
        
        # Ensure we're using the base "API/downloads" and "API/extracted" directories
        # Find the "API/downloads" and "API/extracted" in the path
        download_base = Path("API/downloads")
        extract_base = Path("API/extracted")
        # Ensure we're using the base "API/downloads" and "API/extracted" directories
        # Find the "API/downloads" and "API/extracted" in the path
        download_base = Path("API/downloads")
        extract_base = Path("API/extracted")
        
        # Delete entire base directories if they exist
        if download_base.exists():
            shutil.rmtree(download_base)
  
        
        if extract_base.exists():
            shutil.rmtree(extract_base)

        
        # Create fresh directories
        download_base.mkdir(parents=True, exist_ok=True)
        extract_base.mkdir(parents=True, exist_ok=True)
        
        # 1. Find the study
        search_url = f"{ORTHANC_URL}/tools/find"
        search_payload = {
            "Level": "Study",
            "Query": {"StudyInstanceUID": study_instance_uid}
        }
        
        response = requests.post(
            search_url,
            json=search_payload,
            auth=(USERNAME, PASSWORD),
            verify=False,
            timeout=30
        )
        response.raise_for_status()
        
        studies = response.json()
        if not studies:
            return False, [], None
        
        orthanc_study_id = studies[0]
        
        # Set paths for new files using base directories
        zip_path = download_base / f"{orthanc_study_id}.zip"
        extract_path = extract_base / orthanc_study_id
        
        # 2. Download study as ZIP
        download_url = f"{ORTHANC_URL}/studies/{orthanc_study_id}/archive"
        
        response = requests.get(
            download_url,
            auth=(USERNAME, PASSWORD),
            verify=False,
            timeout=120
        )
        response.raise_for_status()
        
        # 3. Save ZIP to downloads directory
        zip_path.write_bytes(response.content)
        
        # 4. Extract to extracted directory
        extract_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 5. Get list of extracted DICOM files
        extracted_files = [f for f in extract_path.rglob('*') if f.is_file()]
        
        if not extracted_files:
            print(f" No files found after extraction")
            return False, [], None
        
        # 6. Find the actual folder containing DICOM files
        dicom_folder = extracted_files[0].parent
        
        # Convert to absolute paths
        extracted_files_abs = [str(f.absolute()) for f in extracted_files]
        folder_path = str(dicom_folder.absolute())
        
        return True, extracted_files_abs, folder_path
        
    except requests.exceptions.HTTPError as e:
        print(f" HTTP Error: {e}")
        return False, [], None
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return False, [], None


def download_single_instance(study_instance_uid, output_filename):
    """
    Download and save first DICOM instance from a study.
    Deletes existing output file before saving.
    
    Args:
        study_instance_uid: The DICOM Study Instance UID
        output_filename: Path to save the DICOM file
    
    Returns:
        tuple: (success: bool, folder_path: str)
    """
    try:
        # Delete existing output file if it exists
        output_path = Path(output_filename)
        if output_path.exists():
            output_path.unlink()
        
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        success, files, folder_path = download_study_by_uid(study_instance_uid)
        
        if success and files:
            files.sort()
            shutil.copy(files[0], output_filename)
            output_abs_path = str(output_path.absolute())
            return True, folder_path
        
        return False, None
        
    except Exception as e:
        print(f" Error: {e}")
        return False, None


# Example usage:
# if __name__ == "__main__":
#     test_uid = "1.2.826.0.1.3680043.8.1678.201.10638788272906500159.310245"
#     
#     print("=== Downloading Study ===")
#     success, all_files, folder_path = download_study_by_uid(test_uid)
#     
#     if success:
#         print(f"\n✓ Total files: {len(all_files)}")
#         print(f"✓ DICOM folder path: {folder_path}")
#         print("\nFirst 3 files:")
#         for f in all_files[:3]:
#             print(f"  {f}")