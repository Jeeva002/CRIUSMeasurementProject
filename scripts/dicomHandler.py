# Import required modules for DICOM processing and image handling
import pydicom
import cv2

# Import custom module for ultrasound region location detection
from scripts.dicomRegionLocation import USRegionLocation

# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

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

def usImageArea(dicom_path, pixel_array):
    """
    Extract the ultrasound image area from the full DICOM image
    
    This function uses the USRegionLocation class to identify the actual
    ultrasound image region within the DICOM file and crops the pixel array
    to focus on the relevant medical imaging area.
    
    Args:
        dicom_path (str): Path to the DICOM file for metadata analysis
        pixel_array (numpy.ndarray): Pixel array from the DICOM file
        
    Returns:
        tuple: (cropped_region, study_type) - Cropped image array and study type
    """
    


    
    try:
        # Initialize ultrasound region location detector
        logger.debug("Initializing USRegionLocation detector")
        us_region = USRegionLocation(dicom_path)
        
        # Get coordinates of the ultrasound region
        logger.info("Getting ultrasound region coordinates")
        minx0, miny0, maxx1, maxy1, studyType = us_region.get_coordinates()
        
        logger.debug("Raw coordinates - minx0: %s, miny0: %s, maxx1: %s, maxy1: %s", 
                   minx0, miny0, maxx1, maxy1)
        logger.debug("Study type identified: %s", studyType)
        
        # Process coordinates based on number of regions detected
        if len(minx0) >= 2:
            logger.info("Multiple regions detected (%d regions), calculating combined bounds", len(minx0))
            
            # Calculate combined bounding box for multiple regions
            minX = min(minx0[0], minx0[1])
            minY = min(miny0[0], miny0[1])
            maxX = max(maxx1[0], maxx1[1])
            maxY = max(maxy1[0], maxy1[1])
            
            logger.debug("Combined bounds - minX: %d, minY: %d, maxX: %d, maxY: %d", 
                       minX, minY, maxX, maxY)
            
        else:
            logger.info("Single region detected, using direct coordinates")
            
            # Use coordinates from single region
            minX = minx0[0]
            minY = miny0[0]
            maxX = maxx1[0]
            maxY = maxy1[0]
            
            logger.debug("Single region bounds - minX: %d, minY: %d, maxX: %d, maxY: %d", 
                       minX, minY, maxX, maxY)
        
        # Crop the image to the ultrasound region

        logger.debug("Cropping region: [%d:%d, %d:%d]", minY, maxY, minX, maxX)
        
        cropedRegion = pixel_array[minY:maxY, minX:maxX]
        
        logger.info("Ultrasound image area extraction completed successfully")

        
        return cropedRegion, studyType
        
    except Exception as e:
        # Handle any errors during region extraction
        logger.error("Error extracting ultrasound image area: %s", str(e))
        logger.error("Exception type: %s", type(e).__name__)
        logger.error("DICOM path: %s", dicom_path)
        
        # Return original image if cropping fails
        logger.warning("Returning original pixel array due to cropping error")
        return pixel_array, None

def display_image(image, window_name='DICOM Image'):
    """
    Display image using OpenCV
    
    This function creates an OpenCV window to display the processed image
    and waits for user input before closing the window.
    
    Args:
        image (numpy.ndarray): Image array to display
        window_name (str): Name of the display window
    """
    
    logger.info("Displaying image in OpenCV window: %s", window_name)
    logger.debug("Image shape: %s", image.shape if hasattr(image, 'shape') else 'Unknown')
    logger.debug("Image data type: %s", image.dtype if hasattr(image, 'dtype') else 'Unknown')
    
    try:
        # Display the image in OpenCV window
        logger.debug("Creating OpenCV window and displaying image")
        cv2.imshow(window_name, image)
        
        logger.info("Image displayed successfully")
        print("Image displayed")
        print("Press any key to exit.")
        
        # Wait for user input and then close windows
        logger.debug("Waiting for user input (key press)")
        cv2.waitKey(0)
        
        logger.debug("Destroying OpenCV windows")
        cv2.destroyAllWindows()
        
        logger.info("Image display completed and windows closed")
        
    except Exception as e:
        # Handle any errors during image display
        logger.error("Error displaying image: %s", str(e))
        logger.error("Exception type: %s", type(e).__name__)
        logger.error("Window name: %s", window_name)
        
        # Try to close windows even if display failed
        try:
            cv2.destroyAllWindows()
            logger.debug("OpenCV windows destroyed after error")
        except:
            logger.error("Failed to destroy OpenCV windows after display error")