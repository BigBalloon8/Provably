import logging

def get_logger():
    logger = logging.Logger("provably")
    formatter = logging.Formatter("\n%(asctime)s - %(message)s", "%Y-%m-%d %H:%M:%S \n")
    file_handler = logging.FileHandler("out.md", mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger
