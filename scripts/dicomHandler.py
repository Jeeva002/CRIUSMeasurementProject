# Import required modules for DICOM processing and image handling
import pydicom
import cv2
from PIL import Image
import os
import numpy as np
# Import custom module for ultrasound region location detection


# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()
def dicom_to_pngUpdated(dicom_path):
    """
    Convert a DICOM file to PNG format.
    
    Args:
        dicom_path (str): Path to the DICOM file
        output_path (str): Path where PNG will be saved. 
                          If None, saves in same directory with .png extension
    """
    try:
        # Read DICOM file
        dicom = pydicom.dcmread(dicom_path)
        
        # Extract pixel data
        logger.debug("Reading DICOM file with pydicom")
        pixel_array = dicom.pixel_array
        logger.info("DICOM file loaded successfully")
        # Normalize pixel values to 0-255 range
        pixel_array = ((pixel_array - pixel_array.min()) / 
                       (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)
        logger.info("pixel array loaded successfully")
        # Convert to PIL Image
        image = Image.fromarray(pixel_array)
        logger.info("image conversion loaded successfully")
        # Handle grayscale images
        if image.mode == 'L':
            image = image.convert('RGB')
        logger.info("image L loaded successfully")
        cv_image = np.array(image)        # PIL gives RGB array
        cv_image = cv_image[:, :, ::1]        # no need to flip if you keep RGB
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGB2BGR)  # convert to BGR
      
            


        return True ,cv_image
       
    except Exception as e:
        print(f" Error converting {dicom_path}: {str(e)}")
        return False,cv_image

def dicom_to_png(dicom_path):
    """
    Convert a DICOM file to PNG format using OpenCV
    
    This function reads a DICOM file, processes the pixel data based on photometric
    interpretation, and returns the processed pixel array that can be used for
    image processing or saved as PNG.
    
    Args:
        dicom_path (str): Path to the input DICOM file
        output_path (str): Path for the output PNG file (optional, not used in current implementation)
    
    Returns:
        tuple: (success_bool, pixel_array) - Success status and processed pixel array
    """
    
    logger.info("Starting DICOM to PNG conversion: %s", dicom_path)

    
    try:
        # Read the DICOM file
        logger.debug("Reading DICOM file with pydicom")
        dicom_data = pydicom.dcmread(dicom_path)
        
        logger.info("DICOM file loaded successfully")

        
        # Check if photometric interpretation is available
        if hasattr(dicom_data, 'PhotometricInterpretation'):
            original_interpretation = dicom_data.PhotometricInterpretation
            logger.debug("Original photometric interpretation: %s", original_interpretation)
            
            # Handle MONOCHROME1 format (inverted grayscale)
            if dicom_data.PhotometricInterpretation == 'MONOCHROME1':
                logger.debug("Converting photometric interpretation to YBR_FULL")
                
                # Change photometric interpretation
                dicom_data.PhotometricInterpretation = "YBR_FULL"
                pixel_array = dicom_data.pixel_array
                
                logger.debug("Pixel array extracted. Shape: %s, Data type: %s", 
                           pixel_array.shape, pixel_array.dtype)
                
                # Note: Inversion commented out in original code
                # pixel_array = 255 - pixel_array
                logger.debug("MONOCHROME1 processing completed (inversion skipped)")
                
            # Handle RGB format
            elif dicom_data.PhotometricInterpretation == 'RGB':
                logger.info("Processing RGB format DICOM")
                logger.debug("Converting RGB to BGR for OpenCV compatibility")
                
                # Change photometric interpretation
                dicom_data.PhotometricInterpretation = "YBR_FULL"
                bgr = dicom_data.pixel_array
                
                # Convert RGB to BGR for OpenCV (OpenCV uses BGR color order)
                pixel_array = cv2.cvtColor(bgr, cv2.COLOR_RGB2BGR)
                
                logger.debug("RGB to BGR conversion completed. New shape: %s", pixel_array.shape)
                
            else:
                # Handle other photometric interpretations
                logger.info("Processing other photometric interpretation: %s", original_interpretation)
                pixel_array = dicom_data.pixel_array
                logger.debug("Using pixel array as-is for interpretation: %s", original_interpretation)
        
        else:
            # No photometric interpretation available
            logger.warning("No PhotometricInterpretation attribute found in DICOM file")
            pixel_array = dicom_data.pixel_array
            logger.debug("Using raw pixel array without interpretation processing")
        
        logger.info("DICOM to PNG conversion completed successfully")

        return True, pixel_array
        
    except FileNotFoundError:
        # Handle case where DICOM file doesn't exist
        logger.error("DICOM file not found: %s", dicom_path)
        print(f"Error: DICOM file '{dicom_path}' not found")
        return False, None
        
    except Exception as e:
        # Handle any other errors during DICOM processing
        logger.error("Error converting DICOM file: %s", str(e))
        logger.error("Exception type: %s", type(e).__name__)
        logger.error("DICOM file path: %s", dicom_path)
        
        print(f"Error converting DICOM file: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False, None

