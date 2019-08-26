import time
import krpc
import pytest
import sys

sys.path.append(r"C:\Users\samue")

from kRPC_Automation.log_setup import logger
from kRPC_Automation.tests.test_runner import test_runner, PytestExitCodes
from kRPC_Automation.data_collection.data_streams import stream_value, wait_for, log_and_print



def run_preflight_tests():
    preflight_tests_path = r"C:\Users\samue\kRPC_Automation\tests\preflight\preflight_tests.py"
    preflight_check = test_runner(preflight_tests_path)
    return preflight_check

def single_burn_stage(conn, vessel, manned=True):
    success = False
    if vessel.situation.name != "pre_launch":
        return False

    # Set up telemetry streams
    ut = conn.add_stream(getattr, conn.space_center, 'ut')
    surface_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
    mean_altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
    stage_2_fuel_obj = vessel.resources_in_decouple_stage(2, cumulative = False)
    stage_2_fuel = conn.add_stream(stage_2_fuel_obj.amount, 'LiquidFuel')

    log_and_print(f"Stage 2 Fuel: {stage_2_fuel()}")
    log_and_print(f"Stage 2 Fuel: {stage_2_fuel()}")

    log_and_print("Wait 5 seconds to launch...")

    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(88, 90)

    log_and_print("Wait 5 seconds to launch...")
    time.sleep(5)
    log_and_print("Launching...")

    vessel.control.activate_next_stage()

    log_and_print("Wait for surface altitude to reach 2000")
    wait_for(surface_altitude, '>', 2000)
    vessel.auto_pilot.target_pitch_and_heading(65, 90)
    log_and_print("Wait for surface altitude to reach 5000")
    wait_for(surface_altitude, '>', 5000)
    vessel.auto_pilot.target_pitch_and_heading(45, 90)

    log_and_print("Wait for fuel to run out")
    wait_for(stage_2_fuel, '==', 0)

    time.sleep(1)
    log_and_print("Ditch the empty tank...")
    vessel.control.activate_next_stage()

    log_and_print("Disengage auto-pilot")
    vessel.auto_pilot.disengage()

    log_and_print(f"Wait for vessel to reach apoapsis: (apoapsis())")
    wait_for(surface_altitude, '>', apoapsis, changing_value=True, factor=0.8)



    log_and_print(f"Height - {apoapsis()} reached. Run Science Experiments")
    run_all_science_experiments(vessel)

    log_and_print("Wait for vessel to reach 3000 m above ground")
    wait_for(surface_altitude, '<=', 3000)

    log_and_print("Deploying Parachute(s).")
    try:
        for parachute in vessel.parts.parachutes:
            parachute.deploy()
    except:
        log_and_print("No Parachutes on Board")

    time.sleep(3)
    time_warp_to_land(conn, vessel)

    log_and_print("Wait for vessel to reach the ground")
    wait_for(surface_altitude, '<=', 10)

def N_burn_stage(conn, vessel, manned=True, N_burn_stages=2):
    success = False
    if vessel.situation.name != "pre_launch":
        return False

    # Set up telemetry streams
    ut = conn.add_stream(getattr, conn.space_center, 'ut')
    surface_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
    mean_altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
    apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
    periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
    stage_2_fuel_obj = vessel.resources_in_decouple_stage(2, cumulative = False)
    stage_2_fuel = conn.add_stream(stage_2_fuel_obj.amount, 'LiquidFuel')
    stage_1_fuel_obj = vessel.resources_in_decouple_stage(1, cumulative = False)
    stage_1_fuel = conn.add_stream(stage_1_fuel_obj.amount, 'LiquidFuel')

    log_and_print(f"Stage 2 Fuel: {stage_2_fuel()}")
    log_and_print(f"Stage 1 Fuel: {stage_1_fuel()}")

    # Engage Autopilot and set heading
    vessel.auto_pilot.engage()
    vessel.auto_pilot.target_pitch_and_heading(90, 90)

    log_and_print("Wait 5 seconds to launch...")
    time.sleep(5)
    log_and_print("Launching...")

    log_and_print("Wait for surface altitude to reach 2000")
    wait_for(surface_altitude, '>', 2000)
    vessel.auto_pilot.target_pitch_and_heading(70, 90)
    log_and_print("Wait for surface altitude to reach 10000")
    wait_for(surface_altitude, '>', 5000)
    vessel.auto_pilot.target_pitch_and_heading(45, 90)

    log_and_print("Wait for fuel to run out")
    wait_for(stage_2_fuel, '==', 0)

    log_and_print(f"Wait for vessel to reach apoapsis: (apoapsis())")
    wait_for(mean_altitude, '>', apoapsis, changing_value=True, factor=0.8)
    log_and_print(f"Set heading to horizon and activate activate next stage")
    vessel.auto_pilot.target_pitch_and_heading(0, 90)
    vessel.control.activate_next_stage()

    log_and_print("Wait for periapsis alt to exceed 70km")
    wait_for(periapsis, '>', 70000)
    time.sleep(1)
    log_and_print("Cut throttle and rotate...")
    vessel.control.throttle = 0
    vessel.auto_pilot.target_pitch_and_heading(0, 270)

    input("Press enter when ready to de-orbit...")

    log_and_print(f"Run Science Experiments")
    run_all_science_experiments(vessel)

    time.sleep(1)

    vessel.control.throttle = 1
    log_and_print("Wait for fuel to run out")
    wait_for(stage_1_fuel, '==', 0)

    time.sleep(1)
    log_and_print("Ditch the empty tank...")
    vessel.control.activate_next_stage()

    log_and_print("Disengage auto-pilot")
    vessel.auto_pilot.disengage()


    log_and_print("Wait for vessel to reach 3000 m above ground")
    wait_for(surface_altitude, '<', 3000)

    log_and_print("Deploying Parachute(s).")
    try:
        for parachute in vessel.parts.parachutes:
            parachute.deploy()
    except:
        log_and_print("No Parachutes on Board")

    time.sleep(3)
    time_warp_to_land(conn, vessel)

    log_and_print("Wait for vessel to reach the ground")
    wait_for(surface_altitude, '<=', 10)

def time_warp_to_land(conn, vessel, recover=False):
    if vessel.parts.parachutes[0].state.name == "active" or vessel.parts.parachutes[0].state.name == "semi_deployed":
        pass
    else:
        assert False, f"Parachute state is {vessel.parts.parachutes[0].state.name}"
    space_center = conn.space_center
    space_center.physics_warp_factor = 3

    surface_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')

    log_and_print("Waiting until landing...")
    wait_for(surface_altitude, '<=', 100)
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


if __name__ == "__main__":
    result = run_preflight_tests()
    if result == PytestExitCodes.ALL_PASSING:
        log_and_print("Ready to Launch!")
        print("Ready to Launch!")
    else:
        exit(1)
    conn = krpc.connect(name="Connection",address='192.168.0.11',rpc_port=5000,stream_port=5001)
    vessel = conn.space_center.active_vessel
    #run_all_science_experiments(vessel)
    single_burn_stage(conn, vessel, 'SolidFuel')
