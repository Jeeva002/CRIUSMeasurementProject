# Import required modules for DICOM processing and image handling
from scripts.dicomHandler import dicom_to_png, usImageArea, display_image
from scripts.ultrasoundTableAnalyzer import UltrasoundTableDetector
from scripts.dicomFileManager import readDirectory

# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging
import os

# Initialize logger using the external logging setup
logger = setup_logging()

def detect_tables_in_ultrasound(image):
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
        candidates, enhanced, scores = detector.detect_measurement_table(image)
        logger.debug("Table detection completed. Candidates found: %s", len(candidates) if candidates else 0)
        
        # Identify organ name from the image
        logger.info("Identifying organ name from the image")
        organLabel = detector.identifyOrganName(image)
        logger.debug("Organ identified: %s", organLabel)
        
        # Check if any tables were detected
        if scores is not None:
            logger.info("Table(s) detected successfully. Processing best candidate...")
            logger.debug("Number of scored candidates: %s", len(scores))
            logger.debug("Best score index: %s", scores[0] if scores else "None")
            
            # Extract structured data from the best table candidate
            logger.info("Extracting structured data from detected table")
            structuredData = detector.extract_table_content(enhanced, candidates[scores[0]]['bbox'])

            organ_dict = {'organLabel': organLabel}
            structuredData.insert(0, organ_dict)
            logger.debug("Structured data keys: %s", list(structuredData) if structuredData else "None")
            logger.debug("Organ identified: %s", organLabel)
            return structuredData, image, organLabel
        else:
            # No tables found in the image
            logger.warning("No measurement tables detected in the ultrasound image")
            return None, None, None
            
    except Exception as e:
        # Log any errors that occur during table detection
        logger.error("Error occurred during table detection: %s", str(e))
        logger.error("Exception type: %s", type(e).__name__)
        return None, None, None

def processDicom(dicomDirectory=None):
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
    
    try:
        # Set the DICOM directory path (hardcoded for this example)
     #   dicomDirectory = 'C:\\Users\\Welcome\\Documents\\organized_dicom\\PELVIS_US\\E0000037'
        logger.info("Processing DICOM directory: %s", dicomDirectory)
        allMeasurementData = {}
        sliceNumber = 1
        
        # Verify directory exists
        if not os.path.exists(dicomDirectory):
            logger.error("DICOM directory does not exist: %s", dicomDirectory)
            return
        
        # Read all DICOM files from the specified directory
        logger.info("Reading DICOM files from directory")
        dicomPathList, metaDataList = readDirectory(dicomDirectory)
        logger.info("Found %d DICOM files to process", len(dicomPathList))
        logger.debug("metaData: %s", metaDataList)
        
        # Process each DICOM file in the directory
        for idx, dicom in enumerate(dicomPathList):
            logger.info("Processing DICOM file %d/%d: %s", idx + 1, len(dicomPathList), dicom)
            
            try:
                # Convert DICOM file to PNG format
                logger.debug("Converting DICOM to PNG format")
                success, pixelArray = dicom_to_png(dicom)
                
                if not success:
                    logger.error("Failed to convert DICOM to PNG: %s", dicom)
                    continue
                
                logger.debug("DICOM conversion successful. Pixel array shape: %s", 
                        pixelArray.shape if hasattr(pixelArray, 'shape') else type(pixelArray))
                
                # Crop the ultrasound image to focus on the relevant area
                logger.debug("Cropping ultrasound image area")
                cropped_image, studyType = usImageArea(dicom, pixelArray)
                logger.debug("Image cropping completed. Study type: %s", studyType)
                
                # Detect and extract measurement tables from the cropped image
                logger.info("Analyzing cropped image for measurement tables")
                structured_data, result_img, organName = detect_tables_in_ultrasound(cropped_image)
                
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
                    allMeasurementData[slice_key] = []
                
                # Append the structured data to the slice
                allMeasurementData[slice_key].append(structured_data)
                sliceNumber = sliceNumber + 1
                
                # # Display the processed image
                # logger.debug("Displaying cropped image")
                # display_image(cropped_image)
                
       
            except Exception as e:
                # Log errors for individual file processing
                logger.error("Error processing DICOM file %s: %s", dicom, str(e))
                logger.error("Exception type: %s", type(e).__name__)
                continue
            
        logger.info("=== DICOM Processing Session Completed === %s %s",allMeasurementData,metaDataList)
        return allMeasurementData,metaDataList
    except Exception as e:
        # Log any major errors in the main function
        logger.critical("Critical error in main function: %s", str(e))
        logger.critical("Exception type: %s", type(e).__name__)
        raise

# if __name__ == "__main__":
#     # Entry point of the program
#     logger.info("Program started from command line")
#     try:
#         main()
#     except Exception as e:
#         logger.critical("Program terminated due to unhandled exception: %s", str(e))
#         raise
#     finally:
#         logger.info("Program execution completed")