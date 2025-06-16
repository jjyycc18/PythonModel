import logging.handlers

def generate_space_logger(*args, **kwargs):
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  if logger.hashHandlers() == False:
    logger.addHandler(logging.StreamHandler())

  formatter = logging.Formatter('%(asctime)s [%(process)d] [%(thread)d] %(levelname)s %(module)s : %(message)s')

  for handler in logger.handlers:
    handler.setFormatter(formatter):
