import logging.handlers
import sys
def generate_space_logger(*args, **kwargs):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.addHandler(logging.StreamHandler(sys.stdout))
    else:
        logger.addHandler(logging.StreamHandler(sys.stdout))
    formatter = logging.Formatter('%(asctime)s [%(process)d] [%(thread)d] %(levelname)s %(module)s : %(message)s')
    for handler in logger.handlers:
        handler.setFormatter(formatter)