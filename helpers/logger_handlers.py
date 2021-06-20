import logging
from sys import stdout
from logging.handlers import TimedRotatingFileHandler

from helpers import misc


_log_directory = "logs/"


def get_console_handler():
    """
    Returns console handler which outputs to stdout with log level of info
    :return: stdout StreamHandler
    """
    console_handler = logging.StreamHandler(stdout)
    console_handler.setLevel(logging.INFO)
    return console_handler


def get_file_handler() -> TimedRotatingFileHandler:
    """
    Returns file handler which outputs to file with log level of info
    File output is done in a way that logs are separated into 10 files where each file is valid for 1 day
    Oldest one gets rewritten by the newest one.
    Log messages have a timestamp prefix
    :return: TimedRotatingFileHandler
    """
    misc.check_create_directory(_log_directory)
    log_file_full_path = _log_directory + "log.txt"
    file_handler = TimedRotatingFileHandler(log_file_full_path, when="D", backupCount=10, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s [%(name)s/%(funcName)s]", "%d-%m-%Y %H:%M:%S")
    )
    file_handler.setLevel(logging.INFO)
    return file_handler
