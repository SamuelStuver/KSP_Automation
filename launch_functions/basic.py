import time
import krpc
import pytest
import sys
import math
sys.path.append(r"C:\Users\samue")

from kRPC_Automation.log_setup import logger
from kRPC_Automation.tests.test_runner import test_runner, PytestExitCodes
from kRPC_Automation.data_collection.data_streams import MissionData, log_and_print



def run_preflight_tests():
    preflight_tests_path = r"C:\Users\samue\kRPC_Automation\tests\preflight\preflight_tests.py"
    preflight_check = test_runner(preflight_tests_path)
    return preflight_check

def single_burn_stage(mission):
    vessel = mission.vessel
    success = False
    if vessel.situation.name != "pre_launch":
        return False

    print(f"N_Stages: {mission.n_stages}")
    for s in mission.stages:
        print(s.decouple_stage, s.has_fuel())

    log_and_print("Wait 5 seconds to launch...")
    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(90, 90)

    log_and_print("Wait 5 seconds to launch...")
    time.sleep(5)
    log_and_print("Launching...")

    mission.activate_stage()

    mission.wait_for("surface_altitude", '>', 2000)
    vessel.auto_pilot.target_pitch_and_heading(65, 90)
    mission.wait_for("surface_altitude", '>', 5000)
    vessel.auto_pilot.target_pitch_and_heading(45, 90)

    mission.current_stage.wait_for_no_fuel()

    time.sleep(1)
    log_and_print("Ditch the empty tank...")
    mission.activate_stage()

    log_and_print("Disengage auto-pilot")
    vessel.auto_pilot.disengage()

    log_and_print(f"Wait for vessel to reach apoapsis: {mission.apoapsis()}")
    mission.wait_for("surface_altitude", '>', mission.apoapsis, changing_value=True, factor=0.8)


    log_and_print(f"Height - {mission.apoapsis()} reached. Run Science Experiments")
    run_all_science_experiments(vessel)


    mission.wait_for("surface_altitude", '<=', 3000)

    log_and_print("Deploying Parachute(s).")
    try:
        for parachute in vessel.parts.parachutes:
            parachute.deploy()
    except:
        log_and_print("No Parachutes on Board")

    time.sleep(3)
    time_warp_to_land(mission)

    log_and_print("Wait for vessel to reach the ground")
    mission.wait_for("surface_altitude", '<=', 10)

def N_burn_stage(mission):
    success = False
    if vessel.situation.name != "pre_launch":
        return False

    # Set up telemetry streams
    ut = conn.add_stream(getattr, conn.space_center, 'ut')
    surface_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
    mean_altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
    periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')

    stage_2_fuel_obj = vessel.resources_in_decouple_stage(3, cumulative = False)
    stage_2_fuel = conn.add_stream(stage_2_fuel_obj.amount, 'LiquidFuel')
    stage_1_fuel_obj = vessel.resources_in_decouple_stage(2, cumulative = False)
    stage_1_fuel = conn.add_stream(stage_1_fuel_obj.amount, 'LiquidFuel')


    log_and_print(f"Stage 2 Fuel: {stage_2_fuel()}")
    log_and_print(f"Stage 1 Fuel: {stage_1_fuel()}")


    # Engage Autopilot and set heading
    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(90, 90)

    log_and_print("Wait 5 seconds to launch...")
    time.sleep(5)
    log_and_print("Launching...")
    vessel.control.activate_next_stage()


    mission.wait_for(surface_altitude, '>', 2000)
    vessel.auto_pilot.target_pitch_and_heading(70, 90)
    mission.wait_for(surface_altitude, '>', 5000)
    vessel.auto_pilot.target_pitch_and_heading(45, 90)

    log_and_print("Wait for fuel to run out")
    mission.wait_for(stage_2_fuel, '==', 0)

    vessel.control.activate_next_stage()
    log_and_print(f"Wait for apoapsis to exceed 80000km")
    mission.wait_for(apoapsis, '>', 80000)
    log_and_print(f"Apoapsis is {apoapsis()}. Rotate to Horizon and Cut Throttle")
    vessel.auto_pilot.target_pitch_and_heading(0, 90)
    vessel.control.throttle = 0

    delta_v_to_circularize = calc_circularization_delta_v(vessel)
    log_and_print(f"Need delta v of {delta_v_to_circularize} m/s to circularize")
    time_to_burn = burn_time(vessel, delta_v_to_circularize)
    log_and_print(f"Burn time to circularize is {time_to_burn}")

    log_and_print(f"Wait for time to apoapsis to reach {time_to_burn / 2} seconds")
    time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
    mission.wait_for(time_to_apoapsis, '<', (time_to_burn / 2))
    log_and_print(f"Throttle back up")
    vessel.control.throttle = 1

    mission.wait_for(periapsis, '>', 70000)
    log_and_print("Cut throttle and rotate...")
    vessel.control.throttle = 0
    vessel.auto_pilot.target_pitch_and_heading(0, 270)

    input("Press enter when ready to de-orbit...")

    log_and_print(f"Run Science Experiments")
    run_all_science_experiments(vessel)

    time.sleep(1)

    vessel.control.throttle = 1
    mission.wait_for(stage_1_fuel, '==', 0)

    time.sleep(1)
    log_and_print("Ditch the empty tank...")
    vessel.control.activate_next_stage()

    log_and_print("Disengage auto-pilot")
    vessel.auto_pilot.disengage()


    mission.wait_for(surface_altitude, '<', 3000)

    log_and_print("Deploying Parachute(s).")
    try:
        for parachute in vessel.parts.parachutes:
            parachute.deploy()
    except:
        log_and_print("No Parachutes on Board")

    time.sleep(3)
    time_warp_to_land(conn, vessel)

    log_and_print("Wait for vessel to reach the ground")
    mission.wait_for(surface_altitude, '<=', 10)

def time_warp_to_land(mission, recover=False):
    vessel = mission.vessel
    if vessel.parts.parachutes[0].state.name == "active" or vessel.parts.parachutes[0].state.name == "semi_deployed":
        pass
    else:
        assert False, f"Parachute state is {vessel.parts.parachutes[0].state.name}"
    space_center = conn.space_center
    space_center.physics_warp_factor = 3

    surface_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')

    log_and_print("Waiting until landing...")
    mission.wait_for("surface_altitude", '<=', 100)
    space_center.physics_warp_factor = 0

    if recover:
        while not vessel.recoverable:
            time.sleep(1)

        if vessel.recoverable:
            time.sleep(10)
            vessel.recover()

    return True

def run_all_science_experiments(vessel):
    for part in vessel.parts.with_module('ModuleScienceExperiment'):
        part.experiment.run()

def calc_circularization_delta_v(vessel):
    # Plan circularization burn (using vis-viva equation)
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    return delta_v

def burn_time(vessel, delta_v):
    F = vessel.available_thrust
    Isp = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v/Isp)
    flow_rate = F / Isp
    burn_time = (m0 - m1) / flow_rate

    return burn_time


if __name__ == "__main__":
    result = run_preflight_tests()
    if result == PytestExitCodes.ALL_PASSING:
        log_and_print("Ready to Launch!")
        print("Ready to Launch!")
    else:
        exit(1)
    conn = krpc.connect(name="Connection",address='192.168.0.11',rpc_port=5000,stream_port=5001)
    vessel = conn.space_center.active_vessel
    mission = MissionData(conn, vessel)
    #run_all_science_experiments(vessel)
    #N_burn_stage(mission)
    single_burn_stage(mission)
