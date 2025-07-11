import logging
import os

def setup_logging(log_dir="logs"):
    """
    Setup logging configuration with two files:
    - all.log: Contains all log messages (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - error.log: Contains only ERROR and CRITICAL messages
    """
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler for all logs
    all_log_handler = logging.FileHandler(os.path.join(log_dir, 'all.log'))
    all_log_handler.setLevel(logging.DEBUG)
    all_log_handler.setFormatter(formatter)
    
    # Create file handler for error logs only
    error_log_handler = logging.FileHandler(os.path.join(log_dir, 'error.log'))
    error_log_handler.setLevel(logging.ERROR)
    error_log_handler.setFormatter(formatter)
    
    # Create console handler (optional - remove if you don't want console output)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(all_log_handler)
    logger.addHandler(error_log_handler)
    logger.addHandler(console_handler)
    
    return logger

# Example usage in your main program
if __name__ == "__main__":
    # Setup logging
    logger = setup_logging()
    
    # Example log messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")