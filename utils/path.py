import os
import sys

def resource_path(relative_path, no_meipass=False):
    if hasattr(sys, '_MEIPASS') and not no_meipass:
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)