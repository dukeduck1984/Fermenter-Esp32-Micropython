import logging


def init_logger(logger_name, level='WARNING', filename='mylogs.log'):
    """The getLogger helper
    Usage example:

    from logger import init_logger

    logger = init_logger(__name__, 'your_log_filename.log')
    logger.debug('This is a debug message')
    logger.error('This is an error')

    try:
        1/0
    except Exception as e:
        logger.exception(e, 'Cannot divided by zero!')


    :param logger_name: string; logger name
    :param filename: string: logger filename
    :return: Logger class
    """
    _level_dict = {
        # A serious error, indicating that the program itself may be unable to continue running.
        'CRITICAL': logging.CRITICAL,
        # Due to a more serious problem, the software has not been able to perform some function.
        'ERROR': logging.ERROR,
        # An indication that something unexpected happened, or indicative of some problem in the near
        # future (e.g. ‘disk space low’). The software is still working as expected.
        'WARNING': logging.WARNING,
        # Confirmation that things are working as expected.
        # Report events that occur during normal operation of a program
        # (e.g. for status monitoring or fault investigation)
        'INFO': logging.INFO,
        # Detailed information, typically of interest only when diagnosing problems.
        'DEBUG': logging.DEBUG
    }
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(logger_name)
    logger.setLevel(_level_dict.get(level.upper()))
    log_file_handler = logging.FileHandler(filename)
    log_formatter = logging.Formatter(log_format)
    log_file_handler.setFormatter(log_formatter)
    logger.addHandler(log_file_handler)
    
    return logger
