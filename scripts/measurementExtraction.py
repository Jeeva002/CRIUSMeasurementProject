# Import required modules for DICOM processing and image handling
from scripts.dicomHandler import  dicom_to_pngUpdated
from scripts.ultrasoundTableAnalyzer import UltrasoundTableDetector
from scripts.dicomFileManager import readDirectory
import pkg_resources
import numpy as np
import cv2
import traceback
import sys
libraries = [
    "paddleocr",
    "paddlepaddle",
    "opencv-python",
    "numpy",
    "scikit-image",
    "pydicom",
    "fastapi",
    "uvicorn",
    "python-multipart"
]

for lib in libraries:
    try:
        version = pkg_resources.get_distribution(lib).version
        print(f"{lib}: {version}")
    except pkg_resources.DistributionNotFound:
        print(f"{lib}: NOT INSTALLED")
# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging
import os

# Initialize logger using the external logging setup
logger = setup_logging()

def detect_tables_in_ultrasound(image,yoloDetector,organLabelFlag):
    """
    Analyzes ultrasound images to detect and extract measurement tables
    
    This function performs the following operations:
    1. Initializes the UltrasoundTableDetector
    2. Detects measurement tables in the image
    3. Identifies organ labels from the image
    4. Extracts structured data from detected tables
    
    Args:
        image: Input ultrasound image array/object
        
    Returns:
        tuple: (structured_data, image, organ_label) or (None, None, None) if no table found
    """
    
    # Log function entry
    logger.info("Starting table detection in ultrasound image")

    
    try:
        
        detector = UltrasoundTableDetector()
        
        # Detect measurement tables in the image
        logger.info("Detecting measurement tables in the image")
        
        roiList = detector.detect_measurement_table(image,yoloDetector)
       
        
        # Identify organ name from the image
        print("identify organ")
        logger.info("Identifying organ name from the image")
        if organLabelFlag:
           organLabel = detector.identifyOrganName(image)
        else:
           organLabel=[]
        print("identified",organLabel)
        if not organLabel:
            print("unknown")
            organLabel = "unknown"
        else:
              organLabel=', '.join(organLabel)
              print("else")
        logger.debug("Organ identified: %s", organLabel)
        print("identified",organLabel)
        # Check if any tables were detected
        print("roi list",roiList)
        if roiList and len(roiList) > 0:
            logger.info("Table(s) detected successfully. Processing all candidates...")

            final_structured_data = {
                "organLabel": organLabel,
                "value": []
            }

            for idx, roi in enumerate(roiList):
                logger.info("Processing ROI %d with bbox %s", idx, roi)

                structuredData = detector.extract_table_content(image, roi)

                if structuredData and "value" in structuredData:
                    # Append ROI-wise values as a separate list
                    final_structured_data["value"].append(structuredData["value"])

                    logger.debug(
                        "Added %d values for ROI %d",
                        len(structuredData["value"]),
                        idx
                    )
                else:
                    logger.warning("No structured data extracted for ROI %d", idx)

            # If at least one ROI produced data
            if final_structured_data["value"]:
                return final_structured_data, image, organLabel
            else:
                return None, image, organLabel

        else:
            logger.warning("No measurement tables detected in the ultrasound image")
            return None, None, None

    except Exception as e:
        # Log the error message
        logger.error("Error occurred during table detection: %s", str(e))
        logger.error("Exception type: %s", type(e).__name__)

        # Get traceback info
        tb = sys.exc_info()[2]
        lineno = tb.tb_lineno
        logger.error("Occurred at line: %d", lineno)
        logger.error("Full traceback:\n%s", traceback.format_exc())

        return None, None, None

