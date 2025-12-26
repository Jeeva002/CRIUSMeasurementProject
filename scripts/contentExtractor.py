# Import required modules for image processing and OCR
from scripts.OCRProcessor import OCRHandlerOBJ

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
    
    def __init__(self, text_analyzer):
        """
        Initialize the ContentExtractor with OCR handler and text analyzer
        
        Args:
            ocr_handler: Handler for OCR operations
            text_analyzer: Analyzer for structuring extracted text data
        """
        logger.info("Initializing ContentExtractor")


        self.text_analyzer = text_analyzer
        
        logger.info("ContentExtractor initialized successfully")

    def extract_table_content(self, image, bbox,flag):
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
            result = OCRHandlerOBJ.get_ocr_result(roi,flag)

            # Check if OCR returned valid results (PaddleOCR 3.2 structure)
            if not result or len(result) == 0:
                logger.warning("OCR returned no results for table region")
                return {}
            
            logger.info("OCR completed successfully. Processing text elements...")
            
            
            # Extract text elements from PaddleOCR 3.2 result structure
            text_elements = []
            
            # In PaddleOCR 3.2, result is a list with one element containing a dictionary
            if isinstance(result, list) and len(result) > 0:
                result_dict = result[0]
                
                # Extract rec_texts, rec_scores, and rec_boxes
                texts = result_dict.get('rec_texts', [])
                scores = result_dict.get('rec_scores', [])
                boxes = result_dict.get('rec_boxes', [])
                
                logger.info("Processing %d text elements from OCR result", len(texts))
                
                # Process each detected text element
                for line_idx, (text, confidence, box) in enumerate(zip(texts, scores, boxes)):
                    try:
                        # Calculate center position of the text bounding box
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
                        
                        logger.debug("Processed text element %d: '%s' (conf: %.3f)", 
                                   line_idx, text, confidence)
                        
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
     
            result = OCRHandlerOBJ.get_ocr_result(img)
            
            # Check if OCR returned valid results (PaddleOCR 3.2 structure)
            if not result or len(result) == 0:
                logger.warning("OCR returned no results for organ identification")
                return []
            
            # Extract all text content from OCR results
            all_text = ""
            
            # In PaddleOCR 3.2, result is a list with one element containing a dictionary
            if isinstance(result, list) and len(result) > 0:
                result_dict = result[0]
                
                # Extract rec_texts
                texts = result_dict.get('rec_texts', [])
                
                logger.debug("OCR completed. Processing %d text lines for organ keywords", len(texts))
                
                # Combine all text for keyword search
                for line_idx, text in enumerate(texts):
                    try:
                        all_text += text.lower() + " "
                        logger.debug("Line %d text: '%s'", line_idx, text)
                    except Exception as e:
                        logger.error("Error processing OCR line %d for organ identification: %s", 
                                   line_idx, str(e))
                        continue
            
            logger.debug("Combined text for keyword search: '%s'", all_text.strip())
            
            # Define medical organ keywords to search for
            keywords = ["right kidney", "rt kidney", "lt kidney", "LT KIDNEY","left kidney", "kidney", 
                       "renal", "nephron", "ureter", "bladder", "rt ovary","RT OVARY" ,"lt ovary", 
                       "uterus", "subscap ten", "breast", "rt breast", "lt breast", 
                       "rt ax", "lt ax", "transplant kidney"]

            # Sort keywords by length in descending order
            keywords_sorted = sorted(keywords, key=len, reverse=True)
            logger.debug("Searching for organ keywords: %s", keywords_sorted)

            found_keywords = []
            remaining_text = all_text.lower()  # Convert to lowercase for case-insensitive matching

            for keyword in keywords_sorted:
                if keyword.lower() in remaining_text:
                    found_keywords.append(keyword)
                    logger.debug("Found organ keyword: '%s'", keyword)
                    # Remove the found keyword from remaining text to avoid substring matches
                    remaining_text = remaining_text.replace(keyword.lower(), "", 1)

            logger.info("Organ identification completed. Found %d organ keywords", len(found_keywords))
            logger.info("Identified organs: %s", found_keywords)
          
            if not found_keywords:
                return []
            else:
                return found_keywords
            
        except Exception as e:
            # Log any errors that occur during organ identification
            logger.error("Error during organ label identification: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            return []
        
