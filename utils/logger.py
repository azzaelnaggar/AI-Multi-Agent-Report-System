# utils/logger.py
# Purpose:
# Create a global logging system that writes logs to a file and shows them in the terminal.
##########
# utils/logger.py is responsible for:
# Creating a single shared logger for the whole project
# Logging everything to both:
# 1 -logs/system.log
# 2 -the terminal
# Formatting messages with timestamps and levels
# Preventing duplicate handlers


import logging
import os

def setup_logger(name="multiagent", logfile="logs/system.log"):
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
