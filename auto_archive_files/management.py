"""A simple monitor with alerts for Unix
"""


import argparse
import logging

from simple_monitor_alert.monitor import Monitors
from simple_monitor_alert.sma import SMA, SMAService

from auto_archive_files.archiver import Archiver


def create_logger(name, level=logging.INFO):
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-7s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--warning', help='set logging to warning', action='store_const', dest='loglevel',
                        const=logging.WARNING, default=logging.INFO)
    parser.add_argument('--quiet', help='set logging to ERROR', action='store_const', dest='loglevel',
                        const=logging.ERROR, default=logging.INFO)
    parser.add_argument('--debug', help='set logging to DEBUG',
                        action='store_const', dest='loglevel',
                        const=logging.DEBUG, default=logging.INFO)
    parser.add_argument('--verbose', help='set logging to COMM',
                        action='store_const', dest='loglevel',
                        const=5, default=logging.INFO)
    parser.add_argument('config_or_configpath')
    args = parser.parse_args(argv[1:])

    create_logger('archiver', args.loglevel)

    Archiver(args.config_or_configpath).archive()
