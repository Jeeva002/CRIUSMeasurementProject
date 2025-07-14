# Import required modules for image processing and OCR
import cv2

# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

class ContentExtractor:
    """
    A class responsible for extracting and structuring content from detected table regions
    in medical ultrasound images using OCR (Optical Character Recognition).
    
    This class handles:
    - Table content extraction from specific image regions
    - OCR processing of extracted regions
    - Text analysis and structuring
    - Organ label identification from medical images
    """
    
    def __init__(self, ocr_handler, text_analyzer):
        """
        Initialize the ContentExtractor with OCR handler and text analyzer
        
        Args:
            ocr_handler: Handler for OCR operations
            text_analyzer: Analyzer for structuring extracted text data
        """
        logger.info("Initializing ContentExtractor")

        
        self.ocr_handler = ocr_handler
        self.text_analyzer = text_analyzer
        
        logger.info("ContentExtractor initialized successfully")

    def extract_table_content(self, image, bbox):
        """
        Extract and structure the content from detected table region
        
        This method:
        1. Extracts the region of interest (ROI) from the image using bounding box coordinates
        2. Performs OCR on the extracted region
        3. Processes the OCR results to extract text with positions
        4. Structures the data using the text analyzer
        
        Args:
            image: Input image containing the table
            bbox: Bounding box coordinates (x, y, width, height) of the table region
            
        Returns:
            dict: Structured data extracted from the table, or empty dict if extraction fails
        """
        
        logger.info("Starting table content extraction")
        logger.debug("Bounding box coordinates: %s", bbox)
        
        try:
            # Extract bounding box coordinates
            x, y, w, h = bbox
     
            roi = image[y:y+h, x:(x+w)]
            roi2 = image[y:y+h, x:(x+w)+4]  # Extended ROI for comparison
            

         

            # Perform OCR on the extracted region
            logger.info("Performing OCR on extracted table region")
            result = self.ocr_handler.get_ocr_result(roi)
            
            # Check if OCR returned valid results
            if not result or not result[0]:
                logger.warning("OCR returned no results for table region")
                return {}
            
            logger.info("OCR completed successfully. Processing text elements...")

            # Extract text with positions from OCR results
            text_elements = []
            for line_idx, line in enumerate(result[0]):
                if line:
                    try:
                        # Extract bounding box coordinates, text, and confidence from OCR result
                        bbox_coords = line[0]
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        # Calculate center position of the text element
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
                        
               
                        
                    except Exception as e:
                        logger.error("Error processing OCR line %d: %s", line_idx, str(e))
                        continue
            
            logger.info("Extracted %d text elements from table region", len(text_elements))
            
            # Structure the extracted data using text analyzer
            logger.info("Structuring extracted text data")
            structured_data = self.text_analyzer.structure_table_data(text_elements)
            
            if structured_data:
                logger.info("Table content extraction completed successfully")
            
            else:
                logger.warning("Text analyzer returned empty structured data")
            
            return structured_data
            
        except Exception as e:
            # Log any errors that occur during table content extraction
            logger.error("Error extracting table content: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            print(f"Error extracting table content: {e}")
            return {}

    def organLabelIdentification(self, img):
        """
        Identify organ labels from medical ultrasound images using OCR and keyword matching
        
        This method:
        1. Performs OCR on the entire image
        2. Extracts all text content
        3. Searches for predefined medical organ keywords
        4. Returns list of found organ-related keywords
        
        Args:
            img: Input medical image for organ identification
            
        Returns:
            list: List of found organ keywords, or empty list if none found
        """
        
        logger.info("Starting organ label identification")
        logger.debug("Input image shape: %s", img.shape if hasattr(img, 'shape') else 'Unknown')
        
        try:
            # Perform OCR on the entire image
            logger.debug("Performing OCR on full image for organ identification")
            result = self.ocr_handler.get_ocr_result(img)
            
            # Check if OCR returned valid results
            if not result or not result[0]:
                logger.warning("OCR returned no results for organ identification")
                return []
            
            logger.debug("OCR completed. Processing %d text lines for organ keywords", len(result[0]))
            
            # Extract all text content from OCR results
            all_text = ""
            for line_idx, line in enumerate(result[0]):
                if line:
                    try:
                        text = line[1][0]
                        all_text += text.lower() + " "
                        logger.debug("Line %d text: '%s'", line_idx, text)
                    except Exception as e:
                        logger.error("Error processing OCR line %d for organ identification: %s", line_idx, str(e))
                        continue
            
            logger.debug("Combined text for keyword search: '%s'", all_text.strip())
            
            # Define medical organ keywords to search for
            keywords = ["right kidney", "left kidney", "kidney", "renal", "nephron", "ureter", 
                       "bladder", "rt ovary", "lt ovary", "uterus"]
            
            logger.debug("Searching for organ keywords: %s", keywords)
            
            # Search for organ keywords in the extracted text
            found_keywords = []
            for keyword in keywords:
                if keyword in all_text:
                    found_keywords.append(keyword)
                    logger.debug("Found organ keyword: '%s'", keyword)
            
            logger.info("Organ identification completed. Found %d organ keywords", len(found_keywords))
            logger.info("Identified organs: %s", found_keywords)
            
          
            if found_keywords==None:
                return None
            else:
              return found_keywords
            
        except Exception as e:
            # Log any errors that occur during organ identification
            logger.error("Error during organ label identification: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            return []