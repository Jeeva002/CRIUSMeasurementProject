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
        # print("text",text_elements)
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
            
          
            processed_values = [" ".join(val.strip() for val in list(item.values())[0]) for item in structured]

          
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