import logging
from logging.handlers import TimedRotatingFileHandler

def initialize_logger():
    logging.basicConfig(datefmt='%Y-%m-%dT%H:%M:%S,%03d.%z', level=logging.DEBUG)

    formatter_verbose = logging.Formatter('%(asctime)s\t-- %(levelname)s  -- %(name)s -- P_%(process)d--%(filename)s--%(funcName)s--%(lineno)s \t-- %(message)s')
    formatter_light = logging.Formatter('%(asctime)s -- %(message)s')

    handler_error = logging.handlers.TimedRotatingFileHandler('/tmp/watcher_status.log', when="d", interval=1, encoding="utf-8", backupCount=30)
    handler_error.setFormatter(formatter_light)
    handler_error.setLevel(logging.WARNING)
    handler_debug = logging.handlers.TimedRotatingFileHandler('/tmp/watcher.log', when="d", interval=1, encoding="utf-8", backupCount=30)
    handler_debug.setFormatter(formatter_verbose)
    handler_debug.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.addHandler(handler_debug)
    logger.addHandler(handler_error)

    return logger
