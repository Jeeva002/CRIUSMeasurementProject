# Import custom modules for OCR, table detection, and content analysis
from OCRProcessor import OCRHandler
from tableDetection import TableDetector
from textAnalyzer import TextAnalyzer
from contentExtractor import ContentExtractor
import heapq
# Import logging setup from external logging configuration file
from logSetup import setup_logging

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
            self.ocr_handler = OCRHandler()
            
            # Initialize table detector for finding rectangular regions
            self.table_detector = TableDetector()
            
            # Initialize text analyzer for scoring measurement content

            self.text_analyzer = TextAnalyzer()
            
            # Initialize content extractor with OCR and text analysis capabilities
   
            self.content_extractor = ContentExtractor(self.ocr_handler, self.text_analyzer)
            
            logger.info("UltrasoundTableDetector initialization completed successfully")
            
        except Exception as e:
            # Log any initialization errors
            logger.error("Error during UltrasoundTableDetector initialization: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            raise

    def detect_measurement_table(self, image):
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

            candidate_regions, enhanced = self.table_detector.detect_rectangular_regions(image)
            logger.debug("Found %d candidate regions", len(candidate_regions) if candidate_regions else 0)
            
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
       

                    measurement_score_single = self.text_analyzer.calculate_measurement_score(roi, self.ocr_handler)
                    measurement_score.append(measurement_score_single)
 
                    
                except Exception as e:
                    # Log errors for individual candidate processing
                    logger.warning("Error processing candidate %d: %s", idx, str(e))
                    measurement_score.append(0.0)  # Default score for failed candidates
                    roi_list.append(None)
            
            # Step 3: Store results in the candidate structure
            logger.debug("Storing measurement scores and ROI data in candidate structure")
            if candidate_regions:
                # Note: This seems to modify the last candidate, might need review
                candidate = candidate_regions[-1]  # This might be a bug in original code
                candidate['measurement_score'] = measurement_score
                candidate['roi'] = roi_list
            
            # Step 4: Find top 10 candidates based on measurement scores
            logger.info("Identifying top 10 candidates based on measurement scores")
            top10Scores = heapq.nlargest(10, range(len(measurement_score)), key=lambda i: measurement_score[i])
            logger.debug("Top 10 score indices: %s", top10Scores)
            
            # Log the scores for debugging
            for i, score_idx in enumerate(top10Scores):
                logger.debug("Rank %d: Index %d, Score %f", i + 1, score_idx, measurement_score[score_idx])
            
            # Step 5: Check if the best candidate meets the minimum threshold
            if top10Scores and measurement_score[top10Scores[0]] >= 4:
                logger.info("Best candidate meets threshold (>= 4). Score: %f", measurement_score[top10Scores[0]])
                
                # Log all top 10 scores for analysis
                logger.debug("All top 10 scores:")
                for i in top10Scores:
                    logger.debug("Score index %d: %f", i, measurement_score[i])
                    print("top10", measurement_score[i])  # Original print statement preserved
                
                logger.info("Measurement table detection completed successfully")
                return candidate_regions, enhanced, top10Scores
            else:
                # Best candidate doesn't meet the threshold
                best_score = measurement_score[top10Scores[0]] if top10Scores else 0
                logger.warning("No candidates meet the minimum threshold of 4. Best score: %f", best_score)
                
                top10Scores = None
                logger.info("Measurement table detection completed - no valid tables found")
                return candidate_regions, enhanced, top10Scores
                
        except Exception as e:
            # Log any errors during the detection process
            logger.error("Error during measurement table detection: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            return None, None, None
    
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
            structured_data = self.content_extractor.extract_table_content(image, bbox)
            

            
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