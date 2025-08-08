import logging
import os


def setup_logging(log_dir="logs", console_level=logging.ERROR, clear_logs=True):
    """
    Setup logging configuration with two files:
    - all.log: Contains all log messages (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - error.log: Contains only ERROR and CRITICAL messages
    
    Args:
        log_dir (str): Directory to store log files
        console_level (int): Logging level for console output
        clear_logs (bool): Whether to clear existing log files
    """
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Define log file paths
    all_log_path = os.path.join(log_dir, 'logData.log')
    error_log_path = os.path.join(log_dir, 'error.log')
    
    # Clear existing log files if they exist and clear_logs is True
    if clear_logs:
        if os.path.exists(all_log_path):
            open(all_log_path, 'w').close()
   
        
        if os.path.exists(error_log_path):
            open(error_log_path, 'w').close()
       
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Keep DEBUG for file logging
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler for all logs
    all_log_handler = logging.FileHandler(all_log_path)
    all_log_handler.setLevel(logging.DEBUG)
    all_log_handler.setFormatter(formatter)
    
    # Create file handler for error logs only
    error_log_handler = logging.FileHandler(error_log_path)
    error_log_handler.setLevel(logging.ERROR)
    error_log_handler.setFormatter(formatter)
    
    # Create console handler with specified level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(all_log_handler)
    logger.addHandler(error_log_handler)
    logger.addHandler(console_handler)
    
    return logger


# Example usage in your main program
if __name__ == "__main__":
    # Setup logging with WARNING level for console and clear existing logs
    logger = setup_logging(console_level=logging.WARNING, clear_logs=True)
    
    # Or setup without clearing existing logs
    # logger = setup_logging(console_level=logging.WARNING, clear_logs=False)
    
