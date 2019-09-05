import logging


def init_logger(logger_name, filename='mylogs.log'):
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
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    log_file_handler = logging.FileHandler(filename)
    log_formatter = logging.Formatter(log_format)
    log_file_handler.setFormatter(log_formatter)
    logger.addHandler(log_file_handler)
    
    return logger
