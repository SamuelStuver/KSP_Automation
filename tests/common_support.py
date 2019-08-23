import krpc
import pytest
from kRPC_Automation.log_setup import logger
import time
from enum import Enum

class Throttle(Enum):
    FULL = 1
    HALF = 0.5
    ZERO = 0

def get_throttle(vessel):
    throttle = vessel.control.throttle
    return throttle

def crew_list(vessel):
    if vessel.crew_capacity == 0:
        logger.info(f"Craft is unmanned.")
        return []
    else:
        logger.info(f"Craft contains {vessel.crew_count} out of {vessel.crew_capacity} crew members")
        return vessel.crew

def set_autopilot(vessel, pitch=90, heading=90):
    logger.info("Engaging Autopilot")
    vessel.auto_pilot.engage()
    logger.info(f"Set pitch to {pitch} and heading to {heading}")
    vessel.auto_pilot.target_pitch_and_heading(pitch, heading)
