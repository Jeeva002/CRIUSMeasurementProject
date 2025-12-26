# Import required modules for OCR processing and regular expressions
from paddleocr import PaddleOCR
import logging
import cv2
import numpy as np
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


    def preProcess(self,roi):
            h, w = roi.shape[:2]

            upscale_2x = cv2.resize(roi, (w*3, h*3), interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(upscale_2x, cv2.COLOR_BGR2GRAY)

            # 2. Convert Gray -> BGR
            

            # 3. Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=5.0, tileGridSize=(8, 8))
            clahe_img = clahe.apply(gray)
            gray_to_bgr = cv2.cvtColor(clahe_img, cv2.COLOR_GRAY2BGR)
            return gray_to_bgr
    def preProcessLabel(self,roi):
        img_float = roi.astype(np.float32) / 255.0
        
        mean = np.mean(img_float)
        
        # dynamic gamma: darker → higher gamma, brighter → lower gamma
        gamma = 1.0 + (0.5 - mean) * 2.0     # output gamma range: 0→2
        
        gamma = np.clip(gamma, 0.3, 2.5)      # safe limits
        
        corrected = np.power(img_float, gamma)
        
        return (corrected * 255).astype("uint8")
    def get_ocr_result(self, roi,preProcess=False):
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
            if preProcess==True:
       
                roi=self.preProcess(roi)
                result = self.ocr.predict(roi)
            else:
                roi=self.preProcessLabel(roi)
                result = self.ocr.predict(roi)
     
                import matplotlib.pyplot as plt


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
        
OCRHandlerOBJ=OCRHandler()