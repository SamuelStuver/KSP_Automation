import time
import krpc
from kRPC_Automation.log_setup import logger

def get_parachutes(vessel):
    parachute_list = list(vessel.parts.with_module("ModuleParachute"))
    logger.debug(f"{len(parachute_list)} Parachute(s) found: ")
    return parachute_list
