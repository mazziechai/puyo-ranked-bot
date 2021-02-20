import logging

logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


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