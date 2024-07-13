
"""
Module used to manage logs
"""

from datetime import datetime

class Logs:
    """
    Logs class
    """
    def __init__(self):
        # DEBUG for debug mode, WARNING for warnings, ERROR for non-fatals errors (non exiting)
        # FATAL for errors leading to exit.
        self.level = 0
        self.facility = ('DEBUG', 'WARNING', 'ERROR', 'FATAL', 'INFO', 'NONE')

    def set_level(self, level):
        """
        Set facility
        """
        self.update_facility(int(level))

    def log(self, facility, msg):
        """
        Log informations
        """
        # Get key of the message facility
        key = self.facility.index(facility)
        # If key is superior or equal to config, print
        if key >= self.level:
            print(f"[{facility}] {datetime.now()} - {msg}", flush=True)

    def update_facility(self, level):
        """
        Update facility
        """
        if self.level != level and 0 <= level <= 5:
            print(f"level={level}")
            msg = f"Updating debug facility from {self.facility[self.level]} \
                    to {self.facility[level]} and above."
            self.log("INFO", msg)
            self.level = level
