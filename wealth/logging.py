import logging
import sys

from .parameters import Environment


def set_up_logging():
    logger = logging.getLogger()
    logger.setLevel(Environment.LOG_LEVEL)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s"))
    logger.addHandler(handler)