def processDicom(dicomDirectory,yoloDetector,metaDataFlag,MeasurementFlag,organLabelFlag):
    """
    Main function to orchestrate DICOM ultrasound processing workflow
    This function handles the complete pipeline:
    1. Sets up the DICOM directory path
    2. Reads all DICOM files from the directory
    3. Processes each DICOM file:
       - Converts DICOM to PNG format
       - Crops the ultrasound image area
       - Detects and extracts measurement tables
       - Displays results
    
    Args:
        dicomDirectory (str, optional): Path to directory containing DICOM files
    """
    
    # Log the start of main processing
    logger.info("=== Starting DICOM Ultrasound Processing Session ===")
    metaDataList={}
    try:
        # Set the DICOM directory path (hardcoded for this example)
     #   dicomDirectory = 'C:\\Users\\Welcome\\Documents\\organized_dicom\\PELVIS_US\\E0000037'
        logger.info("Processing DICOM directory: %s", dicomDirectory)
        print("Processing DICOM directory: %s", dicomDirectory)
        allMeasurementData = {}
        sliceNumber = 1
        
        # Verify directory exists
        if not os.path.exists(dicomDirectory):
            print("DICOM directory does not exist: %s", dicomDirectory)
            logger.error("DICOM directory does not exist: %s", dicomDirectory)
            return
        
        # Read all DICOM files from the specified directory
        logger.info("Reading DICOM files from directory")

        if metaDataFlag and MeasurementFlag==False:
            dicomPathList, metaDataList = readDirectory(dicomDirectory)
            logger.info("Found %d DICOM files to process", len(dicomPathList))
            print("Found %d DICOM files to process", len(dicomPathList))
            logger.debug("metaData: %s", metaDataList)
          
            return metaDataList
        elif metaDataFlag or MeasurementFlag:
            dicomPathList, metaDataList = readDirectory(dicomDirectory)
            logger.info("Found %d DICOM files to process", len(dicomPathList))
            print("Found %d DICOM files to process", len(dicomPathList))
            logger.debug("metaData: %s", metaDataList)
            metaDataList={'patientInformation':metaDataList}
        if MeasurementFlag:
     # Process each DICOM file in the directory
         for idx, dicom in enumerate(dicomPathList):
            logger.info("Processing DICOM file %d/%d: %s", idx + 1, len(dicomPathList), dicom)
            
            try:
                # Convert DICOM file to PNG format
                logger.debug("Converting DICOM to PNG format")
                success, pixelArray = dicom_to_pngUpdated(dicom)
            

                if not success:
                    logger.error("Failed to convert DICOM to PNG: %s", dicom)
                    continue

                logger.debug("DICOM conversion successful. Pixel array shape: %s", 
                        pixelArray.shape if hasattr(pixelArray, 'shape') else type(pixelArray))
                
                # Crop the ultrasound image to focus on the relevant area
                logger.debug("Cropping ultrasound image area")
                # cropped_image, studyType = usImageArea(dicom, pixelArray)
                cropped_image=pixelArray
                #logger.debug("Image cropping completed. Study type: %s", studyType)
                
                # Detect and extract measurement tables from the cropped image
                logger.info("Analyzing cropped image for measurement tables")

                # If numpy array and single-channel, convert to 3-channel BGR
                if isinstance(cropped_image, np.ndarray):
                    if len(cropped_image.shape) == 2:  # grayscale
                        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_GRAY2BGR)
                    elif cropped_image.shape[-1] == 1:  # H, W, 1
                        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_GRAY2BGR)
                if MeasurementFlag:
                  structured_data, result_img, organName = detect_tables_in_ultrasound(cropped_image,yoloDetector,organLabelFlag)
                elif metaDataFlag:
                    return 
                # Log the final results
                if structured_data:
                    logger.info("Table extraction successful for file: %s", dicom)
                    logger.info("Organ identified: %s", organName)
                    logger.debug("Structured data extracted: %s", structured_data)
                else:
                    logger.warning("No structured data extracted from file: %s", dicom)
                
                # Initialize the slice key if it doesn't exist
                slice_key = f'slice{sliceNumber}'
                if slice_key not in allMeasurementData:
                  allMeasurementData[slice_key] = structured_data
                else:
                # If you need to handle multiple entries per slice, you'd need different logic
                  pass
                
                # Append the structured data to the slice
                
                sliceNumber = sliceNumber + 1
                
        
       
            except Exception as e:
                # Log errors for individual file processing
                logger.error("Error processing DICOM file %s: %s", dicom, str(e))
                logger.error("Exception type: %s", type(e).__name__)
                continue
            
         logger.info("=== DICOM Processing Session Completed === %s %s",allMeasurementData,metaDataList)
         return metaDataList,allMeasurementData
    except Exception as e:
        # Log any major errors in the main function
        logger.critical("Critical error in main function: %s", str(e))
        logger.critical("Exception type: %s", type(e).__name__)
        raise

