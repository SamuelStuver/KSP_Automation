import time
import krpc
from kRPC_Automation.log_setup import logger

def abort_launch(conn, vessel):
    if vessel.situation.name in ["pre_launch", "splashed", "landed"]:
        if vessel.recoverable:
            vessel.recover()
            return True

    if vessel.situation.name == "sub_orbital":
        return False
    if vessel.situation.name == "flying":
        return False
    if vessel.situation.name == "orbiting":
        return False
    if vessel.situation.name == "escaping":
        return False
    if vessel.situation.name == "docked":
        return False


def simple_launch(conn, vessel):
    success = False
    if vessel.situation.name != "pre_launch":
        abort_launch(conn_vessel)
        return False

    vessel.auto_pilot.engage()

    logger.info("Wait 5 seconds to launch...")
    time.sleep(5)
    logger.info("Launching...")

    vessel.control.activate_next_stage()
    vessel.auto_pilot.target_pitch_and_heading(60, 180)

    success = wait_for_fuel_to_run_out(conn, vessel)
    if not success:
        return False

    logger.info("Ditch the empty tank...")
    vessel.control.activate_next_stage()

    vessel.auto_pilot.disengage()

    success = wait_for_safe_parachute(conn, vessel)
    if not success:
        return False

    logger.info("Activating Parachute.")
    vessel.control.activate_next_stage()

    time.sleep(3)
    success = time_warp_to_land(conn, vessel)
    if not success:
        return False

    return True

def wait_for_fuel_to_run_out(conn, vessel):
    logger.info("Waiting for fuel to run out...")
    fuel_amount = conn.get_call(vessel.resources.amount, 'SolidFuel')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(fuel_amount),
        conn.krpc.Expression.constant_float(0.1))
    event = conn.krpc.add_event(expr)
    with event.condition:
        event.wait()
    return True

def wait_for_safe_parachute(conn, vessel):
    logger.info("Waiting until safe to deploy parachute...")
    mean_altitude = conn.get_call(getattr, vessel.flight(), 'mean_altitude')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(mean_altitude),
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

    logger.info("Waiting until landing...")
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
