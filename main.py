from pathlib import Path

import os
import psutil
import re


def check_if_process_running(process_name):
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if process_name.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def get_latest_logfile(directory_to_look_into, log_filename_regex):
    paths = sorted(Path(directory_to_look_into).iterdir(), key=os.path.getmtime)
    paths = reversed(paths)
    for path in paths:
        if re.match(log_filename_regex, path.name):
            print(path.name)
            break
    return path


def scan_logfile_for_stats(logfile_path) -> str:
    logs = open(logfile_path, "r").read()
    print(logs)
    matched_accepted_shares = re.findall("Accepted shares [0-9]+", logs)
    matched_incorrect_shares = re.findall("Incorrect shares [^0]", logs)
    matched_average_speed = re.findall('Average speed \(5 min\): [0-9.]+ MH/s', logs)
    if len(matched_incorrect_shares) > 0:
        return matched_incorrect_shares[-1]

if __name__ == "__main__":
    temp = get_latest_logfile("/Users/atulkumar/Documents/watchdog_script", "log.*")
    scan_logfile_for_stats(temp)
