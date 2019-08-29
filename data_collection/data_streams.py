import krpc
import time
import math
from kRPC_Automation.log_setup import logger
import operator

expression_shorthand = {
    "<" : operator.lt,
    "<=": operator.le,
    ">" : operator.gt,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
    "+" : operator.add,
    "-" : operator.sub,
    "*" : operator.mul,
    "/" : operator.truediv,
    "%" : operator.mod,
    "^" : operator.pow,
}

def log_and_print(message):
    logger.info(message)
    print(message)

class MissionData:
    def __init__(self, conn, vessel):
        self.conn = conn
        self.vessel = vessel
        # Universal Time
        self.ut = conn.add_stream(getattr, conn.space_center, 'ut')

        # Flight Data
        self.surface_altitude = conn.add_stream(getattr, vessel.flight(), 'surface_altitude')
        self.mean_altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
        self.latitude = conn.add_stream(getattr, vessel.flight(), 'latitude')
        self.longitude = conn.add_stream(getattr, vessel.flight(), 'longitude')
        self.velocity = conn.add_stream(getattr, vessel.flight(), 'velocity')
        self.direction = conn.add_stream(getattr, vessel.flight(), 'direction')
        self.prograde = conn.add_stream(getattr, vessel.flight(), 'prograde')
        self.retrograde = conn.add_stream(getattr, vessel.flight(), 'retrograde')

        # Orbit Data
        self.apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
        self.periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
        self.semi_major_axis = conn.add_stream(getattr, vessel.orbit, 'semi_major_axis')
        self.orbital_speed = conn.add_stream(getattr, vessel.orbit, 'orbital_speed')
        self.orbital_period = conn.add_stream(getattr, vessel.orbit, 'period')
        self.time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
        self.time_to_periapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_periapsis')

        # Resource Data
        self.fuel_amount = {}
        self.fuel_amount['LiquidFuel'] = conn.add_stream(vessel.resources.amount, 'LiquidFuel')
        self.fuel_amount['SolidFuel'] = conn.add_stream(vessel.resources.amount, 'SolidFuel')

        self.set_get_stage_fuels()

    def set_get_stage_fuels(self):
        self.current_stage = self.vessel.control.current_stage - 1
        self.n_stages = self.vessel.control.current_stage
        self.current_stage_resources = self.vessel.resources_in_decouple_stage(stage=self.current_stage, cumulative=False)

        self.current_stage_solidfuel = self.conn.add_stream(self.current_stage_resources.amount, 'SolidFuel')
        self.current_stage_liquidfuel = self.conn.add_stream(self.current_stage_resources.amount, 'LiquidFuel')

    def wait_for(self, stream_name, expr_symbol, value_waiting_for, changing_value=False, factor=1):
        try:
            stream = getattr(self, stream_name)
        except:
            log_and_print(f"{stream_name} data stream not available")
            return False
        eval_func = expression_shorthand[expr_symbol]
        count = 0
        if changing_value:
            target_value = factor * value_waiting_for()
        else:
            target_value = factor * value_waiting_for

        prev_value = target_value
        time_to_sleep = 1
        log_and_print(f"Waiting for {stream_name} {expr_symbol} {target_value} (changing: {changing_value}) (currently: {stream()})")
        while eval_func(stream(), target_value) is not True:
            if changing_value:
                log_and_print(f"Waiting for {stream_name} {expr_symbol} {target_value} (changing: {changing_value}) (currently: {stream()})")
                count += 1
                log_and_print(f"sleep for 1 second and see change")
                time.sleep(time_to_sleep)
                target_value = factor * value_waiting_for()
                if count == 1:
                    time_to_sleep = .1 * math.fabs((target_value-stream()) / (target_value - prev_value))
                    log_and_print(f"set sleep interval to {time_to_sleep} seconds")

        return True

    def activate_stage(self):
        self.vessel.control.activate_next_stage()
        self.set_get_stage_fuels()
        print("Fuel Amounts (Total):\n", self.fuel_amount['LiquidFuel'](), self.fuel_amount['SolidFuel']())
        print("Solid Fuel (current stage):\n", self.current_stage_solidfuel())
        print("Liquid Fuel (current stage):\n", self.current_stage_liquidfuel())



if __name__ == "__main__":
    pass
