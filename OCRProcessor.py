# Import required modules for OCR processing and regular expressions
from paddleocr import PaddleOCR
import re

# Import logging setup from external logging configuration file
from logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

class OCRHandler:
    """
    OCR Handler class for text extraction from images using PaddleOCR
    
    This class provides functionality to:
    1. Initialize PaddleOCR with optimized parameters
    2. Extract text with position information from regions of interest
    3. Get raw OCR results for further processing
    """
    
    def __init__(self):
        """
        Initialize OCRHandler with PaddleOCR configuration
        
        Sets up PaddleOCR with optimized parameters for medical ultrasound images:
        - Angle classification enabled for rotated text
        - English language support
        - Adjusted detection thresholds for better text recognition
        """
        
        # Log initialization start
        logger.info("Initializing OCRHandler")
        logger.debug("Setting up PaddleOCR with optimized parameters")
        
        try:
            # Initialize PaddleOCR with specific parameters for ultrasound image processing
            logger.debug("Configuring PaddleOCR parameters:")
            logger.debug("- use_angle_cls: True (enables angle classification)")
            logger.debug("- lang: 'en' (English language)")
            logger.debug("- det_db_thresh: 0.3 (lower threshold for text detection)")
            logger.debug("- det_db_box_thresh: 0.5 (lower box threshold)")
            logger.debug("- det_db_unclip_ratio: 2.0 (text region expansion ratio)")
            
            self.ocr = PaddleOCR(
                use_angle_cls=True,      # Enable angle classification for rotated text
                lang='en',               # Set language to English
                det_db_thresh=0.3,       # Lower threshold for text detection sensitivity
                det_db_box_thresh=0.5,   # Lower box threshold for better detection
                det_db_unclip_ratio=2.0  # Text region expansion ratio
            )
            
            logger.info("OCRHandler initialized successfully")
            logger.debug("PaddleOCR instance created with optimized parameters")
            
        except Exception as e:
            # Log initialization errors
            logger.error("Failed to initialize OCRHandler: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            raise

    def extract_text_with_positions(self, roi):
        """
        Extract text with position information using PaddleOCR
        
        This method processes a region of interest (ROI) and extracts all text
        elements along with their spatial coordinates and confidence scores.
        
        Args:
            roi: Region of interest image array/object to process
            
        Returns:
            list: List of dictionaries containing:
                - text: Extracted text string
                - x: Center X coordinate of text bounding box
                - y: Center Y coordinate of text bounding box
                - confidence: OCR confidence score (0.0 to 1.0)
                
        Returns empty list if no text is found or error occurs.
        """
        

        
        try:
            # Perform OCR on the region of interest

            result = self.ocr.ocr(roi, cls=True)

            
            # Check if OCR returned valid results
            if not result or not result[0]:
                return []
            

            
            # Extract text with positions from OCR results
            text_elements = []
            for line_idx, line in enumerate(result[0]):
                if line:
                    logger.debug("Processing text line %d/%d", line_idx + 1, len(result[0]))
                    
                    # Extract bounding box coordinates, text, and confidence
                    bbox_coords = line[0]  # Bounding box coordinates
                    text = line[1][0]      # Extracted text string
                    confidence = line[1][1]  # OCR confidence score
                    
                    logger.debug("Text line %d: '%s' (confidence: %.3f)", 
                               line_idx + 1, text, confidence)
                    
                    # Calculate center position of the text bounding box
                    center_x = (bbox_coords[0][0] + bbox_coords[2][0]) / 2
                    center_y = (bbox_coords[0][1] + bbox_coords[2][1]) / 2
                    

                    
                    # Create structured text element
                    text_element = {
                        'text': text,
                        'x': center_x,
                        'y': center_y,
                        'confidence': confidence
                    }
                    
                    text_elements.append(text_element)
                    logger.debug("Text element added to results")
                else:
                    logger.debug("Skipping empty text line %d", line_idx + 1)
            
            logger.info("Text extraction completed successfully")
            logger.info("Total text elements extracted: %d", len(text_elements))
            logger.debug("Average confidence: %.3f", 
                       sum(elem['confidence'] for elem in text_elements) / len(text_elements) 
                       if text_elements else 0)
            
            return text_elements
            
        except Exception as e:
            # Log errors during text extraction
            logger.error("Error occurred during text extraction with positions: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("ROI type when error occurred: %s", type(roi))
            return []

    def get_ocr_result(self, roi):
        """
        Get raw OCR result from PaddleOCR
        
        This method returns the unprocessed OCR results directly from PaddleOCR,
        useful for custom processing or debugging purposes.
        
        Args:
            roi: Region of interest image array/object to process
            
        Returns:
            OCR result object: Raw result from PaddleOCR containing:
                - Bounding box coordinates
                - Text content
                - Confidence scores
                - Additional metadata
                
        Returns None if OCR fails or error occurs.
        """
        
        # Log function entry

        
        try:

            result = self.ocr.ocr(roi, cls=True)

            
            # Log result summary
            if result and result[0]:


                
                # Log each detected text line for debugging
                for idx, line in enumerate(result[0]):
                    if line:
                        text = line[1][0]
                        confidence = line[1][1]
                        logger.debug("Line %d: '%s' (conf: %.3f)", idx + 1, text, confidence)
            else:
                   pass
            
            return result
            
        except Exception as e:
            # Log errors during raw OCR processing
            logger.error("Error occurred during raw OCR processing: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("ROI type when error occurred: %s", type(roi))
            return None