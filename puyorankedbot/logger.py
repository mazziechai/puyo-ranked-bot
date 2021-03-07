import logging

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
file_handler = logging.FileHandler(filename="../discord.log", encoding="utf-8", mode="w")
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

def log_info(log):
    logger.info(log)

def log_error(log):
    logger.error(log)

def log_debug(log):
    logger.debug(log)

def log_critical(log):
    logger.critical(log)

def log_exception(log):
    logger.exception(log)