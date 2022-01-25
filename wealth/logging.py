import logging
import sys

from .parameters import env


def set_up_wrapper():
    set_up = False

    def _function():
        nonlocal set_up
        if set_up:
            return
        logger = logging.getLogger("wealth")
        logger.setLevel(env.LOG_LEVEL)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s")
        )
        logger.addHandler(handler)
        set_up = True

    return _function


set_up_logging = set_up_wrapper()
