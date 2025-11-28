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
#1.2.826.0.1.3680043.8.1678.201.10638814340534406936.382542
def download_study_by_uid(study_instance_uid, download_dir="API/downloads", extract_dir="API/extracted"):
    """
    Download DICOM study from Orthanc and extract to separate directory.
    
    Args:
        study_instance_uid: The DICOM Study Instance UID
        download_dir: Directory to save ZIP files
        extract_dir: Directory to extract DICOM files
    
    Returns:
        tuple: (success: bool, files_list: list, folder_path: str)
    """
    try:
        # Create directories
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        Path(extract_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. Find the study
        # print(f"Searching for study: {study_instance_uid}")
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
            # print(f"✗ Study not found")
            return False, [], None
        
        orthanc_study_id = studies[0]
        # print(f"✓ Found study (ID: {orthanc_study_id})")
        
        # 2. Download study as ZIP
        download_url = f"{ORTHANC_URL}/studies/{orthanc_study_id}/archive"
        # print(f"Downloading study...")
        
        response = requests.get(
            download_url,
            auth=(USERNAME, PASSWORD),
            verify=False,
            timeout=120
        )
        response.raise_for_status()
        
        # 3. Save ZIP to downloads directory
        zip_path = Path(download_dir) / f"{orthanc_study_id}.zip"
        zip_path.write_bytes(response.content)
        # print(f"✓ Saved ZIP to: {zip_path.absolute()}")
        
        # 4. Extract to extracted directory
        extract_path = Path(extract_dir) / orthanc_study_id
        extract_path.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 5. Get list of extracted DICOM files
        extracted_files = [f for f in extract_path.rglob('*') if f.is_file()]
        
        if not extracted_files:
            print(f"✗ No files found after extraction")
            return False, [], None
        
        # 6. Find the actual folder containing DICOM files (deepest common directory)
        # Get the parent directory of the first DICOM file
        dicom_folder = extracted_files[0].parent
        
        # Convert to absolute paths
        extracted_files_abs = [str(f.absolute()) for f in extracted_files]
        folder_path = str(dicom_folder.absolute())
        
        # print(f"✓ Extracted {len(extracted_files)} files")
        # print(f"✓ DICOM files location: {folder_path}")
        
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
    
    Args:
        study_instance_uid: The DICOM Study Instance UID
        output_filename: Path to save the DICOM file
    
    Returns:
        tuple: (success: bool, folder_path: str)
    """
    try:
        success, files, folder_path = download_study_by_uid(study_instance_uid)
        
        if success and files:
            files.sort()
            shutil.copy(files[0], output_filename)
            output_abs_path = str(Path(output_filename).absolute())
            # print(f"✓ Saved to: {output_abs_path}")
            return True, folder_path
        
        return False, None
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, None


# if __name__ == "__main__":
#     # Test with your study UID
#     test_uid = "1.2.826.0.1.3680043.8.1678.201.10638788272906500159.310245"
    
#     print("=== Downloading Study ===")
#     success, all_files, folder_path = download_study_by_uid(test_uid)
    
#     if success:
#         print(f"\n✓ Total files: {len(all_files)}")
#         print(f"✓ DICOM folder path: {folder_path}")
#         print("\nFirst 3 files:")
#         for f in all_files[:3]:
#             print(f"  {f}")