import logging
import sys

def setup_logger(level=logging.INFO):
    """Configure logger for console output.

    This function sets up the logger with an easy-to-read format and sends output
    to the console. The logger will be configured with a customizable logging level.

    Args:
        level (int, optional): Logging level to use. 
                              Default is logging.INFO.

    Returns:
        None: This function does not return a value, only sets up logger configuration.

    Example:
        >>> setup_logger(logging.DEBUG)
        >>> logging.debug("Debug message")
        >>> logging.info("Info message")
    """
    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)

    root_logger.addHandler(console_handler)