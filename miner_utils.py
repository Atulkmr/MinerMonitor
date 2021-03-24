#!/usr/bin/env python

"""
Provides some functions to extract stats from miner logs.
"""
from pathlib import Path

import os
import psutil
import re

miner_process_name = os.getenv('MINER_PROCESS_NAME')
miner_log_directory = os.getenv('MINER_LOG_DIRECTORY')
miner_logfile_prefix = os.getenv('MINER_LOGFILE_PREFIX')


def check_if_process_running():
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if miner_process_name.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def get_latest_logfile():
    paths = sorted(Path(miner_log_directory).iterdir(), key=os.path.getmtime)
    paths = reversed(paths)
    for path in paths:
        if re.match(miner_logfile_prefix, path.name):
            break
    return path


def scan_logfile_for_incorrect_shares() -> str:
    logfile_path = get_latest_logfile()
    logs = open(logfile_path, "r").read()
    matched_incorrect_shares = re.findall("Incorrect shares [^0]", logs)
    if len(matched_incorrect_shares) > 0:
        return matched_incorrect_shares[-1]


def scan_logfile_for_stats() -> str:
    logfile_path = get_latest_logfile()
    logs = open(logfile_path, "r").read()
    matched_accepted_shares = re.findall("Accepted shares [0-9]+", logs)
    matched_incorrect_shares = re.findall("Incorrect shares [^0]", logs)
    matched_average_speed = re.findall("Average speed \(5 min\): [0-9.]+ MH/s", logs)
    if len(matched_incorrect_shares) > 0:
        return matched_accepted_shares[-1] + os.linesep + matched_average_speed[-1] + os.linesep + \
               matched_incorrect_shares[-1]
    else:
        return matched_accepted_shares[-1] + os.linesep + matched_average_speed[-1]
