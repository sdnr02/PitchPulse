import logging
import sys
from pathlib import Path
from colorlog import ColoredFormatter

def setup_logging(log_level: str = "INFO") -> None:
    """Configures the logging for the entire application"""
    # Creating the logs directory just in case it doesn't already exist
    Path("logs").mkdir(exist_ok=True)

    # Defining the coloured formatting
    color_format = (
        "%(log_color)s%(levelname)-8s%(reset)s "
        "%(blue)s%(asctime)s%(reset)s "
        "%(cyan)s%(name)s%(reset)s "
        "%(white)s%(message)s"
    )

    # Mapping the log types to its relevant colours
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }

    # Creating our custom formatter object
    colored_formatter = ColoredFormatter(
        color_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors=log_colors
    )

    # Creating the handler for printing to the console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(colored_formatter)
    console_handler.setLevel(log_level)

    # Creating the handler for writing to the log file
    file_handler = logging.FileHandler("logs/pitchpulse.log")

    # Defining a custom formatter for the file logging
    file_format = "%(levelname)-8s %(asctime)s %(name)s %(message)s"
    plain_formatter = logging.Formatter(file_format, datefmt='%Y-%m-%d %H:%M:%S')
    
    # Setting handler for our custom file logging
    file_handler.setFormatter(plain_formatter)
    file_handler.setLevel(log_level)

    # Configuring the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Removing any existing loggers in order to prevent duplication
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Adding the new handlers to the root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # A startup message to indicate that the logger has started up successfully
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized successfully")