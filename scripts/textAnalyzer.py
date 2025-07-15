# Import required modules for regular expressions
import re

# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

class TextAnalyzer:
    """
    Text Analysis class for processing OCR results from ultrasound measurement tables
    
    This class provides functionality to:
    1. Calculate measurement scores to identify table regions
    2. Split measurement text into structured components
    3. Structure text elements into key-value pairs
    4. Process and organize measurement data from OCR results
    """
    
    def __init__(self):
        """
        Initialize TextAnalyzer
        
        Sets up the text analysis system with default parameters and patterns
        for medical measurement detection and processing.
        """
        
        # Log initialization
        logger.info("Initializing TextAnalyzer")
        logger.debug("TextAnalyzer instance created successfully")
        
        # Log configuration parameters
        logger.debug("Text analysis configuration:")
        logger.debug("- Same line threshold: 15 pixels")
        logger.debug("- Measurement pattern types: 2 (unit patterns, key patterns)")
        logger.debug("- Bonus scoring: cm (2x), vol (2x)")
        logger.debug("- Split measurement patterns: 2 (detailed, simple)")
        
        logger.info("TextAnalyzer initialization completed")

    def calculate_measurement_score(self, roi, ocr_handler):
        """
        Calculate how likely this region contains measurement data
        
        This method analyzes OCR results to score regions based on the presence
        of measurement-related text patterns, units, and medical terminology.
        Higher scores indicate higher likelihood of containing measurement tables.
        
        Args:
            roi: Region of interest image array
            ocr_handler: OCR handler instance for text extraction
            
        Returns:
            int: Measurement score (0 = no measurement indicators, higher = more likely)
        """
        
        # Log function entry

        try:
            # Get OCR results from the region of interest
            result = ocr_handler.get_ocr_result(roi)            
            # Check if OCR returned valid results
            if not result or not result[0]:
     
                return 0
            
            logger.info("OCR results found, processing text for measurement scoring")
            logger.debug("Number of text lines detected: %d", len(result[0]))
            
            # Extract all text from OCR results
            all_text = ""
            text_line_count = 0
            
            for line_idx, line in enumerate(result[0]):
                if line:
                    text = line[1][0]
                    confidence = line[1][1]
           
                    all_text += text.lower() + " "
                    text_line_count += 1
                else:
                    pass
            
            logger.debug("Text extraction completed - Lines processed: %d", text_line_count)
            logger.debug("Combined text: '%s'", all_text.strip())
            
            # Define measurement patterns for scoring
            logger.debug("Defining measurement patterns for scoring")
            measurement_patterns = [
                r'\d*\.?\d+\s*(?:mm|cm(?:\^?3)?|ml)',  # Numbers with units (mm, cm, cm^3, ml)
                r'\b(?:cm|vol|d1|d2|d|l|l1|l2)\b',     # Key measurement terms
            ]
            
            logger.debug("Measurement patterns defined:")
            for i, pattern in enumerate(measurement_patterns):
                logger.debug("Pattern %d: %s", i + 1, pattern)
            
            # Calculate base score from pattern matching
            score = 0
            total_matches = 0
            
            logger.info("Analyzing text for measurement patterns")
            for pattern_idx, pattern in enumerate(measurement_patterns):
                matches = re.findall(pattern, all_text)
                pattern_matches = len(matches)
                score += pattern_matches
                total_matches += pattern_matches
                
                logger.debug("Pattern %d matches: %d", pattern_idx + 1, pattern_matches)
                if matches:
                    logger.debug("Pattern %d found matches: %s", pattern_idx + 1, matches)
            
            logger.debug("Base score from pattern matching: %d", score)
            
            # Apply bonus scoring for specific terms

            
            # Bonus for 'cm' occurrences
            cm_patterns = all_text.count('cm')
            cm_bonus = cm_patterns * 2
            score += cm_bonus
            logger.debug("'cm' occurrences: %d, bonus added: %d", cm_patterns, cm_bonus)
            
            # Bonus for 'vol' occurrences
            vol_patterns = all_text.count('vol')
            vol_bonus = vol_patterns * 2
            score += vol_bonus
            logger.debug("'vol' occurrences: %d, bonus added: %d", vol_patterns, vol_bonus)
            
            # Calculate final score
            final_score = score
            logger.info("Final measurement score: %d", final_score)
            

            return final_score
            
        except Exception as e:
            # Log errors during measurement score calculation
            logger.error("Error occurred during measurement score calculation: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("ROI type when error occurred: %s", type(roi))
            return 0

    def split_measurement(self, text):
        """
        Split measurement text into structured components
        
        This method attempts to parse measurement text using multiple patterns
        to extract meaningful components like measurement labels and values.
        
        Args:
            text (str): Input text to split into measurement components
            
        Returns:
            tuple or None: Tuple of measurement components if successful, None if no match
        """
        
        # Log function entry
        logger.debug("Starting measurement text splitting")
        logger.debug("Input text: '%s'", text)
        
        try:
            # Pattern 1: number + space + letters/numbers + measurement
            # Example: "1 d1 2.5 cm" -> ('1', 'd1', '2.5 cm')
            pattern1 = r'(\d+)\s+(\d*[a-zA-Z]+\d*)\s*[.\s]*\s*(\d+(?:\.\d+)?\s*cm)'
            logger.debug("Trying pattern 1: %s", pattern1)
            
            match1 = re.match(pattern1, text)
            if match1:
                result = tuple(part for part in match1.groups() if part)
                logger.debug("Pattern 1 matched successfully")
                logger.debug("Pattern 1 groups: %s", match1.groups())
                logger.debug("Pattern 1 result: %s", result)
                logger.info("Text split successful using pattern 1: %s", result)
                return result
            
            logger.debug("Pattern 1 did not match")
            
            # Pattern 2: letters/numbers (including digits+letters without space) + measurement
            # Example: "d1 2.5 cm" -> ('d1', '2.5 cm')
            pattern2 = r'(\d*[a-zA-Z]+\d*)\s*[.\s]*\s*(\d+(?:\.\d+)?\s*cm)'
            logger.debug("Trying pattern 2: %s", pattern2)
            
            match2 = re.match(pattern2, text)
            if match2:
                result = tuple(part for part in match2.groups() if part)
                logger.debug("Pattern 2 matched successfully")
                logger.debug("Pattern 2 groups: %s", match2.groups())
                logger.debug("Pattern 2 result: %s", result)
                logger.info("Text split successful using pattern 2: %s", result)
                return result
            
            logger.debug("Pattern 2 did not match")
            
            # No patterns matched
            logger.debug("No patterns matched for text: '%s'", text)
            logger.info("Text split failed - no matching patterns found")
            return None
            
        except Exception as e:
            # Log errors during text splitting
            logger.error("Error occurred during measurement text splitting: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("Input text when error occurred: '%s'", text)
            return None

    def structure_table_data(self, text_elements):
        """
        Attempt to structure text elements into key-value pairs
        
        This method organizes OCR text elements by their spatial positions,
        groups them into lines, and processes each line to extract structured
        measurement data.
        
        Args:
            text_elements (list): List of text elements with position information
            
        Returns:
            list: Structured data containing measurement components and text
        """
        
        # Log function entry
        logger.info("Starting table data structuring")
        
        # Log input elements for debugging
        for i, element in enumerate(text_elements):
            logger.debug("Element %d: text='%s', x=%.2f, y=%.2f, conf=%.3f", 
                    i + 1, element['text'], element['x'], element['y'], element['confidence'])
        
        try:
            structured = []
            
            # Filter out unwanted characters/elements
            unwanted_chars = {'-', '_', '|', '/', '\\', '~', '`', '^', '*', '+', '='}
            
            # Filter text elements to remove unwanted standalone characters
            filtered_elements = []
            for element in text_elements:
                text = element['text'].strip()
                # Skip if text is empty, whitespace only, or a standalone unwanted character
                if not text or text in unwanted_chars:
                    logger.debug("Filtering out unwanted element: '%s'", text)
                    continue
                # Skip if text is only punctuation or symbols (but keep measurement-related ones)
                if len(text) == 1 and text in '.,;:!?@#$%&()[]{}':
                    logger.debug("Filtering out standalone punctuation: '%s'", text)
                    continue
                filtered_elements.append(element)
            
            logger.info("Filtered %d elements, %d remaining", 
                    len(text_elements) - len(filtered_elements), len(filtered_elements))
            
            # Sort by Y coordinate (top to bottom)
            filtered_elements.sort(key=lambda x: x['y'])
            
            # Group elements by similar Y coordinates (same line)
            lines = []
            current_line = []
            same_line_threshold = 15
            
            for element_idx, element in enumerate(filtered_elements):
                logger.debug("Processing element %d/%d: '%s' at (%.2f, %.2f)", 
                        element_idx + 1, len(filtered_elements), element['text'], 
                        element['x'], element['y'])
                
                if not current_line:
                    # First element in line
                    current_line.append(element)
                else:
                    # Check if element is on the same line
                    y_diff = abs(element['y'] - current_line[-1]['y'])
                    
                    if y_diff < same_line_threshold:
                        # Same line - add to current line
                        current_line.append(element)
                    else:
                        # New line - finalize current line and start new one
                        # Sort current line by X coordinate (left to right)
                        current_line.sort(key=lambda x: x['x'])
                        lines.append(current_line)
                        current_line = [element]
            
            # Add the last line
            if current_line:
                current_line.sort(key=lambda x: x['x'])
                lines.append(current_line)
            
            logger.info("Line grouping completed - Total lines: %d", len(lines))
            
            lineNumber = 1
            for line_idx, line in enumerate(lines):
                logger.debug("Processing line %d/%d with %d elements", 
                            line_idx + 1, len(lines), len(line))
                
                # Create a new dictionary for each line
                line_words = {}
                line_words[f'Value{lineNumber}'] = []  # Initialize the list for this line
                
                for word_idx, word in enumerate(line):
                    logger.debug("Processing word %d/%d: '%s'", 
                                word_idx + 1, len(line), word['text'])
                    
                    # Additional filtering at word level
                    word_text = word['text'].strip()
                    if not word_text or word_text in unwanted_chars:
                        logger.debug("Skipping unwanted word: '%s'", word_text)
                        continue
                    
                    # Attempt to split measurement text
                    result = self.split_measurement(word_text)
                    logger.debug("Split measurement result: %s", result)
                    
                    if result is not None:
                        # Successfully split measurement
                        line_words[f'Value{lineNumber}'].extend(result)
                    else:
                        # Keep original text if splitting failed
                        line_words[f'Value{lineNumber}'].append(word_text)
                
                # Only add line if it has content
                if line_words[f'Value{lineNumber}']:
                    structured.append(line_words)
                    lineNumber += 1
            
            print("structures", structured)
            processed_values = [" ".join(val.strip() for val in list(item.values())[0]) for item in structured]

            print("structured2", processed_values)
            structured_dict = {"value": processed_values}
            
            # Log final structured data
            logger.debug("Final structured data:")
            for i, item in enumerate(structured):
                if isinstance(item, tuple):
                    logger.debug("Item %d (tuple): %s", i + 1, item)
                else:
                    logger.debug("Item %d (text): '%s'", i + 1, item)
            
            return structured_dict
            
        except Exception as e:
            # Log errors during table data structuring
            logger.error("Error occurred during table data structuring: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("Input text elements count when error occurred: %d", len(text_elements))
            return []