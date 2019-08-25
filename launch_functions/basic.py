import time
import krpc
import pytest
import sys

sys.path.append(r"C:\Users\samue")

from kRPC_Automation.log_setup import logger
from kRPC_Automation.tests.test_runner import test_runner, PytestExitCodes
from kRPC_Automation.data_collection.data_streams import stream_value

def log_and_print(message):
    logger.info(message)
    print(message)

def run_preflight_tests():
    preflight_tests_path = r"C:\Users\samue\kRPC_Automation\tests\preflight\preflight_tests.py"
    preflight_check = test_runner(preflight_tests_path)
    return preflight_check

def simple_launch(conn, vessel):
    success = False
    if vessel.situation.name != "pre_launch":
        return False



    vessel.auto_pilot.engage()

    log_and_print("Wait 5 seconds to launch...")
    time.sleep(5)
    log_and_print("Launching...")

    vessel.control.activate_next_stage()

    success = wait_for_surf_alt(conn, vessel,2000)
    vessel.auto_pilot.target_pitch_and_heading(75, 90)
    success = wait_for_surf_alt(conn, vessel,20000)
    vessel.auto_pilot.target_pitch_and_heading(45, 90)

    success = wait_for_fuel_to_run_out(conn, vessel)
    if not success:
        return False

    log_and_print("Ditch the empty tank...")
    vessel.control.activate_next_stage()

    vessel.auto_pilot.disengage()

    success = wait_for_safe_parachute(conn, vessel)
    if not success:
        return False

    log_and_print("Activating Parachute.")
    vessel.control.activate_next_stage()

    time.sleep(3)
    success = time_warp_to_land(conn, vessel)
    if not success:
        return False

    return True


def wait_for_fuel_to_run_out(conn, vessel):
    log_and_print("Waiting for fuel to run out...")
    fuel_amount = conn.get_call(vessel.resources.amount, 'SolidFuel')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(fuel_amount),
        conn.krpc.Expression.constant_float(0.1))
    event = conn.krpc.add_event(expr)
    with event.condition:
        event.wait()
    return True


def wait_for_safe_parachute(conn, vessel):
    log_and_print("Waiting until safe to deploy parachute...")
    mean_altitude = conn.get_call(getattr, vessel.flight(), 'surf_altitude')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(mean_altitude),
        conn.krpc.Expression.constant_double(2000))
    event = conn.krpc.add_event(expr)
    with event.condition:
        event.wait()
    return True

def wait_for_surf_alt(conn, vessel, alt):
    log_and_print(f"Waiting until altitude reaches {alt}...")
    surf_altitude = conn.get_call(getattr, vessel.flight(), 'surf_altitude')
    expr = conn.krpc.Expression.greater_than(
        conn.krpc.Expression.call(surf_altitude),
        conn.krpc.Expression.constant_double(2000))
    event = conn.krpc.add_event(expr)
    with event.condition:
        event.wait()
    return True



def time_warp_to_land(conn, vessel, recover=False):
    if vessel.parts.parachutes[0].state.name == "active" or vessel.parts.parachutes[0].state.name == "semi_deployed":
        pass
    else:
        assert False, f"Parachute state is {vessel.parts.parachutes[0].state.name}"
    space_center = conn.space_center
    space_center.physics_warp_factor = 3

    log_and_print("Waiting until landing...")
    surface_altitude = conn.get_call(getattr, vessel.flight(), 'surface_altitude')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(surface_altitude),
        conn.krpc.Expression.constant_double(50))
    event = conn.krpc.add_event(expr)
    with event.condition:
        event.wait()
    space_center.physics_warp_factor = 0

    if recover:
        while not vessel.recoverable:
            time.sleep(1)

        if vessel.recoverable:
            time.sleep(10)
            vessel.recover()

    return True


if __name__ == "__main__":
    result = run_preflight_tests()
    if result == PytestExitCodes.ALL_PASSING:
        log_and_print("Ready to Launch!")
        print("Ready to Launch!")
    else:
        exit(1)

    conn = krpc.connect(name="Connection",address='192.168.0.11',rpc_port=5000,stream_port=5001)
    vessel = conn.space_center.active_vessel
    simple_launch(conn, vessel)
