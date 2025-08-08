# Import required modules for DICOM processing
import pydicom

# Import logging setup from external logging configuration file
from scripts.logSetup import setup_logging

# Initialize logger using the external logging setup
logger = setup_logging()

class USRegionLocation():
    """
    A class to extract and manage ultrasound region coordinates from DICOM files
    
    This class handles the extraction of ultrasound region boundaries from DICOM metadata,
    specifically targeting the ultrasound regions sequence to identify measurement areas
    within the ultrasound image.
    
    Attributes:
        dicomPath (str): Path to the DICOM file
        dicomData: Parsed DICOM data object
        studyInfo: Study description from DICOM metadata
        imageType: Image type information from DICOM metadata
        x0, y0, x1, y1: Region coordinate boundaries
    """
    
    def __init__(self, dicomData):
        """
        Initialize the USRegionLocation object with DICOM data
        
        Args:
            dicomData (str): Path to the DICOM file to be processed
        """

        
        try:
            # Store the DICOM file path
            self.dicomPath = dicomData

            
            # Initialize the region coordinates as instance variables

            self.x0, self.y0, self.x1, self.y1 = self.getMeasurementRegions()

        except Exception as e:
            logger.error("Error during USRegionLocation initialization: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            raise

    def getMeasurementRegions(self):
        """
        Extract measurement regions from the DICOM file
        
        This method reads the DICOM file and extracts study information and image type
        before calling the region extraction method.
        
        Returns:
            tuple: (x0, y0, x1, y1) coordinate arrays for all available regions
        """
        # Log function entry

        
        try:
            # Read the DICOM file

            self.dicomData = pydicom.dcmread(self.dicomPath)

            
            # Extract study information from DICOM metadata

            self.studyInfo = self.dicomData[0x0008, 0x1030]

            
            # Extract image type information from DICOM metadata

            self.imageType = self.dicomData[0x0008, 0x0008]

            
            # Get all available regions from the DICOM data

            return self.getAllAvailableRegions()
            
        except Exception as e:
            logger.error("Error in getMeasurementRegions: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            raise

    def getAllAvailableRegions(self):
        """
        Extract all available ultrasound regions from DICOM metadata
        
        This method processes the ultrasound regions sequence from the DICOM file
        to extract boundary coordinates for each region. It handles multiple regions
        and collects all coordinate boundaries.
        
        Returns:
            tuple: (min_x0, min_y0, max_x1, max_y1) lists containing coordinates for all regions
        """

        
        try:
            # Access the ultrasound regions sequence from DICOM metadata

            regions_sequence = self.dicomData[(0x0018, 0x6011)]  # Common tag for ultrasound regions

            
            # Initialize coordinate lists for all regions
            min_x0 = []
            min_y0 = []
            max_x1 = []
            max_y1 = []
            

            
            # Process each region in the sequence
            for i, region in enumerate(regions_sequence):

                
                # Access Region Location Min X0 coordinate
                if (0x0018, 0x6018) in region:
                    x0_value = region[(0x0018, 0x6018)].value
                    min_x0.append(x0_value)

                else:
                    logger.warning("Region %d - Min X0 coordinate not found", i + 1)
                
                # Access Region Location Min Y0 coordinate
                if (0x0018, 0x601a) in region:
                    y0_value = region[(0x0018, 0x601a)].value
                    min_y0.append(y0_value)

                else:
                    logger.warning("Region %d - Min Y0 coordinate not found", i + 1)
                
                # Access Region Location Max X1 coordinate
                if (0x0018, 0x601c) in region:
                    x1_value = region[(0x0018, 0x601c)].value
                    max_x1.append(x1_value)

                else:
                    logger.warning("Region %d - Max X1 coordinate not found", i + 1)
                
                # Access Region Location Max Y1 coordinate
                if (0x0018, 0x601e) in region:
                    y1_value = region[(0x0018, 0x601e)].value
                    max_y1.append(y1_value)

                else:
                    logger.warning("Region %d - Max Y1 coordinate not found", i + 1)
            


            

            
            return min_x0, min_y0, max_x1, max_y1
            
        except Exception as e:
            logger.error("Error in getAllAvailableRegions: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            raise
    
    def get_coordinates(self):
        """
        Retrieve the extracted coordinates and study information
        
        This method provides access to the region coordinates that were extracted
        during object initialization, along with the study information from the DICOM file.
        
        Returns:
            tuple: (x0, y0, x1, y1, studyInfo) containing coordinate arrays and study information
        """

        
        try:
            # Return the stored coordinates and study information            
            return self.x0, self.y0, self.x1, self.y1, self.studyInfo
            
        except Exception as e:
            logger.error("Error retrieving coordinates: %s", str(e))
            logger.error("Exception type: %s", type(e).__name__)
            raise