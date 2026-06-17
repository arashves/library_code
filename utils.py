import logging

def Alogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s | %(name)-10s | %(levelname)-12s | %(message)s')
    file_handler = logging.FileHandler('library.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


