import pytest
import time
from kRPC_Automation.tests.common_fixtures import krpc_connect, setup_active_vessel
from kRPC_Automation.tests.common_support import Throttle, get_throttle, set_autopilot, crew_list
from kRPC_Automation.tests.preflight.preflight_support import get_parachutes

from kRPC_Automation.log_setup import logger

g_accel = 9.81


def test_connection(krpc_connect):
    conn = krpc_connect
    assert conn is not None


def test_active_vessel(setup_active_vessel):
    vessel = setup_active_vessel
    assert vessel is not None


def test_safety_parts(setup_active_vessel):
    vessel = setup_active_vessel
    parachutes = get_parachutes(vessel)
    assert len(parachutes) > 0, f"No Parachutes found on-board {vessel.name}!"


def test_situation(setup_active_vessel):
    vessel = setup_active_vessel
    assert vessel.situation.name == "pre_launch", "Vessel is not in pre-launch state"

    #assert (vessel.thrust / (vessel.mass * g_accel)) > 1, f"TWR < 1, cannot lift off"


def zzztest_check_for_crew(setup_active_vessel):
    vessel = setup_active_vessel
    crew = crew_list(vessel)
    useful_crew = 0
    for c in crew:
        logger.debug(c.type)
        if c.type.name == "crew":
            useful_crew += 1
    assert useful_crew > 0, f"No controllable crew members are on board"


def test_control(setup_active_vessel):
    vessel = setup_active_vessel
    vessel.control.throttle = Throttle.FULL.value
    time.sleep(1)
    assert get_throttle(vessel) == Throttle.FULL.value

    set_autopilot(vessel, pitch=90, heading=90)

    assert vessel.auto_pilot.target_pitch == 90 and vessel.auto_pilot.target_heading == 90


def test_check_for_science(setup_active_vessel):
    pass
