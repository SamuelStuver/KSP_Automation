import krpc
import pytest
from kRPC_Automation.log_setup import logger
import time

def establish_connection(name="Connection", address='192.168.0.11', rpc_port=5000, stream_port=5001):
    logger.debug(f"Attempting to connect to {address}:{rpc_port}")
    try:
        conn = krpc.connect(
                            name="Connection",
                            address='192.168.0.11',
                            rpc_port=5000,
                            stream_port=5001
                            )
        logger.debug(f"Successfully connected to {address}:{rpc_port}")
        return conn
    except:
        logger.error(f"failed to connect to {address}:{rpc_port}")
        return None

def check_for_active_vessel(conn):
    logger.debug("Checking for active for vessel...")
    try:
        vessel = conn.space_center.active_vessel
        logger.info(
            f"Active Vessel Found:\n"
            f"Vessel:    {vessel.name}\n"
            f"Type:      {vessel.type}\n"
            f"Situation: {vessel.situation}\n"
            f"Biome:     {vessel.biome}\n"
            f"Crew:      {[c.name for c in vessel.crew]}\n"
            f"Mass:      {vessel.mass}"
            )
        return vessel
    except krpc.error.RPCErro as err:
        logger.error(err)
        return None


def wait_for_fuel_to_run_out(conn, vessel):
    logger.info("Waiting for fuel to run out...")
    fuel_amount = conn.get_call(vessel.resources.amount, 'SolidFuel')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(fuel_amount),
        conn.krpc.Expression.constant_float(0.1))
    event = conn.krpc.add_event(expr)
    with event.condition:
        event.wait()

def wait_for_safe_parachute(conn, vessel):
    logger.info("Waiting until safe to deploy parachute...")
    mean_altitude = conn.get_call(getattr, vessel.flight(), 'mean_altitude')
    expr = conn.krpc.Expression.less_than(
        conn.krpc.Expression.call(mean_altitude),
        conn.krpc.Expression.constant_double(2000))
    event = conn.krpc.add_event(expr)
    with event.condition:
        event.wait()

def time_warp_to_land(conn, vessel):
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

    while not vessel.recoverable:
        time.sleep(1)

    if vessel.recoverable:
        time.sleep(10)
        vessel.recover

if __name__ == "__main__":

    conn = establish_connection()
    vessel = check_for_active_vessel(conn)

    print(conn.vessel)
