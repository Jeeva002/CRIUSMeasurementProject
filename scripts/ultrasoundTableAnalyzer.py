# Import custom modules for OCR, table detection, and content analysis

import traceback
import sys
from scripts.textAnalyzer import TextAnalyzer
from scripts.contentExtractor import ContentExtractor
import heapq
# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

class UltrasoundTableDetector:
    """
    Main class for detecting and extracting measurement tables from ultrasound images
    
    This class orchestrates the complete workflow of:
    1. Detecting rectangular regions that might contain tables
    2. Scoring regions based on measurement content
    3. Extracting structured data from the best candidates
    4. Identifying organ labels from ultrasound images
    """
    
    def __init__(self):
        """
        Initialize the UltrasoundTableDetector with required components
        
        Sets up all the necessary handlers and processors for:
        - OCR processing
        - Table detection
        - Text analysis
        - Content extraction
        """
        
        # Log initialization start
        logger.info("Initializing UltrasoundTableDetector")
        
        try:
            # Initialize OCR handler for text recognition
   
            
            # Initialize table detector for finding rectangular regions

            
            # Initialize text analyzer for scoring measurement content

            self.text_analyzer = TextAnalyzer()
            
            # Initialize content extractor with OCR and text analysis capabilities
   
            self.content_extractor = ContentExtractor(self.text_analyzer)
       
            logger.info("UltrasoundTableDetector initialization completed successfully")
            
        except Exception as e:
            # Log any initialization errors
            logger.error("Error during UltrasoundTableDetector initialization: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            raise

    def detect_measurement_table(self, image,yoloDetector):
        """
        Main function to detect measurement tables in ultrasound images
        
        This method performs the complete detection pipeline:
        1. Detects rectangular regions that could contain tables
        2. Extracts ROI (Region of Interest) from each candidate
        3. Calculates measurement scores for each ROI
        4. Identifies the top 10 candidates based on scores
        5. Returns results if the best candidate meets the threshold
        
        Args:
            image: Input ultrasound image array
            
        Returns:
            tuple: (candidate_regions, enhanced_image, top_scores) or (candidate_regions, enhanced_image, None)
        """
        

        
        try:
        
            candidate_regions= yoloDetector.detect(image)
            
            logger.debug("Found %d candidate regions", len(candidate_regions) if candidate_regions else 0)
            print("candidate region",candidate_regions)
            # Initialize lists to store ROI data and measurement scores
            roi_list = []
            measurement_score = []
            
            # Step 2: Process each candidate region
            logger.info("Processing candidate regions for measurement content")
     
            for idx, candidate in enumerate(candidate_regions):
                
                
                try:
                    # Extract ROI from the candidate region
                    roi = candidate['roi']
                    roi_list.append(roi)
                    
                except Exception as e:
                    # Log errors for individual candidate processing
                    logger.warning("Error processing candidate %d: %s", idx, str(e))
                    measurement_score.append(0.0)  # Default score for failed candidates
                    roi_list.append(None)
      
            return roi_list
        except Exception as e:
            # Log the error message
            logger.error("Error during measurement table detection: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            
 
    def extract_table_content(self, image, bbox):
        """
        Extract and structure the content from detected table region
        
        This method delegates to the content extractor to:
        1. Extract text from the specified bounding box region
        2. Structure the extracted text into a meaningful format
        3. Return the structured data for further processing
        
        Args:
            image: Input ultrasound image array
            bbox: Bounding box coordinates defining the table region
            
        Returns:
            dict: Structured data extracted from the table region
        """
        
        # Log function entry
      
        logger.info("Starting table content extraction")
        logger.debug("Bounding box coordinates: %s", bbox)
        logger.debug("Image shape: %s", image.shape if hasattr(image, 'shape') else type(image))
        
        try:
            # Delegate to content extractor for table processing
            logger.debug("Delegating to content extractor for table processing")
           
            structured_data = self.content_extractor.extract_table_content(image, bbox,True)
            

      
            return structured_data
            
        except Exception as e:
            # Log any errors during content extraction
            logger.error("Error during table content extraction: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            return None
    
    def identifyOrganName(self, image):
        """
        Identify the organ name from the ultrasound image
        
        This method uses the content extractor to:
        1. Analyze the ultrasound image for organ labels
        2. Extract and identify the organ name
        3. Return the identified organ name
        
        Args:
            image: Input ultrasound image array
            
        Returns:
            str: Identified organ name or None if not found
        """
        
        # Log function entry
        logger.info("Starting organ name identification")
        logger.debug("Image shape: %s", image.shape if hasattr(image, 'shape') else type(image))
        
        try:
            # Delegate to content extractor for organ identification
            logger.debug("Delegating to content extractor for organ identification")
            organ_name = self.content_extractor.organLabelIdentification(image)
            
            # Log identification results
            if organ_name:
                logger.info("Organ identification completed successfully: %s", organ_name)
            else:
                logger.warning("No organ name identified from the image")
            
            return organ_name
            
        except Exception as e:
            # Log any errors during organ identification
            logger.error("Error during organ name identification: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            return None