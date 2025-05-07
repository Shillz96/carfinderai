import logging
import os
from logging.handlers import RotatingFileHandler

# Check if we're running on Vercel
IS_VERCEL = os.environ.get('VERCEL', '') == '1'

# Create logs directory if it doesn't exist and we're not on Vercel
if not IS_VERCEL:
    os.makedirs('logs', exist_ok=True)

def setup_logger(name, log_file='logs/carfinder.log', level=logging.INFO):
    """
    Set up a logger with console and file handlers
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file (ignored on Vercel)
        level (int): Logging level
    
    Returns:
        logging.Logger: Configured logger
    """
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler (always used)
    console_handler = logging.StreamHandler()
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add formatters to handlers
    console_handler.setFormatter(formatter)
    
    # Only add file handler if not running on Vercel
    if not IS_VERCEL:
        try:
            # File handler configuration (runs only if not on Vercel)
            file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
            file_handler.setFormatter(formatter)
            if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
                logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not create file handler: {e}")
    
    # Add console handler if not already present
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in logger.handlers):
        logger.addHandler(console_handler)
    
    return logger # Return the configured logger 