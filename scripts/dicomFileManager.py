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

def extract_dicom_value(dicom_data, tag):
    """
    Extract value from DICOM data element, handling both simple values and complex objects
    
    Args:
        dicom_data: DICOM dataset object
        tag: DICOM tag tuple (e.g., (0x0010, 0x0010))
        
    Returns:
        str or None: Extracted value as string, None if not found
    """
    try:
        if tag in dicom_data:
            element = dicom_data[tag]
            
            # Use pydicom's built-in string representation
            # This automatically handles PersonName objects and byte strings
            value = str(element.value) if element.value is not None else None
            
            return value
        return None
    except Exception as e:
        logger.warning("Error extracting value for tag %s: %s", tag, str(e))
        return None

def clean_dicom_string(value):
    """
    Clean DICOM string values by removing control characters and extra whitespace
    
    Args:
        value: Raw DICOM string value (can be bytes, str, or other types)
        
    Returns:
        str: Cleaned string value
    """
    if value is None:
        return None
    
    # Handle byte strings by decoding them first
    if isinstance(value, bytes):
        try:
            # Try UTF-8 decoding first
            value_str = value.decode('utf-8').strip()
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails
            try:
                value_str = value.decode('latin-1').strip()
            except UnicodeDecodeError:
                # If both fail, convert to string representation and remove b' prefix
                value_str = str(value)
                if value_str.startswith("b'") and value_str.endswith("'"):
                    value_str = value_str[2:-1]  # Remove b' and trailing '
    else:
        # Convert to string if not already
        value_str = str(value)
        # Handle string representations of bytes (like "b'text'")
        if value_str.startswith("b'") and value_str.endswith("'"):
            value_str = value_str[2:-1]  # Remove b' and trailing '
    
    # Remove control characters like ^ and clean up
    cleaned = value_str.replace('^', ' ').strip()
    
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    
    return cleaned if cleaned else None

def findMetaData(dicomPath):
    """
    Extract comprehensive metadata from a DICOM file
    
    This function reads the DICOM file and extracts various metadata fields,
    properly handling complex data types and formatting.
    
    Args:
        dicomPath (str): Path to the DICOM file
        
    Returns:
        dict or None: Dictionary containing extracted metadata, None if extraction fails
    """
    
    logger.debug("Extracting metadata from DICOM file: %s", dicomPath)
    
    try:
        # Read DICOM metadata
        logger.debug("Reading DICOM metadata for information extraction")
        dicomMetaData = pydicom.dcmread(dicomPath)
        
        # Extract all relevant DICOM tags with proper handling
        dicom_info = {
            "PatientName": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0010, 0x0010))),
            "PatientID": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0010, 0x0020))),
            "PatientAge": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0010, 0x0030))),
            "PatientGender": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0010, 0x0040))),
            "HospitalName": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0008, 0x0080))),
            "PhysicianName": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0008, 0x0090))),
            "scanType": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0008, 0x1030))),
            "scanDate": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0008, 0x0020))),
            "scanTime": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0008, 0x0030))),
            "scanModality": clean_dicom_string(extract_dicom_value(dicomMetaData, (0x0008, 0x0060)))
        }
        
        logger.info("Metadata extracted successfully from: %s", dicomPath)
        logger.debug("Extracted metadata: %s", dicom_info)
        
        return dicom_info
        
    except Exception as e:
        # Metadata extraction failed
        logger.warning("Metadata extraction failed for DICOM file: %s - Error: %s", dicomPath, str(e))
        print("Metadata not available in the dicom file")
        return None

def readDirectory(dicomDirectory):
    """
    Read and process all DICOM files from a specified directory
    
    This function:
    1. Lists all files in the given directory
    2. Validates each file to check if it's a valid DICOM file
    3. Collects all valid DICOM file paths
    4. Extracts metadata from the first valid DICOM file
    
    Args:
        dicomDirectory (str): Path to the directory containing DICOM files
        
    Returns:
        tuple: (list, dict or None) - (list of valid DICOM paths, metadata dict)
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
        
        # Extract metadata from the first valid DICOM file
        logger.info("Extracting metadata from first DICOM file")
        metaDataList = findMetaData(dicomPathList[0])
        
        if metaDataList:
            logger.info("Successfully extracted metadata")
        else:
            logger.warning("Could not extract metadata from DICOM files")
        
        logger.info("Directory processing completed successfully")
        logger.debug("Final results - DICOM files: %d, Metadata available: %s", len(dicomPathList), bool(metaDataList))
        
        return dicomPathList, metaDataList
        
    except Exception as e:
        # Handle any unexpected errors during directory processing
        logger.error("Error occurred while reading DICOM directory: %s", str(e))
        logger.error("Exception type: %s", type(e).__name__)
        logger.error("Directory path: %s", dicomDirectory)
        
        print("dicom directory does not exist")
        return None, None

