import language_tool_python
import os
from pathlib import Path

# Import the logging setup
from scripts.logSetup import setup_logging

# Initialize logger
logger = setup_logging()

# --- Configuration ---
DOWNLOAD_DIR_NAME = "language_tool_model"
DOWNLOAD_DIR = Path.cwd() / DOWNLOAD_DIR_NAME
LTP_PATH_STR = str(DOWNLOAD_DIR.resolve()) 

logger.debug("Configuration - DOWNLOAD_DIR_NAME: %s", DOWNLOAD_DIR_NAME)
logger.debug("Configuration - DOWNLOAD_DIR: %s", DOWNLOAD_DIR)
logger.debug("Configuration - LTP_PATH_STR: %s", LTP_PATH_STR)

# Set LTP_PATH environment variable for download/load location
if os.environ.get('LTP_PATH') != LTP_PATH_STR:
    os.environ['LTP_PATH'] = LTP_PATH_STR
    logger.info("Set LTP_PATH for download/load location: %s", LTP_PATH_STR)
else:
    logger.debug("LTP_PATH already set to: %s", LTP_PATH_STR)

# --- Grammar Checker Class (Simplified) ---

class GrammarChecker:
    """Grammar checker that loads the model once and can be reused"""
    
    def __init__(self, language='en-US'):
        """Initialize and load the grammar tool once"""
        logger.info("Initializing GrammarChecker with language: %s", language)
        
        try:
            # Check if the expected JAR file or directory exists for better messaging
            # We rely on the rglob() from pathlib for recursive search
            logger.debug("Checking for existing model files in: %s", DOWNLOAD_DIR)
            is_model_present = any(DOWNLOAD_DIR.rglob('LanguageTool-*.jar'))
            
            if not is_model_present:
                logger.warning("Model not found in '%s/'. Attempting download...", DOWNLOAD_DIR_NAME)
            else:
                logger.info("Model files found in '%s/'. Loading model...", DOWNLOAD_DIR_NAME)
                
            # This will download if not present (to LTP_PATH) or load if present
            logger.debug("Initializing LanguageTool with language: %s", language)
            self.tool = language_tool_python.LanguageTool(language)
            
            logger.info("Grammar checker model loaded successfully!")
            
        except Exception as e:
            logger.error("Failed to initialize grammar checker: %s", str(e), exc_info=True)
            raise
    
    def check_and_correct(self, text):
        """Check grammar and return corrected text"""
        logger.debug("Starting grammar check. Input text length: %d characters", len(text) if text else 0)
        
        if not text or not text.strip():
            logger.warning("Empty or whitespace-only text provided. Returning as-is.")
            return text
        
        try:
            logger.debug("Input text preview: %s...", text[:100] if len(text) > 100 else text)
            
            # Perform grammar correction
            corrected_text = self.tool.correct(text)
            
            # Log correction details
            changes_made = text != corrected_text
            logger.debug("Correction complete. Changes made: %s", changes_made)
            logger.debug("Corrected text length: %d characters", len(corrected_text))
            
            if changes_made:
                logger.info("Grammar corrections applied to text")
                logger.debug("Corrected text preview: %s...", corrected_text[:100] if len(corrected_text) > 100 else corrected_text)
            else:
                logger.info("No grammar corrections needed")
            
            return corrected_text
            
        except Exception as e:
            logger.error("Error during grammar checking: %s", str(e), exc_info=True)
            logger.warning("Returning original text due to error")
            return text
    
    def close(self):
        """Close the grammar tool when done"""
        logger.info("Closing grammar checker...")
        
        try:
            self.tool.close()
            logger.info("Grammar checker closed successfully")
            
        except Exception as e:
            logger.error("Error while closing grammar checker: %s", str(e), exc_info=True)