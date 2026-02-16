import logging
from functools import partial

def get_logger():
    logger = logging.Logger("provably")
    formatter = logging.Formatter("%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler = logging.FileHandler("out.log", mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
