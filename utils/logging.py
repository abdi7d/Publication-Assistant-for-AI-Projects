# utils/logging.py
import logging
import sys

def configure_logging(level=logging.INFO):
    root = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(level)
