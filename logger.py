def init_logger(logger_name, filename='sys.log'):
    """The getLogger helper
    Usage example:

    import logging
    from logger import init_logger

    logging.basicConfig(level=logging.INFO)

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
    import logging
    import uos

    if 'sd' in uos.listdir():
        if not 'log' in uos.listdir('sd'):
            uos.mkdir('sd/log')
        filepath = 'sd/log/' + filename
    else:
        filepath = filename

    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_formatter = logging.Formatter(log_format)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    log_file_handler = logging.FileHandler(filename=filepath)
    log_file_handler.setFormatter(log_formatter)
    log_file_handler.setLevel(logging.INFO)
    logger.addHandler(log_file_handler)

    log_stream_handler = logging.StreamHandler()
    log_stream_handler.setFormatter(log_formatter)
    log_stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(log_stream_handler)

    return logger
