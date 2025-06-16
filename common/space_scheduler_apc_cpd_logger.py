import logging.handlers
def generate_space_ui_scheduler_apc_cpd_logger(*args, **kwargs):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    l_log_file_nm = './log/space_ui_scheduler_apc_cpd.log'
    l_log_file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=l_log_file_nm, when='midnight', interval=1,
        encoding='utf-8', backupCount=7)
    l_log_file_handler.suffix = '%Y-%m-%d'
    if logger.hasHandlers() is False:
        logger.addHandler(logging.StreamHandler())
        logger.addHandler(l_log_file_handler)
    formatter = logging.Formatter('%(asctime)s [%(process)d] [%(thread)d] %(levelname)s %(module)s : %(message)s')
    for handler in logger.handlers:
        handler.setFormatter(formatter)