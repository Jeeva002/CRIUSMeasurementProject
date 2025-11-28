# Import required modules for OCR processing and regular expressions
from paddleocr import PaddleOCR
import logging
import cv2
# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

class OCRHandler:
    """
    OCR Handler class for text extraction from images using PaddleOCR 3.2
    
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
        logging.getLogger("ppocr").disabled = True
        try:
            # Initialize PaddleOCR with specific parameters for ultrasound image processing
            logger.debug("Configuring PaddleOCR parameters:")
            logger.debug("- use_angle_cls: True (enables angle classification)")
            logger.debug("- lang: 'en' (English language)")
            
            self.ocr = PaddleOCR(
                use_angle_cls=True,      # Enable angle classification for rotated text
                lang='en'                # Set language to English
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
        Extract text with position information using PaddleOCR 3.2
        
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
            # Perform OCR on the region of interest using predict() method (PaddleOCR 3.2)
            result = self.ocr.predict(roi)
       
            # Check if OCR returned valid results
            if result is None or len(result) == 0:
                logger.info("No text detected in the image")
                return []
            
            # Extract text elements from PaddleOCR 3.2 result structure
            text_elements = []
            
            # In PaddleOCR 3.2, result is a list with one element containing a dictionary
            if isinstance(result, list) and len(result) > 0:
                result_dict = result[0]
    
                # Extract rec_texts, rec_scores, and rec_boxes
                texts = result_dict.get('rec_texts', [])
                scores = result_dict.get('rec_scores', [])
                boxes = result_dict.get('rec_boxes', [])
       
                logger.info("Total text elements extracted: %d", len(texts))
                
                # Process each detected text element
                for idx, (text, confidence, box) in enumerate(zip(texts, scores, boxes)):
                    logger.debug("Processing text line %d/%d", idx + 1, len(texts))
                    logger.debug("Text line %d: '%s' (confidence: %.3f)", idx + 1, text, confidence)
                    
                    # Calculate center position of the text bounding box
                    # box is a numpy array with shape [N, 2] containing polygon points
                    if box.ndim == 2 and box.shape[1] == 2:
                        center_x = float(box[:, 0].mean())
                        center_y = float(box[:, 1].mean())
                    else:
                        # Fallback: try to reshape if needed
                        box_reshaped = box.reshape(-1, 2)
                        center_x = float(box_reshaped[:, 0].mean())
                        center_y = float(box_reshaped[:, 1].mean())
                    
                    # Create structured text element
                    text_element = {
                        'text': text,
                        'x': center_x,
                        'y': center_y,
                        'confidence': confidence
                    }
                    
                    text_elements.append(text_element)
                    logger.debug("Text element added to results")
            
            logger.info("Text extraction completed successfully")
            if text_elements:
                logger.debug("Average confidence: %.3f", 
                           sum(elem['confidence'] for elem in text_elements) / len(text_elements))
            
            return text_elements
            
        except Exception as e:
            # Log errors during text extraction
            logger.error("Error occurred during text extraction with positions: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("ROI type when error occurred: %s", type(roi))
            return []
    def preProcess(self,roi):
            h, w = roi.shape[:2]

            upscale_2x = cv2.resize(roi, (w*2, h*2), interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(upscale_2x, cv2.COLOR_BGR2GRAY)

            # 2. Convert Gray -> BGR
            

            # 3. Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            clahe_img = clahe.apply(gray)
            gray_to_bgr = cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR)
            return gray_to_bgr
    def get_ocr_result(self, roi):
        """
        Get raw OCR result from PaddleOCR 3.2
        
        This method returns the unprocessed OCR results directly from PaddleOCR,
        useful for custom processing or debugging purposes.
        
        Args:
            roi: Region of interest image array/object to process
            
        Returns:
            OCR result object: Raw result from PaddleOCR 3.2 containing:
                - rec_texts: List of recognized texts
                - rec_scores: List of confidence scores
                - rec_boxes: List of bounding box coordinates
                
        Returns None if OCR fails or error occurs.
        """
        
        try:
            # Perform OCR using predict() method (PaddleOCR 3.2)
           # roi=self.preProcess(roi)
            result = self.ocr.predict(roi)
        
            # Log result summary
            if result and len(result) > 0:
                result_dict = result[0]
                texts = result_dict.get('rec_texts', [])
                scores = result_dict.get('rec_scores', [])
               
                logger.info("Raw OCR result obtained: %d text elements detected", len(texts))
                
                # Log each detected text line for debugging
                for idx, (text, confidence) in enumerate(zip(texts, scores)):
                    logger.debug("Line %d: '%s' (conf: %.3f)", idx + 1, text, confidence)
            else:
                logger.info("No text detected in raw OCR result")
            
            return result
            
        except Exception as e:
            # Log errors during raw OCR processing
            logger.error("Error occurred during raw OCR processing: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("ROI type when error occurred: %s", type(roi))
            return None