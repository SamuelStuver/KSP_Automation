import pytest
import time
from example_support import check_for_active_vessel, wait_for_fuel_to_run_out, wait_for_safe_parachute, time_warp_to_land
from example_fixtures import krpc_connect
from log_setup import logger


def test_detect_vessel(krpc_connect):
    conn = krpc_connect
    vessel = check_for_active_vessel(conn)
    assert vessel is not None, "No active vessel found"


def test_vessel_ready_to_launch(krpc_connect):
    conn = krpc_connect
    vessel = check_for_active_vessel(conn)
    assert vessel is not None, "No active vessel found"
    assert vessel.situation.name == "pre_launch", "Vessel is not in pre-launch state"


    vessel.auto_pilot.target_pitch_and_heading(90, 90)
    vessel.auto_pilot.engage()
    vessel.control.throttle = 1
    time.sleep(1)
    assert vessel.control.throttle == 1
    return True

def test_launch(krpc_connect):

    conn = krpc_connect
    vessel = check_for_active_vessel(conn)
    assert vessel is not None, "No active vessel found"
    assert vessel.situation.name == "pre_launch", "Vessel is not in pre-launch state"
    vessel.auto_pilot.target_pitch_and_heading(90, 90)
    vessel.auto_pilot.engage()
    vessel.control.throttle = 1
    logger.info("Wait 5 seconds to launch...")
    time.sleep(5)
    logger.info("Launching...")

    vessel.control.activate_next_stage()
    vessel.auto_pilot.target_pitch_and_heading(60, 180)

    wait_for_fuel_to_run_out(conn, vessel)
    logger.info("Ditch the empty tank...")
    vessel.control.activate_next_stage()

    vessel.auto_pilot.disengage()
    vessel.auto_pilot.sas = True
    wait_for_safe_parachute(conn, vessel)

    logger.info("Activating Parachute.")
    vessel.control.activate_next_stage()
    vessel.auto_pilot.sas = False

    time.sleep(3)
    time_warp_to_land(conn, vessel)
