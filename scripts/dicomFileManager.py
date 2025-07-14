# Import required modules for image processing and DICOM handling
import cv2
import pydicom
import os

# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

def isDicomFile(dicomPath):
    """
    Verify if a given file path points to a valid DICOM file
    
    This function attempts to read the file using pydicom library to determine
    if it's a valid DICOM file format.
    
    Args:
        dicomPath (str): File path to check for DICOM validity
        
    Returns:
        tuple: (bool, str or None) - (True, dicomPath) if valid DICOM, (False, None) if invalid
    """
    
    logger.debug("Checking if file is valid DICOM: %s", dicomPath)
    
    try:
        # Attempt to read the file as a DICOM file
        logger.debug("Attempting to read DICOM file with pydicom")
        verifyDicomFile = pydicom.dcmread(dicomPath)
        
        logger.debug("File successfully validated as DICOM: %s", dicomPath)
        return True, dicomPath
        
    except Exception as e:
        # File is not a valid DICOM file or cannot be read
        logger.debug("File is not a valid DICOM file: %s - Error: %s", dicomPath, str(e))
        return False, None

def findMetaData(dicomPath):
    """
    Extract the scan type information from a DICOM file's metadata
    
    This function reads the DICOM file and extracts the StudyDescription tag
    (0x0008, 0x1030) which typically contains the scan type information.
    
    Args:
        dicomPath (str): Path to the DICOM file
        
    Returns:
        str or None: Scan type description if found, None if not available
    """
    
    logger.debug("Extracting scan type from DICOM file: %s", dicomPath)
    
    try:
        # Read DICOM metadata
        logger.debug("Reading DICOM metadata for scan type extraction")
        dicomMetaData = pydicom.dcmread(dicomPath)
        
        # Extract StudyDescription tag (0x0008, 0x1030)
        dicom_info = {
            "PatientName": dicomMetaData.get((0x0010, 0x0010), None).value if (0x0010, 0x0010) in dicomMetaData else None,
            "PatientID": dicomMetaData.get((0x0010, 0x0020), None).value if (0x0010, 0x0020) in dicomMetaData else None,
            "PatientAge": dicomMetaData.get((0x0010, 0x0030), None).value if (0x0010, 0x0030) in dicomMetaData else None,
            "PatientGender": dicomMetaData.get((0x0010, 0x0040), None).value if (0x0010, 0x0040) in dicomMetaData else None,
            "HospitalName": dicomMetaData.get((0x0008, 0x0080), None).value if (0x0008, 0x0080) in dicomMetaData else None,
            "PhysicianName": dicomMetaData.get((0x0008, 0x0090), None).value if (0x0008, 0x0090) in dicomMetaData else None,
            "scanType": dicomMetaData.get((0x0008, 0x1030), None).value if (0x0008, 0x1030) in dicomMetaData else None,
            "scanDate": dicomMetaData.get((0x0008, 0x0020), None).value if (0x0008, 0x0020) in dicomMetaData else None,
            "scanTime": dicomMetaData.get((0x0008, 0x0030), None).value if (0x0008, 0x0030) in dicomMetaData else None,
            "scanModality": dicomMetaData.get((0x0008, 0x0060), None).value if (0x0008, 0x0060) in dicomMetaData else None
        }
        logger.info("Scan type extracted successfully: %s", dicom_info['scanType'])
        logger.debug("Scan type from file %s: %s", dicomPath, dicom_info['scanType'])
        
        return dicom_info
        
    except Exception as e:
        # Scan type information is not available in the DICOM file
        logger.warning("Scan type not available in DICOM file: %s - Error: %s", dicomPath, str(e))
        print("scan type not available in the dicom file")
        return None

def readDirectory(dicomDirectory):
    """
    Read and process all DICOM files from a specified directory
    
    This function:
    1. Lists all files in the given directory
    2. Validates each file to check if it's a valid DICOM file
    3. Collects all valid DICOM file paths
    4. Extracts scan type information from the first valid DICOM file
    
    Args:
        dicomDirectory (str): Path to the directory containing DICOM files
        
    Returns:
        tuple: (list, str or None) - (list of valid DICOM paths, scan type name)
               Returns (None, None) if directory doesn't exist or other errors occur
    """
    
    logger.info("Starting to read DICOM directory: %s", dicomDirectory)
    
    try:
        # Check if directory exists
        if not os.path.exists(dicomDirectory):
            logger.error("DICOM directory does not exist: %s", dicomDirectory)
            print("dicom directory does not exist")
            return None, None
        
        # Check if path is actually a directory
        if not os.path.isdir(dicomDirectory):
            logger.error("Provided path is not a directory: %s", dicomDirectory)
            print("dicom directory does not exist")
            return None, None
        
        # Initialize list to store valid DICOM file paths
        dicomPathList = []
        
        # Get list of all files in the directory
        logger.debug("Listing files in directory")
        dicomFileList = os.listdir(dicomDirectory)
        logger.info("Found %d files in directory to process", len(dicomFileList))
        
        # Process each file in the directory
        for file_idx, dicomFileName in enumerate(dicomFileList):
            logger.debug("Processing file %d/%d: %s", file_idx + 1, len(dicomFileList), dicomFileName)
            
            # Create full path to the file
            dicomPath = os.path.join(dicomDirectory, dicomFileName)
            
            # Check if the file is a valid DICOM file
            success, dicomPaths = isDicomFile(dicomPath)
            
            if success:
                # File is a valid DICOM file
                dicomPathList.append(dicomPaths)
                logger.debug("Added valid DICOM file to list: %s", dicomFileName)
            else:
                # File is not a valid DICOM file, skip it
                logger.debug("Skipping non-DICOM file: %s", dicomFileName)
                pass
        
        logger.info("DICOM file validation completed. Found %d valid DICOM files", len(dicomPathList))
        
        # Check if any valid DICOM files were found
        if not dicomPathList:
            logger.warning("No valid DICOM files found in directory: %s", dicomDirectory)
            return [], None
        
        # Extract scan type from the first valid DICOM file
        logger.info("Extracting scan type from first DICOM file")
        metaDataList = findMetaData(dicomPathList[0])
        
        if metaDataList:
            logger.info("Successfully extracted scan type: %s", metaDataList)
        else:
            logger.warning("Could not extract scan type from DICOM files")
        
        logger.info("Directory processing completed successfully")
        logger.debug("Final results - DICOM files: %d, Scan type: %s", len(dicomPathList), metaDataList)
        
        return dicomPathList, metaDataList
        
    except Exception as e:
        # Handle any unexpected errors during directory processing
        logger.error("Error occurred while reading DICOM directory: %s", str(e))
        logger.error("Exception type: %s", type(e).__name__)
        logger.error("Directory path: %s", dicomDirectory)
        
        print("dicom directory does not exist")
        return None, None

# Example usage (commented out)
# readDirectory('C:\\Users\\Welcome\\Desktop\\IMG2DICOM')