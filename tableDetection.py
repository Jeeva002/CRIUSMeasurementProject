# Import required modules for computer vision and image processing
import cv2
import numpy as np

# Import logging setup from external logging configuration file
from logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

class TableDetector:
    """
    Table Detection class for identifying rectangular regions in ultrasound images
    
    This class provides functionality to:
    1. Detect edges using Sobel edge detection
    2. Identify rectangular regions that could be measurement tables
    3. Filter and validate potential table candidates
    4. Extract regions of interest for further processing
    """
    
    def __init__(self):
        """
        Initialize TableDetector
        
        Sets up the table detection system with default parameters.
        No specific configuration needed for basic operation.
        """
        
        # Log initialization
        logger.info("Initializing TableDetector")
        logger.debug("TableDetector instance created successfully")
        
        # Log configuration parameters that will be used
        logger.debug("Default detection parameters:")
        logger.debug("- Image upscale factor: 3x")
        logger.debug("- Edge threshold: 50")
        logger.debug("- Horizontal kernel size: (30, 1)")
        logger.debug("- Vertical kernel size: (1, 10)")
        logger.debug("- Minimum area threshold: 2 pixels")
        logger.debug("- Minimum X position: 100 pixels")
        
        logger.info("TableDetector initialization completed")

    def sobel_edge_detection(self, gray):
        """
        Apply Sobel edge detection to grayscale image
        
        This method performs edge detection using Sobel operators in both
        horizontal and vertical directions, then combines them for comprehensive
        edge detection suitable for table boundary identification.
        
        Args:
            gray: Grayscale input image array
            
        Returns:
            numpy.ndarray: Combined Sobel edge detection result as uint8 array
        """
        

        
        try:
            # Apply Sobel operator in X direction (vertical edges)

            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)

            
            # Apply Sobel operator in Y direction (horizontal edges)

            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)

            
            # Combine X and Y gradients using magnitude calculation

            sobel_combined = np.sqrt(sobelx**2 + sobely**2)

            
            # Convert to uint8 for further processing

            result = sobel_combined.astype(np.uint8)

            

            return result
            
        except Exception as e:
            # Log errors during edge detection
            logger.error("Error occurred during Sobel edge detection: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("Input gray image shape when error occurred: %s", gray.shape)
            raise

    def detect_rectangular_regions(self, image):
        """
        Detect rectangular regions that could be measurement tables
        
        This method performs a comprehensive table detection pipeline:
        1. Upscales the image for better feature detection
        2. Converts to grayscale and applies edge detection
        3. Enhances horizontal and vertical lines
        4. Finds contours and filters for rectangular shapes
        5. Validates candidates based on area and position criteria
        
        Args:
            image: Input color image array (BGR format)
            
        Returns:
            tuple: (candidate_regions, processed_image) where:
                - candidate_regions: List of dictionaries with detected table regions
                - processed_image: Upscaled image used for processing
        """
        
 
        try:
            # Get original image dimensions
            height, width = image.shape[:2]

            

            upscale_factor = 3
            new_width = width * upscale_factor
            new_height = height * upscale_factor
            logger.debug("Upscaling to: %dx%d (factor: %dx)", new_width, new_height, upscale_factor)
            
            normalUpscale = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            
            # Crop rightmost pixels to remove potential artifacts
            logger.debug("Cropping rightmost 4 pixels to remove artifacts")
            normalUpscale = normalUpscale[:, :-4]
 
            
            # Convert to grayscale for edge detection
            logger.debug("Converting upscaled image to grayscale")
            gray = cv2.cvtColor(normalUpscale, cv2.COLOR_BGR2GRAY)
            logger.debug("Grayscale conversion completed")
            
            # Apply edge detection
            logger.info("Applying edge detection to grayscale image")
            edges = self.sobel_edge_detection(gray)
            logger.debug("Edge detection completed")
            
            # Apply threshold to create binary image
            logger.debug("Applying threshold to create binary image")
            threshold_value = 50
            _, binary = cv2.threshold(edges, threshold_value, 100, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            logger.debug("Threshold applied - Value: %d, Non-zero pixels: %d", 
                       threshold_value, np.count_nonzero(binary))
            
            # Create morphological kernels for line enhancement
            logger.debug("Creating morphological kernels for line enhancement")
            kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))  # Horizontal lines
            kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))  # Vertical lines
            logger.debug("Kernels created - Horizontal: (30,1), Vertical: (1,10)")
            
            # Enhance horizontal and vertical lines separately
            logger.info("Enhancing horizontal and vertical lines")
            horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_h)
            vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_v)
            logger.debug("Line enhancement completed")
            
            # Make lines thicker for better detection
            logger.debug("Applying dilation to make lines thicker")
            kernel_thick = np.ones((2, 2), np.uint8)
            horizontal = cv2.dilate(horizontal, kernel_thick, iterations=1)
            vertical = cv2.dilate(vertical, kernel_thick, iterations=1)
            logger.debug("Line thickening completed")
            
            # Combine horizontal and vertical lines
            logger.debug("Combining horizontal and vertical lines")
            enhanced_lines = cv2.bitwise_or(horizontal, vertical)
            logger.debug("Line combination completed")
            
            # Create copy for contour visualization
            forContour = normalUpscale.copy()
            logger.debug("Created copy for contour visualization")
            
            # Find contours in the enhanced lines
            logger.info("Finding contours in enhanced lines")
            contours, _ = cv2.findContours(enhanced_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            logger.info("Found %d contours", len(contours))
            
            # Draw contours for visualization
            logger.debug("Drawing contours for visualization")
            cv2.drawContours(forContour, contours, -1, (0, 255, 0), 3)
            logger.debug("Contours drawn successfully")
            
            # Process each contour to find valid rectangular regions
            logger.info("Processing contours to find rectangular regions")
            candidate_regions = []
            count = 0
            min_area = 2
            min_x_position = 30

            
            for contour in contours:
                count += 1
   
                
                # Calculate contour area
                area = cv2.contourArea(contour)

                
                # Filter by minimum area
                if area < min_area:

                    continue
                
                # Check if contour is roughly rectangular
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                
                # Filter by rectangle criteria and position
                if len(approx) >= 4 and w > min_x_position:
              
                    
                    # Extract region of interest
                    roi = normalUpscale[y:y+h, x:x+w]

                    
                    # Calculate aspect ratio
                    aspect_ratio = w / h if h > 0 else 0

                    
                    # Create candidate region dictionary
                    candidate_region = {
                        'bbox': (x, y, w, h),
                        'roi': roi,
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    }
                    
                    candidate_regions.append(candidate_region)                   

                else:
                     pass
            
            # Log final results
            logger.info("Rectangular region detection completed")
            logger.info("Total candidate regions found: %d", len(candidate_regions))
            
            # if candidate_regions:
            #     logger.debug("Candidate regions summary:")
            #     for i, region in enumerate(candidate_regions):
            #         logger.debug("Region %d: Area=%.2f, Aspect=%.2f, BBox=(%d,%d,%d,%d)", 
            #                    i+1, region['area'], region['aspect_ratio'], 
            #                    *region['bbox'])
            # else:
            #     logger.warning("No candidate regions found matching the criteria")
            
            return candidate_regions, normalUpscale
            
        except Exception as e:
            # Log errors during region detection
            logger.error("Error occurred during rectangular region detection: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            logger.debug("Input image shape when error occurred: %s", image.shape)
            raise